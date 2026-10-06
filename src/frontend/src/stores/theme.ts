/**
 * @module MOD-IB-24
 * @implements IFC-IB-328 深浅色主题切换（运维控制台外壳）
 * @author software-developer
 *
 * 主题状态的**唯一**持有者。
 *
 * 只做一件事：把 `light | dark` 写到 `<html>` 的 `data-theme` 属性与 `dark` 类上。
 * 前者驱动本项目的令牌（`styles/theme.css`），后者驱动 Element Plus 的深色变量 ——
 * 两个开关必须**同时**设置，只设一个会出现「自家卡片变深了，组件库控件还是白的」。
 *
 * ## 为什么**不**持久化主题偏好（这是一个刻意的取舍）
 *
 * 直觉做法是写 `localStorage`。本项目**不**这么做，原因有两条：
 *
 *   1. **与既有纪律冲突**：`scripts/selfcheck.py` 的 `frontend_config_discipline`
 *      对前端源码做「视图侧零持久化（ADR-14）」的全仓断言 —— 其目标是保证「配置真源只有
 *      定义文档一个」。为一个 UI 偏好去放宽这条断言，会把「哪些持久化是允许的」变成
 *      需要逐案判断的问题，而这正是该断言当初要消除的东西。
 *   2. **不引入未登记的键名**：`tech_stack §1.4` 只登记了两个客户端键名
 *      （`IB_AUTH_LOGIN_PATH` / `IB_AUTH_SESSION_STORAGE_KEY`）。新增一个存储键属于
 *      「悄悄扩大对外契约」，应当先回设计登记，而不是在实现里顺手加。
 *
 * 因此主题偏好是**会话内**的，并在每次加载时回到 `prefers-color-scheme`（系统偏好）。
 * 对绝大多数用户而言这正是他们期望的结果 —— 切到深色通常是「系统就是深色」。
 * 若 PM 裁决需要跨会话记忆，正确顺序是：先登记键名 → 再在此处持久化（见遗留 MINOR）。
 */

import { computed, ref } from 'vue';

export type ThemeName = 'light' | 'dark';

/** 系统偏好（`prefers-color-scheme`）。无法探测时取浅色（保守，不擅自替用户决定）。 */
function preferred(): ThemeName {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

const current = ref<ThemeName>('light');

/** 把主题名应用到文档根（唯一副作用发生地）。 */
function apply(name: ThemeName): void {
  const root = document.documentElement;
  root.setAttribute('data-theme', name);
  root.classList.toggle('dark', name === 'dark');
}

export function initTheme(): void {
  current.value = preferred();
  apply(current.value);
}

export function useTheme() {
  const isDark = computed(() => current.value === 'dark');
  function set(name: ThemeName): void {
    current.value = name;
    apply(name);
  }
  function toggle(): void {
    set(current.value === 'dark' ? 'light' : 'dark');
  }
  return { theme: current, isDark, setTheme: set, toggleTheme: toggle };
}
