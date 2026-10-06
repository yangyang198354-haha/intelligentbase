/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 / 328 / 329 应用级单例装配（客户端 + 会话）
 * @author software-developer
 *
 * 应用级单例的**唯一**装配点。
 *
 * 为什么单独一个文件：`main.ts`（引导）、`router`（守卫）、各视图都需要同一份
 * `ApiClient` 与 `Session` 实例。若各自 `new` 一份，会出现「登录页写入的令牌，
 * 控制台读不到」这类极难定位的问题（两个 `sessionStorage` 视图不同步、401 回调注册在
 * 另一个实例上）。集中在此导出，谁需要谁 import，实例全局唯一。
 *
 * 现有页面（上传 / 问答 / 重建 / 配置）**保持** `client` 经 props 注入的既有契约
 * （R1~R12 的写法不变），由路由的 `props` 工厂从本文件取实例注入。新增的 R13 视图
 * 直接用本文件导出的 `session`（它们需要的是会话态，不是裸客户端）。
 */

import { apiClient } from '../api/client';
import { createSession } from '../stores/session';

/** 全局唯一的 API 客户端（与 `client.ts` 导出的 `apiClient` 是同一实例）。 */
export const client = apiClient;

/** 全局唯一的会话。 */
export const session = createSession(apiClient);
