<script setup lang="ts">
/**
 * @module MOD-R28-18
 * @implements IFC-R28-028 联网全局用量上限页（“系统管理 → 联网上限”；**仅 admin**）
 * @depends MOD-R28-17（client.getWebGovernance / putWebGovernance）, IFC-R28-023 / 024
 *
 * 全局上限由管理员设定，项目管理员只能在其内调低（保存期超限被服务端拒绝）。
 * 本页是管理入口而非权限边界：非 admin 的读写一律服务端 403；范围由服务端返回的 `hard_max` 决定。
 * 上限对**新回合**立即生效，不需要重启服务。
 */
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';

import { client } from '../app/env';
import { ApiClientError, type WebGovernanceDto } from '../api/client';

const loading = ref(false);
const saving = ref(false);
const loadError = ref('');
const loaded = ref<WebGovernanceDto | null>(null);
const form = reactive({ max_calls_per_turn: 5, max_fetch_bytes_per_turn: 1048576, max_seconds_per_turn: 30 });

function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 403) return '当前账户无权管理联网上限（仅管理员可操作）。';
    if (err.status === 503) return '联网上限存储暂不可用，请稍后重试（服务端不会以默认值冒充）。';
    return err.message || fallback;
  }
  return '无法连接服务，请确认服务已启动。';
}

function fill(dto: WebGovernanceDto): void {
  loaded.value = dto;
  form.max_calls_per_turn = dto.max_calls_per_turn;
  form.max_fetch_bytes_per_turn = dto.max_fetch_bytes_per_turn;
  form.max_seconds_per_turn = dto.max_seconds_per_turn;
}

async function load(): Promise<void> {
  loading.value = true;
  loadError.value = '';
  try {
    fill(await client.getWebGovernance());
  } catch (err) {
    loadError.value = messageOf(err, '加载联网上限失败。');
  } finally {
    loading.value = false;
  }
}

async function save(): Promise<void> {
  saving.value = true;
  try {
    fill(
      await client.putWebGovernance({
        max_calls_per_turn: Number(form.max_calls_per_turn),
        max_fetch_bytes_per_turn: Number(form.max_fetch_bytes_per_turn),
        max_seconds_per_turn: Number(form.max_seconds_per_turn),
      }),
    );
    ElMessage.success('联网上限已保存，对新回合立即生效');
  } catch (err) {
    ElMessage.error(messageOf(err, '保存联网上限失败。'));
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="web-governance">
    <div class="head">
      <div>
        <h2 class="ib-page-title">联网上限</h2>
        <p class="ib-page-sub">
          每个回合内顾问可使用的联网调用上限（全局）。项目内的联网授权参数只能在此范围内调低；超出会在保存配置时被拒绝。
        </p>
      </div>
    </div>

    <el-alert v-if="loadError" type="error" :closable="false" show-icon :title="loadError" class="load-error" />

    <el-card v-loading="loading" class="ib-card">
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="每回合联网调用次数上限">
          <el-input-number
            v-model="form.max_calls_per_turn"
            :min="1"
            :max="loaded?.hard_max.max_calls_per_turn ?? 20"
            :step="1"
          />
          <span class="ib-muted unit">次（1 ~ {{ loaded?.hard_max.max_calls_per_turn ?? 20 }}）</span>
        </el-form-item>
        <el-form-item label="每回合网页抓取总字节上限">
          <el-input-number
            v-model="form.max_fetch_bytes_per_turn"
            :min="10000"
            :max="loaded?.hard_max.max_fetch_bytes_per_turn ?? 5242880"
            :step="10000"
          />
          <span class="ib-muted unit">字节（10000 ~ {{ loaded?.hard_max.max_fetch_bytes_per_turn ?? 5242880 }}）</span>
        </el-form-item>
        <el-form-item label="每回合联网累计耗时上限">
          <el-input-number
            v-model="form.max_seconds_per_turn"
            :min="1"
            :max="loaded?.hard_max.max_seconds_per_turn ?? 120"
            :step="1"
          />
          <span class="ib-muted unit">秒（1 ~ {{ loaded?.hard_max.max_seconds_per_turn ?? 120 }}）</span>
        </el-form-item>
      </el-form>
      <div class="actions">
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        <el-button :disabled="loading" @click="load">重新载入</el-button>
      </div>
      <p class="ib-muted meta">
        最后更新：{{ loaded?.updated_at || '—' }}（{{ loaded?.updated_by || '—' }}）。
        尚未设置时使用保守默认值（5 次 / 1048576 字节 / 30 秒）。
      </p>
    </el-card>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.load-error {
  margin-bottom: 12px;
}

.unit {
  margin-left: 12px;
  font-size: 12px;
}

.actions {
  display: flex;
  gap: 12px;
}

.meta {
  font-size: 12px;
  margin-top: 12px;
}
</style>
