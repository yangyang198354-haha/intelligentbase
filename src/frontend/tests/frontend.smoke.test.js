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

// --------------------------------------------------------------------------- //
// R13 前端冒烟：登录 / 会话 / 控制台外壳 / 零旁路（TC-FE-007 ~ TC-FE-013）
//
// 溯源：US-IB-21（登录 + 无粘贴令牌入口）、US-IB-22（首登改密）、US-IB-23（账户管理
//       requiresAdmin）、US-IB-25（无 Cookie / 仅 Authorization）、US-IB-26（左导航 +
//       右内容 / 主题 / 中文 / 无 CDN）、US-IB-27（会话态）。
// 说明：本项目无组件测试框架，此处做**源码结构**断言（与既有 R10 层同一策略）；
//       对 App.vue 的断言刻意采用**结构性**判据（<input / setToken 等），避免被散文误触发。
// --------------------------------------------------------------------------- //

const r13 = {
  app: join(root, 'src', 'App.vue'),
  main: join(root, 'src', 'main.ts'),
  client: join(root, 'src', 'api', 'client.ts'),
  session: join(root, 'src', 'stores', 'session.ts'),
  theme: join(root, 'src', 'stores', 'theme.ts'),
  router: join(root, 'src', 'router', 'index.ts'),
  login: join(root, 'src', 'views', 'LoginPage.vue'),
  changePw: join(root, 'src', 'views', 'ChangePasswordPage.vue'),
  accounts: join(root, 'src', 'views', 'AccountsPage.vue'),
  layout: join(root, 'src', 'layouts', 'ConsoleLayout.vue'),
};

/** 去掉 `/* … *​/` 与 `// …` 注释后再断言 —— 避免把文档里「我们不再做 X」的说明误判为 X。 */
const stripComments = (text) =>
  text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

describe('R13 前端冒烟：登录 / 会话 / 控制台外壳 / 零旁路', () => {
  it('7. App.vue 不再有「粘贴访问令牌」入口（结构性判据，非散文）', () => {
    const text = stripComments(readText(r13.app));
    assert.match(text, /<router-view\s*\/>/, 'App.vue 应为路由出口');
    assert.doesNotMatch(text, /<input\b/, 'App.vue 不得再出现任何输入框（含粘贴令牌入口）');
    assert.doesNotMatch(text, /setToken\(|saveToken|v-model/, 'App.vue 不得保留令牌写入入口');
    assert.doesNotMatch(text, /type="password"/, 'App.vue 不得内含口令输入（应在登录页）');
  });

  it('8. main.ts 不再从 URL 读令牌（零 `?token=` 迁移分支）', () => {
    const text = stripComments(readText(r13.main));
    assert.doesNotMatch(text, /searchParams|location\.search|access_token|setToken\(/,
      'main.ts 不得保留从 URL 读取 / 写入令牌的逻辑');
    assert.match(text, /setUnauthorizedHandler\(/, '全局 401 处理应接到会话层');
    assert.match(text, /\.use\(router\)/, '应挂载路由');
  });

  it('9. 登录页结构（用户名 + 口令，统一错误文案防枚举）', () => {
    const text = stripComments(readText(r13.login));
    assert.match(text, /autocomplete="username"/, '缺少用户名输入');
    assert.match(text, /type="password"/, '缺少口令输入');
    assert.match(text, /autocomplete="current-password"/, '口令输入应声明 current-password');
    assert.match(text, /session\.login\(/, '登录应经会话层');
    assert.match(text, /用户名或口令不正确/, '登录失败应统一文案');
    assert.doesNotMatch(text, /用户不存在|账户不存在|用户名已存在/, '登录页不得提示账户是否存在');
  });

  it('10. 路由守卫：hash 模式 + 未登录→登录 + 改密→改密页 + requiresAdmin', () => {
    const text = stripComments(readText(r13.router));
    assert.match(text, /createWebHashHistory/, '应使用 hash 路由（避免刷新深链接 404）');
    assert.match(text, /beforeEach/, '缺少准入守卫');
    assert.match(text, /session\.bootstrap\(\)/, '守卫应先经 /api/auth/me 确认身份');
    assert.match(text, /name: 'login'/, '未登录应跳登录页');
    assert.match(text, /change-password/, '改密态应跳改密页');
    assert.match(text, /mustChangePassword/, '守卫应处理改密态');
    assert.match(text, /requiresAdmin/, '账户管理页应标注 requiresAdmin');
    assert.match(text, /session\.isAdmin/, 'requiresAdmin 应以会话角色判定');
  });

  it('11. 控制台外壳：左导航 + 右内容 + 主题切换 + 中文', () => {
    const text = stripComments(readText(r13.layout));
    assert.match(text, /<aside\b/, '缺少左侧导航');
    assert.match(text, /<main\b/, '缺少右侧内容区');
    assert.match(text, /toggleTheme/, '缺少主题切换');
    assert.match(text, /requiresAdmin/, '导航应按 requiresAdmin 过滤');
    assert.match(text, /管理员|运维/, '角色文案应为中文');
  });

  it('12. 会话令牌只经 sessionStorage + Authorization（无 Cookie / 无 localStorage）', () => {
    const client = stripComments(readText(r13.client));
    const others = [r13.session, r13.theme].map((p) => stripComments(readText(p))).join('\n');
    assert.match(client, /sessionStorage/, '令牌应存 sessionStorage');
    assert.match(client, /Authorization/, '每个请求应显式注入 Authorization');
    assert.match(client, /Bearer/, '应使用 Bearer 方案');
    for (const [name, text] of [['client.ts', client], ['session/theme.ts', others]]) {
      assert.doesNotMatch(text, /document\.cookie/, `${name} 不得读写 Cookie`);
      assert.doesNotMatch(text, /localStorage\.(get|set|remove)Item/, `${name} 不得持久化到 localStorage`);
    }
  });

  it('13. R13 依赖本地打包 + 锁同步 + 源码零 CDN', () => {
    const pkg = readJson(pkgPath);
    const lock = readJson(lockPath);
    for (const name of ['element-plus', 'vue-router']) {
      assert.ok(pkg.dependencies[name], `package.json 缺少 R13 依赖 ${name}`);
      assert.ok(lock.packages[`node_modules/${name}`], `package-lock.json 未解析 ${name}（npm ci 会 EUSAGE）`);
    }
    for (const p of [r13.app, r13.main, r13.client, r13.layout, r13.login, r13.router]) {
      const text = readText(p);
      for (const host of FORBIDDEN_CDN_HOSTS) {
        assert.ok(!text.includes(host), `${p} 出现公网 CDN 引用：${host}`);
      }
    }
  });
});
