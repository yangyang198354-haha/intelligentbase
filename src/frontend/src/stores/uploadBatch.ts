/**
 * @module MOD-014
 * @implements 批量上传批次状态机（计划 → 冲突确认 → 逐文件上传 → 汇总）；消费 IFC-025 的
 *             `planUpload` / `uploadBatchItem` / `getUploadBatch`
 * @author software-developer
 *
 * 与 `stores/project.ts` 同构（模块级 `reactive` 工厂，不引入 Pinia）。
 *
 * ## 要点
 *
 * * **并发固定为 2**（REQ-NFUNC-006）：逐文件 `PUT`，单文件失败只影响该项（REQ-NFUNC-007）。
 * * **计划先行**：先 `dry_run` 取限额错误 / 同名冲突，用户选择后才提交批次；关闭冲突弹窗而未选择 =
 *   取消整次上传（此时只做过 dry_run，服务端无任何变化，AC-011-04）。
 * * **进度单调不减**：`processed` 含计划期跳过项；每个条目至多计一次（重试失败项不重复计数）。
 * * **页面刷新恢复**：只把 `batch_id` 存进 `sessionStorage`（不落 `localStorage`），刷新后用
 *   `getUploadBatch` 取汇总；浏览器无法保留 `File` 对象，故未上传的项需要用户重新选择。
 */

import { reactive } from 'vue';

import {
  ApiClientError,
  type ApiClient,
  type ConflictActionTs,
  type ConflictInfo,
  type UploadPlanResponse,
} from '../api/client';

export const UPLOAD_CONCURRENCY = 2;
const BATCH_KEY = 'ib_upload_batch';

export type UploadPhase = 'idle' | 'planning' | 'conflict' | 'uploading' | 'done' | 'error';
export type RowState = 'planned' | 'accepted' | 'skipped' | 'failed';

export interface UploadRow {
  client_idx: number;
  rel_path: string;
  state: RowState;
  reason_code: string | null;
}

export interface UploadBatchState {
  phase: UploadPhase;
  message: string;
  batchId: string;
  total: number;
  processed: number;
  rows: UploadRow[];
  conflicts: ConflictInfo[];
  /** 页面刷新后恢复的汇总：无 File 对象，不能继续上传。 */
  restored: boolean;
}

/** 跳过 / 失败原因码 → 中文（未知码原样显示，不吞）。 */
export const REASON_LABEL: Record<string, string> = {
  UNSUPPORTED_TYPE: '不支持的文件类型',
  EMPTY_FILE: '文件为空',
  TOO_LARGE: '超出单文件大小上限',
  NAME_INVALID: '名称不合法',
  USER_SKIPPED: '已按你的选择跳过',
  CONFLICT_UNRESOLVED: '同名冲突未处理',
  MAGIC_MISMATCH: '文件内容与扩展名不符',
  SIZE_MISMATCH: '实际大小与声明不符',
  NAME_CONFLICT: '同名冲突',
  CONTENT_UNCHANGED: '内容未变化',
  DOC_BUSY: '该文件正在处理中',
  DEPTH_EXCEEDED: '目录层级超出上限',
  TARGET_MISSING: '目标已不存在',
  INVALID_FILE: '文件不合法',
  SERVER_ERROR: '服务暂时不可用，可重试',
  NETWORK: '网络异常，可重试',
};

function describeLimit(err: ApiClientError): string {
  const raw = err.details?.details as { limit?: number; actual?: number } | undefined;
  const mb = (n: number) => `${(n / 1024 / 1024).toFixed(0)} MB`;
  if (err.code === 'limit_files' && raw?.limit !== undefined) {
    return `单次最多上传 ${raw.limit} 个文件（当前 ${raw.actual ?? '?'}）`;
  }
  if (err.code === 'limit_total_bytes' && raw?.limit !== undefined) {
    return `单次上传总大小超过上限（当前 ${mb(raw.actual ?? 0)}，上限 ${mb(raw.limit)}）`;
  }
  if (err.code === 'depth_exceeded' && raw?.limit !== undefined) {
    return `目录层级最多 ${raw.limit} 层`;
  }
  return err.message;
}

export function createUploadBatch(api: ApiClient) {
  const state = reactive<UploadBatchState>({
    phase: 'idle',
    message: '',
    batchId: '',
    total: 0,
    processed: 0,
    rows: [],
    conflicts: [],
    restored: false,
  });

  let files: File[] = [];
  let targetFolderId = '';
  let resolutions: Record<string, ConflictActionTs> = {};
  const counted = new Set<number>();

  function relPathOf(file: File): string {
    return (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
  }

  function reset(): void {
    files = [];
    resolutions = {};
    counted.clear();
    state.phase = 'idle';
    state.message = '';
    state.batchId = '';
    state.total = 0;
    state.processed = 0;
    state.rows = [];
    state.conflicts = [];
    state.restored = false;
    sessionStorage.removeItem(BATCH_KEY);
  }

  function fail(err: unknown): void {
    state.phase = 'error';
    if (err instanceof ApiClientError) {
      if (err.status === 409 && err.conflicts.length) {
        state.conflicts = err.conflicts;
        state.phase = 'conflict';
        return;
      }
      state.message = err.status === 403 ? '当前令牌无管理权限，无法上传。' : describeLimit(err);
      return;
    }
    state.message = '无法连接服务，请确认后端已启动。';
  }

  async function plan(): Promise<void> {
    const entries = files.map((f, i) => ({ client_idx: i, rel_path: relPathOf(f), size: f.size }));
    try {
      const preview = await api.planUpload({
        target_folder_id: targetFolderId,
        dry_run: true,
        entries,
        resolutions,
      });
      if (preview.conflicts.length) {
        state.conflicts = preview.conflicts.map((c) => ({
          rel_path: c.rel_path,
          existing: { kind: c.kind, id: c.existing_id, name: c.existing_name },
        }));
        state.phase = 'conflict';
        return;
      }
      const committed = await api.planUpload({
        target_folder_id: targetFolderId,
        dry_run: false,
        entries,
        resolutions,
      });
      await startUploading(committed);
    } catch (err) {
      fail(err);
    }
  }

  async function startUploading(committed: UploadPlanResponse): Promise<void> {
    state.batchId = committed.batch_id ?? '';
    state.total = committed.total;
    state.rows = committed.items.map((item) => ({
      client_idx: item.client_idx,
      rel_path: item.rel_path,
      state: item.action === 'skip' ? 'skipped' : 'planned',
      reason_code: item.reason_code,
    }));
    counted.clear();
    state.rows.filter((r) => r.state === 'skipped').forEach((r) => counted.add(r.client_idx));
    state.processed = counted.size;
    state.conflicts = [];
    state.phase = 'uploading';
    if (state.batchId) sessionStorage.setItem(BATCH_KEY, state.batchId);
    await drain(state.rows.filter((r) => r.state === 'planned').map((r) => r.client_idx));
  }

  async function sendOne(idx: number): Promise<void> {
    const row = state.rows.find((r) => r.client_idx === idx);
    if (!row) return;
    try {
      const res = await api.uploadBatchItem(state.batchId, idx, files[idx]);
      row.state = res.state;
      row.reason_code = res.reason_code;
    } catch (err) {
      row.state = 'failed';
      row.reason_code =
        err instanceof ApiClientError && err.status === 503 ? 'SERVER_ERROR' : err instanceof ApiClientError ? err.code : 'NETWORK';
    }
    if (!counted.has(idx)) {
      counted.add(idx);
      state.processed = counted.size;
    }
  }

  async function drain(queue: number[]): Promise<void> {
    const pending = [...queue];
    const worker = async (): Promise<void> => {
      for (let idx = pending.shift(); idx !== undefined; idx = pending.shift()) {
        await sendOne(idx);
      }
    };
    await Promise.all(Array.from({ length: UPLOAD_CONCURRENCY }, worker));
    state.phase = 'done';
    try {
      const summary = await api.getUploadBatch(state.batchId);
      // 以服务端为准校准终态（本地只可能少记，不会多记）
      for (const item of summary.items) {
        const row = state.rows.find((r) => r.client_idx === item.client_idx);
        if (row && item.state !== 'planned') {
          row.state = item.state;
          row.reason_code = item.reason_code;
        }
      }
    } catch {
      /* 汇总校准失败不影响已有结果 */
    }
  }

  return {
    state,
    /** 选择文件后开始：先 dry_run 计划，再按需弹冲突，最后提交批次并上传。 */
    async begin(picked: File[], folderId: string): Promise<void> {
      reset();
      files = picked;
      targetFolderId = folderId;
      state.phase = 'planning';
      await plan();
    },
    /** 冲突弹窗确认后继续（键 = 冲突的 rel_path）。 */
    async resolveConflicts(chosen: Record<string, ConflictActionTs>): Promise<void> {
      resolutions = { ...resolutions, ...chosen };
      state.phase = 'planning';
      await plan();
    },
    /** 取消整次上传（弹窗关闭未选择 / 用户主动关闭）。 */
    cancel(): void {
      reset();
    },
    /** 重试失败项（服务端按 client_idx 幂等）。 */
    async retryFailed(): Promise<void> {
      if (state.restored || !state.batchId) return;
      const queue = state.rows.filter((r) => r.state === 'failed').map((r) => r.client_idx);
      if (!queue.length) return;
      state.phase = 'uploading';
      await drain(queue);
    },
    /** 页面刷新后用 sessionStorage 里的 batch_id 取汇总（仅展示）。 */
    async restore(): Promise<void> {
      const id = sessionStorage.getItem(BATCH_KEY);
      if (!id || state.phase !== 'idle') return;
      try {
        const summary = await api.getUploadBatch(id);
        state.batchId = id;
        state.total = summary.total;
        state.rows = summary.items.map((i) => ({
          client_idx: i.client_idx,
          rel_path: i.rel_path,
          state: i.state,
          reason_code: i.reason_code,
        }));
        state.processed = summary.total - summary.pending;
        state.restored = true;
        state.phase = 'done';
        state.message = summary.pending
          ? `页面刷新前的上传尚有 ${summary.pending} 项未完成，请重新选择这些文件上传。`
          : '';
      } catch {
        sessionStorage.removeItem(BATCH_KEY);
      }
    },
  };
}

export type UploadBatchStore = ReturnType<typeof createUploadBatch>;
