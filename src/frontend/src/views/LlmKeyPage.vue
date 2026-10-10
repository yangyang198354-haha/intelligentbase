<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-376（REV-18）LLM Key 管理页（写入 / 清除；**仅 admin**）
 * @depends MOD-IB-24（app/env 单例）, MOD-IB-23（IFC-IB-374）
 * @author software-developer
 *
 * LLM Key 管理（管理员）——「系统管理 → LLM Key 管理」。
 *
 * ## 凭据纪律（硬约束，C-IB-42 / REQ-NFR-IB-20）
 *
 *   * 界面**只显示** `configured` / `masked` / `updated_at`，**永不**回显明文；
 *   * `masked` 是服务端固定占位掩码（不含明文任何前 / 后缀字符）；前端**不**自行拼掩码；
 *   * 写入用 `type="password"`，提交后**立即清空**输入框；明文**不**入任何前端状态外的日志；
 *   * 唯一写入口 = `PUT /api/llm-key`。
 *
 * ## 生效口径显式提示（ADR-32 / IFC-IB-376）
 *
 * 本页**不得**出现任何「即时生效」暗示：保存 / 清除后须**重启 `ib-web` / `ib-worker`**
 * 才重新装配生效，**重启由用户手工执行**（代理不执行生产重启）。
 */
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import { client } from '../app/env';
import { ApiClientError, type LlmKeyStatus } from '../api/client';

const status = ref<LlmKeyStatus | null>(null);
const loading = ref(false);
const loadError = ref('');

const secret = ref('');
const saving = ref(false);
const clearing = ref(false);

const configured = computed(() => status.value?.configured === true);

function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 403) return '当前账户无权管理 LLM Key（仅管理员可操作）。';
    if (err.status === 400) return err.message || 'Key 不能为空。';
    return err.message || fallback;
  }
  return '无法连接服务，请确认服务已启动。';
}

// 后端返回 UTC ISO（如 2026-10-07T09:46:52Z），界面按本地时区显示为
// yyyy-mm-dd hh:mm:ss（Anthropic 风格：时间一律本地、可读）。
function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

async function load(): Promise<void> {
  loading.value = true;
  loadError.value = '';
  try {
    status.value = await client.llmKeyStatus();
  } catch (err) {
    loadError.value = messageOf(err, '加载 LLM Key 状态失败。');
  } finally {
    loading.value = false;
  }
}

async function save(): Promise<void> {
  const value = secret.value.trim();
  if (!value) {
    ElMessage.warning('请输入 Key');
    return;
  }
  saving.value = true;
  try {
    status.value = await client.setLlmKey(value);
    secret.value = ''; // 明文立即清空，不留驻组件状态
    ElMessage.success('Key 已保存；**重启 ib-web / ib-worker 后生效**（重启由用户手工执行）');
  } catch (err) {
    ElMessage.error(messageOf(err, '保存 Key 失败。'));
  } finally {
    saving.value = false;
  }
}

async function clear(): Promise<void> {
  try {
    await ElMessageBox.confirm(
      '清除后，服务重启将以「未配置」态启动：依赖 LLM 的功能（问答 / 路由 / 聚合）将 fail-closed。确定继续？',
      '清除 LLM Key',
      { confirmButtonText: '清除', cancelButtonText: '取消', type: 'warning' },
    );
  } catch {
    return; // 用户取消
  }
  clearing.value = true;
  try {
    await client.clearLlmKey();
    status.value = { configured: false, masked: '', updated_at: null };
    ElMessage.success('Key 已清除；**重启 ib-web / ib-worker 后生效**（重启由用户手工执行）');
  } catch (err) {
    ElMessage.error(messageOf(err, '清除 Key 失败。'));
  } finally {
    clearing.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="llm-key">
    <div class="head">
      <div>
        <h2 class="ib-page-title">LLM Key 管理</h2>
        <p class="ib-page-sub">
          全局唯一 Key（单行存储）。界面只显示是否已配置与掩码，**不回显明文**。
        </p>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      type="error"
      :closable="false"
      show-icon
      :title="loadError"
      class="load-error"
    />

    <el-card class="ib-card" v-loading="loading">
      <div class="status-row">
        <span class="label">当前状态</span>
        <el-tag v-if="configured" type="success" disable-transitions>已配置</el-tag>
        <el-tag v-else type="info" disable-transitions>未配置</el-tag>
      </div>
      <div class="status-row">
        <span class="label">掩码</span>
        <span class="mono">{{ configured ? status?.masked : '—' }}</span>
      </div>
      <div class="status-row">
        <span class="label">最后更新</span>
        <span class="mono">{{ fmtDate(status?.updated_at) }}</span>
      </div>

      <el-divider />

      <el-form label-position="top" @submit.prevent>
        <el-form-item label="写入 / 覆盖 Key">
          <el-input
            v-model="secret"
            type="password"
            show-password
            autocomplete="off"
            placeholder="粘贴 DeepSeek API Key（仅提交给服务端，不在前端留存）"
            @keyup.enter="save"
          />
        </el-form-item>
      </el-form>
      <div class="actions">
        <el-button type="primary" :loading="saving" @click="save">保存 Key</el-button>
        <el-button type="danger" plain :loading="clearing" :disabled="!configured" @click="clear">
          清除 Key
        </el-button>
      </div>

      <el-alert
        class="effect-hint"
        type="warning"
        :closable="false"
        show-icon
        title="保存 / 清除后不即时生效：须重启 ib-web / ib-worker 重新装配后方生效（重启由用户手工执行）。"
      />
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

.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
}

.label {
  width: 96px;
  color: var(--ib-text-muted);
  font-size: 13px;
}

.mono {
  font-family: var(--ib-font-mono, monospace);
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.effect-hint {
  margin-top: 16px;
}

.form-hint {
  font-size: 12px;
  margin: 0;
}
</style>
