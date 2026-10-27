<script setup lang="ts">
/** @module MOD-R26-20  并发冲突：放弃并重新载入 / 另存为草稿副本（OQ-R26-09=B）。 */
import type { ConflictReceiptDto } from '../../api/client';

defineProps<{ visible: boolean; receipt: ConflictReceiptDto | null }>();
const emit = defineEmits<{ (e: 'reload'): void; (e: 'save-draft'): void; (e: 'close'): void }>();
</script>

<template>
  <el-dialog :model-value="visible" title="配置已被他人更新" width="560px" @close="emit('close')">
    <p>你基于版本 {{ receipt?.base_version }} 编辑，当前最新版本为 {{ receipt?.head_version }}；你的保存未覆盖他人改动。</p>
    <p v-if="receipt && !receipt.base_available">你的基线版本已被修剪，下列冲突对象为全部对象。</p>
    <ul>
      <li v-for="(c, i) in receipt?.conflicts ?? []" :key="i">{{ c.kind }}：{{ c.object_id }}（{{ c.fields.join('、') }}）</li>
    </ul>
    <template #footer>
      <el-button @click="emit('save-draft')">另存为草稿副本</el-button>
      <el-button type="primary" @click="emit('reload')">放弃并重新载入</el-button>
    </template>
  </el-dialog>
</template>
