<script setup lang="ts">
/**
 * @module MOD-014
 * @implements 云盘式资料浏览与管理（REQ-FUNC-003 / 004 / 005 / 006 / 008 / 009 / 012 / 013）
 * @author software-developer
 *
 * 当前目录列表（文件夹在前）、面包屑与"返回上级"、分页（<=100/页）、新建文件夹、重命名、
 * 移动（目标目录选择）、更新（覆盖内容）、删除入口；显示 `uploaded_at / content_updated_at /
 * indexed_at`（本地时区到秒，`—` 表示无）；`permissions.can_manage` 为假时隐藏全部写操作。
 *
 * HTTP 只经 `props.client`（`api/client.ts`）；更新成功（202）后整表重新 `browse`（`doc_id` 会变，A-06）。
 * 仅在存在"处理中 / 更新中"的条目时轮询（2s），全部落定后自动停止。
 */
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';

import {
  ApiClientError,
  type ApiClient,
  type ConflictActionTs,
  type ConflictInfo,
  type FileItem,
  type FolderItem,
  type LibraryPage,
} from '../../api/client';
import ConflictDialog from './ConflictDialog.vue';
import FolderDeleteDialog from './FolderDeleteDialog.vue';
import UploadBatchPanel from './UploadBatchPanel.vue';

const props = defineProps<{ client: ApiClient }>();
const emit = defineEmits<{ (e: 'unauthorized'): void }>();

const PAGE_SIZE = 50;
const STATUS_LABEL: Record<FileItem['status'], string> = {
  pending: '排队中',
  parsing: '解析中',
  indexed: '已入库',
  failed: '失败',
};

const data = ref<LibraryPage | null>(null);
const folderId = ref('');
const page = ref(1);
const loading = ref(false);
const error = ref('');
const notice = ref('');
const busyKey = ref('');

const selected = reactive<Record<string, boolean>>({});
const renaming = ref<{ kind: 'file' | 'folder'; id: string; name: string } | null>(null);
const newFolderName = ref('');
const showNewFolder = ref(false);
const deleting = ref<{ id: string; name: string } | null>(null);

// 更新（覆盖内容）：隐藏的文件选择框 + 冲突弹窗
const updateInput = ref<HTMLInputElement | null>(null);
let updateTarget: FileItem | null = null;
type PendingConflict = {
  mode: 'move' | 'update';
  conflicts: ConflictInfo[];
  resume: (resolutions: Record<string, ConflictActionTs>) => Promise<void>;
};
const pendingConflict = ref<PendingConflict | null>(null);

// 移动：目标目录选择器
const moving = ref<{ entries: { kind: 'file' | 'folder'; id: string }[]; excluded: string[] } | null>(null);
const moveData = ref<LibraryPage | null>(null);
const moveFolderId = ref('');

const canManage = computed(() => data.value?.permissions.can_manage === true);
const folders = computed(() => (data.value?.items ?? []).filter((i): i is FolderItem => i.kind === 'folder'));
const files = computed(() => (data.value?.items ?? []).filter((i): i is FileItem => i.kind === 'file'));
const totalPages = computed(() => Math.max(1, Math.ceil((data.value?.total ?? 0) / PAGE_SIZE)));
const hasInFlight = computed(() =>
  files.value.some((f) => f.status === 'pending' || f.status === 'parsing' || f.update_state === 'updating'),
);
const selectedEntries = computed(() => {
  const out: { kind: 'file' | 'folder'; id: string }[] = [];
  for (const f of folders.value) if (selected[`folder:${f.folder_id}`]) out.push({ kind: 'folder', id: f.folder_id });
  for (const f of files.value) if (selected[`file:${f.doc_id}`]) out.push({ kind: 'file', id: f.doc_id });
  return out;
});

let pollTimer: number | null = null;
function stopPolling(): void {
  if (pollTimer !== null) {
    window.clearTimeout(pollTimer);
    pollTimer = null;
  }
}
function schedulePoll(): void {
  stopPolling();
  if (!hasInFlight.value) return;
  pollTimer = window.setTimeout(async () => {
    await load(true);
    schedulePoll();
  }, 2000);
}
watch(hasInFlight, (value) => (value ? schedulePoll() : stopPolling()));
onBeforeUnmount(stopPolling);

const CODE_TEXT: Record<string, string> = {
  name_empty: '名称不能为空。',
  name_illegal_char: '名称不能包含 / 或 \\，也不能是 . 或 ..。',
  name_too_long: '名称过长（上限 255 个字符）。',
  name_conflict: '同目录下已存在同名条目（不区分大小写）。',
  depth_exceeded: '目录层级已达上限。',
  move_into_self: '不能移动到自身或其子目录。',
  ext_change_not_allowed: '不允许修改文件扩展名。',
  doc_busy: '该文件正在处理中，暂不能更新。',
  update_in_progress: '该文件正在更新中。',
};

function describe(err: unknown): string {
  if (err instanceof ApiClientError) {
    if (err.status === 401) {
      emit('unauthorized');
      return '登录状态已失效，请重新填写访问令牌。';
    }
    if (err.status === 403) return '当前令牌无管理权限，或无权操作该项目。';
    if (err.status === 404) return '目标不存在，或不在当前项目内。';
    return CODE_TEXT[err.code] ?? err.message;
  }
  return '无法连接服务，请确认后端已启动（waitress 监听 127.0.0.1:18080）。';
}

function clearSelection(): void {
  for (const key of Object.keys(selected)) delete selected[key];
}

async function load(silent = false): Promise<void> {
  if (!silent) loading.value = true;
  try {
    data.value = await props.client.browse({ folder_id: folderId.value, page: page.value, page_size: PAGE_SIZE });
    if (!silent) error.value = '';
  } catch (err) {
    if (err instanceof ApiClientError && err.status === 404 && folderId.value) {
      folderId.value = ''; // 当前目录已被删除：回到根
      page.value = 1;
      await load(silent);
      return;
    }
    error.value = describe(err);
  } finally {
    loading.value = false;
  }
}

async function reload(): Promise<void> {
  await load();
  schedulePoll();
}

function enter(id: string): void {
  folderId.value = id;
  page.value = 1;
  clearSelection();
  notice.value = '';
  void reload();
}

function goUp(): void {
  const crumbs = data.value?.breadcrumb ?? [];
  enter(crumbs.length >= 2 ? crumbs[crumbs.length - 2].folder_id : '');
}

function turnPage(delta: number): void {
  page.value = Math.min(totalPages.value, Math.max(1, page.value + delta));
  void reload();
}

async function guarded(key: string, action: () => Promise<void>): Promise<void> {
  busyKey.value = key;
  error.value = '';
  notice.value = '';
  try {
    await action();
  } catch (err) {
    error.value = describe(err);
  } finally {
    busyKey.value = '';
  }
}

// ---- 新建文件夹 / 重命名 ----
async function createFolder(): Promise<void> {
  const name = newFolderName.value;
  await guarded('new-folder', async () => {
    await props.client.createFolder(folderId.value, name);
    newFolderName.value = '';
    showNewFolder.value = false;
    await reload();
  });
}

function startRename(kind: 'file' | 'folder', id: string, name: string): void {
  renaming.value = { kind, id, name };
}

async function submitRename(): Promise<void> {
  const target = renaming.value;
  if (!target) return;
  await guarded(`${target.kind}:${target.id}`, async () => {
    if (target.kind === 'folder') await props.client.renameFolder(target.id, target.name);
    else await props.client.renameFile(target.id, target.name);
    renaming.value = null;
    await reload();
  });
}

// ---- 删除 / 重试 ----
async function removeFile(file: FileItem): Promise<void> {
  if (!window.confirm(`确认删除「${file.name}」？其向量与原文将一并清除，不可恢复。`)) return;
  await guarded(`file:${file.doc_id}`, async () => {
    await props.client.deleteFile(file.doc_id);
    await reload();
  });
}

async function retryFile(file: FileItem): Promise<void> {
  await guarded(`file:${file.doc_id}`, async () => {
    await props.client.retryFile(file.doc_id);
    await reload();
  });
}

async function discardUpdate(file: FileItem): Promise<void> {
  await guarded(`file:${file.doc_id}`, async () => {
    await props.client.discardRevision(file.doc_id);
    await reload();
  });
}

function onDeleteClosed(changed: boolean): void {
  deleting.value = null;
  if (changed) {
    clearSelection();
    void reload();
  }
}

// ---- 更新（覆盖内容）----
function startUpdate(file: FileItem): void {
  updateTarget = file;
  updateInput.value?.click();
}

async function onUpdatePicked(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const picked = input.files?.[0] ?? null;
  input.value = '';
  const target = updateTarget;
  if (!picked || !target) return;
  await guarded(`file:${target.doc_id}`, async () => {
    await runUpdate(target, picked);
  });
}

async function runUpdate(target: FileItem, picked: File): Promise<void> {
  try {
    const result = await props.client.updateFile(target.doc_id, picked);
    if (result.changed) notice.value = `已提交更新，将重新索引为「${result.final_name}」；完成前旧版本仍可检索。`;
    else notice.value = '内容未变化，未重新索引。';
    await reload();
  } catch (err) {
    if (err instanceof ApiClientError && err.status === 409 && err.code === 'name_conflict' && err.conflicts.length) {
      // 新文件名与同目录另一条目 Y 同名：覆盖 = 用新文件更新 Y（X 不变）；两者都保留 = X 更新并自动改名
      pendingConflict.value = {
        mode: 'update',
        conflicts: err.conflicts,
        resume: async (resolutions) => {
          const choice = resolutions[target.doc_id] ?? 'skip';
          const existing = err.conflicts[0].existing;
          if (choice === 'skip') return;
          await guarded(`file:${target.doc_id}`, async () => {
            if (choice === 'overwrite') {
              if (existing.kind !== 'file') throw new ApiClientError({ status: 400, code: 'bad_request', message: '不能用文件覆盖同名文件夹，请选择跳过或两者都保留。' });
              const res = await props.client.updateFile(existing.id, picked);
              notice.value = res.changed ? '已用新文件更新同名文件，重新索引中。' : '内容未变化，未重新索引。';
            } else {
              const res = await props.client.updateFile(target.doc_id, picked, 'rename');
              notice.value = res.changed ? '已提交更新，显示名已自动改名。' : '内容未变化，未重新索引。';
            }
            await reload();
          });
        },
      };
      return;
    }
    throw err;
  }
}

// ---- 移动 ----
function startMove(entries: { kind: 'file' | 'folder'; id: string }[]): void {
  if (!entries.length) return;
  moving.value = { entries, excluded: entries.filter((e) => e.kind === 'folder').map((e) => e.id) };
  void loadMoveTarget('');
}

async function loadMoveTarget(id: string): Promise<void> {
  moveFolderId.value = id;
  try {
    moveData.value = await props.client.browse({ folder_id: id, page: 1, page_size: 100 });
  } catch (err) {
    error.value = describe(err);
  }
}

const moveFolders = computed(() =>
  (moveData.value?.items ?? []).filter(
    (i): i is FolderItem => i.kind === 'folder' && !(moving.value?.excluded ?? []).includes(i.folder_id),
  ),
);

async function confirmMove(resolutions?: Record<string, ConflictActionTs>): Promise<void> {
  const job = moving.value;
  if (!job) return;
  const target = moveFolderId.value;
  await guarded('move', async () => {
    try {
      const res = await props.client.moveEntries({ entries: job.entries, target_folder_id: target, resolutions });
      moving.value = null;
      clearSelection();
      notice.value = `已移动 ${res.moved.length} 项${res.skipped.length ? `，跳过 ${res.skipped.length} 项` : ''}。`;
      await reload();
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 409 && err.conflicts.length) {
        pendingConflict.value = {
          mode: 'move',
          conflicts: err.conflicts,
          resume: (chosen) => confirmMove({ ...(resolutions ?? {}), ...chosen }),
        };
        return;
      }
      throw err;
    }
  });
}

async function onConflictConfirm(resolutions: Record<string, ConflictActionTs>): Promise<void> {
  const pending = pendingConflict.value;
  pendingConflict.value = null;
  if (pending) await pending.resume(resolutions);
}

// ---- 展示 ----
function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

// 后端返回 UTC ISO，界面按本地时区显示为 yyyy-mm-dd hh:mm:ss；无值显示 —。
function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

onMounted(reload);
</script>

<template>
  <div class="browser">
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>

    <UploadBatchPanel v-if="canManage" :client="client" :target-folder-id="folderId" @finished="reload" />

    <nav class="crumbs" aria-label="当前位置">
      <button type="button" class="link" :disabled="!folderId" @click="enter('')">根目录</button>
      <template v-for="crumb in data?.breadcrumb ?? []" :key="crumb.folder_id">
        <span class="sep">/</span>
        <button type="button" class="link" @click="enter(crumb.folder_id)">{{ crumb.name }}</button>
      </template>
      <button v-if="folderId" type="button" class="ghost up" @click="goUp">返回上级</button>
    </nav>

    <div class="toolbar">
      <template v-if="canManage">
        <button v-if="!showNewFolder" type="button" class="ghost" @click="showNewFolder = true">新建文件夹</button>
        <form v-else class="inline" @submit.prevent="createFolder">
          <input v-model="newFolderName" type="text" maxlength="255" placeholder="文件夹名称" aria-label="文件夹名称" />
          <button type="submit" :disabled="busyKey === 'new-folder'">创建</button>
          <button type="button" class="ghost" @click="showNewFolder = false">取消</button>
        </form>
        <button type="button" class="ghost" :disabled="!selectedEntries.length" @click="startMove(selectedEntries)">
          移动所选（{{ selectedEntries.length }}）
        </button>
      </template>
      <button type="button" class="ghost" :disabled="loading" @click="reload">刷新</button>
      <span class="hint">
        共 {{ data?.total ?? 0 }} 项{{ hasInFlight ? '（处理中，自动刷新）' : '' }}
      </span>
    </div>

    <input ref="updateInput" type="file" accept=".pdf,.txt,.md,.markdown,.docx" hidden @change="onUpdatePicked" />

    <table>
      <thead>
        <tr>
          <th v-if="canManage" class="check"></th>
          <th>名称</th>
          <th>大小</th>
          <th>状态</th>
          <th>上传时间</th>
          <th>最近更新</th>
          <th>索引成功</th>
          <th v-if="canManage">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="folder in folders" :key="`d-${folder.folder_id}`">
          <td v-if="canManage" class="check">
            <input v-model="selected[`folder:${folder.folder_id}`]" type="checkbox" :aria-label="`选择文件夹 ${folder.name}`" />
          </td>
          <td class="name">
            <template v-if="renaming?.kind === 'folder' && renaming.id === folder.folder_id">
              <form class="inline" @submit.prevent="submitRename">
                <input v-model="renaming.name" type="text" maxlength="255" aria-label="新名称" />
                <button type="submit">保存</button>
                <button type="button" class="ghost" @click="renaming = null">取消</button>
              </form>
            </template>
            <button v-else type="button" class="link folder" @click="enter(folder.folder_id)">
              <span class="tag">文件夹</span> {{ folder.name }}
            </button>
          </td>
          <td>—</td>
          <td>—</td>
          <td>{{ fmtDate(folder.created_at) }}</td>
          <td>—</td>
          <td>—</td>
          <td v-if="canManage" class="actions">
            <button type="button" class="ghost" @click="startRename('folder', folder.folder_id, folder.name)">重命名</button>
            <button type="button" class="ghost" @click="startMove([{ kind: 'folder', id: folder.folder_id }])">移动</button>
            <button type="button" class="ghost" @click="deleting = { id: folder.folder_id, name: folder.name }">删除</button>
          </td>
        </tr>

        <tr v-for="file in files" :key="`f-${file.doc_id}`">
          <td v-if="canManage" class="check">
            <input v-model="selected[`file:${file.doc_id}`]" type="checkbox" :aria-label="`选择文件 ${file.name}`" />
          </td>
          <td class="name" :title="file.name">
            <template v-if="renaming?.kind === 'file' && renaming.id === file.doc_id">
              <form class="inline" @submit.prevent="submitRename">
                <input v-model="renaming.name" type="text" maxlength="255" aria-label="新名称" />
                <button type="submit">保存</button>
                <button type="button" class="ghost" @click="renaming = null">取消</button>
              </form>
            </template>
            <template v-else>{{ file.name }}</template>
          </td>
          <td>{{ humanSize(file.size_bytes) }}</td>
          <td>
            <span :class="['badge', file.status]">{{ STATUS_LABEL[file.status] }}</span>
            <!-- 失败原因只显示错误码，不回显解析器原文（可能含文件内容片段） -->
            <span v-if="file.error_code" class="hint">（{{ file.error_code }}）</span>
            <span v-if="file.status === 'indexed' && !file.searchable" class="hint">已索引，重建切换后可检索</span>
            <span v-if="file.update_state === 'updating'" class="badge pending">更新中（旧版本仍可检索）</span>
            <span v-if="file.update_state === 'update_failed'" class="badge failed">
              更新失败（旧版本仍有效）<template v-if="file.update_error_code">（{{ file.update_error_code }}）</template>
            </span>
          </td>
          <td>{{ fmtDate(file.uploaded_at) }}</td>
          <td>{{ fmtDate(file.content_updated_at) }}</td>
          <td>{{ fmtDate(file.indexed_at) }}</td>
          <td v-if="canManage" class="actions">
            <button v-if="file.status === 'failed' || file.update_state === 'update_failed'" type="button" :disabled="busyKey === `file:${file.doc_id}`" @click="retryFile(file)">重试</button>
            <button v-if="file.update_state === 'update_failed'" type="button" class="ghost" :disabled="busyKey === `file:${file.doc_id}`" @click="discardUpdate(file)">放弃更新</button>
            <button type="button" class="ghost" @click="startRename('file', file.doc_id, file.name)">重命名</button>
            <button type="button" class="ghost" @click="startMove([{ kind: 'file', id: file.doc_id }])">移动</button>
            <button type="button" class="ghost" :disabled="file.status === 'pending' || file.status === 'parsing' || file.update_state === 'updating'" @click="startUpdate(file)">更新</button>
            <button type="button" class="ghost" :disabled="busyKey === `file:${file.doc_id}`" @click="removeFile(file)">删除</button>
          </td>
        </tr>

        <tr v-if="!folders.length && !files.length && !loading">
          <td :colspan="canManage ? 8 : 6" class="empty">此目录暂无内容</td>
        </tr>
      </tbody>
    </table>

    <div v-if="totalPages > 1" class="pager">
      <button type="button" class="ghost" :disabled="page <= 1" @click="turnPage(-1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button type="button" class="ghost" :disabled="page >= totalPages" @click="turnPage(1)">下一页</button>
    </div>

    <!-- 移动目标选择 -->
    <div v-if="moving" class="overlay" @click.self="moving = null">
      <div class="dialog" role="dialog" aria-modal="true" aria-label="移动到">
        <h3>移动到…</h3>
        <nav class="crumbs">
          <button type="button" class="link" :disabled="!moveFolderId" @click="loadMoveTarget('')">根目录</button>
          <template v-for="crumb in moveData?.breadcrumb ?? []" :key="crumb.folder_id">
            <span class="sep">/</span>
            <button type="button" class="link" @click="loadMoveTarget(crumb.folder_id)">{{ crumb.name }}</button>
          </template>
        </nav>
        <ul class="targets">
          <li v-for="f in moveFolders" :key="f.folder_id">
            <button type="button" class="link" @click="loadMoveTarget(f.folder_id)">{{ f.name }}</button>
          </li>
          <li v-if="!moveFolders.length" class="hint">此目录下没有可进入的子文件夹</li>
        </ul>
        <footer>
          <button type="button" class="ghost" @click="moving = null">取消</button>
          <button type="button" :disabled="busyKey === 'move'" @click="confirmMove()">移动到此处</button>
        </footer>
      </div>
    </div>

    <FolderDeleteDialog
      v-if="deleting"
      :client="client"
      :folder-id="deleting.id"
      :folder-name="deleting.name"
      @close="onDeleteClosed"
    />

    <ConflictDialog
      v-if="pendingConflict"
      :mode="pendingConflict.mode"
      :conflicts="pendingConflict.conflicts"
      @confirm="onConflictConfirm"
      @cancel="pendingConflict = null"
    />
  </div>
</template>

<style scoped>
.browser {
  margin-top: 8px;
}
.toolbar,
.crumbs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 10px 0;
}
.sep {
  color: var(--ib-text-muted);
}
.inline {
  display: flex;
  align-items: center;
  gap: 6px;
}
input[type='text'] {
  padding: 5px;
  border: 1px solid var(--ib-border);
  border-radius: 6px;
}
button {
  padding: 4px 10px;
  border: 1px solid var(--ib-accent);
  background: var(--ib-accent);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
}
button.ghost {
  background: var(--ib-bg-elevated);
  color: var(--ib-accent);
}
button.link {
  background: none;
  border: none;
  color: var(--ib-accent);
  padding: 0;
  text-decoration: underline;
}
button.link:disabled {
  color: var(--ib-text-muted);
  text-decoration: none;
}
button.folder {
  font-size: 14px;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th,
td {
  border-bottom: 1px solid var(--ib-border);
  padding: 8px;
  text-align: left;
}
.check {
  width: 28px;
}
.name {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tag {
  display: inline-block;
  padding: 0 6px;
  border-radius: 8px;
  font-size: 12px;
  background: var(--ib-bg-sunken);
  color: var(--ib-text-muted);
}
.badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  background: var(--ib-bg-sunken);
  margin-right: 4px;
}
.badge.indexed {
  background: var(--ib-accent-green-soft);
  color: var(--ib-accent-green);
}
.badge.failed {
  background: var(--ib-danger-soft);
  color: var(--ib-danger);
}
.badge.parsing,
.badge.pending {
  background: var(--ib-warning-soft);
  color: var(--ib-warning);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.actions button {
  padding: 3px 8px;
  font-size: 13px;
}
.empty {
  text-align: center;
  color: var(--ib-text-muted);
  padding: 24px;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 12px 0;
}
.hint {
  color: var(--ib-text-muted);
  font-size: 13px;
}
.error {
  background: var(--ib-danger-soft);
  border: 1px solid var(--ib-danger);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--ib-danger);
}
.notice {
  background: var(--ib-accent-green-soft);
  border: 1px solid var(--ib-accent-green);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--ib-accent-green);
}
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}
.dialog {
  width: min(520px, 92vw);
  max-height: 80vh;
  overflow: auto;
  background: var(--ib-bg-elevated);
  border: 1px solid var(--ib-border);
  border-radius: 10px;
  padding: 16px 20px;
}
.dialog h3 {
  margin: 0 0 8px;
}
.targets {
  list-style: none;
  padding: 0;
  margin: 8px 0;
}
.targets li {
  padding: 4px 0;
}
.dialog footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
</style>
