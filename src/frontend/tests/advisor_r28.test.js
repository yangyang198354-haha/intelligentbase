/**
 * [REV-28 / GROUP_D] 顾问前端测试（node:test，零新增依赖；MOD-R28-17 / MOD-R28-18）。
 *
 * 做法（同 config_studio_r27.test.js）：
 *  1. advisorPlan.ts——用工程已有的 `typescript` 在内存中转译为 ESM，把 './graphModel' 说明符替换为其转译后的 data: URL，真实执行；
 *  2. client.ts——转译后真实实例化 ApiClient，以替身 `fetch` / `sessionStorage` 捕获请求（不触网），验证 createProject / 联网上限接口的请求形状；
 *  3. 组件与页面壳（.vue / router / layout）——无挂载环境，只读源码、剥注释后做结构断言。
 *
 * 局限（如实）：没有组件挂载环境与可用的无头浏览器，且不得新增依赖——复选框的实际渲染 / 点击、画布上顾问节点的拖拽与连线、
 * “加入顾问”按钮点击后的 ElMessage / ElMessageBox 弹窗、联网上限页的表单交互无法在此验证，列入 e2e_test_report 的人工验证清单。
 * 层级口径：unit = advisorPlan / client 的真实执行；integration = 源码结构契约（组件 ↔ 纯逻辑 ↔ 路由 / 导航）；e2e（替代口径）= 纯函数 + 请求形状的多步串联。
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';

import ts from 'typescript';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, '..', 'src');
const read = (...p) => readFileSync(join(src, ...p), 'utf8');
const stripComments = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/[^\n]*/g, '$1').replace(/<!--[\s\S]*?-->/g, '');

const transpile = (...p) =>
  ts.transpileModule(read(...p), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
const toUrl = (js) => `data:text/javascript;base64,${Buffer.from(js).toString('base64')}`;
const swap = (js, spec, url) => js.replace(new RegExp(`(['"])${spec.replace(/[./]/g, '\\$&')}\\1`, 'g'), `'${url}'`);

const GM_URL = toUrl(transpile('components', 'config', 'graphModel.ts'));
const AP = await import(toUrl(swap(transpile('components', 'config', 'advisorPlan.ts'), './graphModel', GM_URL)));
const CL = await import(toUrl(transpile('api', 'client.ts')));

// ------------------------------------------------------------------ 夹具
const clone = (o) => JSON.parse(JSON.stringify(o));
const node = (id, kind, extra = {}) => ({ id, kind, x: 0, y: 0, ...extra });
const expert = (name, label, extra = {}) => ({
  name, cn_label: label, keywords: [], exemplars: [], is_data_expert: false, is_delegating: false, is_default: false, status: 'active', max_steps: 4,
  knowledge_scope: { mode: 'all', folder_ids: [] }, ...extra,
});
const BUILTIN = {
  id: 'advisor', name: 'advisor', cn_label: '顾问', summary: '面向客户的专业顾问',
  expert: { name: 'advisor', cn_label: '顾问', keywords: [], exemplars: [], is_data_expert: false, is_delegating: true, is_default: false },
  prompt_main: '# 顾问种子提示词\n面向客户，礼貌专业。', default_tool_grants: [], wiring_version: 1,
};
/** 规范基线（kb-agent 默认）：start → route-1 →(kb-agent|__else__→kb-agent)；kb-agent → end。 */
const canonicalDoc = () => ({
  schema_version: 2,
  route: { tau: 0.65, margin: 0.05, max_expert_steps: 8, default_expert: 'kb-agent' },
  experts: [expert('kb-agent', '知识库助手', { is_default: true })],
  tool_grants: [{ expert_name: 'kb-agent', tool_names: ['search_knowledge'], param_values: [] }],
  graph: {
    nodes: [node('start', 'start'), node('route-1', 'route', { x: 220 }), node('kb-agent', 'agent', { x: 460, expert: 'kb-agent', input_mode: 'query_only' }), node('end', 'end', { x: 700 })],
    edges: [
      { id: 'e-start', source: 'start', target: 'route-1' },
      { id: 'e-r1', source: 'route-1', target: 'kb-agent', branch_key: 'kb-agent' },
      { id: 'e-else', source: 'route-1', target: 'kb-agent', branch_key: '__else__' },
      { id: 'e-o1', source: 'kb-agent', target: 'end' },
    ],
  },
});
const sortById = (xs) => [...xs].sort((a, b) => (a.id > b.id ? 1 : -1));

// ====================================================================== 单元：advisorPlan（US-003 / US-005）
describe('advisorPlan 纯函数（真实执行）', () => {
  it('TC-FE-R28-001 hasAdvisor 判据 = 名为 advisor ∧ is_delegating ∧ 未停用（AQ5=A）', () => {
    const d = canonicalDoc();
    assert.equal(AP.hasAdvisor(d), false);
    const mk = (o) => ({ ...d, experts: [...d.experts, expert('advisor', '顾问', o)] });
    assert.equal(AP.hasAdvisor(mk({ is_delegating: true })), true);
    assert.equal(AP.hasAdvisor(mk({ is_delegating: false })), false);
    assert.equal(AP.hasAdvisor(mk({ is_delegating: true, status: 'disabled' })), false);
    assert.equal(AP.hasAdvisor({ ...d, experts: [expert('other', '别的', { is_delegating: true })] }), false);
    assert.equal(AP.ADVISOR_ID, 'advisor');
  });

  it('TC-FE-R28-002 addAdvisor 规范形态：自动接线（agent→顾问、路由 __else__→顾问、顾问→结束），顾问 with_upstream，授权为空，种子提示词补丁', () => {
    const d = canonicalDoc();
    const r = AP.addAdvisor(d, d.graph, BUILTIN);
    assert.equal(r.wired, true);
    assert.ok(AP.hasAdvisor(r.doc));
    const adv = r.graph.nodes.find((n) => n.id === 'advisor');
    assert.deepEqual([adv.kind, adv.expert, adv.input_mode], ['agent', 'advisor', 'with_upstream']);
    const edges = (id) => r.graph.edges.find((e) => e.id === id);
    assert.equal(edges('e-else').target, 'advisor');
    assert.equal(edges('e-o1').target, 'advisor');
    assert.equal(edges('e-r1').target, 'kb-agent'); // 按名委托分支仍直达 kb-agent
    const out = r.graph.edges.filter((e) => e.source === 'advisor');
    assert.equal(out.length, 1);
    assert.equal(out[0].target, 'end');
    assert.ok(r.graph.nodes.find((n) => n.id === 'end').x > d.graph.nodes.find((n) => n.id === 'end').x); // 结束节点右移腾位
    const ex = r.doc.experts.find((e) => e.name === 'advisor');
    assert.deepEqual([ex.status, ex.is_delegating, ex.is_default], ['active', true, false]);
    assert.deepEqual(r.doc.tool_grants.find((g) => g.expert_name === 'advisor'), { expert_name: 'advisor', tool_names: [], param_values: [] }); // 联网工具默认未授权
    assert.deepEqual(r.promptPatch, { expert: 'advisor', main: BUILTIN.prompt_main });
    assert.match(r.message, /未保存/);
  });

  it('TC-FE-R28-003 addAdvisor 不修改入参（纯函数），且对已有顾问幂等', () => {
    const d = canonicalDoc();
    const snapshot = JSON.stringify(d);
    const r = AP.addAdvisor(d, d.graph, BUILTIN);
    assert.equal(JSON.stringify(d), snapshot);
    const again = AP.addAdvisor(r.doc, r.graph, BUILTIN);
    assert.equal(again.promptPatch, null);
    assert.equal(again.wired, true);
    assert.equal(again.doc.experts.filter((e) => e.name === 'advisor').length, 1);
    assert.match(again.message, /已加入/);
  });

  it('TC-FE-R28-004 addAdvisor 非规范形态：不猜测接线，仅放入未连线节点并 wired=false + 手工连线提示', () => {
    const d = canonicalDoc();
    d.graph.nodes.push(node('condition-1', 'condition', { predicate: { kind: 'keyword', branches: [] } }));
    d.graph.edges.push({ id: 'e-c', source: 'route-1', target: 'condition-1' });
    const r = AP.addAdvisor(d, d.graph, BUILTIN);
    assert.equal(r.wired, false);
    assert.match(r.message, /手工连线/);
    const adv = r.graph.nodes.find((n) => n.id === 'advisor');
    assert.ok(adv);
    assert.equal(r.graph.edges.filter((e) => e.source === 'advisor' || e.target === 'advisor').length, 0); // 未连线
    assert.equal(r.graph.edges.length, d.graph.edges.length);
    assert.deepEqual(r.promptPatch, { expert: 'advisor', main: BUILTIN.prompt_main });
  });

  it('TC-FE-R28-005 removeAdvisor：加入→移除往返恢复规范图、专家集与授权', () => {
    const d = canonicalDoc();
    const added = AP.addAdvisor(d, d.graph, BUILTIN);
    const removed = AP.removeAdvisor(added.doc, added.graph);
    assert.deepEqual(sortById(removed.graph.nodes.map((n) => ({ id: n.id, kind: n.kind, expert: n.expert, input_mode: n.input_mode }))),
      sortById(d.graph.nodes.map((n) => ({ id: n.id, kind: n.kind, expert: n.expert, input_mode: n.input_mode }))));
    assert.deepEqual(sortById(removed.graph.edges), sortById(d.graph.edges));
    assert.deepEqual(removed.doc.experts.map((e) => e.name), ['kb-agent']);
    assert.deepEqual(removed.doc.tool_grants, d.tool_grants);
    assert.equal(removed.promptPatch, null);
    assert.match(removed.message, /回滚找回/);
  });

  it('TC-FE-R28-006 removeAdvisor 边界：未加入 ⇒ 原样；顾问为默认专家 ⇒ 不可移除', () => {
    const d = canonicalDoc();
    const none = AP.removeAdvisor(d, d.graph);
    assert.equal(none.doc.experts.length, d.experts.length);
    assert.match(none.message, /未加入/);
    const added = AP.addAdvisor(d, d.graph, BUILTIN);
    const asDefault = { ...added.doc, experts: added.doc.experts.map((e) => (e.name === 'advisor' ? { ...e, is_default: true } : e)) };
    const blocked = AP.removeAdvisor(asDefault, added.graph);
    assert.equal(blocked.doc.experts.length, asDefault.experts.length);
    assert.match(blocked.message, /默认专家/);
  });

  it('TC-FE-R28-007 多 agent 规范图：每个叶子 agent 都改接顾问，往返无损', () => {
    const d = canonicalDoc();
    d.experts.push(expert('contract-agent', '合同审查助手'));
    d.tool_grants.push({ expert_name: 'contract-agent', tool_names: ['search_knowledge'], param_values: [] });
    d.graph.nodes.splice(3, 0, node('contract-agent', 'agent', { x: 460, y: 110, expert: 'contract-agent', input_mode: 'query_only' }));
    d.graph.edges.push({ id: 'e-r2', source: 'route-1', target: 'contract-agent', branch_key: 'contract-agent' }, { id: 'e-o2', source: 'contract-agent', target: 'end' });
    const a = AP.addAdvisor(d, d.graph, BUILTIN);
    assert.equal(a.wired, true);
    assert.deepEqual(a.graph.edges.filter((e) => e.target === 'advisor').map((e) => e.source).sort(), ['contract-agent', 'kb-agent', 'route-1']);
    const r = AP.removeAdvisor(a.doc, a.graph);
    assert.deepEqual(sortById(r.graph.edges), sortById(d.graph.edges));
  });
});

// ====================================================================== 单元：client 请求形状（US-002 / US-016）
const fakeClient = () => {
  const calls = [];
  globalThis.sessionStorage = { getItem: () => 'tok', setItem() {}, removeItem() {} };
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return { ok: true, status: 200, text: async () => '{}', headers: { get: () => null } };
  };
  return { c: new CL.ApiClient(''), calls };
};

describe('ApiClient 请求形状（真实执行，替身 fetch）', () => {
  it('TC-FE-R28-010 createProject 缺省 / false：请求体与升级前逐字相同（不带 enable_advisor 键）', async () => {
    const { c, calls } = fakeClient();
    await c.createProject('p1', '名称');
    await c.createProject('p2', '名称', { enableAdvisor: false });
    await c.createProject('p3', '名称', {});
    assert.equal(calls[0].init.body, JSON.stringify({ project_id: 'p1', name: '名称' }));
    assert.equal(calls[1].init.body, JSON.stringify({ project_id: 'p2', name: '名称' }));
    assert.equal(calls[2].init.body, JSON.stringify({ project_id: 'p3', name: '名称' }));
    for (const k of calls) assert.ok(!k.init.body.includes('enable_advisor'));
    assert.equal(calls[0].url, '/api/projects');
    assert.equal(calls[0].init.method, 'POST');
  });

  it('TC-FE-R28-011 createProject enableAdvisor===true：仅此时请求体带 enable_advisor:true；带 Bearer 头；非 true 值不带键', async () => {
    const { c, calls } = fakeClient();
    await c.createProject('p1', '名称', { enableAdvisor: true });
    assert.equal(calls[0].init.body, JSON.stringify({ project_id: 'p1', name: '名称', enable_advisor: true }));
    assert.equal(calls[0].init.headers.Authorization, 'Bearer tok');
    await c.createProject('p2', '名称', { enableAdvisor: 'true' });
    await c.createProject('p3', '名称', { enableAdvisor: 1 });
    assert.ok(!calls[1].init.body.includes('enable_advisor') && !calls[2].init.body.includes('enable_advisor'));
  });

  it('TC-FE-R28-012 getWebGovernance / putWebGovernance：路径、方法、JSON 体与头', async () => {
    const { c, calls } = fakeClient();
    await c.getWebGovernance();
    await c.putWebGovernance({ max_calls_per_turn: 3, max_fetch_bytes_per_turn: 500000, max_seconds_per_turn: 20 });
    assert.equal(calls[0].url, '/api/web-governance');
    assert.ok(!calls[0].init.method || calls[0].init.method === 'GET');
    assert.equal(calls[1].url, '/api/web-governance');
    assert.equal(calls[1].init.method, 'PUT');
    assert.deepEqual(JSON.parse(calls[1].init.body), { max_calls_per_turn: 3, max_fetch_bytes_per_turn: 500000, max_seconds_per_turn: 20 });
    assert.equal(calls[1].init.headers['Content-Type'], 'application/json');
  });
});

// ====================================================================== 集成：源码结构契约（组件 ↔ 纯逻辑 ↔ 路由 / 导航）
describe('源码结构契约', () => {
  const projects = stripComments(read('views', 'ProjectsPage.vue'));
  const studio = stripComments(read('views', 'ConfigStudio.vue'));
  const panel = stripComments(read('components', 'config', 'AgentDetailPanel.vue'));
  const router = stripComments(read('router', 'index.ts'));
  const layout = stripComments(read('layouts', 'ConsoleLayout.vue'));
  const govPage = stripComments(read('views', 'WebGovernancePage.vue'));
  const clientSrc = stripComments(read('api', 'client.ts'));

  it('TC-FE-R28-020 ProjectsPage：“启用顾问”复选框存在、绑定 enable_advisor、初始与重置均为 false（OQ-R28-05=A），提交经 client.createProject', () => {
    assert.match(projects, /reactive\(\{ project_id: '', name: '', enable_advisor: false \}\)/);
    assert.match(projects, /<el-checkbox v-model="createForm\.enable_advisor">启用顾问<\/el-checkbox>/);
    assert.match(projects, /createForm\.enable_advisor = false;/); // 打开对话框 / 提交后重置为未勾选
    assert.match(projects, /client\.createProject\(createForm\.project_id\.trim\(\), createForm\.name\.trim\(\), \{\s*enableAdvisor: createForm\.enable_advisor,?\s*\}\)/);
    assert.ok(!/enable_advisor:\s*true/.test(projects), '不得有默认勾选');
    assert.match(projects, /默认不勾选/);
  });

  it('TC-FE-R28-021 ConfigStudio：加入 / 移除顾问按钮仅编辑档可见（!readonly），互斥显示；加入需目录有内置顾问；经纯函数 addAdvisor / removeAdvisor', () => {
    assert.match(studio, /v-if="!readonly && !advisorAdded"[^>]*:disabled="!builtinAdvisor"[^>]*@click="onAddAdvisor">加入顾问/);
    assert.match(studio, /v-if="!readonly && advisorAdded"[^>]*@click="onRemoveAdvisor">移除顾问/);
    assert.match(studio, /import \{ addAdvisor, hasAdvisor, removeAdvisor \} from '\.\.\/components\/config\/advisorPlan'/);
    assert.match(studio, /function onAddAdvisor\(\): void \{[\s\S]*?if \(!doc \|\| !builtin \|\| readonly\.value\) return;/);
    assert.match(studio, /function onRemoveAdvisor\(\): void \{[\s\S]*?readonly\.value\) return;/);
    // 加入：非规范形态给出手工连线提示；移除：二次确认 + 走可撤销的 applyRemoval
    assert.match(studio, /ElMessageBox\.alert\(r\.message, '请手工连线'/);
    assert.match(studio, /window\.confirm\('确认移除顾问？/);
    assert.match(studio, /store\.applyRemoval\('顾问「advisor」'/);
    // 加入 / 移除只改草稿（store.document / applyRemoval），函数体内不发任何 HTTP 请求
    const addBody = studio.match(/function onAddAdvisor\(\): void \{[\s\S]*?\n\}/)[0];
    const rmBody = studio.match(/function onRemoveAdvisor\(\): void \{[\s\S]*?\n\}/)[0];
    assert.ok(!/client\./.test(addBody) && !/client\./.test(rmBody) && !/await /.test(addBody + rmBody));
  });

  it('TC-FE-R28-022 AgentDetailPanel：顾问只读说明 / is_delegating 开关 / 域名占位 / 全局上限提示；写入控件受 readonly 约束', () => {
    assert.match(panel, /v-if="expert\(\)\?\.name === 'advisor'" class="advisor-note"/);
    assert.match(panel, /<el-checkbox :model-value="expert\(\)\?\.is_delegating" :disabled="readonly"/);
    assert.match(panel, /s\.name\.endsWith\('_domains'\) \? '逗号分隔域名'/);
    assert.match(panel, /v-if="t\.startsWith\('web_'\) && catalog\?\.web\?\.caps"/);
    assert.match(panel, /全局上限：每回合 \{\{ catalog\.web\.caps\.max_calls_per_turn \}\} 次/);
    assert.match(panel, /:disabled="readonly" :placeholder="s\.name\.endsWith/); // 参数输入框在查看档禁用
  });

  it('TC-FE-R28-023 路由与导航：web-governance 路由仅 admin；挂在“系统管理”下；导航项排序追加 web-governance', () => {
    assert.match(router, /path: 'web-governance',\s*name: 'web-governance',\s*component: WebGovernancePage,\s*meta: \{ title: '联网上限', requiresAdmin: true \}/);
    assert.match(router, /import WebGovernancePage from '\.\.\/views\/WebGovernancePage\.vue'/);
    // REV-29 MOD-R29-22 契约变更；授权 GR-C-001 REWORK_AUTHORIZED：SYSTEM_ORDER 严格为五项（末尾追加 'mcp'）
    assert.match(layout, /const SYSTEM_ORDER = \['accounts', 'projects', 'llm-key', 'web-governance', 'mcp'\];/);
    // 既有三项的相对顺序不变
    const order = layout.match(/SYSTEM_ORDER = \[([^\]]*)\]/)[1].split(',').map((s) => s.trim().replace(/'/g, ''));
    assert.deepEqual(order.slice(0, 3), ['accounts', 'projects', 'llm-key']);
  });

  it('TC-FE-R28-024 WebGovernancePage：HTTP 只经 client（无 fetch / axios / 外链），403 / 503 有专门文案，保存后用服务端返回回填', () => {
    assert.match(govPage, /import \{ client \} from '\.\.\/app\/env'/);
    assert.ok(!/\bfetch\(/.test(govPage) && !/axios/.test(govPage));
    assert.ok(!/https?:\/\//.test(govPage), '运行期禁止外链 / CDN');
    assert.match(govPage, /err\.status === 403\) return '当前账户无权管理联网上限（仅管理员可操作）。'/);
    assert.match(govPage, /err\.status === 503\) return '联网上限存储暂不可用/);
    assert.match(govPage, /fill\(\s*await client\.putWebGovernance\(/);
    assert.match(govPage, /Number\(form\.max_calls_per_turn\)/);
  });

  it('TC-FE-R28-025 新增前端代码无 axios / CDN / 外链字体；client.ts 无 axios（package.json 约束）', () => {
    for (const s of [govPage, stripComments(read('components', 'config', 'advisorPlan.ts'))]) {
      assert.ok(!/axios/.test(s) && !/https?:\/\/(cdn|fonts)\./.test(s));
    }
    assert.ok(!/from 'axios'/.test(clientSrc) && !/require\('axios'\)/.test(clientSrc));
    const pkg = JSON.parse(readFileSync(join(here, '..', 'package.json'), 'utf8'));
    assert.ok(!('axios' in { ...pkg.dependencies, ...pkg.devDependencies }));
  });

  it('TC-FE-R28-026 client.ts 类型：BuiltinAgentDto / WebCatalogDto / WebGovernanceDto 已导出；目录响应可选字段 builtin_agents / web（旧后端兼容）', () => {
    for (const t of ['BuiltinAgentDto', 'WebCatalogDto', 'WebGovernanceDto']) assert.match(clientSrc, new RegExp(`export interface ${t}`));
    assert.match(clientSrc, /builtin_agents\?: BuiltinAgentDto\[\];/);
    assert.match(clientSrc, /web\?: WebCatalogDto;/);
    assert.match(clientSrc, /hard_max: \{ max_calls_per_turn: number; max_fetch_bytes_per_turn: number; max_seconds_per_turn: number \};/);
  });
});

// ====================================================================== E2E（替代口径）：纯函数 + 请求形状串联
describe('旅程（替代口径：纯函数 + 请求形状，非真实浏览器）', () => {
  it('TC-FE-R28-E01 管理员建项目 → 编辑者加入顾问 → 序列化草稿 → 再移除：请求体与图在每一步符合约定', async () => {
    const { c, calls } = fakeClient();
    await c.createProject('proj_adv', '顾问项目', { enableAdvisor: true });
    assert.deepEqual(JSON.parse(calls[0].init.body), { project_id: 'proj_adv', name: '顾问项目', enable_advisor: true });
    const base = canonicalDoc();
    const a = AP.addAdvisor(base, base.graph, BUILTIN);
    // 草稿可序列化为发布请求体（服务端 validate_graph 是唯一裁决者；本地只保证结构完整）
    const body = JSON.parse(JSON.stringify({ base_version: 1, document: a.doc, prompts: { advisor: { main: a.promptPatch.main } } }));
    assert.equal(body.document.experts.length, 2);
    assert.equal(body.document.graph.edges.filter((e) => e.source === 'advisor' || e.target === 'advisor').length, 3);
    assert.equal(body.prompts.advisor.main, BUILTIN.prompt_main);
    const r = AP.removeAdvisor(a.doc, a.graph);
    assert.deepEqual(sortById(r.graph.edges), sortById(base.graph.edges));
    assert.equal(AP.hasAdvisor(r.doc), false);
  });

  it('TC-FE-R28-E02 admin 调整联网上限：读 → 改 → 写，请求体仅三个整数键', async () => {
    const { c, calls } = fakeClient();
    const cur = { max_calls_per_turn: 5, max_fetch_bytes_per_turn: 1048576, max_seconds_per_turn: 30, hard_max: {}, updated_at: '', updated_by: '' };
    await c.getWebGovernance();
    await c.putWebGovernance({ max_calls_per_turn: cur.max_calls_per_turn - 2, max_fetch_bytes_per_turn: cur.max_fetch_bytes_per_turn, max_seconds_per_turn: cur.max_seconds_per_turn });
    const sent = JSON.parse(calls[1].init.body);
    assert.deepEqual(Object.keys(sent).sort(), ['max_calls_per_turn', 'max_fetch_bytes_per_turn', 'max_seconds_per_turn']);
    assert.ok(Object.values(sent).every((v) => Number.isInteger(v)));
    assert.equal(sent.max_calls_per_turn, 3);
  });
});
