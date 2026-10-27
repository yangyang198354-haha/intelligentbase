<script setup lang="ts">
/** @module MOD-R26-19  悬停卡片（节点 / 边共用）：内容全部文本插值，不执行任何来自配置的标记。 */
import type { HoverCardModel } from './graphModel';

defineProps<{ model: HoverCardModel; x: number; y: number }>();
</script>

<template>
  <div class="hover-card" :style="{ left: `${x}px`, top: `${y}px` }" role="tooltip">
    <strong>{{ model.title }}</strong>
    <dl>
      <template v-for="l in model.lines" :key="l.label">
        <dt>{{ l.label }}</dt>
        <dd>{{ l.value }}</dd>
      </template>
    </dl>
  </div>
</template>

<style scoped>
.hover-card {
  position: absolute;
  z-index: 20;
  max-width: 320px;
  padding: 8px 12px;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  box-shadow: var(--el-box-shadow-light);
  pointer-events: none;
  font-size: 12px;
}
dl {
  margin: 6px 0 0;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 8px;
}
dt {
  color: var(--el-text-color-secondary);
}
dd {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
