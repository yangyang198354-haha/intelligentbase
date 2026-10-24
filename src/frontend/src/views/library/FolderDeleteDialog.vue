<script setup lang="ts">
/**
 * @module MOD-014
 * @implements 删除文件夹：二次确认（显示子文件夹 / 文件数）+ 循环 `deleteFolderStep` 至 done + 失败清单
 *             （REQ-FUNC-006 / AC-006-01~04；ADR-008 分步删除）
 * @author software-developer
 *
 * 后端每步至多处理一批文件并返回 `{done, failed[], remaining_files}`；本组件重复调用直到 `done`。
 * 某步既没有删除任何文件、也没有进展（全部失败 / 无变化）时停止循环并展示失败清单，
 * 避免无限重发；失败文件及其目录链仍在资料库中可见，可稍后重试。
 */
import { onMounted, ref } from 'vue';

import { ApiClientError, type ApiClient, type FolderDeleteStep, type FolderDetail } from '../../api/client';

const props = defineProps<{ client: ApiClient; folderId: string; folderName: string }>();
const emit = defineEmits<{ (e: 'close', changed: boolean): void }>();

const detail = ref<FolderDetail | null>(null);
const phase = ref<'confirm' | 'running' | 'finished'>('confirm');
const error = ref('');
const deletedFiles = ref(0);
const lastStep = ref<FolderDeleteStep | null>(null);

onMounted(async () => {
  try {
    detail.value = await props.client.getFolder(props.folderId);
  } catch (err) {
    error.value = err instanceof ApiClientError ? err.message : '无法连接服务。';
  }
});

async function run(): Promise<void> {
  phase.value = 'running';
  error.value = '';
  try {
    for (;;) {
      const step = await props.client.deleteFolderStep(props.folderId);
      lastStep.value = step;
      deletedFiles.value += step.deleted_files;
      if (step.done) break;
      if (step.deleted_files === 0) break; // 无进展：交给用户查看失败清单
    }
  } catch (err) {
    error.value = err instanceof ApiClientError ? err.message : '无法连接服务。';
  } finally {
    phase.value = 'finished';
  }
}
</script>

<template>
  <div class="overlay" @click.self="phase !== 'running' && emit('close', deletedFiles > 0)">
    <div class="dialog" role="dialog" aria-modal="true" aria-label="删除文件夹">
      <h3>删除文件夹「{{ folderName }}」</h3>

      <template v-if="phase === 'confirm'">
        <p v-if="detail">
          将删除其中 <strong>{{ detail.subtree_folders }}</strong> 个子文件夹和
          <strong>{{ detail.subtree_files }}</strong> 个文件；向量与原文将一并清除，<strong>不可恢复</strong>。
        </p>
        <p v-else-if="!error" class="hint">正在统计…</p>
        <footer>
          <button type="button" class="ghost" @click="emit('close', false)">取消</button>
          <button type="button" class="danger" :disabled="!detail" @click="run">确认删除</button>
        </footer>
      </template>

      <template v-else>
        <p v-if="phase === 'running'" class="hint">正在删除…（已删除 {{ deletedFiles }} 个文件）</p>
        <template v-else>
          <p v-if="lastStep?.done" class="ok">已删除：共 {{ deletedFiles }} 个文件。</p>
          <p v-else class="warn">
            删除未完成：已删除 {{ deletedFiles }} 个文件，仍剩 {{ lastStep?.remaining_files ?? 0 }} 个文件。
          </p>
          <div v-if="lastStep?.failed.length">
            <p class="warn">以下文件删除失败（仍保留在原位置，可稍后重试）：</p>
            <ul class="failed">
              <li v-for="f in lastStep.failed" :key="f.doc_id">{{ f.path }}（{{ f.error_code }}）</li>
            </ul>
          </div>
        </template>
        <footer>
          <button type="button" :disabled="phase === 'running'" @click="emit('close', deletedFiles > 0)">关闭</button>
        </footer>
      </template>

      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
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
  width: min(560px, 92vw);
  max-height: 80vh;
  overflow: auto;
  background: var(--ib-bg-elevated);
  border: 1px solid var(--ib-border);
  border-radius: 10px;
  padding: 16px 20px;
}
h3 {
  margin: 0 0 8px;
}
footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
button {
  padding: 5px 12px;
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
button.danger {
  background: var(--ib-danger);
  border-color: var(--ib-danger);
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.failed {
  font-size: 13px;
  word-break: break-all;
}
.hint {
  color: var(--ib-text-muted);
}
.ok {
  color: var(--ib-accent-green);
}
.warn {
  color: var(--ib-warning);
}
.error {
  background: var(--ib-danger-soft);
  border: 1px solid var(--ib-danger);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--ib-danger);
}
</style>
