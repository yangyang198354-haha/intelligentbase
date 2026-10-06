<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 登录页（用户名 + 口令；替代 R1~R12 的「粘贴访问令牌」入口）
 * @depends MOD-IB-24（app/env 会话单例）, MOD-IB-23（IFC-IB-316）
 * @author software-developer
 *
 * 登录页。
 *
 * ## 为什么登录失败**只**给一句「用户名或口令不正确」
 *
 * 服务端刻意把「用户不存在」「口令错误」「账户停用」合并成同一个 401（防存在性 / 状态
 * 探测预言机）。前端若把三者拆开提示，等于**替攻击者**把服务端好不容易合并掉的信息又
 * 分开输出。同理，`429`（条件性限速）可以独立提示 —— 它不泄露任何账户信息。
 *
 * ## 口令不进任何日志 / 存储
 *
 * 口令只存在于本组件的 `ref` 中，提交后立即清空；**不**写 URL、**不**写
 * `sessionStorage`、**不**进控制台日志。`autocomplete` 用 `current-password` 让
 * 浏览器密码管理器正常工作（这是**允许**的：本机密码管理器不属「服务端记录凭据」）。
 */
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

import { session } from '../app/env';
import { ApiClientError } from '../api/client';

const router = useRouter();
const route = useRoute();

const username = ref('');
const password = ref('');
const submitting = ref(false);
const errorText = ref('');

const canSubmit = computed(
  () => username.value.trim().length > 0 && password.value.length > 0 && !submitting.value,
);

/** 登录后要去的地方：优先 `?next=`（守卫带过来的原目标），否则首页。 */
function landing(): string {
  const next = route.query.next;
  if (typeof next === 'string' && next.startsWith('/') && !next.startsWith('//')) return next;
  return '/';
}

async function submit(): Promise<void> {
  if (!canSubmit.value) return;
  submitting.value = true;
  errorText.value = '';
  try {
    const user = await session.login(username.value.trim(), password.value);
    password.value = '';
    // 改密态由路由守卫统一收敛到改密页（服务端才是强制者，前端只负责引导）。
    await router.replace(landing());
    if (!user.must_change_password) ElMessage.success('登录成功');
  } catch (err) {
    password.value = '';
    if (err instanceof ApiClientError) {
      errorText.value =
        err.status === 429
          ? '登录尝试过于频繁，请稍后再试。'
          : err.status === 401
            ? '用户名或口令不正确。'
            : err.message || '登录失败，请稍后重试。';
    } else {
      errorText.value = '无法连接服务，请确认服务已启动。';
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <section class="panel">
      <header class="brand">
        <div class="mark" aria-hidden="true">知</div>
        <div>
          <h1>企业知识库基座</h1>
          <p class="ib-muted">请使用账户登录</p>
        </div>
      </header>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input
            v-model="username"
            size="large"
            autocomplete="username"
            placeholder="请输入用户名"
            :disabled="submitting"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-form-item label="口令">
          <el-input
            v-model="password"
            type="password"
            size="large"
            show-password
            autocomplete="current-password"
            placeholder="请输入口令"
            :disabled="submitting"
            @keyup.enter="submit"
          />
        </el-form-item>

        <el-alert
          v-if="errorText"
          class="login-error"
          type="error"
          :closable="false"
          show-icon
          :title="errorText"
        />

        <el-button
          type="primary"
          size="large"
          class="submit"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="submit"
        >
          登录
        </el-button>
      </el-form>

      <p class="hint ib-muted">
        会话凭据经请求头 <code>Authorization</code> 传递，不使用 Cookie 会话。
      </p>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--ib-bg);
}

.panel {
  width: 100%;
  max-width: 380px;
  background: var(--ib-bg-elevated);
  border: 1px solid var(--ib-border);
  border-radius: var(--ib-radius);
  box-shadow: var(--ib-shadow-md);
  padding: 32px 28px 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.mark {
  width: 40px;
  height: 40px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--ib-accent);
  color: #fff;
  font-size: 20px;
  font-weight: 600;
}

.brand h1 {
  font-size: 18px;
  margin: 0;
}

.brand p {
  margin: 2px 0 0;
  font-size: 13px;
}

.login-error {
  margin-bottom: 12px;
}

.submit {
  width: 100%;
  margin-top: 4px;
}

.hint {
  margin: 16px 0 0;
  font-size: 12px;
  text-align: center;
}
</style>
