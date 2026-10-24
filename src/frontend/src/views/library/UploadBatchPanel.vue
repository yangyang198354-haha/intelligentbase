<script setup lang="ts">
/**
 * @module MOD-014
 * @implements 文件夹 / 多文件上传面板：计划（限额错误、冲突）→ 并发 2 逐文件上传 → 汇总
 *             （REQ-FUNC-001 / 002 / 007 / 011 / 015；ADR-003）
 * @author software-developer
 *
 * 选择入口：`<input type="file" webkitdirectory multiple>`（读取 `webkitRelativePath`）与多文件选择；
 * 浏览器不支持 `webkitdirectory` 时隐藏文件夹入口（A-09）。
 * 整体进度"已处理 N / 总数"单调不减（含计划期跳过项）；结束后展示成功 / 跳过 / 失败三数，
 * 并逐项列出跳过与失败的相对路径与原因。
 */
import { computed, onMounted, ref } from 'vue';

import type { ApiClient, ConflictActionTs } from '../../api/client';
import { REASON_LABEL, createUploadBatch } from '../../stores/uploadBatch';
import ConflictDialog from './ConflictDialog.vue';

const props = defineProps<{ client: ApiClient; targetFolderId: string }>();
const emit = defineEmits<{ (e: 'finished'): void }>();

const store = createUploadBatch(props.client);
const state = store.state;

const supportsDirectory = ref(false);

onMounted(() => {
  supportsDirectory.value = 'webkitdirectory' in document.createElement('input');
  void store.restore();
});

const busy = computed(() => state.phase === 'planning' || state.phase === 'uploading');
const counts = computed(() => {
  const c = { accepted: 0, skipped: 0, failed: 0, pending: 0 };
  for (const row of state.rows) {
    if (row.state === 'accepted') c.accepted += 1;
    else if (row.state === 'skipped') c.skipped += 1;
    else if (row.state === 'failed') c.failed += 1;
    else c.pending += 1;
  }
  return c;
});
const problemRows = computed(() => state.rows.filter((r) => r.state === 'skipped' || r.state === 'failed'));

function reasonText(code: string | null): string {
  if (!code) return '';
  return REASON_LABEL[code] ?? code;
}

async function onPicked(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const picked = Array.from(input.files ?? []);
  input.value = ''; // 允许再次选择同一批文件
  if (!picked.length) return;
  await store.begin(picked, props.targetFolderId);
  if (state.phase === 'done') emit('finished');
}

async function onResolved(resolutions: Record<string, ConflictActionTs>): Promise<void> {
  await store.resolveConflicts(resolutions);
  if (state.phase === 'done') emit('finished');
}

async function retry(): Promise<void> {
  await store.retryFailed();
  emit('finished');
}

function close(): void {
  store.cancel();
  emit('finished');
}
</script>

<template>
  <section class="batch">
    <div class="pickers">
      <label v-if="supportsDirectory" class="btn">
        上传文件夹
        <input
          type="file"
          webkitdirectory
          multiple
          :disabled="busy"
          hidden
          @change="onPicked"
        />
      </label>
      <label class="btn">
        上传文件
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.md,.markdown,.docx"
          :disabled="busy"
          hidden
          @change="onPicked"
        />
      </label>
      <span class="hint">支持 PDF / TXT / Markdown / DOCX；文件夹内的子目录结构会原样保留。</span>
    </div>

    <p v-if="state.phase === 'planning'" class="hint">正在检查上传清单…</p>
    <p v-if="state.phase === 'error'" class="error" role="alert">
      {{ state.message }}
      <button type="button" class="link" @click="close">知道了</button>
    </p>

    <div v-if="state.phase === 'uploading' || state.phase === 'done'" class="progress">
      <div class="bar" role="progressbar" :aria-valuenow="state.processed" :aria-valuemax="state.total">
        <div class="fill" :style="{ width: state.total ? `${(state.processed / state.total) * 100}%` : '0%' }"></div>
      </div>
      <span>已处理 {{ state.processed }} / {{ state.total }}</span>
    </div>

    <div v-if="state.phase === 'done'" class="summary">
      <p>
        成功 <strong>{{ counts.accepted }}</strong> · 跳过 <strong>{{ counts.skipped }}</strong> · 失败
        <strong>{{ counts.failed }}</strong>
        <span v-if="counts.pending"> · 未上传 {{ counts.pending }}</span>
      </p>
      <p v-if="state.message" class="hint">{{ state.message }}</p>
      <ul v-if="problemRows.length" class="problems">
        <li v-for="row in problemRows" :key="row.client_idx">
          <span :class="['tag', row.state]">{{ row.state === 'failed' ? '失败' : '跳过' }}</span>
          {{ row.rel_path }}
          <span class="hint">{{ reasonText(row.reason_code) }}</span>
        </li>
      </ul>
      <div class="actions">
        <button v-if="counts.failed && !state.restored" type="button" @click="retry">重试失败项</button>
        <button type="button" class="ghost" @click="close">关闭汇总</button>
      </div>
    </div>

    <ConflictDialog
      v-if="state.phase === 'conflict'"
      mode="upload"
      :conflicts="state.conflicts"
      @confirm="onResolved"
      @cancel="close"
    />
  </section>
</template>

<style scoped>
.batch {
  margin: 12px 0;
}
.pickers {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.btn {
  display: inline-block;
  padding: 6px 12px;
  border: 1px solid var(--ib-accent);
  background: var(--ib-accent);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0;
  font-size: 13px;
}
.bar {
  flex: 1;
  max-width: 360px;
  height: 8px;
  background: var(--ib-bg-sunken);
  border-radius: 4px;
  overflow: hidden;
}
.fill {
  height: 100%;
  background: var(--ib-accent);
  transition: width 0.2s;
}
.summary {
  border: 1px solid var(--ib-border);
  border-radius: 8px;
  padding: 8px 12px;
}
.problems {
  max-height: 200px;
  overflow: auto;
  padding-left: 16px;
  font-size: 13px;
  word-break: break-all;
}
.tag {
  display: inline-block;
  padding: 0 6px;
  border-radius: 8px;
  font-size: 12px;
  background: var(--ib-warning-soft);
  color: var(--ib-warning);
}
.tag.failed {
  background: var(--ib-danger-soft);
  color: var(--ib-danger);
}
.actions {
  display: flex;
  gap: 8px;
}
.actions button {
  padding: 4px 12px;
  border: 1px solid var(--ib-accent);
  background: var(--ib-accent);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
}
.actions button.ghost {
  background: var(--ib-bg-elevated);
  color: var(--ib-accent);
}
.link {
  background: none;
  border: none;
  color: var(--ib-accent);
  cursor: pointer;
  text-decoration: underline;
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
