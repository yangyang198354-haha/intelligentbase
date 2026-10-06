/**
 * @module MOD-IB-24
 * @implements IFC-IB-335 项目上下文 store（当前项目选择与传播；`available` / `current` /
 *             `select` / `headerValue`；ops 不可切换）
 * @depends MOD-IB-23（IFC-IB-333 HTTP 契约，仅契约）
 * @author software-developer
 *
 * 「当前项目」的**唯一**持有者（R14）。
 *
 * ## 为什么不用 Pinia
 *
 * 与 `stores/session.ts` **同构**（模块级 `reactive` + `computed` + 动作）：项目上下文只有
 * 「一个列表 + 一个当前项 + 几个动作」，模块级状态足够。引入 Pinia 会多一层依赖与一套需要
 * 跟随升级的 API，换来的收益（跨模块共享、devtools）在本规模下不成立（沿用 `session.ts`
 * 的既有理由）。
 *
 * ## fail-closed：`current` 为空 ⇒ 不注入头
 *
 * `headerValue()` 在 `current === null` 时返回**空对象** —— `client.ts` 据此**不注入**
 * `X-IB-Project`，服务端 `effective_project` 取全局哨兵，项目级端点继续 fail-closed
 * （**未选项目即不泄露**，ADR-28 约束③）。这是**刻意保留**的纪律，不是「未实现的默认」。
 *
 * ## ops 结构上不可切换（三重）
 *
 *   1. 服务端项目列表对 ops 只回其自身项目（`IFC-IB-333`，长度恒为 1）；
 *   2. 本 store 的 `select()` **仅 admin 生效**（ops 调用为 no-op）；
 *   3. 服务端对「头值 ≠ 绑定项目」的 ops 请求返回 `403 project_mismatch`（`IFC-IB-334`）。
 *
 * ## 切换项目后必须重置项目内视图态
 *
 * `select()` 只改 `current`；**重置**由 `ConsoleLayout.vue` 对 `<router-view>` 施加
 * `:key="projectContext.current ?? 'none'"` 完成 —— 切换即强制重挂载现有页面，销毁其组件内
 * 状态（会话历史 / 文件列表 / 可视化草稿），避免「旧项目数据显示在新项目下」的**串项显示**。
 */

import { computed, reactive } from 'vue';

import type { ApiClient, ProjectSummary } from '../api/client';

type ProjectState = {
  /** 当前主体**可见**的项目集合（由服务端裁定：admin 全部 / ops 仅自身）。 */
  available: ProjectSummary[];
  /** 当前项目 id；`null` = **未选择** ⇒ `headerValue()` 返回空对象（不注入头）。 */
  current: string | null;
  /** 最近一次 `load` 的错误文案（供界面提示）；**不含**任何凭据值。 */
  error: string;
};

export function createProjectContext(api: ApiClient) {
  const state = reactive<ProjectState>({ available: [], current: null, error: '' });

  /** 当前主体角色（由 `load` 记录）；`select` 据此限制为「仅 admin 可调用」。 */
  let role: 'admin' | 'ops' | null = null;

  const isSelected = computed(() => state.current !== null);

  /** 当前项目名（供只读展示 / 选择器标题）；未选中时为空串。 */
  const currentName = computed(
    () => state.available.find((p) => p.project_id === state.current)?.name ?? '',
  );

  /**
   * 项目头的**唯一**取值出口（IFC-IB-335 / 336）。
   *
   * `current` 非空时含键 `X-IB-Project`，否则为空对象。`client.ts` 的 `headers()` 只读本方法。
   */
  function headerValue(): Record<string, string> {
    return state.current ? { 'X-IB-Project': state.current } : {};
  }

  /**
   * 加载可见项目并确定 `current`（IFC-IB-335）。
   *
   * * **ops**：结果集恒为 1 → `current` 锁定为该唯一项（不可切换）；结果集为空（绑定项目
   *   未登记）时保持 `null`（fail-closed，不臆造）。
   * * **admin**：结果集为全部项目 → `current` 缺省为**空**；若结果集**恰为 1 项**则**预选**
   *   该项 —— 即 ADR-28 吸收 Option A 的「单项目预选」便利，**仍显式发送请求头**。
   *
   * 请求失败 ⇒ `current = null`（不注入头，fail-closed）并记录 `error`；**不抛**。
   */
  async function load(role_: 'admin' | 'ops', ownProjectId: string | null): Promise<void> {
    role = role_;
    state.error = '';
    try {
      const items = await api.listProjects();
      state.available = items;
      if (role_ === 'ops') {
        // ops 结果集恒为 1：优先取与账户自身绑定一致的那项，否则取唯一项。
        const own = ownProjectId ? items.find((p) => p.project_id === ownProjectId) : undefined;
        state.current = (own ?? items[0])?.project_id ?? null;
      } else {
        state.current = items.length === 1 ? items[0].project_id : null;
      }
    } catch (exc) {
      state.available = [];
      state.current = null;
      state.error = exc instanceof Error ? exc.message : '项目列表加载失败';
    }
  }

  /**
   * 选择当前项目（**仅 admin 生效**；ops 调用为 no-op）。
   *
   * 只接受 `available` 中可见的项目 id（防止把任意字符串当项目名注入头）。
   * 设置后由 `ConsoleLayout.vue` 的 `<router-view :key>` 重置项目内视图态。
   */
  function select(projectId: string): void {
    if (role !== 'admin') return; // ops 结构上不可切换
    const id = (projectId || '').trim();
    if (!id || !state.available.some((p) => p.project_id === id)) return;
    state.current = id;
  }

  /** 清空（登出 / `401` 时调用）—— 同时清除 `current`，回到「未选项目」的 fail-closed 态。 */
  function clear(): void {
    role = null;
    state.available = [];
    state.current = null;
    state.error = '';
  }

  return { state, isSelected, currentName, headerValue, load, select, clear };
}

export type ProjectContext = ReturnType<typeof createProjectContext>;
