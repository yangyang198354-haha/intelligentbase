<script setup lang="ts">
// MOD-R26-20/21 档位管理（US-010 / AC-010-02）：列出本项目账号及其配置档位，管理档可修改；变更审计由后端 PUT 同事务写入。
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';

import { ApiClientError, type AccessItemDto, type ApiClient, type ConfigLevel } from '../../api/client';

const props = defineProps<{ client: ApiClient; level: ConfigLevel }>();

const LEVEL_LABEL: Record<ConfigLevel, string> = { view: '查看', edit: '编辑', manage: '管理' };
const LEVELS: ConfigLevel[] = ['view', 'edit', 'manage'];

const items = ref<AccessItemDto[]>([]);
const loading = ref(false);
const error = ref('');
const savingId = ref('');

// 仅体验层：服务端对 GET/PUT 一律要求 manage 档，非管理档得 403。
const canManage = computed(() => props.level === 'manage');

function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 403) return '权限不足：调整档位需要“管理”档。';
    return err.message || fallback;
  }
  return fallback;
}

async function load(): Promise<void> {
  if (!canManage.value) return;
  loading.value = true;
  error.value = '';
  try {
    items.value = (await props.client.getAccess()).items;
  } catch (err) {
    error.value = messageOf(err, '账号档位载入失败');
  } finally {
    loading.value = false;
  }
}

async function change(row: AccessItemDto, next: ConfigLevel): Promise<void> {
  if (next === row.config_level || savingId.value) return;
  savingId.value = row.user_id;
  try {
    await props.client.putAccess(row.user_id, next);
    ElMessage.success(`已将 ${row.username} 调整为“${LEVEL_LABEL[next]}”档（已写审计）`);
  } catch (err) {
    ElMessage.error(
      err instanceof ApiClientError && err.status === 409
        ? '不能降级本项目最后一个“管理”档账号'
        : messageOf(err, '调整档位失败'),
    );
  } finally {
    savingId.value = '';
    await load(); // 以服务端为准刷新显示
  }
}

onMounted(load);
</script>

<template>
  <div class="access">
    <p v-if="!canManage" class="hint">仅“管理”档账号可查看与调整本项目账号的配置档位。</p>
    <template v-else>
      <p class="hint">查看：只读；编辑：可修改并发布；管理：另可回滚、采纳漂移、调整档位。每次调整都会写入审计。</p>
      <p v-if="error" class="err">{{ error }}</p>
      <el-table v-loading="loading" :data="items" size="small" empty-text="本项目暂无账号">
        <el-table-column prop="username" label="账号" min-width="120" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">{{ row.status === 'active' ? '启用' : '停用' }}</template>
        </el-table-column>
        <el-table-column label="配置档位" width="160">
          <template #default="{ row }">
            <el-select
              :model-value="row.config_level"
              size="small"
              :disabled="savingId === row.user_id"
              @change="(v: ConfigLevel) => change(row, v)"
            >
              <el-option v-for="l in LEVELS" :key="l" :label="LEVEL_LABEL[l]" :value="l" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </div>
</template>

<style scoped>
.hint {
  color: var(--ib-text-muted);
  font-size: 13px;
}
.err {
  color: var(--ib-danger);
}
</style>
