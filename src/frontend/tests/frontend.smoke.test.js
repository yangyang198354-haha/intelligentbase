/**
 * @module MOD-IB-24
 * @implements IFC-IB-296（R7 可视化配置页 / @vue-flow/core 本地打包的**可回归**冒烟入口）
 * @author software-developer
 *
 * ## R10 前端冒烟测试（最小骨架，供 REV-10-2 的 test-engineer 扩写）
 *
 * ### 为什么是「零新增依赖」
 *
 * CI 用 Node 20（`.github/workflows/ci.yml` 的 `setup-node`），自带 `node:test` + `node:assert`，
 * 足够做**源码结构**与**构建产物**断言；引入 vitest/jest 只会给 4GB 内存的目标机再加一层
 * 依赖与体积。本文件只 import `node:` 内建模块 —— **不**新增任何运行期或开发期依赖。
 *
 * ### 为什么断言里要盯住 `package-lock.json`
 *
 * R10 的**根因**是「`package.json` 声明了 `@vue-flow/core`，而 `package-lock.json` 里没有它」：
 * `npm ci` 先比对两者，不一致即 `EUSAGE` 失败，CI 阶段9 在 `npm run build` **之前**就倒下。
 * 因此「锁与 package.json 保持同步」本身就是一条必须常驻的回归断言（用例 2）。
 *
 * ### dist 断言为何是「条件式」的
 *
 * `dist/` 是 `npm run build` 的产物，且刻意不入库（见 `.gitignore`）。若强制要求它存在，
 * 本文件在「先测后建」的顺序下会必然失败 —— 那不是发现了缺陷，而是搞错了前置条件。
 * 故 `dist` 相关用例以「目录存在」为**前置条件**（存在才检查其内容），属前置条件判断，
 * 不是被削弱的断言。
 */
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');

const pkgPath = join(root, 'package.json');
const lockPath = join(root, 'package-lock.json');
const configPagePath = join(root, 'src', 'views', 'ConfigPage.vue');
const appVuePath = join(root, 'src', 'App.vue');
const distDir = join(root, 'dist');

const readJson = (p) => JSON.parse(readFileSync(p, 'utf8'));
const readText = (p) => readFileSync(p, 'utf8');

/** 运行期禁止加载的公网 CDN（AC-IB-17-06 / REQ-NFR-IB-08）。 */
const FORBIDDEN_CDN_HOSTS = [
  'cdn.jsdelivr.net',
  'unpkg.com',
  'cdnjs.cloudflare.com',
  'cdn.skypack.dev',
  'esm.sh',
];

describe('R10 前端冒烟：@vue-flow/core 打包与锁同步', () => {
  it('1. package.json 声明 @vue-flow/core 依赖', () => {
    const pkg = readJson(pkgPath);
    assert.ok(
      pkg.dependencies && pkg.dependencies['@vue-flow/core'],
      'package.json 的 dependencies 缺少 @vue-flow/core',
    );
    assert.ok(pkg.dependencies.vue, 'package.json 的 dependencies 缺少 vue');
  });

  it('2. package-lock.json 与 package.json 同步（R10 根因回归闸）', () => {
    const lock = readJson(lockPath);
    const pkg = readJson(pkgPath);

    // 2a. 锁内必须实际解析出该包（R10 前此处为 0 命中）。
    assert.ok(
      lock.packages['node_modules/@vue-flow/core'],
      'package-lock.json 未解析 @vue-flow/core —— npm ci 会因锁不同步而 EUSAGE 失败',
    );
    assert.equal(
      typeof lock.packages['node_modules/@vue-flow/core'].version,
      'string',
      '@vue-flow/core 的锁定版本缺失',
    );

    // 2b. 锁根节点的 dependencies 必须与 package.json 声明一致。
    const lockRootDeps = lock.packages['']?.dependencies ?? {};
    for (const name of Object.keys(pkg.dependencies)) {
      assert.ok(lockRootDeps[name], `锁根节点 dependencies 缺少 ${name}（锁与 package.json 失同步）`);
    }

    // 2c. 传递依赖必须被完整锁定（否则 npm ci 无法离线复现）。
    for (const name of ['node_modules/@vueuse/core', 'node_modules/d3-zoom']) {
      assert.ok(lock.packages[name], `package-lock.json 缺少传递依赖 ${name}`);
    }
  });

  it('3. ConfigPage.vue 从本地包导入 Vue Flow 与样式（非 CDN）', () => {
    const text = readText(configPagePath);
    assert.match(text, /from\s+'@vue-flow\/core'/, 'ConfigPage.vue 未从 @vue-flow/core 导入');
    assert.match(text, /@vue-flow\/core\/dist\/style\.css/, '缺少 @vue-flow/core 基础样式导入');
    assert.match(text, /@vue-flow\/core\/dist\/theme-default\.css/, '缺少 Vue Flow 默认主题导入');
  });

  it('4. 编排图只读不变量（IFC-IB-296：拓扑运行期不可编辑）', () => {
    const text = readText(configPagePath);
    assert.match(text, /<VueFlow/, 'ConfigPage.vue 未渲染 <VueFlow>');
    assert.match(text, /:nodes-draggable="false"/, '节点必须不可拖拽（只读）');
    assert.match(text, /:nodes-connectable="false"/, '节点必须不可连线（只读）');
    // 不得提供运行期增删**图节点**的入口（专家集合可编辑不在此列）。
    assert.doesNotMatch(
      text,
      /nodes\.value\.push|nodes\.value\.splice/,
      '禁止在运行期增删图节点（拓扑不可编辑）',
    );
  });

  it('5. 源码与入口零外发 CDN 引用（AC-IB-17-06）', () => {
    const text = readText(configPagePath) + '\n' + readText(appVuePath);
    for (const host of FORBIDDEN_CDN_HOSTS) {
      assert.ok(!text.includes(host), `源码出现公网 CDN 引用：${host}`);
    }
  });

  it('6. 构建产物存在且入口不自外网加载（需先 npm run build）', (t) => {
    if (!existsSync(distDir) || !statSync(distDir).isDirectory()) {
      t.diagnostic('dist/ 不存在 —— 跳过产物断言（请先 `npm run build`）');
      return;
    }
    const indexHtml = join(distDir, 'index.html');
    assert.ok(existsSync(indexHtml), 'dist/index.html 缺失');

    const assetsDir = join(distDir, 'assets');
    assert.ok(existsSync(assetsDir), 'dist/assets 缺失');
    assert.ok(
      readdirSync(assetsDir).some((f) => f.endsWith('.js')),
      'dist/assets 下没有 JS 产物',
    );

    const html = readText(indexHtml);
    for (const host of FORBIDDEN_CDN_HOSTS) {
      assert.ok(!html.includes(host), `dist/index.html 引用公网 CDN：${host}`);
    }
    assert.doesNotMatch(
      html,
      /(?:src|href)="https?:\/\//,
      'dist/index.html 存在绝对外网 URL 引用（应全部为相对路径）',
    );
  });
});
