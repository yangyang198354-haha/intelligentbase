<script setup lang="ts">
/** @module MOD-R26-20  保存前差异确认：校验错误逐条展示且无“忽略”选项；仅在无错误时可确认。 */
import { ref } from 'vue';

import type { DiffItemDto, ValidationErrorItem } from '../../api/client';

const KIND_LABEL: Record<string, string> = {
  agent_added: '新增 agent', agent_removed: '删除 agent', agent_disabled: '停用 agent', agent_enabled: '启用 agent',
  agent_field: '修改 agent 字段', prompt: '修改 提示词', tool_grant: '修改 工具授权', tool_param: '修改 工具参数',
  knowledge_scope: '修改 知识范围', route_param: '修改 路由参数', node_added: '新增节点', node_removed: '删除节点',
  node_changed: '修改节点', edge_added: '新增边', edge_removed: '删除边', edge_changed: '修改边', layout: '调整布局',
};

defineProps<{ visible: boolean; items: DiffItemDto[]; layoutOnly: boolean; errors: ValidationErrorItem[]; busy: boolean }>();
const emit = defineEmits<{ (e: 'confirm', message?: string): void; (e: 'cancel'): void }>();
const message = ref('');

function line(i: DiffItemDto): string {
  const kind = KIND_LABEL[i.kind] ?? i.kind;
  const delta = i.before !== null || i.after !== null ? `：${i.before ?? '∅'} → ${i.after ?? '∅'}` : '';
  return `${kind}：${i.object_id}${i.field ? ` · ${i.field}` : ''}${delta}`;
}
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
      <ul><li v-for="(i, k) in items" :key="k">{{ line(i) }}</li></ul>
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
