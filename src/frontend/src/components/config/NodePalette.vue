<script setup lang="ts">
/** @module MOD-R26-19  节点面板：仅列受限节点类型（无代码 / 表达式节点）。只读档不渲染。 */
import type { NodeKind } from '../../api/client';
import { ADDABLE_KINDS, KIND_LABEL } from './graphModel';

defineProps<{ readonly: boolean }>();
const emit = defineEmits<{ (e: 'add-node', kind: NodeKind): void }>();
</script>

<template>
  <div v-if="!readonly" class="palette">
    <span class="hint">新增节点：</span>
    <el-button v-for="k in ADDABLE_KINDS" :key="k" size="small" @click="emit('add-node', k)">
      {{ KIND_LABEL[k] }}
    </el-button>
  </div>
</template>

<style scoped>
.palette {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
</style>
