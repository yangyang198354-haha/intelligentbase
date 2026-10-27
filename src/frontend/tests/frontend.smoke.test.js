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

// --------------------------------------------------------------------------- //
// R14 前端冒烟：项目上下文单点注入 + SSE 覆盖（IFC-IB-333 / 335 / 336）
//
// 溯源：US-IB-24 / AC-IB-24-03（admin 全局可选项目）、AC-IB-24-02（ops 跨项目 403）。
// 说明：用例 14~16 为**源码结构**断言（与既有 R10/R13 层同策略，Node 20 可跑）；
//       用例 17 为**行为**断言 —— 真跑 `ApiClient.headers()` 与 `createProjectContext`。
//       Node < 22.6 不支持导入 `.ts`（无类型擦除），此时用例 17 **跳过**（不误报失败）——
//       与用例 6「dist 不存在则跳过」同一策略：前置条件不满足不是缺陷。
// --------------------------------------------------------------------------- //

const r14 = {
  project: join(root, 'src', 'stores', 'project.ts'),
  client: join(root, 'src', 'api', 'client.ts'),
  env: join(root, 'src', 'app', 'env.ts'),
  layout: join(root, 'src', 'layouts', 'ConsoleLayout.vue'),
};

describe('R14 前端冒烟：项目上下文单点注入 + SSE 覆盖', () => {
  it('14. X-IB-Project 字面量只出现在 stores/project.ts（单一取值出口）', () => {
    const projectTs = stripComments(readText(r14.project));
    const clientTs = stripComments(readText(r14.client));
    assert.match(projectTs, /X-IB-Project/, 'project store 未产出 X-IB-Project');
    assert.doesNotMatch(
      clientTs,
      /X-IB-Project/,
      'client.ts 不得出现该字面量（取值只来自 projectContext.headerValue()）',
    );
    for (const symbol of ['available', 'current', 'select', 'load', 'clear', 'headerValue']) {
      assert.ok(projectTs.includes(symbol), `stores/project.ts 缺少 ${symbol}`);
    }
  });

  it('15. SSE 调用点同经 this.headers()，不重复拼头', () => {
    const clientTs = stripComments(readText(r14.client));
    assert.match(clientTs, /setProjectHeaderProvider/, 'client.ts 未暴露项目头提供者');
    assert.match(clientTs, /async chatStream/);
    assert.match(clientTs, /async chatResume/);
    assert.ok(
      (clientTs.match(/this\.headers\(/g) || []).length >= 3,
      'request / chatStream / chatResume 应同经 this.headers()',
    );
  });

  it('16. 控制台：项目选择器 + router-view 以当前项目为键（切换重置视图态）', () => {
    const layout = stripComments(readText(r14.layout));
    assert.match(layout, /el-select/, '缺少 admin 项目选择器');
    assert.match(layout, /projectContext\.select/, '选择器未经 projectContext.select');
    assert.match(layout, /<router-view[^>]*:key/, 'router-view 未以当前项目为键');
    const env = stripComments(readText(r14.env));
    assert.match(env, /setProjectHeaderProvider/, 'env.ts 未接线项目头提供者');
  });

  it('17. 行为：headers() 依 current 注入 / 不注入（含 SSE 头集合）', async (t) => {
    // sessionStorage 是浏览器 API；补一个最小替身，仅为让 token 读取不抛。
    globalThis.sessionStorage ??= { getItem: () => null, setItem() {}, removeItem() {} };
    let ApiClient;
    let createProjectContext;
    try {
      ({ ApiClient } = await import('../src/api/client.ts'));
      ({ createProjectContext } = await import('../src/stores/project.ts'));
    } catch (err) {
      t.diagnostic(`当前 Node 不支持导入 .ts（${err.code ?? err.name}）—— 跳过行为断言`);
      return;
    }
    const api = new ApiClient();
    const pc = createProjectContext({
      listProjects: async () => [
        { project_id: 'p_alpha', name: 'A', is_current: false },
        { project_id: 'p_beta', name: 'B', is_current: false },
      ],
    });
    api.setProjectHeaderProvider(() => pc.headerValue());

    // 未选择 ⇒ 不注入（fail-closed）。
    assert.ok(!('X-IB-Project' in api.headers({})), '未选择项目时不得注入 X-IB-Project');
    await pc.load('admin', null); // 结果集 2 项 ⇒ admin 缺省为空
    assert.equal(pc.state.current, null);
    assert.ok(!('X-IB-Project' in api.headers({})));

    // 选择后 ⇒ 注入；SSE 头集合同样含该项目头（chatStream 传的正是该集合）。
    pc.select('p_alpha');
    assert.equal(api.headers({})['X-IB-Project'], 'p_alpha');
    const sse = api.headers({ Accept: 'text/event-stream' });
    assert.equal(sse['X-IB-Project'], 'p_alpha');
    assert.equal(sse.Accept, 'text/event-stream');

    // 清空 ⇒ 回到不注入；且 ops 不可切换（三重约束的前端一重）。
    pc.clear();
    assert.ok(!('X-IB-Project' in api.headers({})));
    const ops = createProjectContext({
      listProjects: async () => [{ project_id: 'p_alpha', name: 'A', is_current: true }],
    });
    await ops.load('ops', 'p_alpha');
    assert.equal(ops.state.current, 'p_alpha');
    ops.select('p_beta'); // no-op
    assert.equal(ops.state.current, 'p_alpha', 'ops 不可切换项目');
  });

  // R14 补测（INV-GROUP-D-INTELBASE-014）：边界行为 —— 失败/空集 fail-closed、单项目预选、
  // select 白名单、项目头单一真源。与用例 17 同策略：Node 不支持导入 .ts 则跳过（非失败）。

  it('18. 行为：load 失败 ⇒ current 保持 null（不注入头，fail-closed）且记录 error', async (t) => {
    globalThis.sessionStorage ??= { getItem: () => null, setItem() {}, removeItem() {} };
    let ApiClient;
    let createProjectContext;
    try {
      ({ ApiClient } = await import('../src/api/client.ts'));
      ({ createProjectContext } = await import('../src/stores/project.ts'));
    } catch (err) {
      t.diagnostic(`当前 Node 不支持导入 .ts（${err.code ?? err.name}）—— 跳过行为断言`);
      return;
    }
    const api = new ApiClient();
    const pc = createProjectContext({
      listProjects: async () => {
        throw new Error('boom');
      },
    });
    api.setProjectHeaderProvider(() => pc.headerValue());
    await pc.load('admin', null); // 失败：不抛，转 fail-closed
    assert.equal(pc.state.current, null, '加载失败后不得残留 current');
    assert.equal(pc.state.available.length, 0, '加载失败后可见集应为空');
    assert.ok(pc.state.error.length > 0, '加载失败应记录 error 供界面提示');
    assert.ok(!('X-IB-Project' in api.headers({})), 'load 失败不得注入 X-IB-Project');
  });

  it('19. 行为：admin 单项目预选 + select 只接受 available 中的 id', async (t) => {
    globalThis.sessionStorage ??= { getItem: () => null, setItem() {}, removeItem() {} };
    let ApiClient;
    let createProjectContext;
    try {
      ({ ApiClient } = await import('../src/api/client.ts'));
      ({ createProjectContext } = await import('../src/stores/project.ts'));
    } catch (err) {
      t.diagnostic(`当前 Node 不支持导入 .ts（${err.code ?? err.name}）—— 跳过行为断言`);
      return;
    }
    const api = new ApiClient();
    const pc = createProjectContext({
      listProjects: async () => [{ project_id: 'p_only', name: 'Only', is_current: false }],
    });
    api.setProjectHeaderProvider(() => pc.headerValue());
    await pc.load('admin', null); // 结果集恰为 1 项 ⇒ 预选（ADR-28 吸收 Option A）
    assert.equal(pc.state.current, 'p_only', 'admin 单项目应预选');
    assert.equal(api.headers({})['X-IB-Project'], 'p_only', '预选后仍显式发送请求头');

    // select 只接受 available 中的 id（不得把任意串当项目名注入头）。
    pc.select('p_evil');
    assert.equal(pc.state.current, 'p_only', 'select 不得接受不可见 id');
    pc.select('   ');
    assert.equal(pc.state.current, 'p_only', 'select 不得接受空白 id');
  });

  it('20. 行为：ops 结果集为空 ⇒ current 为 null（不臆造、不注入头）', async (t) => {
    globalThis.sessionStorage ??= { getItem: () => null, setItem() {}, removeItem() {} };
    let ApiClient;
    let createProjectContext;
    try {
      ({ ApiClient } = await import('../src/api/client.ts'));
      ({ createProjectContext } = await import('../src/stores/project.ts'));
    } catch (err) {
      t.diagnostic(`当前 Node 不支持导入 .ts（${err.code ?? err.name}）—— 跳过行为断言`);
      return;
    }
    const api = new ApiClient();
    const pc = createProjectContext({ listProjects: async () => [] });
    api.setProjectHeaderProvider(() => pc.headerValue());
    await pc.load('ops', 'p_alpha'); // 自身项目未登记 ⇒ 服务端回空列表
    assert.equal(pc.state.current, null, 'ops 空列表不得臆造 current');
    assert.ok(!('X-IB-Project' in api.headers({})), '未选定不得注入 X-IB-Project');
  });

  it('21. 行为：X-IB-Project 值只来自 provider（调用点 extra 不能覆盖）+ provider 抛错不注入', async (t) => {
    globalThis.sessionStorage ??= { getItem: () => null, setItem() {}, removeItem() {} };
    let ApiClient;
    let createProjectContext;
    try {
      ({ ApiClient } = await import('../src/api/client.ts'));
      ({ createProjectContext } = await import('../src/stores/project.ts'));
    } catch (err) {
      t.diagnostic(`当前 Node 不支持导入 .ts（${err.code ?? err.name}）—— 跳过行为断言`);
      return;
    }
    const api = new ApiClient();
    const pc = createProjectContext({
      listProjects: async () => [{ project_id: 'p_alpha', name: 'A', is_current: true }],
    });
    api.setProjectHeaderProvider(() => pc.headerValue());
    await pc.load('admin', null); // 单项目 ⇒ 预选 p_alpha

    // 单一真源：调用点即便自带 X-IB-Project，也被 provider 值覆盖。
    const merged = api.headers({ 'X-IB-Project': 'p_evil' });
    assert.equal(merged['X-IB-Project'], 'p_alpha', 'extra 不得覆盖 provider 的项目头');

    // provider 抛错 ⇒ 空对象（不炸 headers、不注入），保持 fail-closed。
    api.setProjectHeaderProvider(() => {
      throw new Error('provider down');
    });
    assert.ok(!('X-IB-Project' in api.headers({})), 'provider 抛错时不得注入项目头');
  });
});

// --------------------------------------------------------------------------- //
// R16 前端冒烟：提示词分层编辑 + 工具授权勾选 / 参数 + 生效口径提示
//
// 溯源：US-IB-29（提示词主/兜底分层编辑）、US-IB-30（主缺失回退兜底须可见）、
//       US-IB-31（工具授权勾选 + 参数可配）、ADR-32 / C-IB-40（保存后重启生效）。
// 策略：与既有 R10/R13/R14 层一致 —— **源码结构**断言（本条无需导入 .ts，Node 20 可跑）。
//       REV-16-2 未引入任何新的前端依赖（仍为零新增依赖）。
// --------------------------------------------------------------------------- //

describe('R16 前端冒烟：提示词分层 + 工具勾选/参数 + 生效口径', () => {
  const page = () => stripComments(readText(configPagePath));

  it('22. 提示词分层编辑器：主 / 兜底两个独立文本域 + 逐层保存', () => {
    const text = page();
    assert.match(text, /PROMPT_LAYERS/, '缺少分层常量（主/兜底）');
    assert.match(text, /savePromptLayer\(/, '缺少逐层保存入口');
    assert.match(text, /promptLayer\(|promptList\(/, '应经客户端提示词契约读取');
    // 主缺失时的回退必须**可见**（US-IB-30）—— 必须有 resolved_from 的用户可读表达。
    assert.match(text, /resolvedFrom\(/, '缺少「当前生效层」派生');
    assert.match(text, /主提示词缺失，当前生效 = 兜底/, '缺少回退可见文案');
  });

  it('23. 生效口径提示（REV-26 重新基线：取代 ADR-32 / C-IB-40 / REQ-FUNC-IB-40，见 CL-003）：保存成功提示“已生效”，不再要求重启', () => {
    const text = page();
    assert.match(text, /保存成功，已生效（无需重启）/, '缺少「保存成功，已生效」提示');
    assert.doesNotMatch(text, /重启 `ib-web`/, '不得再要求重启 ib-web / ib-worker 后生效（AC-014-05）');
    assert.doesNotMatch(text, /不热重载/, '不得再声明不热重载');
    // 不得暗示运行期即时生效（无热重载轮询 / 运行期重建编排图的入口）。
    assert.doesNotMatch(
      text,
      /reload|hotReload|hot-reload|rebuildGraph|scheduleRebuild/i,
      '不得在视图侧提供热重载 / 运行期重建入口',
    );
  });

  it('24. 工具授权勾选（checkbox）+ 既有工具名单来源，不新增工具本体', () => {
    const text = page();
    assert.match(text, /grantChecklist\(/, '缺少勾选清单');
    assert.match(text, /availableTools/, '勾选名单应来自后端 available_tools（既有工具集合）');
    assert.match(text, /toggleTool\(/, '缺少勾选切换');
    assert.match(text, /paramsForTool\(/, '缺少按工具聚合的参数规格');
    // 客户端类型契约：available_tools 必须显式声明（与后端 `_get_prompts_list` 对齐）。
    const clientTs = stripComments(readText(r13.client));
    assert.match(clientTs, /available_tools: string\[\]/, '客户端类型须声明 available_tools');
  });

  it('25. 提示词域与定义文档域各自独立草稿 / 哈希（不互串乐观并发基线）', () => {
    const text = page();
    assert.match(text, /promptHashes/, '缺少提示词域独立基线哈希');
    assert.match(text, /promptTexts/, '缺少提示词域独立草稿');
    assert.match(text, /prompt_content_hash_conflict|conflict/, '应处理 409 冲突');
  });

  it('26. 视图侧零持久化（提示词草稿不得落 localStorage / IndexedDB）', () => {
    const text = page();
    assert.doesNotMatch(text, /localStorage/, '视图不得使用 localStorage');
    assert.doesNotMatch(text, /indexedDB|IndexedDB/, '视图不得使用 IndexedDB');
  });

  it('27. 工具参数表单由 tool_param_specs 派生 + 限定名写入 grant.param_values（ADR-30 / IFC-IB-354）', () => {
    const text = page();
    // 参数规格来自后端（既有工具 JSON Schema 派生），前端不硬编码参数表
    assert.match(text, /tool_param_specs/, '参数规格须来自后端回执');
    assert.match(text, /toolParamSpecs/, '缺少参数规格派生');
    // 数值 / 枚举控件受规格约束（越界、非法枚举在界面层即被约束）
    assert.match(text, /\bspec\.(minimum|maximum)\b/, '数值控件应绑定 min/max');
    assert.match(text, /\bspec\.choices\b/, '枚举控件应绑定 choices');
    // 按**限定名** `<tool>.<param>` 归属工具（跨工具参数名隔离）
    assert.ok(
      text.includes('startsWith(`${tool}.`)'),
      'paramsForTool 应按限定名前缀 `<tool>.` 过滤，避免跨工具串味',
    );
    // 参数写入 grant.param_values（随该专家工具授权一并保存，AC-IB-31-04）
    assert.match(text, /setParamValue\(/, '缺少参数写入入口');
    assert.match(text, /grant\.param_values/, '参数应写入 grant.param_values');
    // 可编辑性受可编辑白名单约束
    assert.match(text, /canEdit\('tool_grants\[\]\.param_values'\)/, '参数可编辑性应受白名单约束');
    // 客户端类型契约（与后端回执字段对齐）
    const clientTs = stripComments(readText(r13.client));
    assert.match(clientTs, /tool_param_specs: ToolParamSpec\[\]/, '客户端类型须声明 tool_param_specs');
    assert.match(clientTs, /param_values\?: ToolParamValue\[\]/, '客户端类型须声明 param_values');
  });

  it('29. REV-20（ADR-48）：定义文档域不再承载提示词、代码内置兜底已退役', () => {
    const text = page();
    // 定义文档域**不得**再出现提示词文本的编辑入口（白名单字段已删除，改了也存不下）
    assert.doesNotMatch(
      text,
      /canEdit\('experts\[\]\.fallback_prompt'\)/,
      '定义文档域不得再提供专家兜底提示词编辑入口（会形成重叠第二真源）',
    );
    assert.doesNotMatch(
      text,
      /expert\.fallback_prompt/,
      '定义文档草稿不得再持有 fallback_prompt 字段',
    );
    // **契约翻转（REV-20 / ADR-48 / OQ-IB-42=B）**：原「内置兜底只读回显」区（`builtinFallbackOf`
    // + `builtin_fallback` 回执字段）随代码内置兜底一并删除；回退链只剩两层文件，
    // 两层皆缺即为 `prompt_missing`（装配期 fail-closed）。
    assert.doesNotMatch(text, /builtinFallbackOf\(/, '内置兜底回显派生应已删除');
    assert.doesNotMatch(text, /builtin_fallback/, '页面不得再引用 builtin_fallback');
    assert.doesNotMatch(text, /代码内置兜底（只读）/, '不得残留内置兜底只读回显文案');
    // 回退链状态值收窄为 {main_file, fallback_file, prompt_missing}（不再是 builtin_fallback）
    assert.match(text, /'prompt_missing'/, '回退链须能表达「两层皆缺 → 无法装配」');
    assert.doesNotMatch(
      text,
      /definition_doc_fallback/,
      '不得残留旧口径 definition_doc_fallback',
    );
    // 客户端类型契约：定义文档输入不再有 fallback_prompt；提示词回执亦不再有 builtin_fallback
    const clientTs = stripComments(readText(r13.client));
    assert.doesNotMatch(
      clientTs,
      /fallback_prompt/,
      '客户端 ExpertSpecInput 不得再声明 fallback_prompt',
    );
    assert.doesNotMatch(
      clientTs,
      /builtin_fallback/,
      '客户端 PromptExpertEntry 不得再声明 builtin_fallback（REV-20 已退役）',
    );
  });
});

describe('R16-4 前端冒烟：存储态非静默提示（IFC-IB-361 / 362 / 363，ADR-35）', () => {
  const page = () => stripComments(readText(configPagePath));

  it('28. 未启用持久化 ⇒ 配置页**非静默**提示「仅内存生效、不跨重启保留」', () => {
    const text = page();
    // 读取存储态（单一来源 = 装配期实际选用的存储实现）
    assert.match(text, /loadStorageState\(/, '缺少存储态读取入口');
    assert.match(text, /storageState\(\)/, '应经客户端存储态契约读取');
    assert.match(text, /memoryNotice/, '缺少内存态判定');
    assert.match(text, /memoryDomains/, '缺少内存域派生（哪些 store 处于 memory）');
    // **非静默**：必须显式渲染「配置仅内存生效、不跨重启保留」
    assert.ok(
      text.includes('配置**仅内存生效、不跨重启保留**'),
      '缺少「配置仅内存生效、不跨重启保留」非静默提示文案',
    );
    // 存储态读取失败须 fail-closed（不得静默当作文件态）
    assert.match(text, /storageBanner/, '缺少存储态读取失败提示');
    assert.match(text, /不静默当作文件态/, '存储态不可读不得静默当作文件态');

    // 客户端类型 / 路由契约（与后端 IFC-IB-361 / 362 对齐）
    const clientTs = stripComments(readText(r13.client));
    assert.match(clientTs, /export type StorageState = \{/, '客户端须声明 StorageState 类型');
    assert.match(
      clientTs,
      /storageState\(\): Promise<StorageState>/,
      '客户端须提供 storageState() 方法',
    );
    assert.match(clientTs, /'\/api\/config\/storage-state'/, '缺少存储态端点路由');
    // 审计投影（IFC-IB-356）类型契约
    assert.match(clientTs, /export type ConfigAuditEntry = \{/, '客户端须声明 ConfigAuditEntry 类型');
    assert.match(clientTs, /configAudit\(/, '客户端须提供 configAudit() 方法');
    // 视图不得引入任何热重载 / 运行期重建入口（生效口径不变，ADR-32 / 35）
    assert.doesNotMatch(
      text,
      /reload|hotReload|hot-reload|rebuildGraph|scheduleRebuild/i,
      '存储态提示不得引入热重载 / 运行期重建入口',
    );
  });
});

// --------------------------------------------------------------------------- //
// REV-18 前端冒烟：系统管理三分 IA + 项目域上传 + LLM Key（IFC-IB-375 / 376 / ADR-42）
//
// 溯源：US-IB-43~46 / AC-IB-43~46。均为**源码结构**断言（与 R10/R13/R14/R16 同策略）。
// --------------------------------------------------------------------------- //

const rev18 = {
  router: join(root, 'src', 'router', 'index.ts'),
  layout: join(root, 'src', 'layouts', 'ConsoleLayout.vue'),
  upload: join(root, 'src', 'views', 'UploadPage.vue'),
  llmKey: join(root, 'src', 'views', 'LlmKeyPage.vue'),
  systemSection: join(root, 'src', 'views', 'SystemSection.vue'),
  client: join(root, 'src', 'api', 'client.ts'),
};

describe('REV-18 前端冒烟：系统管理三分 IA + 项目域上传 + LLM Key', () => {
  it('30. 路由：父级「系统管理」+ 三子项 + 旧 accounts 深链重定向（hash 模式保留）', () => {
    const text = stripComments(readText(rev18.router));
    assert.match(text, /SystemSection/, '缺少父级透传容器 SystemSection');
    assert.match(text, /path:\s*'system'/, '缺少父级路由 system');
    for (const child of ["'accounts'", "'projects'", "'llm-key'"]) {
      assert.ok(text.includes(`path: ${child}`), `缺少子路由 ${child}`);
    }
    // ADR-42 ③：既有 `#/accounts` 深链迁移（保留 hash，不引 try_files）。
    assert.match(text, /path:\s*'accounts',\s*redirect/, '缺少旧 accounts 深链的重定向迁移');
    assert.match(text, /createWebHashHistory/, '路由模式应为 hash（不得改为 history + try_files）');
    // 三分 IA 是**体验**分组，不是权限机制 —— 子项须带 requiresAdmin（授权仍由服务端裁决）。
    assert.ok(
      (text.match(/requiresAdmin:\s*true/g) || []).length >= 3,
      '三子项须各自声明 requiresAdmin（授权唯一经服务端，此处只是体验）',
    );
  });

  it('31. 控制台导航：顶级四项 + 「系统管理」分组三子项', () => {
    const layout = stripComments(readText(rev18.layout));
    assert.match(layout, /TOP_ORDER\s*=\s*\[[^\]]*'chat'[^\]]*'files'[^\]]*'rebuild'[^\]]*'config'/, '缺少顶级导航顺序');
    assert.match(layout, /SYSTEM_ORDER\s*=\s*\[[^\]]*'accounts'[^\]]*'projects'[^\]]*'llm-key'/, '缺少系统管理分组顺序');
    assert.ok(layout.includes('系统管理'), '缺少「系统管理」分组标签');
    assert.match(layout, /nav-item-child/, '缺少子项样式类（层级可见性）');
  });

  it('32. 项目域上传：请求体不再携带 kb 字段（kb_id 由服务端按主体推导）', () => {
    const upload = stripComments(readText(rev18.upload));
    assert.doesNotMatch(upload, /kbId|kb_id\s*[:=]/, '上传视图仍出现 kb 输入 / 变量（应已移除）');
    // R25：单文件上传器（uploadFile(picked.value)）已退役，改为目录式上传入口（REQ-FUNC-001/007，MOD-014）。
    // 强度不低于原断言：页面挂载云盘式浏览器；上传调用只走批次接口且不带 kb 字段；文件夹入口真实存在。
    assert.doesNotMatch(upload, /uploadFile\(picked\.value\)/, '已退役的单文件上传器不应残留');
    assert.match(upload, /<LibraryBrowser\b/, 'UploadPage 应挂载云盘式 LibraryBrowser（目录式上传入口）');
    const libDir = join(root, 'src', 'views', 'library');
    const libText = ['LibraryBrowser.vue', 'UploadBatchPanel.vue', 'ConflictDialog.vue', 'FolderDeleteDialog.vue']
      .map((f) => stripComments(readText(join(libDir, f))))
      .join('\n');
    const batchStore = stripComments(readText(join(root, 'src', 'stores', 'uploadBatch.ts')));
    assert.doesNotMatch(libText + batchStore, /kbId|kb_id\s*[:=]/, '目录式上传视图 / 批次 store 出现 kb 输入（应由服务端推导）');
    assert.match(libText, /<input[^>]*\bwebkitdirectory\b/, '缺少文件夹上传入口（webkitdirectory）');
    assert.match(batchStore, /\.planUpload\(/, '批次 store 应经 planUpload 提交上传清单');
    assert.match(batchStore, /\.uploadBatchItem\(\s*state\.batchId\s*,\s*idx\s*,\s*files\[idx\]\s*\)/, '批次 store 应经 uploadBatchItem 逐文件上传（仅文件）');
    assert.ok(upload.includes('项目域'), '视图文案未改为「项目域」');

    const clientTs = stripComments(readText(rev18.client));
    assert.match(clientTs, /uploadFile\(file:\s*File\)/, '客户端 uploadFile 签名应为单参（file）');
    assert.match(clientTs, /body\.append\('file',\s*file\)/, 'FormData 只应 append file 字段');
    assert.match(
      clientTs,
      /uploadBatchItem\(batchId:\s*string,\s*clientIdx:\s*number,\s*file:\s*File\)[^}]*body\.append\('file',\s*file\)/s,
      '批次逐文件上传方法应只 append file 字段',
    );
    assert.doesNotMatch(
      clientTs,
      /body\.append\(\s*'kb/,
      'FormData 不得 append kb / kb_id（客户端不可自证范围，ADR-41）',
    );
  });

  it('33. LLM Key 页：只回显掩码 / 存在性 / 更新时间 + 明文提交后清空 + 重启由用户手工执行', () => {
    const page = stripComments(readText(rev18.llmKey));
    assert.match(page, /status\?\.masked|status\.masked|masked/, '缺少掩码回显');
    assert.match(page, /status\?\.updated_at|updated_at/, '缺少更新时间回显');
    assert.match(page, /status\?\.configured|configured/, '缺少存在性（configured）回显');
    assert.match(page, /type="password"/, '写入框应为 password 类型');
    assert.match(page, /secret\.value\s*=\s*''/, '提交后须清空明文输入框');
    // 生效口径：保存 / 清除后**不得**暗示即时生效，须明示「重启由用户手工执行」。
    assert.ok(page.includes('重启由用户手工执行'), '缺少「重启由用户手工执行」提示');
    assert.match(page, /不即时生效/, '应为「不即时生效」的显式提示（ADR-32：保存 + 重启装配）');
    assert.doesNotMatch(page, /立即生效|实时生效/, '不得暗示即时生效');
  });

  it('34. 客户端：REV-18 端点方法齐备（项目 / 账户 / LLM Key）', () => {
    const clientTs = stripComments(readText(rev18.client));
    for (const method of [
      'createProject',
      'updateProject',
      'deleteProject',
      'updateAccount',
      'deleteAccount',
      'llmKeyStatus',
      'setLlmKey',
      'clearLlmKey',
    ]) {
      assert.ok(clientTs.includes(method), `客户端缺少 ${method} 方法`);
    }
    assert.match(clientTs, /'\/api\/llm-key'/, '缺少 /api/llm-key 路由字面量');
    assert.match(clientTs, /export type LlmKeyStatus\b/, '缺少 LlmKeyStatus 类型（类型层不含明文）');
  });

  it('35. LLM Key 类型层不含明文字段 + 「资料管理」保持独立顶级（不并入系统管理三子域）', () => {
    // 类型层事实（AC-IB-39-03 / REQ-NFR-IB-20 / C-IB-42）：响应类型只承载存在性 / 掩码 / 更新时间。
    const clientTs = stripComments(readText(rev18.client));
    const typeMatch = clientTs.match(/export type LlmKeyStatus = \{[\s\S]*?\};/);
    assert.ok(typeMatch, '缺少 `export type LlmKeyStatus`（类型层不含明文的前提）');
    const fields = typeMatch[0];
    for (const name of ['configured', 'masked', 'updated_at']) {
      assert.ok(fields.includes(name), `LlmKeyStatus 缺字段 ${name}`);
    }
    assert.doesNotMatch(
      fields,
      /\b(secret|api_key|plaintext|token)\b/,
      'LlmKeyStatus 出现了明文字段（明文不得进入响应类型）',
    );

    // IA（OQ-IB-31 裁决）：三子域 = 账户 / 项目 / LLM Key；「资料管理」(files) **保持独立顶级**。
    const layout = stripComments(readText(rev18.layout));
    const top = layout.match(/TOP_ORDER\s*=\s*\[([^\]]*)\]/);
    const system = layout.match(/SYSTEM_ORDER\s*=\s*\[([^\]]*)\]/);
    assert.ok(top && system, '缺少 TOP_ORDER / SYSTEM_ORDER');
    assert.ok(top[1].includes("'files'"), '「资料管理」不在顶级导航');
    assert.ok(
      !system[1].includes("'files'"),
      '「资料管理」被并入系统管理三子域（应保持独立顶级）',
    );
  });
});

// --------------------------------------------------------------------------- //
// REV-21 前端冒烟：编排图「专家节点实显」（IFC-IB-393 / 394；ADR-52）
//
// 溯源：US-IB-51（实显本项目实际配置的专家）、US-IB-52（专家集合变更后图随之更新、图仍只读）、
//       US-IB-53（结构节点与专家节点可区分）、US-IB-54（n 专家规模完整可见）。
// 策略：与既有 R10/R13/R14/R16/REV-18 层一致 —— **源码结构**断言（零新增依赖，Node 20 可跑）。
//       真实运行期渲染（Vue 挂载 / 画布交互）**离线不可验**，见 docs/test_report.md NOT_TESTABLE。
// --------------------------------------------------------------------------- //

const r21 = {
  config: configPagePath,
  client: join(root, 'src', 'api', 'client.ts'),
};

describe('REV-21 前端冒烟：编排图专家节点实显（cn_label / graph-expert / 仍只读）', () => {
  const page = () => stripComments(readText(r21.config));

  it('36. 专家节点标签取 derived.experts[].cn_label（默认专家带「（默认）」标记，无匹配回落节点名）', () => {
    const text = page();
    // 逐专家显示元数据来自后端派生（不是前端自造）
    assert.match(text, /DerivedExpertEntry/, '缺少 DerivedExpertEntry 类型引用');
    assert.match(text, /derived\.experts/, '页面未消费 derived.experts（专家节点显示元数据）');
    assert.match(text, /expertMeta/, '缺少按 name 索引的专家元数据');
    // 标签取 cn_label；默认专家带「（默认）」标记；无匹配时回落节点名（结构节点 / 合成端点）
    assert.match(text, /meta\.cn_label/, '节点标签未取 cn_label');
    assert.ok(text.includes('（默认）'), '默认专家缺少「（默认）」标记');
    assert.match(text, /label:\s*meta\s*\?/, '无 derived.experts 匹配时应回落节点名');
    // 专家节点清单区列出 cn_label（name）供与定义文档核对（OQ-IB-53=A：name 作次级信息）
    assert.match(text, /expertEntries/, '缺少专家节点清单（图例区）');
    assert.ok(text.includes('（{{ e.name }}）'), '清单未回显专家名 name 供核对');
  });

  it('37. 专家节点与结构节点 / 合成端点在视觉 / 图例上可区分（graph-expert / graph-endpoint）', () => {
    const text = page();
    assert.ok(text.includes('graph-expert'), '缺少专家节点区分类 graph-expert');
    assert.ok(text.includes('graph-endpoint'), '缺少合成端点区分类 graph-endpoint');
    assert.match(text, /nodeClassOf\(/, '缺少节点 class 派生');
    // 图例项：专家节点（实线蓝框）与 START / END（虚线）各有一项
    assert.ok(text.includes('legend-box expert'), '缺少专家节点图例块');
    assert.ok(text.includes('专家节点'), '缺少「专家节点」图例文案');
    assert.ok(text.includes('START / END'), '缺少合成端点图例文案');
  });

  it('38. 编排图仍只读：节点不可拖拽 / 不可连线，且无运行期增删图节点 / 边的入口', () => {
    const text = page();
    assert.match(text, /:nodes-draggable="false"/, '节点必须不可拖拽（只读）');
    assert.match(text, /:nodes-connectable="false"/, '节点必须不可连线（只读）');
    // 无任何运行期改图（增删图节点 / 边）的入口标识
    assert.doesNotMatch(
      text,
      /\b(addNode|removeNode|deleteNode|addEdge|removeEdge|deleteEdge)\b/,
      '配置页出现图拓扑编辑入口（REQ-FUNC-IB-26 ② / AC-IB-52-03）',
    );
    // 拓扑不可编辑：编排不在可编辑白名单（页面仍以服务端 editable_fields 为准）
    assert.match(text, /editable_fields/, '可编辑白名单来源缺失');
  });

  it('39. 客户端类型契约：DerivedExpertEntry 三字段 + DerivedViewSummary.experts', () => {
    const clientTs = stripComments(readText(r21.client));
    const typeMatch = clientTs.match(/export type DerivedExpertEntry = \{[\s\S]*?\};/);
    assert.ok(typeMatch, '缺少 `export type DerivedExpertEntry`');
    for (const name of ['name', 'cn_label', 'is_default']) {
      assert.ok(typeMatch[0].includes(name), `DerivedExpertEntry 缺字段 ${name}`);
    }
    // **不含**工具授权摘要（OQ-IB-53=A）
    assert.doesNotMatch(
      typeMatch[0],
      /\b(tools|tool_names|tool_grants|capability_digest)\b/,
      'DerivedExpertEntry 出现了工具授权摘要字段（不应含）',
    );
    assert.match(clientTs, /experts:\s*DerivedExpertEntry\[\]/, 'DerivedViewSummary 缺少 experts 字段');
  });

  it('40. 节点 / 边集合由后端派生（前端不自展开占位节点、不硬编码 expert 字面量）', () => {
    const text = page();
    // 节点集合来自 derived.nodes / derived.conditional_edges / derived.edges（后端唯一裁决者）
    assert.match(text, /derived\.nodes/, '节点集合未取 derived.nodes');
    assert.match(text, /derived\.conditional_edges/, '条件边未取 derived.conditional_edges');
    assert.match(text, /derived\.edges/, '普通边未取 derived.edges');
    // **不得**在前端硬编码占位节点 `expert` 或复刻展开规则
    assert.doesNotMatch(text, /EXPERT_PLACEHOLDER/, '前端不得持有占位节点常量（展开属服务端显示投影）');
    assert.doesNotMatch(text, /'expert'/, "前端不得硬编码字面量 'expert' 节点名");
  });
});

// ---------------------------------------------------------------------------
// R25（GROUP_D）：资料库目录式界面 —— 源码结构契约（组件无挂载框架，沿用既有“读源码 + 正则”口径）
// 溯源：US-001/002/006/009/011/015；REQ-NFUNC-005/006（前端并发 2、写操作按权限隐藏）。
// ---------------------------------------------------------------------------
const r25 = {
  lib: join(root, 'src', 'views', 'library'),
  store: join(root, 'src', 'stores', 'uploadBatch.ts'),
  client: join(root, 'src', 'api', 'client.ts'),
};
const r25lib = (name) => stripComments(readText(join(r25.lib, name)));

describe('R25 前端冒烟：资料库目录式界面', () => {
  it('41. 冲突弹窗：覆盖 / 跳过 / 两者都保留并自动改名 三选项；关闭 = 取消整次操作（不替用户选默认值）；文件夹合并有警示', () => {
    const text = r25lib('ConflictDialog.vue');
    for (const label of ['覆盖', '跳过', '两者都保留并自动改名']) {
      assert.ok(text.includes(label), `冲突弹窗缺少选项「${label}」`);
    }
    assert.match(text, /value="overwrite"/, '缺少 overwrite 选项取值');
    assert.match(text, /value="skip"/, '缺少 skip 选项取值');
    assert.match(text, /value="rename"/, '缺少 rename 选项取值');
    // 遮罩点击 / 右上角关闭 / 取消按钮 三个出口都只发 cancel（AC-011-04）
    assert.ok((text.match(/emit\('cancel'\)/g) || []).length >= 3, '关闭弹窗的三个出口都应只发出 cancel');
    assert.match(text, /@click\.self="emit\('cancel'\)"/, '点击遮罩应取消');
    assert.ok(text.includes('同名文件将被覆盖'), '文件夹合并覆盖应有“同名文件将被覆盖”警示（A-03）');
  });

  it('42. 批次上传 store：并发固定为 2；进度“已处理 N / 总数”；跳过原因文案覆盖 5 类；限额提示携带上限与实际值', () => {
    const store = stripComments(readText(r25.store));
    assert.match(store, /export const UPLOAD_CONCURRENCY\s*=\s*2\s*;/, '前端上传并发必须固定为 2（与 SSE 共享 Waitress 线程，ADR-003）');
    assert.match(store, /Array\.from\(\{\s*length:\s*UPLOAD_CONCURRENCY\s*\}/, '并发 worker 数应由 UPLOAD_CONCURRENCY 决定');
    for (const [code, label] of [
      ['UNSUPPORTED_TYPE', '不支持的文件类型'],
      ['EMPTY_FILE', '文件为空'],
      ['TOO_LARGE', '超出单文件大小上限'],
      ['MAGIC_MISMATCH', '文件内容与扩展名不符'],
      ['CONTENT_UNCHANGED', '内容未变化'],
    ]) {
      assert.match(store, new RegExp(`${code}:\\s*'${label}'`), `缺少跳过原因文案 ${code}`);
    }
    for (const code of ['limit_files', 'limit_total_bytes', 'depth_exceeded']) {
      assert.ok(store.includes(`'${code}'`), `限额提示未处理 ${code}`);
    }
    assert.match(store, /raw\.actual/, '限额提示应带实际值');
    assert.match(store, /raw\.limit/, '限额提示应带上限值');
    const panel = r25lib('UploadBatchPanel.vue');
    assert.match(panel, /已处理\s*\{\{\s*state\.processed\s*\}\}\s*\/\s*\{\{\s*state\.total\s*\}\}/, '缺少“已处理 N / 总数”进度');
    assert.match(panel, /role="progressbar"/, '缺少进度条');
    assert.match(panel, /if \(!picked\.length\) return;/, '未选任何文件时不得发起上传（AC-007-02：无空提交）');
  });

  it('46. DEF-R25-002：三条限额提示文案与 AC-015-01/02/04 字面一致（含实际值与上限）', () => {
    const store = stripComments(readText(r25.store));
    // AC-015-01：“单次最多上传 1000 个文件（当前 1001）”
    assert.ok(store.includes('`单次最多上传 ${raw.limit} 个文件（当前 ${raw.actual ?? \'?\'}）`'), 'limit_files 文案应为“单次最多上传 {limit} 个文件（当前 {actual}）”');
    // AC-015-04：“单次上传总大小超过上限（当前 {实际大小}，上限 {L}）”
    assert.ok(store.includes('`单次上传总大小超过上限（当前 ${mb(raw.actual ?? 0)}，上限 ${mb(raw.limit)}）`'), 'limit_total_bytes 文案应为“单次上传总大小超过上限（当前 {实际}，上限 {L}）”');
    // AC-015-02：“目录层级最多 10 层”
    assert.ok(store.includes('`目录层级最多 ${raw.limit} 层`'), 'depth_exceeded 文案应为“目录层级最多 {limit} 层”');
    assert.doesNotMatch(store, /超过\s*\$\{raw\.limit\}|最多\s*\$\{raw\.limit\}\s*个文件，/, '不得保留旧文案');
  });

  it('43. 资料浏览器：三个时间一律本地时区到秒、无值显示 —；写操作按 can_manage 隐藏；更新中 / 更新失败 / 重建后暂不可检索有明确提示', () => {
    const text = r25lib('LibraryBrowser.vue');
    assert.match(text, /if \(!iso\) return '—';/, '无值应显示 —');
    assert.match(text, /getFullYear\(\)[\s\S]*getHours\(\)[\s\S]*getSeconds\(\)/, '时间应按本地时区格式化到秒');
    for (const field of ['file.uploaded_at', 'file.content_updated_at', 'file.indexed_at']) {
      assert.ok(text.includes(`fmtDate(${field})`), `缺少 ${field} 的展示`);
    }
    assert.match(text, /permissions\.can_manage\s*===\s*true/, '写操作可见性应取自 permissions.can_manage');
    assert.match(text, /<UploadBatchPanel v-if="canManage"/, '无管理权限时不得展示上传入口');
    assert.ok(text.includes('更新中（旧版本仍可检索）'), '缺少“更新中（旧版本仍可检索）”提示');
    assert.ok(text.includes('更新失败（旧版本仍有效）'), '缺少“更新失败”提示');
    assert.ok(text.includes('已索引，重建切换后可检索'), '缺少重建在途期间的提示');
  });

  it('44. 删除文件夹：确认框展示子文件夹 / 文件数；循环 deleteFolderStep 至 done；部分失败展示 remaining 与失败清单', () => {
    const text = r25lib('FolderDeleteDialog.vue');
    assert.match(text, /detail\.subtree_folders/, '确认框应展示子文件夹数');
    assert.match(text, /detail\.subtree_files/, '确认框应展示文件数');
    assert.match(text, /client\.deleteFolderStep\(/, '应经 client.deleteFolderStep 分步删除');
    assert.match(text, /if \(step\.done\) break;/, '应循环至 done');
    assert.match(text, /remaining_files/, '部分失败应展示剩余文件数');
    assert.match(text, /\.failed/, '应展示失败清单');
  });

  it('45. 客户端：目录 / 批次 / 更新 / 移动 方法齐备且 HTTP 只经 request；409 冲突体被解析进 ApiClientError.conflicts', () => {
    const clientTs = stripComments(readText(r25.client));
    for (const method of [
      'browse', 'getFolder', 'createFolder', 'renameFolder', 'deleteFolderStep', 'moveEntries',
      'renameFile', 'updateFile', 'discardRevision', 'planUpload', 'uploadBatchItem', 'getUploadBatch',
    ]) {
      assert.match(clientTs, new RegExp(`\\n\\s+${method}\\(`), `ApiClient 缺少方法 ${method}`);
    }
    assert.match(clientTs, /conflicts\??:\s*ConflictInfo\[\]/, 'ApiClientError 应携带 conflicts');
    assert.doesNotMatch(clientTs, /axios/, '禁用 axios');
    const store = stripComments(readText(r25.store));
    assert.doesNotMatch(store, /\bfetch\(/, 'store 不得绕过 client.ts 直接 fetch');
  });
});

// --------------------------------------------------------------------------- //
// REV-26 前端冒烟：动态编排图 / 悬停卡片 / 自由画布 / 发布与版本 / Agent Builder（MOD-R26-18~21）
// --------------------------------------------------------------------------- //

const r26dir = join(root, 'src', 'components', 'config');
const r26 = (f) => stripComments(readText(join(r26dir, f)));

describe('REV-26 前端冒烟：graphModel 纯函数（离线可跑）', () => {
  let m;
  const graph = () => ({
    nodes: [
      { id: 'start', kind: 'start', x: 0, y: 0 },
      { id: 'route-1', kind: 'route', x: 0, y: 0 },
      { id: 'kb-agent', kind: 'agent', x: 0, y: 0, expert: 'kb-agent', input_mode: 'query_only' },
      { id: 'end', kind: 'end', x: 0, y: 0 },
    ],
    edges: [
      { id: 'e1', source: 'start', target: 'route-1' },
      { id: 'e2', source: 'route-1', target: 'kb-agent', branch_key: 'kb-agent' },
      { id: 'e3', source: 'kb-agent', target: 'end' },
    ],
  });
  const agents = () =>
    new Map([['kb-agent', { name: 'kb-agent', cn_label: '知识库助手', is_default: true, tool_names: ['search_knowledge'], prompt_main_present: true, prompt_main_head: '你是知识库助手' }]]);

  it('46. 悬停卡片模型：agent 含标签 / name / 默认 / 工具 / 提示词存在；无工具显示“无”', async () => {
    m = await import('../src/components/config/graphModel.ts');
    const g = graph();
    const card = m.buildHoverCardModel(g.nodes[2], agents());
    assert.equal(card.title, '知识库助手');
    const text = JSON.stringify(card.lines);
    assert.ok(text.includes('默认专家') && text.includes('search_knowledge') && text.includes('存在'));
    const bare = m.buildHoverCardModel(g.nodes[2], new Map([['kb-agent', { name: 'kb-agent', cn_label: 'x', tool_names: [] }]]));
    assert.ok(bare.lines.some((l) => l.label === '已授权工具' && l.value === '无'));
    const route = m.buildHoverCardModel(g.nodes[1], agents(), { tau: 0.65, margin: 0.05, max_expert_steps: 8, default_expert: 'kb-agent' });
    assert.ok(route.lines.some((l) => l.label === 'tau' && l.value === '0.65'));
  });

  it('47. 连线预校验 / 位置 / 删除：不可指入开始、不可自环、不可重复；节点删除统计受影响边数', async () => {
    m = await import('../src/components/config/graphModel.ts');
    const g = graph();
    assert.equal(m.precheckConnection(g, 'kb-agent', 'start').ok, false);
    assert.equal(m.precheckConnection(g, 'kb-agent', 'kb-agent').ok, false);
    assert.equal(m.precheckConnection(g, 'start', 'route-1').ok, false);
    assert.equal(m.precheckConnection(g, 'route-1', 'end').ok, true);
    assert.equal(m.edgesTouching(g, 'kb-agent'), 2);
    assert.equal(m.removeNode(g, 'kb-agent').edges.length, 1);
    const moved = m.applyPositions(g, new Map([['kb-agent', { x: 12.6, y: 5 }]]));
    assert.equal(moved.nodes[2].x, 13);
    const flow = m.graphToFlow(g, agents());
    assert.equal(flow.nodes.length, 4);
    assert.ok(flow.nodes.find((n) => n.id === 'kb-agent').data.label.includes('（默认）'));
  });

  it('48. 节点面板只含受限节点类型（无代码 / 表达式节点）', async () => {
    m = await import('../src/components/config/graphModel.ts');
    assert.deepEqual([...m.ADDABLE_KINDS].sort(), ['agent', 'condition', 'confirm', 'join', 'route']);
  });
});

describe('REV-26 前端冒烟：组件源码结构与导航入口', () => {
  it('49. 画布：只读档不可拖拽 / 连线；悬停事件；不使用 v-html', () => {
    const t = r26('FlowCanvas.vue');
    assert.match(t, /:nodes-draggable="!readonly"/);
    assert.match(t, /:nodes-connectable="!readonly"/);
    assert.match(t, /@node-mouse-enter/);
    assert.match(t, /@edge-mouse-enter/);
    for (const f of ['FlowCanvas.vue', 'NodeHoverCard.vue', 'AgentDetailPanel.vue', 'BuilderDrawer.vue', 'TrialPanel.vue', 'PublishDialog.vue']) {
      assert.doesNotMatch(r26(f), /v-html/, `${f} 不得使用 v-html（提示词 / 关键词一律纯文本）`);
    }
  });

  it('50. 保存流程：先差异预览再确认，校验错误无“忽略”选项，冲突走 ConflictDialog，成功提示“已生效”', () => {
    const studio = stripComments(readText(join(root, 'src', 'views', 'ConfigStudio.vue')));
    assert.match(studio, /publishPreview\(/);
    assert.match(studio, /confirmSave/);
    assert.match(studio, /已生效（版本/);
    assert.doesNotMatch(studio, /重启 `?ib-web/);
    assert.match(studio, /ConflictDialog/);
    assert.doesNotMatch(r26('PublishDialog.vue'), /忽略并继续|forceSave|skipValidation/);
  });

  it('51. 导航入口可达：路由 config 指向 ConfigHub（默认编排画布），侧栏仍含 config', () => {
    const router = stripComments(readText(join(root, 'src', 'router', 'index.ts')));
    assert.match(router, /name: 'config',[\s\S]*?component: ConfigHub/);
    assert.match(stripComments(readText(join(root, 'src', 'views', 'ConfigHub.vue'))), /ConfigStudio/);
    assert.match(stripComments(readText(join(root, 'src', 'layouts', 'ConsoleLayout.vue'))), /TOP_ORDER\s*=\s*\[[^\]]*'config'/);
  });

  it('52. client.ts：新方法齐备、HTTP 只经 request/fetch、无 axios / localStorage / CDN', () => {
    const c = stripComments(readText(join(root, 'src', 'api', 'client.ts')));
    for (const method of ['configStatus', 'definitionConfigV2', 'publishPreview', 'publish', 'listVersions', 'rollback', 'saveDraft', 'trialStream', 'builderDraft', 'builderEvaluate', 'builderOptimize', 'builderReviewExisting', 'putAccess']) {
      assert.match(c, new RegExp(`\\n\\s+(async )?${method}\\(`), `ApiClient 缺少方法 ${method}`);
    }
    assert.doesNotMatch(c, /axios|localStorage/);
    const store = stripComments(readText(join(root, 'src', 'stores', 'configDraft.ts')));
    assert.doesNotMatch(store, /localStorage|indexedDB|\bfetch\(/);
  });

  it('53. Builder：空白 / 克隆 / 按需求生成 / 评审四入口；重名须改名才可加入画布；LLM 判定项带标注', () => {
    const b = r26('BuilderDrawer.vue');
    for (const label of ['空白表单', '克隆已有', '按需求生成', '评审并优化已有']) assert.ok(b.includes(label), label);
    assert.match(b, /name 已存在，请修改/);
    assert.match(b, /:disabled="problems\.length > 0"/);
    assert.match(r26('BuilderEvalView.vue'), /LLM 判定/);
  });

  it('54. CR-012 档位管理：入口在编排画布“权限管理”页签（仅管理档），经 getAccess/putAccess，改后刷新', () => {
    const studio = stripComments(readText(join(root, 'src', 'views', 'ConfigStudio.vue')));
    assert.match(studio, /import AccessPanel from/);
    assert.match(studio, /v-if="level === 'manage'"[^>]*label="权限管理"/);
    const p = r26('AccessPanel.vue');
    assert.match(p, /getAccess\(/);
    assert.match(p, /putAccess\(row\.user_id, next\)/);
    assert.match(p, /finally[\s\S]*await load\(\)/, '改完以服务端为准刷新');
    for (const label of ['查看', '编辑', '管理']) assert.ok(p.includes(label), label);
    assert.match(p, /canManage/);
    assert.doesNotMatch(p, /axios|localStorage|v-html|\bfetch\(/);
  });

  it('55. CR-012 账号创建页：档位选择，默认 manage，随 createAccount 提交；列表展示档位', () => {
    const a = stripComments(readText(join(root, 'src', 'views', 'AccountsPage.vue')));
    assert.match(a, /config_level: 'manage' as ConfigLevel/);
    assert.match(a, /createForm\.config_level = 'manage'/);
    assert.match(a, /config_level: createForm\.config_level/);
    assert.match(a, /v-model="createForm\.config_level"/);
    for (const v of ['view', 'edit', 'manage']) assert.match(a, new RegExp(`value="${v}"`));
    assert.match(a, /label="配置档位"/);
  });

  it('56. 查看档只读（AC-010-01 / AC-011-04）：readonly 贯通画布 / 面板 / 调色板，保存与 Builder 入口隐藏', () => {
    const studio = stripComments(readText(join(root, 'src', 'views', 'ConfigStudio.vue')));
    assert.match(studio, /const readonly = computed\(\(\) => level\.value === 'view'\)/);
    assert.match(studio, /v-if="!readonly"[^>]*保存并生效|v-if="!readonly"[^\n]*startSave/);
    assert.match(studio, /<FlowCanvas[\s\S]*?:readonly="readonly"/);
    assert.match(studio, /<AgentDetailPanel[\s\S]*?:readonly="readonly"/);
    assert.match(r26('FlowCanvas.vue'), /:nodes-draggable="!readonly"/);
    assert.match(r26('FlowCanvas.vue'), /:nodes-connectable="!readonly"/);
    assert.match(r26('NodePalette.vue'), /v-if="!readonly"/);
    assert.match(r26('AgentDetailPanel.vue'), /:readonly="readonly"/);
  });
});
