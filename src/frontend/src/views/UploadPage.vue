<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-256（消费 IFC-IB-242 列表 / 243 上传 / 244 删除 / 245 重试）
 *             IFC-IB-376（REV-18）视图由「知识库」改为「**项目域**」：移除「知识库标识」
 *             输入框，上传的 `kb_id` 由服务端按已认证主体 `project_id` 推导（ADR-41）
 * @author software-developer
 *
 * 资料管理页（**项目域**视图）：上传、列表、删除、失败重试。
 *
 * ## 为什么移除「知识库标识」输入框（REV-18 / ADR-41 / IFC-IB-375）
 *
 * 范围**不可由客户端自证**（架构红线 `architecture_design.md:120`）。REV-18 起
 * `kb_id` 由**已认证主体的 `project_id`** 推导（`kb_id ≡ project_id`）：上传请求体
 * **不再携带** kb 字段；`project_id` 经 `X-IB-Project` 头（由 `client.ts` 的 `headers()`
 * 单点注入，来源于当前项目上下文）。服务端**保留** `assert_kb_in_project` 归属断言
 * （失败 403）—— 因此「越权」在服务端仍被结构性拦住。
 *
 * ## 轮询只在「有未完成文档」时进行
 *
 * 上传后文档处于 `pending`/`parsing`，需要刷新才能看到 `indexed`。无条件轮询会让页面
 * 在闲置时也持续打后端（树莓派上每个请求都要 Waitress 线程）。故仅在列表中存在
 * `pending`/`parsing` 项时启动 2s 轮询，全部落定后自动停止。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { ApiClientError, type ApiClient, type DocumentRecord } from '../api/client';

const props = defineProps<{ client: ApiClient }>();
const emit = defineEmits<{ (e: 'unauthorized'): void }>();

const files = ref<DocumentRecord[]>([]);
const total = ref(0);
const loading = ref(false);
const error = ref('');
const statusFilter = ref('');

const picked = ref<File | null>(null);
const uploading = ref(false);
const busyDocId = ref('');

const IN_FLIGHT = new Set(['pending', 'parsing']);
const STATUS_LABEL: Record<DocumentRecord['status'], string> = {
  pending: '排队中',
  parsing: '解析中',
  indexed: '已入库',
  failed: '失败',
};

const hasInFlight = computed(() => files.value.some((f) => IN_FLIGHT.has(f.status)));

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
    await load();
    schedulePoll();
  }, 2000);
}

watch(hasInFlight, (value) => {
  if (value) schedulePoll();
  else stopPolling();
});

onBeforeUnmount(stopPolling);

function describe(err: unknown): string {
  if (err instanceof ApiClientError) {
    if (err.status === 401) {
      emit('unauthorized');
      return '登录状态已失效，请重新填写访问令牌。';
    }
    if (err.status === 403) return '当前令牌无权操作该项目或该知识库。';
    return err.message;
  }
  // 网络层异常（服务未启动、被代理切断）：给出可操作提示，而不是 "TypeError: Failed to fetch"
  return '无法连接服务，请确认后端已启动（waitress 监听 127.0.0.1:18080）。';
}

async function load(): Promise<void> {
  loading.value = true;
  error.value = '';
  try {
    const page = await props.client.listFiles({
      page_size: 50,
      status: statusFilter.value || undefined,
    });
    files.value = page.items;
    total.value = page.total;
  } catch (err) {
    error.value = describe(err);
  } finally {
    loading.value = false;
  }
}

function onPick(event: Event): void {
  const input = event.target as HTMLInputElement;
  picked.value = input.files?.[0] ?? null;
  error.value = '';
}

async function upload(): Promise<void> {
  if (!picked.value) return;
  uploading.value = true;
  error.value = '';
  try {
    // REV-18：仅传文件；kb_id 由服务端按当前项目推导（不再由客户端提交）。
    await props.client.uploadFile(picked.value);
    picked.value = null;
    const input = document.querySelector<HTMLInputElement>('input[type=file]');
    if (input) input.value = ''; // 允许再次选择同一文件
    await load();
    schedulePoll();
  } catch (err) {
    error.value = describe(err);
  } finally {
    uploading.value = false;
  }
}

async function remove(doc: DocumentRecord): Promise<void> {
  // 删除是不可逆的（向量 + 原文 + 台账一并清除），故二次确认。用原生 confirm 以免引入
  // 组件库；若后续页面增多再统一替换为受控对话框。
  if (!window.confirm(`确认删除「${doc.doc_name}」？其向量与原文将一并清除，不可恢复。`)) return;
  busyDocId.value = doc.doc_id;
  error.value = '';
  try {
    await props.client.deleteFile(doc.doc_id);
    await load();
  } catch (err) {
    error.value = describe(err);
  } finally {
    busyDocId.value = '';
  }
}

async function retry(doc: DocumentRecord): Promise<void> {
  busyDocId.value = doc.doc_id;
  error.value = '';
  try {
    await props.client.retryFile(doc.doc_id);
    await load();
    schedulePoll();
  } catch (err) {
    error.value = describe(err);
  } finally {
    busyDocId.value = '';
  }
}

function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

// 后端返回 UTC ISO（如 2026-10-07T09:46:52Z），界面按本地时区显示为
// yyyy-mm-dd hh:mm:ss（Anthropic 风格：表格时间一律本地、可读）。
function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

onMounted(load);
</script>

<template>
  <section class="page">
    <h2>资料管理（项目域）</h2>

    <form class="uploader" @submit.prevent="upload">
      <label>
        选择文件
        <input type="file" accept=".pdf,.txt,.md,.markdown,.docx" @change="onPick" />
      </label>
      <button type="submit" :disabled="!picked || uploading">
        {{ uploading ? '上传中…' : '上传' }}
      </button>
    </form>

    <p v-if="picked" class="hint">
      待上传：{{ picked.name }}（{{ humanSize(picked.size) }}）
    </p>
    <p class="hint">
      支持 PDF / TXT / Markdown / DOCX。资料归属**当前项目**（项目域），
      上传后进入解析队列，状态自动刷新。
    </p>

    <p v-if="error" class="error" role="alert">{{ error }}</p>

    <div class="toolbar">
      <label>
        状态筛选
        <select v-model="statusFilter" @change="load">
          <option value="">全部</option>
          <option value="pending">排队中</option>
          <option value="parsing">解析中</option>
          <option value="indexed">已入库</option>
          <option value="failed">失败</option>
        </select>
      </label>
      <button type="button" :disabled="loading" @click="load">刷新</button>
      <span class="hint">共 {{ total }} 条{{ hasInFlight ? '（解析中，自动刷新）' : '' }}</span>
    </div>

    <table>
      <thead>
        <tr>
          <th>文件名</th>
          <th>项目域</th>
          <th>大小</th>
          <th>切片</th>
          <th>状态</th>
          <th>更新时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="file in files" :key="file.doc_id">
          <td class="name" :title="file.content_sha256">{{ file.doc_name }}</td>
          <td>{{ file.kb_id }}</td>
          <td>{{ humanSize(file.size_bytes) }}</td>
          <td>{{ file.chunk_count }}</td>
          <td>
            <span :class="['badge', file.status]">{{ STATUS_LABEL[file.status] }}</span>
            <!-- 失败原因只显示错误码，不回显解析器原文（可能含文件内容片段） -->
            <span v-if="file.error_code" class="hint">（{{ file.error_code }}）</span>
          </td>
          <td>{{ fmtDate(file.updated_at) }}</td>
          <td class="actions">
            <button
              v-if="file.status === 'failed'"
              type="button"
              :disabled="busyDocId === file.doc_id"
              @click="retry(file)"
            >
              重试
            </button>
            <button
              type="button"
              :disabled="busyDocId === file.doc_id"
              @click="remove(file)"
            >
              删除
            </button>
          </td>
        </tr>
        <tr v-if="!files.length && !loading">
          <td colspan="7" class="empty">暂无资料</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.page {
  padding-top: 16px;
}
.uploader,
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin: 12px 0;
}
label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}
input[type='text'],
select {
  padding: 6px;
  border: 1px solid var(--ib-border);
  border-radius: 6px;
}
button {
  padding: 6px 12px;
  border: 1px solid var(--ib-accent);
  background: var(--ib-accent);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.toolbar button {
  background: var(--ib-bg-elevated);
  color: var(--ib-accent);
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
.name {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  background: var(--ib-bg-sunken);
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
  gap: 6px;
}
.actions button {
  padding: 3px 10px;
  font-size: 13px;
}
.empty {
  text-align: center;
  color: var(--ib-text-muted);
  padding: 24px;
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
</style>
