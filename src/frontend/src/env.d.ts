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

/**
 * R13：客户端配置键（tech_stack §1.4 登记键名的构建期对应物）。
 *
 * 只声明**类型**，不给任何值 —— 值经构建期环境变量注入（缺省时 `client.ts` 用默认值）。
 * 声明它们的意义是：写错键名（`VITE_IB_AUTH_LOGIN_PAHT`）时 `vue-tsc` 直接报错，
 * 而不是静默拿到 `undefined` 再回退默认值（那会让「配置没生效」看起来像「配置本来就不需要」）。
 */
interface ImportMetaEnv {
  readonly VITE_IB_AUTH_LOGIN_PATH?: string;
  readonly VITE_IB_AUTH_SESSION_STORAGE_KEY?: string;
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue';

  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>;
  export default component;
}
