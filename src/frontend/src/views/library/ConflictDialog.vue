<script setup lang="ts">
/**
 * @module MOD-014
 * @implements 同名冲突三选项弹窗（覆盖 / 跳过 / 两者都保留并自动改名；REQ-FUNC-011）
 * @author software-developer
 *
 * 通用于三个场景（由父组件决定 `mode` 与 key 的含义）：
 *  * upload：键 = 冲突的相对路径（文件）或目录前缀（文件夹）；
 *  * move：键 = 发起移动的条目 id；
 *  * update：键 = 被更新的文件 X 的 id（"覆盖" = 用新文件更新同名的 Y，X 不变）。
 *
 * 关闭弹窗而未选择 = 取消整次操作（AC-011-04）：本组件只发出 `cancel`，不替用户选默认值。
 * 文件夹"覆盖"= 合并，选中时显示"同名文件将被覆盖"警示（A-03）。
 */
import { computed, reactive } from 'vue';

import type { ConflictActionTs, ConflictInfo } from '../../api/client';

const props = defineProps<{
  conflicts: ConflictInfo[];
  mode: 'upload' | 'move' | 'update';
}>();
const emit = defineEmits<{
  (e: 'confirm', resolutions: Record<string, ConflictActionTs>): void;
  (e: 'cancel'): void;
}>();

const KIND_LABEL = { file: '文件', folder: '文件夹' } as const;

function keyOf(c: ConflictInfo): string {
  return c.rel_path ?? c.entry?.id ?? c.existing.id;
}

const chosen = reactive<Record<string, ConflictActionTs | ''>>({});
for (const c of props.conflicts) chosen[keyOf(c)] = '';

const complete = computed(() => props.conflicts.every((c) => chosen[keyOf(c)] !== ''));
const overwriteLabel = computed(() =>
  props.mode === 'update' ? '覆盖（用新文件更新同名的那一项）' : '覆盖',
);

function setAll(action: ConflictActionTs): void {
  for (const c of props.conflicts) chosen[keyOf(c)] = action;
}

function confirm(): void {
  if (!complete.value) return;
  const out: Record<string, ConflictActionTs> = {};
  for (const c of props.conflicts) out[keyOf(c)] = chosen[keyOf(c)] as ConflictActionTs;
  emit('confirm', out);
}

function describe(c: ConflictInfo): string {
  const subject = c.rel_path ?? c.entry?.name ?? '';
  return `${subject}（与已有${KIND_LABEL[c.existing.kind]}「${c.existing.name}」同名，不区分大小写）`;
}
</script>

<template>
  <div class="overlay" @click.self="emit('cancel')">
    <div class="dialog" role="dialog" aria-modal="true" aria-label="同名冲突">
      <header>
        <h3>发现同名条目</h3>
        <button type="button" class="close" aria-label="关闭并取消" @click="emit('cancel')">×</button>
      </header>
      <p class="hint">请为下列每一项选择处理方式；选择前不会改动任何已有内容。关闭本窗口将取消本次操作。</p>

      <div class="bulk">
        <span>全部设为：</span>
        <button type="button" @click="setAll('overwrite')">覆盖</button>
        <button type="button" @click="setAll('skip')">跳过</button>
        <button type="button" @click="setAll('rename')">两者都保留</button>
      </div>

      <ul class="list">
        <li v-for="c in conflicts" :key="keyOf(c)">
          <div class="desc">{{ describe(c) }}</div>
          <div class="options" role="radiogroup">
            <label><input v-model="chosen[keyOf(c)]" type="radio" :name="keyOf(c)" value="overwrite" /> {{ overwriteLabel }}</label>
            <label><input v-model="chosen[keyOf(c)]" type="radio" :name="keyOf(c)" value="skip" /> 跳过</label>
            <label><input v-model="chosen[keyOf(c)]" type="radio" :name="keyOf(c)" value="rename" /> 两者都保留并自动改名</label>
          </div>
          <p v-if="chosen[keyOf(c)] === 'overwrite' && c.existing.kind === 'folder'" class="warn">
            文件夹将合并：同名文件将被覆盖，其他文件保留。
          </p>
        </li>
      </ul>

      <footer>
        <button type="button" class="ghost" @click="emit('cancel')">取消</button>
        <button type="button" :disabled="!complete" @click="confirm">确认</button>
      </footer>
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
  width: min(640px, 92vw);
  max-height: 80vh;
  overflow: auto;
  background: var(--ib-bg-elevated);
  border: 1px solid var(--ib-border);
  border-radius: 10px;
  padding: 16px 20px;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
h3 {
  margin: 0;
}
.close {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  color: var(--ib-text-muted);
}
.bulk {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 8px 0;
  font-size: 13px;
}
.list {
  list-style: none;
  padding: 0;
  margin: 8px 0;
}
.list li {
  border-bottom: 1px solid var(--ib-border);
  padding: 8px 0;
}
.desc {
  font-size: 14px;
  word-break: break-all;
}
.options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
  font-size: 13px;
}
.options label {
  display: flex;
  align-items: center;
  gap: 4px;
}
.warn {
  color: var(--ib-warning);
  font-size: 13px;
  margin: 4px 0 0;
}
.hint {
  color: var(--ib-text-muted);
  font-size: 13px;
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
button.ghost,
.bulk button {
  background: var(--ib-bg-elevated);
  color: var(--ib-accent);
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
