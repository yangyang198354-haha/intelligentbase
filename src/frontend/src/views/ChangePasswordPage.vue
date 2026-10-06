<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 首次登录强制改密页（服务端受限会话的可视化）
 * @depends MOD-IB-24（app/env 会话单例）, MOD-IB-23（IFC-IB-319）
 * @author software-developer
 *
 * 修改口令页（含**首次登录强制改密**）。
 *
 * ## 「强制」在服务端，本页只是它的可视化
 *
 * 改密态（`must_change_password=true`）下服务端只放行三个端点：
 * `GET /api/auth/me`、`POST /api/auth/change-password`、`POST /api/auth/logout`
 * （`ibweb/authz.py` 的 `_CHANGE_PASSWORD_ALLOWLIST`），其余一律 403。
 * 因此本页**不是**安全边界：绕过它（直接改 hash 或用 curl）也拿不到任何其它数据。
 * 它存在的意义是让用户知道「现在必须做这件事」，而不是撞一屏幕 403 才反应过来。
 *
 * ## 强度校验在服务端，前端只做同一份规则的**提前提示**
 *
 * 前端按长度做即时提示，但**最终裁决**是服务端（`validate_password_strength`）。
 * 前端放行而服务端拒绝时会显示服务端的可读原因 —— 两处不一致最坏是「提示晚一步」，
 * 不会出现「前端说可以、服务端其实不允许然后静默失败」。
 */
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

import { session } from '../app/env';
import { ApiClientError } from '../api/client';

const router = useRouter();

const oldPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const submitting = ref(false);
const errorText = ref('');

const forced = computed(() => session.mustChangePassword.value);
const minLength = 8;

const localProblem = computed(() => {
  if (newPassword.value && newPassword.value.length < minLength) return `新口令至少 ${minLength} 位`;
  if (confirmPassword.value && newPassword.value !== confirmPassword.value) return '两次输入的新口令不一致';
  return '';
});

const canSubmit = computed(
  () =>
    oldPassword.value.length > 0 &&
    newPassword.value.length >= minLength &&
    newPassword.value === confirmPassword.value &&
    !submitting.value,
);

async function submit(): Promise<void> {
  if (!canSubmit.value) return;
  submitting.value = true;
  errorText.value = '';
  try {
    await session.changePassword(oldPassword.value, newPassword.value);
    oldPassword.value = '';
    newPassword.value = '';
    confirmPassword.value = '';
    ElMessage.success('口令已更新');
    await router.replace('/');
  } catch (err) {
    oldPassword.value = '';
    if (err instanceof ApiClientError) {
      errorText.value = err.message || '修改失败，请重试。';
    } else {
      errorText.value = '无法连接服务，请确认服务已启动。';
    }
  } finally {
    submitting.value = false;
  }
}

async function signOut(): Promise<void> {
  await session.logout();
  await router.replace({ name: 'login' });
}
</script>

<template>
  <div class="change-page">
    <section class="panel">
      <h1>{{ forced ? '首次登录，请修改口令' : '修改口令' }}</h1>
      <p class="ib-muted sub">
        {{
          forced
            ? '为保障账户安全，首次登录必须先设置新口令。在此之前，除本页外的功能均不可用。'
            : '修改成功后，其它已登录的会话将被注销。'
        }}
      </p>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item :label="forced ? '当前口令（初始口令）' : '当前口令'">
          <el-input
            v-model="oldPassword"
            type="password"
            show-password
            autocomplete="current-password"
            :disabled="submitting"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-form-item :label="`新口令（至少 ${minLength} 位，含大小写 / 数字 / 符号中 2 类）`">
          <el-input
            v-model="newPassword"
            type="password"
            show-password
            autocomplete="new-password"
            :disabled="submitting"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-form-item label="确认新口令">
          <el-input
            v-model="confirmPassword"
            type="password"
            show-password
            autocomplete="new-password"
            :disabled="submitting"
            @keyup.enter="submit"
          />
        </el-form-item>

        <p v-if="localProblem" class="local-problem">{{ localProblem }}</p>
        <el-alert v-if="errorText" type="error" :closable="false" show-icon :title="errorText" />

        <div class="actions">
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="submit"
          >
            确认修改
          </el-button>
          <el-button size="large" :disabled="submitting" @click="signOut">退出登录</el-button>
        </div>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
.change-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--ib-bg);
}

.panel {
  width: 100%;
  max-width: 420px;
  background: var(--ib-bg-elevated);
  border: 1px solid var(--ib-border);
  border-radius: var(--ib-radius);
  box-shadow: var(--ib-shadow-md);
  padding: 32px 28px;
}

.panel h1 {
  font-size: 18px;
  margin: 0 0 6px;
}

.sub {
  font-size: 13px;
  margin: 0 0 20px;
}

.local-problem {
  color: var(--ib-warning);
  font-size: 13px;
  margin: 0 0 10px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.actions .el-button {
  flex: 1;
}
</style>
