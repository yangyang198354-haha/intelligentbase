/**
 * @module MOD-IB-24
 * @implements IFC-IB-256/257/258 类型声明（.vue 单文件组件与 Vite 环境）
 * @author software-developer
 *
 * 没有这个文件时 `import App from './App.vue'` 在 `vue-tsc` 下会报
 * TS2307（找不到模块），于是 `npm run build` 的 typecheck 关卡形同虚设 ——
 * 而该关卡正是本前端唯一能拦住「后端契约字段名写错」的机制。
 */
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue';

  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>;
  export default component;
}
