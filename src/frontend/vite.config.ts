/**
 * @module MOD-IB-24
 * @implements IFC-IB-256/257/258 构建配置
 * @author software-developer
 *
 * Vite 配置。
 *
 * ## 代理只在 `dev` 生效
 *
 * 生产由 nginx 把 `/api` 与 `/healthz` 反代到 `127.0.0.1:18080`（见 `deploy/systemd/ib-web.service`
 * 的说明）。vite 的 `server.proxy` 只是开发期便利 —— 若把它当作「部署依赖」，
 * 就会出现「本地能跑、部署 404」的经典故障。
 *
 * ## SSE 必须走同源代理，不能跨域
 *
 * 跨域下 `EventSource` 不接受自定义请求头，而本项目的 SSE **只能**经 `Authorization`
 * 头鉴权（`?token=` 被后端显式拒绝）。因此前端不使用 `EventSource`，而是用 `fetch` +
 * `ReadableStream` 手动解析 SSE（见 `src/api/client.ts`），并要求同源（或带 CORS 预检）。
 */
import { fileURLToPath, URL } from 'node:url';

import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:18080', changeOrigin: false },
      '/healthz': { target: 'http://127.0.0.1:18080', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
    // 关闭 sourcemap：产物会被 `ib-web` 静态托管，sourcemap 会把源码结构一并公开。
    sourcemap: false,
  },
});
