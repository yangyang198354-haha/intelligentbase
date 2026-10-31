<script setup lang="ts">
/** @module MOD-R26-20  保存前差异确认：校验错误逐条展示且无“忽略”选项；仅在无错误时可确认。 */
import { ref } from 'vue';

import type { DiffItemDto, ValidationErrorItem } from '../../api/client';
import { formatDiffLine } from './publishDiff';

defineProps<{ visible: boolean; items: DiffItemDto[]; layoutOnly: boolean; errors: ValidationErrorItem[]; busy: boolean }>();
const emit = defineEmits<{ (e: 'confirm', message?: string): void; (e: 'cancel'): void }>();
const message = ref('');
</script>

<template>
  <el-dialog :model-value="visible" title="确认保存并生效" width="640px" @close="emit('cancel')">
    <div v-if="errors.length">
      <p class="bad">校验未通过，必须先修正后才能保存：</p>
      <ul><li v-for="e in errors" :key="`${e.path}:${e.code}`"><code>{{ e.path }}</code> [{{ e.code }}] {{ e.message }}</li></ul>
    </div>
    <div v-else>
      <p v-if="!items.length">没有任何变更。</p>
      <p v-else-if="layoutOnly">仅调整了节点位置（不改变行为，仍会产生新版本）。</p>
      <ul><li v-for="(i, k) in items" :key="k">{{ formatDiffLine(i) }}</li></ul>
      <el-input v-model="message" maxlength="200" placeholder="变更说明（可选，≤200 字）" />
    </div>
    <template #footer>
      <el-button @click="emit('cancel')">取消</el-button>
      <el-button type="primary" :loading="busy" :disabled="errors.length > 0 || items.length === 0" @click="emit('confirm', message || undefined)">确认并生效</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.bad { color: var(--el-color-danger); }
</style>
