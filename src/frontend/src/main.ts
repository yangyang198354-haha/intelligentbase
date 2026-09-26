/**
 * @module MOD-IB-24
 * @implements IFC-IB-256/257/258 应用引导
 * @author software-developer
 *
 * 应用入口。
 *
 * ## 令牌为什么从 `sessionStorage` 读，而不是从 URL 读
 *
 * 支持 `?token=` 会把令牌写进浏览器历史、Referer 头与 nginx 访问日志 ——
 * FreeArk 已经因为 WS 令牌出现在查询串而泄露过一次。因此前端**只在启动时**从
 * `sessionStorage` 取令牌；没有就引导用户经密码框输入（或由接入方的统一登录页写入）。
 * `sessionStorage` 而非 `localStorage`：关闭标签页即失效，减少共享设备上的长期暴露。
 */
import { createApp } from 'vue';

import App from './App.vue';
import { apiClient } from './api/client';

// 一次性迁移：若旧版把令牌放在 URL 上，取出来立刻从地址栏抹掉（避免继续被日志记录），
// 且**不**保留在 history 里。
const urlToken = new URLSearchParams(window.location.search).get('token');
if (urlToken) {
  sessionStorage.setItem('ib_token', urlToken);
  const cleaned = window.location.pathname + window.location.hash;
  window.history.replaceState(null, '', cleaned);
}

createApp(App, { client: apiClient }).mount('#app');
