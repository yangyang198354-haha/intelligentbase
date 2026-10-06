/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 / 328 应用引导（路由 + 主题 + 会话）
 * @author software-developer
 *
 * 应用入口（R13 重写）。
 *
 * ## 令牌不再从 URL 读
 *
 * R1~R12 在此处有一条「从 `?token=` 迁移旧令牌」的兼容分支。R13 **删除**了它：
 * 登录改为用户名 + 口令（IFC-IB-316），令牌由 `POST /api/auth/login` 返回并由
 * `ApiClient` 写入 `sessionStorage` —— URL 里**不存在**任何把令牌传进来的合法途径。
 * 留着兼容分支等于保留一条「令牌可经 URL 进入系统」的通道（会被 nginx 访问日志完整
 * 记录，FreeArk 已因此泄露过一次），与 R13 的纪律直接冲突。
 *
 * ## 401 的全局处理在这里接上
 *
 * `client.ts` 在**唯一**的 401 发生点回调一次，此处把它接到会话层：清态并跳登录页。
 * 页面因此不再需要各自监听 `unauthorized`（R1~R12 的 `@unauthorized` 写法仍可用，
 * 但新页面不必再接）。
 */

import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import zhCn from 'element-plus/es/locale/lang/zh-cn';
// Element Plus 基础样式与**深色变量**（后者提供 html.dark 下的组件配色）
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';

import './styles/theme.css';

import App from './App.vue';
import { client, projectContext, session } from './app/env';
import { router } from './router';
import { initTheme } from './stores/theme';
import { setUnauthorizedHandler } from './api/client';

initTheme();

// 全局 401：清会话态 + 回登录页。用 `replace` 而非 `push`，避免用户按「后退」又回到
// 一个必然 401 的页面（那会形成「后退 → 401 → 跳登录 → 后退」的死循环观感）。
// R14：同时清空项目上下文 —— 否则「当前项目」会跨会话残留，落到下一个登录者头上。
setUnauthorizedHandler(() => {
  session.clear();
  projectContext.clear();
  const current = router.currentRoute.value;
  if (current.name !== 'login') {
    void router.replace({ name: 'login', query: { next: current.fullPath } });
  }
});

const app = createApp(App);
app.use(ElementPlus, { locale: zhCn });
app.use(router);
app.mount('#app');

// 会话续期（IFC-IB-320）：临近到期时静默延长，避免用户正打字时被踢回登录页。
// 15 分钟一次是保守取值 —— 真正的「是否该延长」由服务端按 renew 窗口决定。
const RENEW_INTERVAL_MS = 15 * 60 * 1000;
window.setInterval(() => {
  if (client.token) void session.renew();
}, RENEW_INTERVAL_MS);
