<script setup lang="ts">
/** @module MOD-R26-20  版本历史与回滚（回滚仅“管理”档可见 / 可用，二次确认）。 */
import { onMounted, ref } from 'vue';

import { ApiClientError, type ApiClient, type ConfigLevel, type DiffItemDto, type VersionRecordDto } from '../../api/client';

const props = defineProps<{ client: ApiClient; level: ConfigLevel; headVersion: number }>();
const emit = defineEmits<{ (e: 'rolled-back', version: number): void }>();

const items = ref<VersionRecordDto[]>([]);
const diff = ref<{ version: number; items: DiffItemDto[] } | null>(null);
const msg = ref('');

async function refresh(): Promise<void> {
  msg.value = '';
  try {
    items.value = (await props.client.listVersions(50)).items;
  } catch (err) {
    msg.value = err instanceof ApiClientError ? err.message : '版本历史载入失败';
  }
}
async function showDiff(v: number): Promise<void> {
  try {
    diff.value = { version: v, items: (await props.client.diffVersions(v, 'head')).items };
  } catch (err) {
    msg.value = err instanceof ApiClientError ? err.message : '差异载入失败';
  }
}
async function rollback(v: number): Promise<void> {
  if (!window.confirm(`确认回滚到版本 ${v}？将产生一个新版本，内容与版本 ${v} 一致。`)) return;
  try {
    const r = await props.client.rollback(v, props.headVersion);
    msg.value = `已回滚，新版本 ${r.version} 已生效`;
    emit('rolled-back', r.version);
    await refresh();
  } catch (err) {
    msg.value = err instanceof ApiClientError ? (err.status === 403 ? '回滚需要“管理”档' : err.message) : '回滚失败';
  }
}
onMounted(refresh);
defineExpose({ refresh });
</script>

<template>
  <div>
    <p v-if="msg" class="hint">{{ msg }}</p>
    <el-table :data="items" size="small" empty-text="暂无版本">
      <el-table-column prop="version" label="版本" width="70" />
      <el-table-column prop="actor" label="保存人" width="120" />
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="summary" label="变更摘要" />
      <el-table-column label="操作" width="170">
        <template #default="{ row }">
          <el-button link size="small" @click="showDiff(row.version)">与当前对比</el-button>
          <el-button v-if="level === 'manage' && row.version !== headVersion" link size="small" type="danger" @click="rollback(row.version)">回滚</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="diff">
      <h5>版本 {{ diff.version }} → 当前的差异</h5>
      <ul><li v-for="(i, k) in diff.items" :key="k">{{ i.kind }}：{{ i.object_id }} {{ i.field }}</li></ul>
      <p v-if="!diff.items.length" class="hint">与当前一致</p>
    </div>
  </div>
</template>

<style scoped>
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
