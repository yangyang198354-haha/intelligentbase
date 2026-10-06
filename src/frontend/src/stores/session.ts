/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 登录 / 会话状态（登录、注销、改密态、会话恢复）
 *             IFC-IB-329 类型化 API 客户端的会话侧封装
 * @depends MOD-IB-23（IFC-IB-316~321 HTTP 契约，仅契约）
 * @author software-developer
 *
 * 会话状态的**唯一**持有者（R13）。
 *
 * ## 为什么不用 Pinia
 *
 * 会话只有「一个令牌 + 一个用户对象 + 几个动作」，用一个模块级 `reactive` 足够；
 * 引入 Pinia 会多一层依赖（树莓派上的静态资源体积）与一套需要跟随升级的 API，
 * 换来的收益（跨模块共享、devtools 集成）在本规模下不成立。
 *
 * ## 前端**不**承担「强制」职责
 *
 * 「首次登录必须改密」是**服务端**强制的（ADR-20）：改密态下服务端只放行
 * `/api/auth/me`、`/api/auth/change-password`、`/api/auth/logout`，其余一律 403。
 * 前端把 `must_change_password` 可视化（跳转改密页、隐藏导航）只是**体验**，
 * 绕过前端（直接调接口）依然会被服务端挡住。这里不存在「前端校验即安全」的假设。
 *
 * ## 令牌位置与 R1 一致
 *
 * 仍存 `sessionStorage`（不是 Cookie、不是 `localStorage`）：关闭标签页即失效，
 * 共享设备上暴露面更小。约定由 `ApiClient` 独占读写，本模块只经它的方法间接使用。
 */

import { computed, reactive } from 'vue';

import type { ApiClient, CurrentUser } from '../api/client';

type SessionState = {
  /** 已从服务端确认身份（区别于「本地有令牌但尚未验证」）。 */
  ready: boolean;
  user: CurrentUser | null;
  /** 最近一次会话操作的错误文案（供登录页展示）；**不含**任何凭据值。 */
  error: string;
};

export function createSession(api: ApiClient) {
  const state = reactive<SessionState>({ ready: false, user: null, error: '' });

  const isAuthenticated = computed(() => state.user !== null);
  const isAdmin = computed(() => state.user?.role === 'admin');
  const mustChangePassword = computed(() => state.user?.must_change_password === true);
  const displayName = computed(() => state.user?.username ?? '');

  /** 清除本地会话态（不调服务端；用于 401 或主动登出后的收尾）。 */
  function clear(): void {
    api.clearToken();
    state.user = null;
    state.ready = true;
  }

  /**
   * 用本地令牌向服务端确认身份（刷新页面 / 首次进入时调用）。
   *
   * 令牌无效或已过期 → 清态并返回 `null`（**不抛**）：调用方（路由守卫）据此跳登录页。
   * 这是「令牌是否还有效」的**唯一**判定方式 —— 前端不解析令牌、不猜过期时间。
   */
  async function bootstrap(): Promise<CurrentUser | null> {
    if (state.ready) return state.user;
    if (!api.token) {
      state.ready = true;
      return null;
    }
    try {
      const user = await api.me();
      state.user = user;
    } catch {
      clear();
    } finally {
      state.ready = true;
    }
    return state.user;
  }

  /**
   * 登录。成功后 `state.user` 即为服务端返回的账户摘要。
   *
   * 失败（401 / 429 / 网络）一律抛 `ApiClientError`，由登录页翻成可读文案；
   * 本函数**不**吞掉错误 —— 否则登录页无法区分「口令错」与「服务端不可用」。
   */
  async function login(username: string, password: string): Promise<CurrentUser> {
    state.error = '';
    const result = await api.login(username, password);
    state.user = {
      user_id: result.user.user_id,
      username: result.user.username,
      role: result.user.role,
      project_id: result.user.project_id,
      must_change_password: result.user.must_change_password,
    };
    state.ready = true;
    return state.user;
  }

  /** 改密（含首次登录强制改密）。成功后本地改密态立即清除。 */
  async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.changePassword(oldPassword, newPassword);
    if (state.user) state.user = { ...state.user, must_change_password: false };
  }

  /** 注销：尽力通知服务端撤销会话，随后**无条件**清本地态。 */
  async function logout(): Promise<void> {
    try {
      await api.logout();
    } catch {
      /* 服务端不可达也要完成本地登出，否则用户被卡在「点登出没反应」 */
    } finally {
      clear();
    }
  }

  /**
   * 会话续期（IFC-IB-320）。失败即视为已失效并清态 —— 绝不「续期失败当成功」，
   * 否则用户会在下一次业务请求时才撞到 401，且中间的操作全部丢失。
   */
  async function renew(): Promise<void> {
    if (!api.token) return;
    try {
      await api.renewSession();
    } catch {
      clear();
    }
  }

  return {
    state,
    isAuthenticated,
    isAdmin,
    mustChangePassword,
    displayName,
    bootstrap,
    login,
    logout,
    changePassword,
    renew,
    clear,
  };
}

export type Session = ReturnType<typeof createSession>;
