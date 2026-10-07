/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 登录页路由 + IFC-IB-328 控制台外壳路由 + 路由守卫
 *             IFC-IB-376（REV-18）父级「系统管理」节点 + 三子项（账户 / 项目 / LLM Key）+ 旧路由迁移
 * @depends MOD-IB-24（app/env 单例）
 * @author software-developer
 *
 * 路由表与**准入守卫**（R13）。
 *
 * ## 为什么用 hash 模式（`createWebHashHistory`）
 *
 * history 模式下刷新 `/accounts` 这类深链接会直接打到服务端，而本服务是 Django + Waitress
 * 静态托管，**没有** `try_files` 回退 → 刷新即 404。要么在 nginx 加回退规则（多一处部署
 * 依赖），要么用 hash 模式（`/#/accounts`，服务端永远只看到 `/`）。后者少一处配置、
 * 少一类「本地能跑线上 404」的缺陷，故取 hash。
 *
 * ## 守卫**只做体验**，不承担安全
 *
 * 守卫挡的是「未登录看到控制台骨架」这种体验问题。真正的准入在服务端：无令牌一律 401、
 * 改密态一律 403、非 admin 的账户接口一律 403。守卫被绕过（改 hash 直连路由）不会
 * 泄露任何数据 —— 页面拿不到 401/403 之外的响应。**禁止**在任何守卫里写「因为前端
 * 判断过了所以跳过服务端校验」这类逻辑。
 */

import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router';

import { client, session } from '../app/env';

import LoginPage from '../views/LoginPage.vue';
import ChangePasswordPage from '../views/ChangePasswordPage.vue';
import ConsoleLayout from '../layouts/ConsoleLayout.vue';
import ChatPage from '../views/ChatPage.vue';
import UploadPage from '../views/UploadPage.vue';
import RebuildPage from '../views/RebuildPage.vue';
import ConfigPage from '../views/ConfigPage.vue';
import AccountsPage from '../views/AccountsPage.vue';
// REV-18（IFC-IB-376 / ADR-42）：系统管理三分 IA 的父级容器与新页面。
import SystemSection from '../views/SystemSection.vue';
import ProjectsPage from '../views/ProjectsPage.vue';
import LlmKeyPage from '../views/LlmKeyPage.vue';

/** 公共路由（不需要登录）。 */
const PUBLIC_ROUTES = new Set(['login']);

/** 改密态下**唯一**可达的页面（与服务端的 403 白名单一一对应，见 ibweb/authz.py）。 */
const PASSWORD_CHANGE_ROUTE = 'change-password';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { title: '登录', public: true },
  },
  {
    path: '/change-password',
    name: PASSWORD_CHANGE_ROUTE,
    component: ChangePasswordPage,
    meta: { title: '修改口令' },
  },
  {
    path: '/',
    component: ConsoleLayout,
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'chat',
        component: ChatPage,
        // 既有页面保持 `client` 经 props 注入的契约（R1~R12 不变）。
        props: () => ({ client }),
        meta: { title: '知识问答' },
      },
      {
        path: 'files',
        name: 'files',
        component: UploadPage,
        props: () => ({ client }),
        meta: { title: '资料管理' },
      },
      {
        path: 'rebuild',
        name: 'rebuild',
        component: RebuildPage,
        props: () => ({ client }),
        meta: { title: '索引重建' },
      },
      {
        path: 'config',
        name: 'config',
        component: ConfigPage,
        props: () => ({ client }),
        meta: { title: '可视化配置' },
      },
      // REV-18（IFC-IB-376 / ADR-42）：父级「系统管理」节点，下挂三子项。
      // **授权与导航解耦（强制）**：父 / 子路由的 `requiresAdmin` 只是体验优化；
      // 授权唯一经服务端（注入的 `AuthzPolicy`）—— 非 admin 一律服务端 403。
      // 父级是**路由结构**上的分组（透传 `<router-view>`），视觉外壳仍由 ConsoleLayout 提供。
      {
        path: 'system',
        component: SystemSection,
        meta: { requiresAdmin: true },
        children: [
          {
            path: 'accounts',
            name: 'accounts',
            component: AccountsPage,
            meta: { title: '账户管理', requiresAdmin: true },
          },
          {
            path: 'projects',
            name: 'projects',
            component: ProjectsPage,
            meta: { title: '项目管理', requiresAdmin: true },
          },
          {
            path: 'llm-key',
            name: 'llm-key',
            component: LlmKeyPage,
            meta: { title: 'LLM Key 管理', requiresAdmin: true },
          },
        ],
      },
      // 既有深链 `#/accounts` 的**迁移**（ADR-42 ③：保留 hash，不引入 `try_files`）：
      // 旧路径重定向到新的三分 IA 路由，避免书签 / 深链失效。
      { path: 'accounts', redirect: { name: 'accounts' } },
    ],
  },
  // 未匹配：回首页（由首页守卫再决定去登录还是去控制台）。
  { path: '/:pathMatch(.*)*', redirect: '/' },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const isPublic = to.meta.public === true || PUBLIC_ROUTES.has(String(to.name ?? ''));

  // 1) 先用本地令牌确认身份（仅在第一次导航时真正请求 `/api/auth/me`）。
  await session.bootstrap();
  const authed = session.isAuthenticated.value;

  // 2) 未登录 → 登录页（已登录时访问登录页 → 送回控制台，避免「登录成功后又看到登录页」）。
  if (!authed) {
    return isPublic ? true : { name: 'login', query: to.fullPath === '/' ? {} : { next: to.fullPath } };
  }
  if (String(to.name ?? '') === 'login') {
    return { path: '/' };
  }

  // 3) 改密态：服务端只放行三个端点，前端把可达页面收敛到改密页（体验层面的强提示）。
  if (session.mustChangePassword.value && String(to.name ?? '') !== PASSWORD_CHANGE_ROUTE) {
    return { name: PASSWORD_CHANGE_ROUTE };
  }
  if (!session.mustChangePassword.value && String(to.name ?? '') === PASSWORD_CHANGE_ROUTE) {
    return { path: '/' };
  }

  // 4) 管理员专属页面。
  if (to.meta.requiresAdmin === true && !session.isAdmin.value) {
    return { name: 'chat' };
  }

  return true;
});

router.afterEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : '';
  document.title = title ? `${title} · 企业知识库基座` : '企业知识库基座';
});
