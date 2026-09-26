<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-256 / 257 / 258 页面宿主与导航
 * @author sub_agent_software_developer
 *
 * 应用外壳：令牌输入 + 三个页面的切换。
 *
 * ## 为什么用 `ref` 切页而不是 vue-router
 *
 * 只有 3 个页面、且都以「查询参数 + 刷新」为代价换不来任何东西；引入 router 会多一层
 * 依赖（影响树莓派上的静态资源体积）并带来 history 模式的 nginx `try_files` 配置要求。
 * 当页面数量或深链接需求增长时再引入 —— 迁移成本主要在 `currentView` 一处。
 */
import { computed, ref } from 'vue';

import ChatPage from './views/ChatPage.vue';
import RebuildPage from './views/RebuildPage.vue';
import UploadPage from './views/UploadPage.vue';
import type { ApiClient } from './api/client';

const props = defineProps<{ client: ApiClient }>();

type ViewKey = 'upload' | 'chat' | 'rebuild';

const VIEWS: { key: ViewKey; label: string }[] = [
  { key: 'upload', label: '资料管理' },
  { key: 'chat', label: '知识问答' },
  { key: 'rebuild', label: '索引重建' },
];

const current = ref<ViewKey>('chat');
const tokenDraft = ref('');
const tokenSet = ref(Boolean(props.client.token));
/** 全局横幅消息（令牌缺失、401 等）；页面内错误各自展示。 */
const notice = ref('');

const activeComponent = computed(() => {
  if (current.value === 'upload') return UploadPage;
  if (current.value === 'rebuild') return RebuildPage;
  return ChatPage;
});

/** 子页面在收到 401 时调用，回到「未认证」态而不是白屏。 */
function onUnauthorized(): void {
  props.client.clearToken();
  tokenSet.value = false;
  notice.value = '登录状态已失效，请重新填写访问令牌。';
}

function saveToken(): void {
  props.client.setToken(tokenDraft.value.trim());
  tokenSet.value = Boolean(props.client.token);
  tokenDraft.value = '';
  notice.value = '';
}

function switchView(key: ViewKey): void {
  current.value = key;
  notice.value = '';
}
</script>

<template>
  <div class="shell">
    <header>
      <h1>企业知识库基座</h1>
      <nav>
        <button
          v-for="view in VIEWS"
          :key="view.key"
          type="button"
          :class="{ active: current === view.key }"
          :disabled="!tokenSet"
          @click="switchView(view.key)"
        >
          {{ view.label }}
        </button>
      </nav>
    </header>

    <p v-if="notice" class="notice">{{ notice }}</p>

    <!--
      未认证时**阻断全部功能**并明确提示。刻意不做「降级为匿名只读」：后端对未带令牌的
      请求一律 401，前端若仍渲染空白表格，用户会以为是「没有数据」而不是「没登录」。
    -->
    <section v-if="!tokenSet" class="gate">
      <h2>需要访问令牌</h2>
      <p>本系统不使用 Cookie 会话，令牌经请求头 <code>Authorization</code> 显式传递。</p>
      <form @submit.prevent="saveToken">
        <input
          v-model="tokenDraft"
          type="password"
          autocomplete="off"
          placeholder="粘贴访问令牌"
          aria-label="访问令牌"
        />
        <button type="submit" :disabled="!tokenDraft.trim()">进入</button>
      </form>
    </section>

    <main v-else>
      <component :is="activeComponent" :client="client" @unauthorized="onUnauthorized" />
    </main>
  </div>
</template>

<style scoped>
.shell {
  font-family: system-ui, -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif;
  max-width: 1080px;
  margin: 0 auto;
  padding: 16px;
  color: #1f2328;
}
header {
  display: flex;
  align-items: baseline;
  gap: 24px;
  border-bottom: 1px solid #d8dee4;
  padding-bottom: 8px;
}
h1 {
  font-size: 18px;
  margin: 0;
}
nav {
  display: flex;
  gap: 8px;
}
nav button {
  background: none;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  color: #57606a;
}
nav button.active {
  border-color: #0969da;
  color: #0969da;
}
nav button:disabled {
  color: #b1bac4;
  cursor: not-allowed;
}
.notice {
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 6px;
  padding: 8px 12px;
}
.gate {
  max-width: 420px;
  margin: 80px auto;
  text-align: center;
}
.gate form {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
.gate input {
  flex: 1;
  padding: 8px;
  border: 1px solid #d8dee4;
  border-radius: 6px;
}
</style>
