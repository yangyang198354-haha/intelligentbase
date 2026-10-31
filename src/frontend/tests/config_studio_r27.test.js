/**
 * [REV-27 / GROUP_D] 节点删除前端测试（node:test，零新增依赖；MOD-R27-07）。
 *
 * 做法：
 *  1. nodeRemoval.ts / publishDiff.ts——用工程已有的 `typescript` 在内存中转译为 ESM，先转译 graphModel.ts 得到 data: URL，
 *     再把二者里的 './graphModel' 说明符替换为该 URL，经 data: URL 导入并真实执行；
 *  2. configDraft.ts——运行期只有 `import { computed, ref } from 'vue'` 一个裸导入，测试用一个 8 行的最小 vue 替身
 *     （ref → {value}，computed → 每次读取重算的 getter）替换该说明符，使**真实 store 代码**离线执行
 *     （dirty / applyRemoval / undoRemoval / load / discard / markSaved 的语义由真实代码给出，替身只提供存取）；
 *  3. 组件与页面壳（.vue）——无挂载环境，只能读源码、剥注释后做结构断言。
 *
 * 局限（如实）：没有组件挂载环境，也没有可用的无头浏览器，且不得新增依赖——浏览器内真实按键、vue-flow 选中态
 * （风险 R-1）、悬停卡片视觉清理、1 秒响应无法在此验证，在 e2e_test_report 的“上线后人工浏览器验收清单”中列出。
 * “旅程”用例（TC-FE-R27-E*）是对真实产品函数 + 真实 store 的多步串联，其编排顺序由结构断言锁定与 ConfigStudio 一致。
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
const GM = await import(GM_URL);
const NR_URL = toUrl(swap(transpile('components', 'config', 'nodeRemoval.ts'), './graphModel', GM_URL));
const NR = await import(NR_URL);
const PD = await import(toUrl(swap(transpile('components', 'config', 'publishDiff.ts'), './graphModel', GM_URL)));
const VUE_SHIM = toUrl('export const ref=(v)=>({value:v});export const computed=(f)=>({get value(){return f();}});');
const draftJs = swap(swap(transpile('stores', 'configDraft.ts'), 'vue', VUE_SHIM), '../components/config/nodeRemoval', NR_URL);
const { createConfigDraft } = await import(toUrl(draftJs));

// ------------------------------------------------------------------ 夹具
const clone = (o) => JSON.parse(JSON.stringify(o));
const node = (id, kind, extra = {}) => ({ id, kind, x: 0, y: 0, ...extra });
const expert = (name, label, extra = {}) => ({
  name, cn_label: label, keywords: [], exemplars: [], is_data_expert: false, is_delegating: false, is_default: false, status: 'active', max_steps: 4,
  knowledge_scope: { mode: 'all', folder_ids: [] }, ...extra,
});
/** 基线文档：kb-agent（默认）、billing-agent（已上图，关键词“发票”）、faq-agent（已定义但未上图）；condition-1 x=300 y=120。 */
const baseDoc = () => ({
  schema_version: 2,
  route: { tau: 0.65, margin: 0.05, max_expert_steps: 8, default_expert: 'kb-agent' },
  experts: [
    expert('kb-agent', '知识库助手', { is_default: true, max_steps: 4 }),
    expert('billing-agent', '账单助手', { keywords: ['发票'] }),
    expert('faq-agent', '常见问题助手'),
  ],
  tool_grants: [
    { expert_name: 'kb-agent', tool_names: ['search_knowledge'], param_values: [] },
    { expert_name: 'billing-agent', tool_names: ['search_knowledge'], param_values: [] },
    { expert_name: 'faq-agent', tool_names: [], param_values: [] },
  ],
  graph: {
    nodes: [
      node('start', 'start'), node('route-1', 'route', { x: 100, y: 120 }),
      node('condition-1', 'condition', { x: 300, y: 120, predicate: { kind: 'keyword', branches: [{ key: 'a', keywords: ['x'] }] } }),
      node('kb-agent', 'agent', { expert: 'kb-agent', input_mode: 'query_only' }),
      node('billing-agent', 'agent', { expert: 'billing-agent', input_mode: 'query_only' }),
      node('join-9', 'join'), node('end', 'end'),
    ],
    edges: [
      { id: 'e1', source: 'start', target: 'route-1' },
      { id: 'e2', source: 'route-1', target: 'condition-1' },
      { id: 'e3', source: 'condition-1', target: 'kb-agent', branch_key: 'a' },
      { id: 'e4', source: 'condition-1', target: 'end', branch_key: '__else__' },
      { id: 'e5', source: 'route-1', target: 'billing-agent', branch_key: 'billing-agent' },
      { id: 'e6', source: 'route-1', target: 'kb-agent', branch_key: '__else__' },
      { id: 'e7', source: 'kb-agent', target: 'end' },
      { id: 'e8', source: 'billing-agent', target: 'end' },
    ],
  },
});
const state = (doc, patch = {}) => ({ document: doc, promptPatch: patch });
const loaded = (patch) => {
  const doc = baseDoc();
  const s = createConfigDraft();
  s.load(doc, 7, doc.graph);
  if (patch) s.promptPatch.value = patch;
  return s;
};
const key = (o = {}) => ({
  key: 'Delete', ctrlKey: false, metaKey: false, altKey: false, shiftKey: false, readonly: false, target: null,
  selectedNodeIds: ['route-1'], selectedEdgeIds: [], ...o,
});
const ids = (g) => g.nodes.map((n) => n.id);
const eids = (g) => g.edges.map((e) => e.id);
const dangling = (g) => g.edges.filter((e) => !ids(g).includes(e.source) || !ids(g).includes(e.target));
/** 对应 ConfigStudio.requestRemove 的步骤 1~5（IFC-R27-011），confirm 以回调模拟 window.confirm。 */
function drive(store, nodeId, { mode = 'canvas', readonly = false, confirm = () => true } = {}) {
  const doc = store.document.value;
  if (!doc || readonly) return { done: false, why: 'readonly' };
  const g = doc.graph;
  const v = NR.removalVerdict(doc, g, nodeId, mode);
  if (!v.ok) return { done: false, why: v.reason };
  const n = g.nodes.find((x) => x.id === nodeId);
  const label = n.kind === 'agent' ? (doc.experts.find((e) => e.name === (n.expert ?? n.id))?.cn_label ?? n.id) : GM.KIND_LABEL[n.kind];
  const plan = NR.planConfirm(g, nodeId, store.isBaselineNode(nodeId), mode, label);
  if (plan.needConfirm && !confirm(plan)) return { done: false, why: 'cancelled', plan };
  const st = state(doc, store.promptPatch.value);
  const next = mode === 'definition' ? NR.deleteAgentDefinition(st, nodeId) : NR.removeFromCanvas(st, nodeId);
  store.applyRemoval(`${label}「${nodeId}」`, next);
  return { done: true, plan, label };
}
const snap = (s) => JSON.stringify({ d: s.document.value, p: s.promptPatch.value });

// ================================================================== 单元：纯函数（真实执行）
describe('R27 nodeRemoval 纯函数——Delete 键判定', () => {
  it('TC-FE-R27-001 isEditableTarget：INPUT/SELECT/TEXTAREA、contenteditable、.nokey/.el-overlay/.el-drawer/dialog 命中；null 与缺方法的桩不命中（US-002 AC-002-03）', () => {
    for (const nodeName of ['INPUT', 'input', 'SELECT', 'TEXTAREA', 'textarea']) assert.equal(NR.isEditableTarget({ nodeName }), true, nodeName);
    assert.equal(NR.isEditableTarget({ nodeName: 'DIV', hasAttribute: (n) => n === 'contenteditable' }), true);
    let sel = '';
    assert.equal(NR.isEditableTarget({ nodeName: 'DIV', closest: (s) => { sel = s; return {}; } }), true);
    for (const part of ['.nokey', '.el-overlay', '.el-drawer', '[role="dialog"]']) assert.ok(sel.includes(part), part);
    assert.equal(NR.isEditableTarget({ nodeName: 'DIV', closest: () => null }), false);
    assert.equal(NR.isEditableTarget({ nodeName: 'DIV' }), false);
    assert.equal(NR.isEditableTarget({}), false);
    assert.equal(NR.isEditableTarget(null), false);
  });

  it('TC-FE-R27-002 Delete + 仅选中 1 个节点 + 焦点在画布 → request(nodeId)（US-002 AC-002-01）', () => {
    assert.deepEqual(NR.decideDeleteKey(key(), baseDoc().graph), { action: 'request', nodeId: 'route-1' });
    assert.deepEqual(NR.decideDeleteKey(key({ target: { nodeName: 'DIV', closest: () => null } }), baseDoc().graph), { action: 'request', nodeId: 'route-1' });
  });

  it('TC-FE-R27-003 Backspace 及其它键不触发（US-002 AC-002-06）', () => {
    for (const k of ['Backspace', 'Del', 'delete', 'Escape', 'Enter', 'x']) {
      assert.deepEqual(NR.decideDeleteKey(key({ key: k }), baseDoc().graph), { action: 'ignore' }, k);
    }
  });

  it('TC-FE-R27-004 查看档（readonly）按 Delete → ignore，且优先于多选提示（US-007 AC-007-02）', () => {
    assert.deepEqual(NR.decideDeleteKey(key({ readonly: true }), baseDoc().graph), { action: 'ignore' });
    assert.deepEqual(NR.decideDeleteKey(key({ readonly: true, selectedNodeIds: ['a', 'b'] }), baseDoc().graph), { action: 'ignore' });
  });

  it('TC-FE-R27-005 任一修饰键（Ctrl/Meta/Alt/Shift）+ Delete → ignore（IFC-R27-002 规则 3）', () => {
    for (const m of ['ctrlKey', 'metaKey', 'altKey', 'shiftKey']) {
      assert.deepEqual(NR.decideDeleteKey(key({ [m]: true }), baseDoc().graph), { action: 'ignore' }, m);
    }
  });

  it('TC-FE-R27-006 焦点在输入框 / 文本域 / 弹窗内按 Delete → ignore，即便画布上选中了节点（US-002 AC-002-03）', () => {
    for (const target of [{ nodeName: 'INPUT' }, { nodeName: 'TEXTAREA' }, { nodeName: 'SELECT' },
      { nodeName: 'DIV', hasAttribute: () => true }, { nodeName: 'DIV', closest: () => ({}) }]) {
      assert.deepEqual(NR.decideDeleteKey(key({ target, selectedNodeIds: ['condition-1'] }), baseDoc().graph), { action: 'ignore' });
    }
  });

  it('TC-FE-R27-007 没有选中节点 / 只选中边 → ignore（边由 vue-flow 既有行为删，US-002 AC-002-02）', () => {
    assert.deepEqual(NR.decideDeleteKey(key({ selectedNodeIds: [] }), baseDoc().graph), { action: 'ignore' });
    assert.deepEqual(NR.decideDeleteKey(key({ selectedNodeIds: [], selectedEdgeIds: ['e1'] }), baseDoc().graph), { action: 'ignore' });
  });

  it('TC-FE-R27-008 多选（2 个节点；或 1 节点 + 1 边）→ hint「请选中单个节点后再删除」，不 request（US-002 AC-002-04）', () => {
    const want = { action: 'hint', text: '请选中单个节点后再删除' };
    assert.deepEqual(NR.decideDeleteKey(key({ selectedNodeIds: ['route-1', 'join-9'] }), baseDoc().graph), want);
    assert.deepEqual(NR.decideDeleteKey(key({ selectedNodeIds: ['route-1'], selectedEdgeIds: ['e1'] }), baseDoc().graph), want);
    assert.equal(NR.MULTI_SELECT_HINT, '请选中单个节点后再删除');
  });
});

describe('R27 nodeRemoval 纯函数——可行性与确认规则', () => {
  it('TC-FE-R27-009 开始 / 结束节点：Delete 被判为 request，但 removalVerdict 拒绝并给出「开始 / 结束节点不可删除」（US-002 AC-002-05、US-006 AC-006-02）', () => {
    const doc = baseDoc();
    for (const id of ['start', 'end']) {
      assert.deepEqual(NR.decideDeleteKey(key({ selectedNodeIds: [id] }), doc.graph), { action: 'request', nodeId: id });
      for (const mode of ['canvas', 'definition']) {
        assert.deepEqual(NR.removalVerdict(doc, doc.graph, id, mode), { ok: false, reason: '开始 / 结束节点不可删除' });
      }
    }
    assert.equal(NR.STRUCTURAL_REMOVE_HINT, '开始 / 结束节点不可删除');
  });

  it('TC-FE-R27-010 默认专家不可删除（canvas 与 definition 两种模式都拒绝），非默认 agent 可删；拒绝按专家名判定而非节点 id（US-005 AC-005-07、ASM-R27-01）', () => {
    const doc = baseDoc();
    const hint = '默认专家不能删除，请先指定其他默认专家';
    assert.equal(NR.DEFAULT_EXPERT_HINT, hint);
    for (const mode of ['canvas', 'definition']) {
      assert.deepEqual(NR.removalVerdict(doc, doc.graph, 'kb-agent', mode), { ok: false, reason: hint });
      assert.deepEqual(NR.removalVerdict(doc, doc.graph, 'billing-agent', mode), { ok: true });
    }
    // ASM-R27-01：节点 id ≠ 专家名。节点 n-kb 指向默认专家 kb-agent；节点 kb-agent 指向非默认的 billing-agent。
    const g = { nodes: [node('n-kb', 'agent', { expert: 'kb-agent' }), node('kb-agent', 'agent', { expert: 'billing-agent' })], edges: [] };
    assert.equal(NR.removalVerdict(doc, g, 'n-kb', 'canvas').ok, false);
    assert.equal(NR.removalVerdict(doc, g, 'kb-agent', 'canvas').ok, true);
  });

  it('TC-FE-R27-011 route / condition / join / confirm 可删；不检查节点是否填写完整或通过校验；不存在的节点被拒（US-001 AC-001-02、US-006 AC-006-03）', () => {
    const doc = baseDoc();
    const incomplete = { nodes: [node('c', 'condition', { predicate: { kind: 'keyword', branches: [] } }), node('cf', 'confirm', { message: '' }),
      node('j', 'join'), node('r', 'route')], edges: [] };
    for (const id of ['c', 'cf', 'j', 'r']) assert.deepEqual(NR.removalVerdict(doc, incomplete, id, 'canvas'), { ok: true }, id);
    assert.deepEqual(NR.removalVerdict(doc, doc.graph, 'ghost', 'canvas'), { ok: false, reason: '节点不存在' });
    assert.deepEqual([...NR.REMOVABLE_KINDS].sort(), ['agent', 'condition', 'confirm', 'join', 'route']);
    assert.deepEqual([...NR.REMOVABLE_KINDS], [...GM.ADDABLE_KINDS]);
  });

  it('TC-FE-R27-012 canvas 确认规则：有 2 条边 → 需确认且文案含「将同时删除 2 条边」（US-004 AC-004-01）', () => {
    const g = baseDoc().graph; // condition-1 连有 e2/e3/e4 共 3 条；用 join 场景另造 2 条
    const g2 = { nodes: [node('start', 'start'), node('condition-1', 'condition'), node('end', 'end')],
      edges: [{ id: 'a', source: 'start', target: 'condition-1' }, { id: 'b', source: 'condition-1', target: 'end', branch_key: '__else__' }] };
    const p = NR.planConfirm(g2, 'condition-1', false, 'canvas', '条件分支');
    assert.equal(p.needConfirm, true);
    assert.equal(p.edgeCount, 2);
    assert.match(p.text, /将同时删除 2 条边/);
    assert.equal(p.text, '确认删除条件分支节点「condition-1」？将同时删除 2 条边。');
    assert.equal(NR.planConfirm(g, 'condition-1', true, 'canvas', '条件分支').edgeCount, 3);
  });

  it('TC-FE-R27-013 canvas 免确认例外：本次新增 + 无边 → 不确认（AC-004-04）；已生效(基线) + 无边 → 确认且文案不含边数（AC-004-05）；新增 + 1 条边 → 确认含「将同时删除 1 条边」（AC-004-06）', () => {
    const lone = { nodes: [node('route-1', 'route'), node('join-9', 'join')], edges: [] };
    const fresh = NR.planConfirm(lone, 'route-1', false, 'canvas', '路由');
    assert.deepEqual([fresh.needConfirm, fresh.edgeCount], [false, 0]);
    const base = NR.planConfirm(lone, 'join-9', true, 'canvas', '汇聚');
    assert.deepEqual([base.needConfirm, base.edgeCount], [true, 0]);
    assert.doesNotMatch(base.text, /条边/);
    const one = { nodes: [node('start', 'start'), node('confirm-1', 'confirm')], edges: [{ id: 'e1', source: 'start', target: 'confirm-1' }] };
    const p = NR.planConfirm(one, 'confirm-1', false, 'canvas', '人工确认');
    assert.equal(p.needConfirm, true);
    assert.match(p.text, /将同时删除 1 条边/);
  });

  it('TC-FE-R27-014 agent 文案：canvas =「从画布移除…定义、工具授权与提示词草稿保留…重新放回画布」；definition = 恒确认，写出定义与工具授权、边数、版本历史，不含「不可恢复」（US-005 AC-005-04）', () => {
    const g = baseDoc().graph; // billing-agent 连有 e5 / e8 共 2 条边
    const c = NR.planConfirm(g, 'billing-agent', false, 'canvas', '账单助手');
    assert.equal(c.needConfirm, true);
    assert.match(c.text, /从画布移除/);
    assert.match(c.text, /将同时删除 2 条边/);
    assert.match(c.text, /定义、工具授权与提示词草稿保留/);
    assert.match(c.text, /重新放回画布/);
    const d = NR.planConfirm(g, 'billing-agent', false, 'definition', '账单助手');
    assert.equal(d.needConfirm, true);
    assert.match(d.text, /「账单助手」（billing-agent）/);
    assert.match(d.text, /移除其定义与工具授权/);
    assert.match(d.text, /并同时删除 2 条边/);
    assert.match(d.text, /版本历史/);
    assert.match(d.text, /历史会话不受影响/);
    assert.doesNotMatch(d.text, /不可恢复/);
    // 无边的 agent：definition 文案不含边数，仍恒确认
    const lone = { nodes: [node('faq-agent', 'agent', { expert: 'faq-agent' })], edges: [] };
    const d0 = NR.planConfirm(lone, 'faq-agent', false, 'definition', '常见问题助手');
    assert.equal(d0.needConfirm, true);
    assert.doesNotMatch(d0.text, /条边/);
  });
});

describe('R27 nodeRemoval 纯函数——草稿变换', () => {
  it('TC-FE-R27-015 删除条件分支节点：入边 1 + 出边 2 全部移除，无悬空边；相邻节点与其配置、其余边逐字不变；不改入参（US-003 AC-003-01）', () => {
    const doc = baseDoc();
    const before = JSON.stringify(doc);
    const out = NR.removeFromCanvas(state(doc), 'condition-1');
    assert.equal(JSON.stringify(doc), before, '入参不得被修改');
    assert.deepEqual(eids(out.document.graph), ['e1', 'e5', 'e6', 'e7', 'e8']);
    assert.equal(ids(out.document.graph).includes('condition-1'), false);
    assert.deepEqual(dangling(out.document.graph), []);
    for (const id of ['route-1', 'kb-agent', 'end']) {
      assert.deepEqual(out.document.graph.nodes.find((n) => n.id === id), doc.graph.nodes.find((n) => n.id === id), id);
    }
    assert.deepEqual(out.document.graph.edges.find((e) => e.id === 'e5'), doc.graph.edges.find((e) => e.id === 'e5'));
  });

  it('TC-FE-R27-016 仅从画布移除 agent：节点与 2 条边（含分支键）消失；experts / tool_grants / promptPatch 引用不变；路由全局参数与其余出边不变（US-005 AC-005-01、US-003 AC-003-02）', () => {
    const doc = baseDoc();
    const patch = { 'billing-agent': { main: '仅回答账单问题' } };
    const out = NR.removeFromCanvas(state(doc, patch), 'billing-agent');
    assert.deepEqual(eids(out.document.graph), ['e1', 'e2', 'e3', 'e4', 'e6', 'e7']);
    assert.equal(out.document.experts, doc.experts);
    assert.equal(out.document.tool_grants, doc.tool_grants);
    assert.equal(out.promptPatch, patch);
    assert.deepEqual(out.document.route, { tau: 0.65, margin: 0.05, max_expert_steps: 8, default_expert: 'kb-agent' });
    assert.deepEqual(out.document.experts.find((e) => e.name === 'billing-agent').keywords, ['发票']);
    assert.deepEqual(out.document.graph.edges.find((e) => e.id === 'e6'), { id: 'e6', source: 'route-1', target: 'kb-agent', branch_key: '__else__' });
    assert.deepEqual(Object.keys(out.document), Object.keys(doc), '顶层键顺序保持');
  });

  it('TC-FE-R27-017 删除 agent 定义：节点 + 相连边 + experts + tool_grants + promptPatch[expert] 全部清除，其余保持；不改入参（US-005 AC-005-05/06）', () => {
    const doc = baseDoc();
    const patch = { 'billing-agent': { main: 'm', fallback: 'f' }, 'kb-agent': { main: 'kb' } };
    const before = JSON.stringify([doc, patch]);
    const out = NR.deleteAgentDefinition(state(doc, patch), 'billing-agent');
    assert.equal(JSON.stringify([doc, patch]), before, '入参不得被修改');
    assert.deepEqual(out.document.experts.map((e) => e.name), ['kb-agent', 'faq-agent']);
    assert.deepEqual(out.document.tool_grants.map((g) => g.expert_name), ['kb-agent', 'faq-agent']);
    assert.deepEqual(out.promptPatch, { 'kb-agent': { main: 'kb' } });
    assert.deepEqual(eids(out.document.graph), ['e1', 'e2', 'e3', 'e4', 'e6', 'e7']);
    assert.deepEqual(NR.unplacedAgents(out.document, out.document.graph).map((a) => a.name), ['faq-agent'], '删除后不再出现在“尚未上图”列表');
  });

  it('TC-FE-R27-018 ASM-R27-01：节点 id ≠ 专家名时，deleteAgentDefinition 按 expert 清定义、按节点 id 删节点；非 agent 节点按 removeFromCanvas 处理', () => {
    const doc = baseDoc();
    doc.graph.nodes.push(node('n-faq', 'agent', { expert: 'faq-agent' }));
    doc.graph.edges.push({ id: 'e9', source: 'route-1', target: 'n-faq', branch_key: 'faq-agent' });
    const out = NR.deleteAgentDefinition(state(doc, { 'faq-agent': { main: 'x' }, 'n-faq': { main: 'y' } }), 'n-faq');
    assert.equal(ids(out.document.graph).includes('n-faq'), false);
    assert.equal(eids(out.document.graph).includes('e9'), false);
    assert.equal(out.document.experts.some((e) => e.name === 'faq-agent'), false);
    assert.equal(out.document.tool_grants.some((g) => g.expert_name === 'faq-agent'), false);
    assert.deepEqual(out.promptPatch, { 'n-faq': { main: 'y' } }, '只清专家名对应的补丁键');
    const j = NR.deleteAgentDefinition(state(baseDoc()), 'join-9');
    assert.deepEqual(j.document.experts.map((e) => e.name), ['kb-agent', 'billing-agent', 'faq-agent']);
    assert.equal(ids(j.document.graph).includes('join-9'), false);
  });

  it('TC-FE-R27-019 dropPromptPatch：键不存在 → 原对象；存在 → 新对象且其余键值引用不变，不改入参', () => {
    const p = { a: { main: '1' }, b: { main: '2' } };
    assert.equal(NR.dropPromptPatch(p, 'zzz'), p);
    const q = NR.dropPromptPatch(p, 'a');
    assert.deepEqual(q, { b: { main: '2' } });
    assert.equal(q.b, p.b);
    assert.deepEqual(Object.keys(p), ['a', 'b']);
  });

  it('TC-FE-R27-020 unplacedAgents：仅从画布移除后出现；停用的不出现；按 experts 顺序；放回画布后消失且定义保持（US-005 AC-005-01/02）', () => {
    const doc = baseDoc();
    assert.deepEqual(NR.unplacedAgents(doc, doc.graph), [{ name: 'faq-agent', cn_label: '常见问题助手' }]);
    const out = NR.removeFromCanvas(state(doc), 'billing-agent');
    assert.deepEqual(NR.unplacedAgents(out.document, out.document.graph).map((a) => a.name), ['billing-agent', 'faq-agent']);
    const disabled = clone(out.document);
    disabled.experts.find((e) => e.name === 'faq-agent').status = 'disabled';
    assert.deepEqual(NR.unplacedAgents(disabled, disabled.graph).map((a) => a.name), ['billing-agent']);
    const back = { nodes: [...out.document.graph.nodes, GM.addNodeOfKind(out.document.graph, 'agent', 'billing-agent')], edges: out.document.graph.edges };
    assert.deepEqual(NR.unplacedAgents(out.document, back).map((a) => a.name), ['faq-agent']);
    const placed = back.nodes.find((n) => n.id === 'billing-agent');
    assert.deepEqual([placed.expert, placed.input_mode], ['billing-agent', 'query_only']);
    assert.deepEqual(out.document.experts.find((e) => e.name === 'billing-agent').keywords, ['发票']);
    assert.deepEqual(back.edges.filter((e) => e.target === 'billing-agent'), [], '重新上图为未连线节点');
  });

  it('TC-FE-R27-021 新增后删除：JSON.stringify 与基线逐字相同（无残留键、顺序保持）——“未保存”可回到基线（US-008 AC-008-02、US-011 AC-011-02）', () => {
    const doc = baseDoc();
    const added = { ...doc, graph: { nodes: [...doc.graph.nodes, GM.addNodeOfKind(doc.graph, 'route')], edges: doc.graph.edges } };
    assert.notEqual(JSON.stringify(added), JSON.stringify(doc));
    const id = added.graph.nodes[added.graph.nodes.length - 1].id;
    assert.equal(id, 'route-2');
    const back = NR.removeFromCanvas(state(added), id);
    assert.equal(JSON.stringify(back.document), JSON.stringify(doc));
  });

  it('TC-FE-R27-022 撤销状态机：recordRemoval / undoAvailable / restoreFrom（US-009 AC-009-03）', () => {
    const slot = NR.recordRemoval('路由「route-1」', '{"d":{"x":1},"p":{"a":1}}', '{"d":{"x":2},"p":{}}');
    assert.deepEqual(slot, { label: '路由「route-1」', before: '{"d":{"x":1},"p":{"a":1}}', after: '{"d":{"x":2},"p":{}}' });
    assert.equal(NR.undoAvailable(slot, '{"d":{"x":2},"p":{}}'), true);
    assert.equal(NR.undoAvailable(slot, '{"d":{"x":3},"p":{}}'), false);
    assert.equal(NR.undoAvailable(null, ''), false);
    assert.deepEqual(NR.restoreFrom(slot), { document: { x: 1 }, promptPatch: { a: 1 } });
  });
});

describe('R27 publishDiff.formatDiffLine', () => {
  const it0 = (kind, object_id, before, after, field = kind.startsWith('node_') ? 'node' : '') => ({ kind, object_id, field, before, after }); // 服务端 node_* 项的 field 恒为 'node'（versioning.py:219-223）

  it('TC-FE-R27-023 node_added / node_removed / node_changed 带中文节点类型；删除 condition 与新增 join 互不混淆；未知类型回落原代码（US-011 AC-011-01/03）', () => {
    assert.equal(PD.formatDiffLine(it0('node_removed', 'condition-9', 'condition', null)), '删除 条件分支节点：condition-9');
    assert.equal(PD.formatDiffLine(it0('node_added', 'join-10', null, 'join')), '新增 汇聚节点：join-10');
    assert.equal(PD.formatDiffLine(it0('node_removed', 'join-9', 'join', null)), '删除 汇聚节点：join-9');
    assert.equal(PD.formatDiffLine(it0('node_changed', 'confirm-1', 'confirm', 'confirm')), '修改 人工确认节点：confirm-1');
    assert.equal(PD.formatDiffLine(it0('node_removed', 'route-1', 'route', null)), '删除 路由节点：route-1');
    assert.equal(PD.formatDiffLine(it0('node_removed', 'kb-agent', 'agent', null)), '删除 agent节点：kb-agent');
    assert.equal(PD.formatDiffLine(it0('node_removed', 'x-1', 'weird', null)), '删除 weird节点：x-1');
    const a = PD.formatDiffLine(it0('node_removed', 'join-9', 'join', null));
    const b = PD.formatDiffLine(it0('node_added', 'join-10', null, 'join'));
    assert.notEqual(a, b);
  });

  it('TC-FE-R27-024 其余 kind 与 R26 现状逐字相同；无类型代码的 node_* 回落旧格式（NFUNC-003，不回归）', () => {
    assert.equal(PD.formatDiffLine(it0('edge_removed', 'e3', 'a->b', null, 'edge')), '删除边：e3 · edge：a->b → ∅');
    assert.equal(PD.formatDiffLine(it0('edge_added', 'e9', null, 'a->b', 'edge')), '新增边：e9 · edge：∅ → a->b');
    assert.equal(PD.formatDiffLine(it0('agent_removed', 'billing-agent', null, null)), '删除 agent：billing-agent');
    assert.equal(PD.formatDiffLine(it0('agent_field', 'kb-agent', '3', '4', 'max_steps')), '修改 agent 字段：kb-agent · max_steps：3 → 4');
    assert.equal(PD.formatDiffLine(it0('prompt', 'kb-agent', 'a', 'b', 'main')), '修改 提示词：kb-agent · main：a → b');
    assert.equal(PD.formatDiffLine(it0('layout', 'kb-agent', null, null)), '调整布局：kb-agent');
    assert.equal(PD.formatDiffLine(it0('unknown_kind', 'z', null, null)), 'unknown_kind：z');
    assert.equal(PD.formatDiffLine(it0('node_removed', 'n', null, null)), '删除节点：n · node');
  });
});

// ================================================================== 集成：真实 store ↔ nodeRemoval ↔ graphModel
describe('R27 configDraft（真实 store 代码 + vue 最小替身）与 nodeRemoval 的衔接', () => {
  it('TC-FE-R27-030 删除含 3 条边的 condition-1 → 撤销：位置 x=300/y=120、类型、分支定义、3 条边端点与分支键回到删除前；快照与基线逐字相同，“未保存”回到 false（US-009 AC-009-01）', () => {
    const s = loaded();
    const base = snap(s);
    const r = drive(s, 'condition-1');
    assert.equal(r.done, true);
    assert.equal(r.plan.edgeCount, 3);
    assert.equal(s.dirty.value, true);
    assert.equal(s.canUndo.value, true);
    assert.equal(s.undoLabel.value, '条件分支「condition-1」');
    assert.equal(s.undoRemoval(), true);
    const n = s.document.value.graph.nodes.find((x) => x.id === 'condition-1');
    assert.deepEqual([n.x, n.y, n.kind], [300, 120, 'condition']);
    assert.deepEqual(n.predicate, { kind: 'keyword', branches: [{ key: 'a', keywords: ['x'] }] });
    assert.deepEqual(s.document.value.graph.edges.filter((e) => e.source === 'condition-1' || e.target === 'condition-1').map((e) => [e.id, e.source, e.target, e.branch_key]),
      [['e2', 'route-1', 'condition-1', undefined], ['e3', 'condition-1', 'kb-agent', 'a'], ['e4', 'condition-1', 'end', '__else__']]);
    assert.equal(snap(s), base);
    assert.equal(s.dirty.value, false);
    assert.equal(s.canUndo.value, false);
    assert.equal(s.undoLabel.value, '');
  });

  it('TC-FE-R27-031 “未保存”判定：新增 route-1 后删除 → dirty 回 false（AC-008-02）；另有最大步数改动时 dirty 仍 true 且该改动保留（AC-008-03）', () => {
    const s = loaded();
    s.setGraph({ nodes: [...s.document.value.graph.nodes, GM.addNodeOfKind(s.document.value.graph, 'route')], edges: s.document.value.graph.edges });
    assert.equal(s.dirty.value, true);
    assert.equal(s.isBaselineNode('route-2'), false);
    const r = drive(s, 'route-2', { confirm: () => assert.fail('新增且无边的节点不应弹确认') });
    assert.equal(r.done, true);
    assert.equal(s.dirty.value, false);

    const t = loaded();
    t.setGraph({ nodes: [...t.document.value.graph.nodes, GM.addNodeOfKind(t.document.value.graph, 'route')], edges: t.document.value.graph.edges });
    const d = clone(t.document.value);
    d.experts.find((e) => e.name === 'kb-agent').max_steps = 3;
    t.document.value = d;
    assert.equal(drive(t, 'route-2').done, true);
    assert.equal(t.dirty.value, true);
    assert.equal(t.document.value.experts.find((e) => e.name === 'kb-agent').max_steps, 3);
  });

  it('TC-FE-R27-032 删除 agent 定义 → 撤销：节点、相连边、专家条目、工具授权、提示词草稿全部恢复且进入保存载荷（US-009 AC-009-02）', () => {
    const s = loaded({ 'billing-agent': { main: '仅回答账单问题' } });
    const r = drive(s, 'billing-agent', { mode: 'definition' });
    assert.equal(r.done, true);
    assert.equal(r.plan.needConfirm, true);
    const gone = s.toPublishPayload();
    assert.equal(gone.document.experts.some((e) => e.name === 'billing-agent'), false);
    assert.deepEqual(gone.prompts, {});
    assert.equal(s.undoRemoval(), true);
    const p = s.toPublishPayload();
    assert.equal(p.document.experts.some((e) => e.name === 'billing-agent'), true);
    assert.equal(p.document.tool_grants.some((g) => g.expert_name === 'billing-agent'), true);
    assert.equal(p.document.graph.nodes.some((n) => n.id === 'billing-agent'), true);
    assert.deepEqual(p.document.graph.edges.filter((e) => e.target === 'billing-agent' || e.source === 'billing-agent').map((e) => e.id), ['e5', 'e8']);
    assert.deepEqual(p.prompts, { 'billing-agent': { main: '仅回答账单问题' } });
  });

  it('TC-FE-R27-033 Builder 加入的 faq-agent（含主/兜底提示词草稿）删除定义后：载荷与文档不含其任何字段，无其它改动则 dirty=false（US-005 AC-005-06）', () => {
    const doc = baseDoc();
    doc.experts = doc.experts.filter((e) => e.name !== 'faq-agent');
    doc.tool_grants = doc.tool_grants.filter((g) => g.expert_name !== 'faq-agent');
    const s = createConfigDraft();
    s.load(doc, 7, doc.graph);
    // 复刻 ConfigStudio.onBuilderAdd 对 store 的写入序列
    const d = s.document.value;
    s.document.value = { ...d, experts: [...d.experts, expert('faq-agent', '常见问题助手')],
      tool_grants: [...d.tool_grants, { expert_name: 'faq-agent', tool_names: ['search_knowledge'], param_values: [] }],
      graph: { nodes: [...d.graph.nodes, GM.addNodeOfKind(d.graph, 'agent', 'faq-agent')], edges: d.graph.edges } };
    s.setPrompt('faq-agent', 'main', '你是 FAQ 助手');
    s.setPrompt('faq-agent', 'fallback', '兜底');
    assert.equal(s.dirty.value, true);
    assert.equal(drive(s, 'faq-agent', { mode: 'definition' }).done, true);
    const p = s.toPublishPayload();
    assert.equal(JSON.stringify(p).includes('faq-agent'), false);
    assert.equal(JSON.stringify(p).includes('FAQ'), false);
    assert.deepEqual(p.prompts, {});
    assert.equal(s.dirty.value, false);
  });

  it('TC-FE-R27-034 撤销失效：其它编辑（拖动 / 改提示词 / 直接赋值）、保存（markSaved）、重新载入（load）、放弃改动（discard）后 canUndo=false 且 undoRemoval 不改动草稿（US-009 AC-009-03）', () => {
    const edits = {
      拖动另一节点: (s) => s.setGraph(GM.applyPositions(s.document.value.graph, new Map([['kb-agent', { x: 50, y: 60 }]]))),
      改提示词: (s) => s.setPrompt('kb-agent', 'main', '新'),
      直接赋值文档: (s) => { s.document.value = { ...s.document.value, route: { ...s.document.value.route, tau: 0.5 } }; },
    };
    for (const [name, edit] of Object.entries(edits)) {
      const s = loaded();
      drive(s, 'join-9');
      assert.equal(s.canUndo.value, true);
      edit(s);
      assert.equal(s.canUndo.value, false, name);
      const after = snap(s);
      assert.equal(s.undoRemoval(), false, name);
      assert.equal(snap(s), after, name);
    }
    const a = loaded(); drive(a, 'join-9'); a.markSaved(8);
    assert.equal(a.canUndo.value, false, 'markSaved');
    const b = loaded(); drive(b, 'join-9'); b.discard();
    assert.equal(b.canUndo.value, false, 'discard');
    const c = loaded(); drive(c, 'join-9'); const d0 = baseDoc(); c.load(d0, 9, d0.graph);
    assert.equal(c.canUndo.value, false, 'load');
    assert.equal(c.undoRemoval(), false);
  });

  it('TC-FE-R27-035 仅最近一次可撤销：连续删除 route-1、join-9 后撤销只恢复 join-9，route-1 保持已删除，且不再有第二次撤销（US-009 AC-009-04）', () => {
    const s = loaded();
    assert.equal(drive(s, 'route-1').done, true);
    assert.equal(drive(s, 'join-9').done, true);
    assert.equal(s.undoLabel.value, '汇聚「join-9」');
    assert.equal(s.undoRemoval(), true);
    assert.equal(ids(s.document.value.graph).includes('join-9'), true);
    assert.equal(ids(s.document.value.graph).includes('route-1'), false);
    assert.equal(s.canUndo.value, false);
    assert.equal(s.undoRemoval(), false);
    assert.equal(ids(s.document.value.graph).includes('route-1'), false);
  });

  it('TC-FE-R27-036 仅从画布移除 billing-agent 后：提示词草稿与定义保留于保存载荷；列表可选；重新上图后值不变（US-005 AC-005-01/02/03 载荷侧）', () => {
    const s = loaded({ 'billing-agent': { main: '仅回答账单问题' } });
    assert.equal(drive(s, 'billing-agent').done, true);
    const p = s.toPublishPayload();
    assert.deepEqual(p.prompts, { 'billing-agent': { main: '仅回答账单问题' } });
    assert.equal(p.document.experts.some((e) => e.name === 'billing-agent'), true);
    assert.equal(p.document.tool_grants.find((g) => g.expert_name === 'billing-agent').tool_names[0], 'search_knowledge');
    assert.equal(NR.unplacedAgents(s.document.value, s.document.value.graph).some((a) => a.name === 'billing-agent'), true);
    s.setGraph({ nodes: [...s.document.value.graph.nodes, GM.addNodeOfKind(s.document.value.graph, 'agent', 'billing-agent')], edges: s.document.value.graph.edges });
    assert.deepEqual(s.toPublishPayload().prompts, { 'billing-agent': { main: '仅回答账单问题' } });
    assert.deepEqual(s.document.value.experts.find((e) => e.name === 'billing-agent').keywords, ['发票']);
  });

  it('TC-FE-R27-037 取消确认：草稿快照逐字不变、不登记撤销、dirty 不变（US-004 AC-004-02、US-010 AC-010-02 草稿保留侧）', () => {
    const s = loaded();
    const base = snap(s);
    const r = drive(s, 'condition-1', { confirm: () => false });
    assert.deepEqual([r.done, r.why], [false, 'cancelled']);
    assert.match(r.plan.text, /将同时删除 3 条边/);
    assert.equal(snap(s), base);
    assert.equal(s.dirty.value, false);
    assert.equal(s.canUndo.value, false);
  });

  it('TC-FE-R27-038 删除后“放弃改动”整体回滚：已生效节点重新出现，提示词补丁清空，撤销位清除（US-008 AC-008-04）', () => {
    const s = loaded();
    const base = snap(s);
    s.setPrompt('kb-agent', 'main', '改了');
    drive(s, 'billing-agent', { mode: 'definition' });
    assert.equal(s.dirty.value, true);
    s.discard();
    assert.equal(snap(s), base);
    assert.equal(s.dirty.value, false);
    assert.equal(ids(s.document.value.graph).includes('billing-agent'), true);
    assert.deepEqual(s.promptPatch.value, {});
  });

  it('TC-FE-R27-039 isBaselineNode：基线内节点 true、本次新增 false、载入前 false；markSaved 后新增节点成为基线（US-004 AC-004-04/05）', () => {
    const fresh = createConfigDraft();
    assert.equal(fresh.isBaselineNode('start'), false);
    const s = loaded();
    assert.equal(s.isBaselineNode('join-9'), true);
    s.setGraph({ nodes: [...s.document.value.graph.nodes, GM.addNodeOfKind(s.document.value.graph, 'join')], edges: s.document.value.graph.edges });
    assert.equal(s.isBaselineNode('join-1'), false);
    s.markSaved(8);
    assert.equal(s.isBaselineNode('join-1'), true);
    // 已生效、无连线的 join-9 → 需确认（canvas），而本次新增的无边节点免确认
    assert.equal(NR.planConfirm(s.document.value.graph, 'join-1', s.isBaselineNode('join-1'), 'canvas', '汇聚').needConfirm, true);
  });

  it('TC-FE-R27-040 ASM-R27-01 贯通：节点 id ≠ 专家名的 agent，经 drive → definition 删除 → 撤销，专家定义与补丁按专家名正确清除 / 恢复', () => {
    const doc = baseDoc();
    doc.graph.nodes.push(node('n-faq', 'agent', { expert: 'faq-agent' }));
    const s = createConfigDraft();
    s.load(doc, 7, doc.graph);
    s.setPrompt('faq-agent', 'main', '草稿');
    const base = snap(s);
    const r = drive(s, 'n-faq', { mode: 'definition' });
    assert.equal(r.done, true);
    assert.equal(r.label, '常见问题助手');
    assert.equal(s.document.value.experts.some((e) => e.name === 'faq-agent'), false);
    assert.deepEqual(s.promptPatch.value, {});
    assert.equal(s.undoRemoval(), true);
    assert.equal(snap(s), base);
  });

  it('TC-FE-R27-041 被拒绝的删除（开始 / 结束 / 默认专家 / 查看档 / 不存在）不改草稿、不登记撤销、dirty 保持 false（US-006、US-007 AC-007-02、US-005 AC-005-07）', () => {
    const s = loaded();
    const base = snap(s);
    for (const [id, opt] of [['start', {}], ['end', {}], ['kb-agent', {}], ['kb-agent', { mode: 'definition' }], ['ghost', {}], ['route-1', { readonly: true }]]) {
      assert.equal(drive(s, id, opt).done, false, `${id}/${JSON.stringify(opt)}`);
    }
    assert.equal(snap(s), base);
    assert.equal(s.dirty.value, false);
    assert.equal(s.canUndo.value, false);
  });
});

// ================================================================== 集成：源码结构事实
describe('R27 源码结构事实（读源码）', () => {
  const nr = stripComments(read('components', 'config', 'nodeRemoval.ts'));
  const draft = stripComments(read('stores', 'configDraft.ts'));
  const canvas = stripComments(read('components', 'config', 'FlowCanvas.vue'));
  const panel = stripComments(read('components', 'config', 'AgentDetailPanel.vue'));
  const studio = stripComments(read('views', 'ConfigStudio.vue'));
  const dlg = stripComments(read('components', 'config', 'PublishDialog.vue'));
  const pd = stripComments(read('components', 'config', 'publishDiff.ts'));
  const fnBody = (s, name) => {
    const i = s.search(new RegExp(`function ${name}\\b`));
    assert.ok(i >= 0, `找不到 ${name}`);
    let depth = 0; let started = false;
    for (let k = s.indexOf('{', s.indexOf(')', i)); k < s.length; k += 1) {
      if (s[k] === '{') { depth += 1; started = true; } else if (s[k] === '}') depth -= 1;
      if (started && depth === 0) return s.slice(i, k + 1);
    }
    return assert.fail(`${name} 括号不平衡`);
  };

  it('TC-FE-R27-050 nodeRemoval.ts / publishDiff.ts 运行期只依赖 ./graphModel，其余均为 import type（可离线加载，无 DOM / Vue 依赖）', () => {
    for (const [n, s] of [['nodeRemoval', nr], ['publishDiff', pd]]) {
      const runtime = (s.match(/^import\s+(?!type\b)[^;]*from\s+'[^']+';/gm) ?? []).map((l) => l.match(/from\s+'([^']+)'/)[1]);
      assert.deepEqual(runtime, ['./graphModel'], `${n} 的运行期导入`);
      assert.doesNotMatch(s, /(?<![.\w])document\.(addEventListener|querySelector|getElementById|body)|(?<![.\w])window\.|localStorage|fetch\(|axios|from 'vue'/, n);
    }
  });

  it('TC-FE-R27-051 configDraft：暴露 applyRemoval / undoRemoval / canUndo / undoLabel / isBaselineNode；load / discard / markSaved 均清撤销位；无本地存储与网络（REQ-NFUNC-002 结构侧证据、US-010 AC-010-01）', () => {
    for (const m of ['applyRemoval', 'undoRemoval', 'canUndo', 'undoLabel', 'isBaselineNode']) assert.match(draft, new RegExp(`\\b${m}\\b`), m);
    for (const f of ['load', 'discard', 'markSaved']) assert.match(fnBody(draft, f), /undoSlot\.value = null/, `${f} 须清撤销位`);
    assert.doesNotMatch(draft, /localStorage|sessionStorage|indexedDB|fetch\(|ApiClient|client\./);
    assert.match(draft, /const canUndo = computed\(\(\) => undoAvailable\(undoSlot\.value, snapshotOf\(\)\)\)/);
  });

  it('TC-FE-R27-052 FlowCanvas：保留 :delete-key-code / deletable:false / 拖拽连线只读开关；挂载注册、卸载移除 keydown；id=config-canvas；Delete 判定读自维护选中集合（US-002、US-007 AC-007-02、风险 R-1 结构侧）', () => {
    assert.match(canvas, /:delete-key-code="readonly \? null : 'Delete'"/);
    assert.match(canvas, /deletable: false/);
    assert.match(canvas, /:nodes-draggable="!readonly"/);
    assert.match(canvas, /:nodes-connectable="!readonly"/);
    assert.match(canvas, /<VueFlow\s+id="config-canvas"/);
    assert.match(canvas, /onMounted\(\(\) => document\.addEventListener\('keydown', onKeyDown\)\)/);
    assert.match(canvas, /onBeforeUnmount\(\(\) => document\.removeEventListener\('keydown', onKeyDown\)\)/);
    assert.match(canvas, /readonly: props\.readonly/);
    assert.match(canvas, /selectedNodeIds: \[\.\.\.selNodes\], selectedEdgeIds: \[\.\.\.selEdges\]/);
    assert.match(canvas, /@nodes-change="onNodesChange"/);
    assert.match(canvas, /@edges-change="onEdgesChange"/);
    assert.match(canvas, /c\.type === 'select'/);
    assert.doesNotMatch(canvas, /getSelectedNodes|getSelectedEdges|useVueFlow/, '不依赖 vue-flow 内部 selected 标志');
    assert.match(canvas, /emit\('request-remove', d\.nodeId\)/);
    assert.match(canvas, /emit\('hint', d\.text\)/);
  });

  it('TC-FE-R27-053 FlowCanvas 图更新后清理悬停卡片与失效选中：目标节点 / 边不在新图中才清，仍在则保留（US-008 AC-008-01 结构侧）', () => {
    const w = canvas.slice(canvas.indexOf('watch('), canvas.indexOf('function place'));
    assert.match(w, /\(\) => props\.graph/);
    assert.match(w, /selNodes\.delete\(id\)/);
    assert.match(w, /selEdges\.delete\(id\)/);
    assert.match(w, /cardTarget\.kind === 'node' \? nodeIds : edgeIds\)\.has\(cardTarget\.id\)/);
    assert.match(w, /card\.value = null/);
    assert.match(canvas, /cardTarget = \{ kind: 'node', id: n\.id \}/);
    assert.match(canvas, /cardTarget = \{ kind: 'edge', id: e\.id \}/);
    assert.match(canvas, /@mouseleave="hide"/);
  });

  it('TC-FE-R27-054 AgentDetailPanel：不再 window.confirm；五类可删节点各有「删除节点」且都在 v-if="!readonly" 容器内；agent 另有「删除 agent」；默认专家两个按钮均禁用并给出提示（US-001 AC-001-02、US-005 AC-005-07、US-007 AC-007-01）', () => {
    assert.doesNotMatch(panel, /window\.confirm|confirm\(/);
    const emits = [...panel.matchAll(/emit\('(request-remove|remove-agent)', node\.id\)/g)];
    assert.equal(emits.filter((m) => m[1] === 'request-remove').length, 5, '五类节点各一个删除节点入口');
    assert.equal(emits.filter((m) => m[1] === 'remove-agent').length, 1);
    for (const m of emits) {
      const before = panel.slice(0, m.index);
      const div = before.slice(before.lastIndexOf('<div'));
      assert.match(div.slice(0, div.indexOf('>')), /v-if="!readonly"/, `${m[0]} 须在 v-if="!readonly" 的容器内`);
    }
    for (const kind of ['route', 'condition', 'confirm', 'join']) assert.match(panel, new RegExp(`node\\?\\.kind === '${kind}'`), kind);
    assert.equal((panel.match(/删除节点<\/el-button>/g) ?? []).length, 5);
    assert.equal((panel.match(/删除 agent<\/el-button>/g) ?? []).length, 1);
    assert.match(panel, /type="danger" :disabled="expert\(\)\?\.is_default" @click="emit\('remove-agent', node\.id\)"/);
    assert.match(panel, /plain :disabled="expert\(\)\?\.is_default" @click="emit\('request-remove', node\.id\)"/);
    assert.match(panel, /<span v-if="expert\(\)\?\.is_default" class="hint">\{\{ DEFAULT_EXPERT_HINT \}\}<\/span>/);
    assert.match(panel, /仅从画布移除，agent 的定义与提示词保留/);
  });

  it('TC-FE-R27-055 AgentDetailPanel：开始 / 结束分支只有说明无按钮；未选中节点显示「点击画布上的节点查看或编辑其配置」且无删除按钮；本轮新增控件只有 el-button（US-006 AC-006-01、US-001 AC-001-04、TC-FE-R26-022 同口径）', () => {
    const se = panel.slice(panel.indexOf("node?.kind === 'start' || node?.kind === 'end'"));
    const seBlock = se.slice(0, se.indexOf('</template>'));
    assert.match(seBlock, /开始 \/ 结束节点不可删除/);
    assert.doesNotMatch(seBlock, /el-button|emit\(/);
    const tail = panel.slice(panel.indexOf('<p v-else class="hint">'));
    assert.match(tail, /^<p v-else class="hint">点击画布上的节点查看或编辑其配置。<\/p>/);
    assert.doesNotMatch(tail.slice(0, tail.indexOf('</div>')), /el-button/);
    const inputs = panel.match(/<el-(input|input-number|checkbox|select|switch)\b[^>]*>/g) ?? [];
    assert.deepEqual(inputs.filter((t) => !/:disabled="readonly"|readonly/.test(t)).map((t) => t.slice(0, 80)), []);
    assert.match(panel, /当前为“查看”档/);
  });

  it('TC-FE-R27-056 ConfigStudio 接线：画布 @request-remove / @hint，面板 @request-remove / @remove-agent；撤销条仅编辑档且 canUndo 时渲染；放回画布选择框（US-009 AC-009-05、US-005 AC-005-02）', () => {
    assert.match(studio, /<FlowCanvas[\s\S]*?@request-remove="\(id: string\) => requestRemove\(id\)"[\s\S]*?@hint="\(t: string\) => ElMessage\.info\(t\)"/);
    assert.match(studio, /<AgentDetailPanel[\s\S]*?@remove-agent="onRemoveAgent"[\s\S]*?@request-remove="\(id: string\) => requestRemove\(id\)"/);
    assert.match(studio, /<div v-if="!readonly && store\.canUndo\.value" class="undo-bar">/);
    assert.match(studio, /@click="onUndo">撤销<\/el-button>/);
    assert.match(studio, /已删除 \{\{ store\.undoLabel\.value \}\}/);
    assert.match(studio, /title="选择要放回画布的 agent"/);
    assert.match(studio, /unplacedAgents\(doc, graph\.value\)/);
    assert.match(studio, /ElMessage\.success\('已撤销删除'\)/);
    assert.doesNotMatch(studio, /将同时删除 \$\{n\} 条边，继续？/, '旧的二次确认已移除');
  });

  it('TC-FE-R27-057 ConfigStudio.requestRemove 编排顺序：只读短路 → 可行性 → 确认规则 → window.confirm → 变换 → applyRemoval → 清选中；删除全程不调用服务端（US-007、US-010 AC-010-01、REQ-NFUNC-002）', () => {
    const b = fnBody(studio, 'requestRemove');
    const order = ['readonly.value', 'removalVerdict(', 'planConfirm(', 'window.confirm(plan.text)', "mode === 'definition' ? deleteAgentDefinition(state, nodeId) : removeFromCanvas(state, nodeId)",
      'store.applyRemoval(', 'selectedId.value = null'].map((t) => b.indexOf(t));
    assert.ok(order.every((i) => i >= 0), `缺少步骤：${order}`);
    assert.deepEqual([...order].sort((x, y) => x - y), order, '步骤顺序');
    assert.match(b, /store\.isBaselineNode\(nodeId\)/);
    assert.match(b, /if \(plan\.needConfirm && !window\.confirm\(plan\.text\)\) return;/);
    assert.match(b, /tab\.value = 'detail'/);
    assert.doesNotMatch(b, /props\.client|publish|fetch|await/, '删除只写内存');
    assert.match(fnBody(studio, 'onRemoveAgent'), /requestRemove\(nodeId, 'definition'\)/);
    assert.match(fnBody(studio, 'onUndo'), /store\.undoRemoval\(\)[\s\S]*selectedId\.value = null/);
    assert.match(fnBody(studio, 'discard'), /store\.discard\(\)/);
    assert.doesNotMatch(studio, /localStorage|sessionStorage|v-html|axios/);
  });

  it('TC-FE-R27-058 保存流程未被改动：保存按钮随 dirty 启停；放弃改动需 dirty；startSave 先 publishPreview 再弹窗、confirmSave 才 publish；成功文案「已生效（版本 N）」后重新载入（US-008 AC-008-02、US-010 AC-010-02/04、US-011 AC-011-02）', () => {
    assert.match(studio, /<el-tag v-if="store\.dirty\.value" type="warning" size="small">未保存<\/el-tag>/);
    assert.match(studio, /:disabled="!store\.dirty\.value" @click="discard">放弃改动/);
    assert.match(studio, /:disabled="!store\.dirty\.value" @click="startSave">保存并生效/);
    const s = fnBody(studio, 'startSave');
    assert.ok(s.indexOf('publishPreview(') >= 0 && s.indexOf('publishPreview(') < s.indexOf('dialog.value = true'));
    assert.doesNotMatch(s, /\.publish\(/);
    const c = fnBody(studio, 'confirmSave');
    assert.match(c, /props\.client\.publish\(/);
    assert.match(c, /ElMessage\.success\(`已生效（版本 \$\{r\.version\}）`\)[\s\S]*await load\(\)/);
    assert.match(studio, /@cancel="dialog = false"/);
  });

  it('TC-FE-R27-059 PublishDialog：经 formatDiffLine 渲染；无本地 KIND_LABEL；校验错误逐条展示且无「忽略」选项、确认按钮在有错误 / 无变更时禁用；取消不提交（US-003 AC-003-03、US-011、smoke 1020 同口径）', () => {
    assert.match(dlg, /import \{ formatDiffLine \} from '\.\/publishDiff'/);
    assert.match(dlg, /\{\{ formatDiffLine\(i\) \}\}/);
    assert.doesNotMatch(dlg, /KIND_LABEL|function line/);
    assert.doesNotMatch(dlg, /忽略/);
    assert.match(dlg, /v-for="e in errors"[\s\S]*\{\{ e\.path \}\}[\s\S]*\{\{ e\.message \}\}/);
    assert.match(dlg, /:disabled="errors\.length > 0 \|\| items\.length === 0"/);
    assert.match(dlg, /@click="emit\('cancel'\)">取消/);
    assert.doesNotMatch(dlg, /v-html|innerHTML/);
  });

  it('TC-FE-R27-060 全部 R27 改动文件：无 v-html / innerHTML / localStorage / axios / CDN / window.confirm 之外的新弹窗依赖；package.json 无新增测试或浏览器依赖（NFUNC-003、C-R27）', () => {
    for (const [n, s] of [['nodeRemoval', nr], ['publishDiff', pd], ['configDraft', draft], ['FlowCanvas', canvas], ['AgentDetailPanel', panel], ['ConfigStudio', studio], ['PublishDialog', dlg]]) {
      assert.doesNotMatch(s, /v-html|innerHTML|localStorage|axios/, n);
      assert.doesNotMatch(s, /https?:\/\/(cdn|unpkg|esm\.sh)/, n);
    }
    const pkg = JSON.parse(readFileSync(join(here, '..', 'package.json'), 'utf8'));
    const deps = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies });
    assert.deepEqual(deps.filter((d) => /playwright|puppeteer|cypress|axios|jsdom|vitest|jest|happy-dom/.test(d)), []);
  });
});

// ================================================================== E2E 级（替代口径）：真实产品函数 + 真实 store 的多步旅程
describe('R27 用户旅程（模型层多步串联；浏览器内交互见人工验收清单）', () => {
  it('TC-FE-R27-E01 旅程 A：选中 condition-1 → Delete → 确认(取消一次、确认一次) → 草稿/载荷/差异清单 → 撤销（US-002/003/004/009/011）', () => {
    const s = loaded();
    const base = snap(s);
    const d = NR.decideDeleteKey(key({ selectedNodeIds: ['condition-1'], target: { nodeName: 'DIV', closest: () => null } }), s.document.value.graph);
    assert.deepEqual(d, { action: 'request', nodeId: 'condition-1' });
    const asked = [];
    assert.equal(drive(s, 'condition-1', { confirm: (p) => { asked.push(p.text); return false; } }).done, false);
    assert.equal(snap(s), base);
    assert.equal(drive(s, 'condition-1', { confirm: (p) => { asked.push(p.text); return true; } }).done, true);
    assert.equal(asked.length, 2);
    assert.match(asked[1], /将同时删除 3 条边/);
    const g = s.toPublishPayload().document.graph;
    assert.equal(ids(g).includes('condition-1'), false);
    assert.deepEqual(dangling(g), []);
    assert.deepEqual(['route-1', 'kb-agent', 'end'].map((i) => ids(g).includes(i)), [true, true, true]);
    assert.equal(s.dirty.value, true);
    // 服务端对该草稿会给出的差异项经 formatDiffLine 渲染（输入形态取自 versioning.py 的 node_removed / edge_removed 项）
    assert.equal(PD.formatDiffLine({ kind: 'node_removed', object_id: 'condition-1', field: 'node', before: 'condition', after: null }), '删除 条件分支节点：condition-1');
    assert.equal(s.undoRemoval(), true);
    assert.equal(snap(s), base);
    assert.equal(s.dirty.value, false);
  });

  it('TC-FE-R27-E02 旅程 B：仅从画布移除 billing-agent → 重新上图 → 再删除定义 → 撤销，提示词草稿全程不丢（US-005 AC-005-01~05）', () => {
    const s = loaded({ 'billing-agent': { main: '仅回答账单问题' } });
    const base = snap(s);
    const r1 = drive(s, 'billing-agent');
    assert.match(r1.plan.text, /从画布移除/);
    assert.equal(NR.unplacedAgents(s.document.value, s.document.value.graph).some((a) => a.name === 'billing-agent'), true);
    s.setGraph({ nodes: [...s.document.value.graph.nodes, GM.addNodeOfKind(s.document.value.graph, 'agent', 'billing-agent')], edges: s.document.value.graph.edges });
    assert.deepEqual(s.promptPatch.value, { 'billing-agent': { main: '仅回答账单问题' } });
    const r2 = drive(s, 'billing-agent', { mode: 'definition' });
    assert.match(r2.plan.text, /移除其定义与工具授权/);
    assert.equal(r2.plan.edgeCount, 0, '重新上图的节点无连线');
    assert.deepEqual(s.promptPatch.value, {});
    assert.equal(NR.unplacedAgents(s.document.value, s.document.value.graph).some((a) => a.name === 'billing-agent'), false);
    assert.equal(s.undoRemoval(), true);
    assert.deepEqual(s.promptPatch.value, { 'billing-agent': { main: '仅回答账单问题' } });
    assert.equal(s.document.value.experts.some((e) => e.name === 'billing-agent'), true);
    assert.notEqual(snap(s), base, '重新上图是一次真实改动');
  });

  it('TC-FE-R27-E03 旅程 C：未完成节点逐个直接删除（condition / join / confirm / route），不被校验拦截，其它改动保留（US-001 AC-001-01/02）', () => {
    const s = loaded();
    const g0 = s.document.value.graph;
    const add = (k) => { const g = s.document.value.graph; s.setGraph({ nodes: [...g.nodes, GM.addNodeOfKind(g, k)], edges: g.edges }); };
    add('condition'); add('join'); add('confirm');
    const d = clone(s.document.value);
    d.experts.find((e) => e.name === 'kb-agent').max_steps = 3;
    s.document.value = d;
    const asked = [];
    for (const id of ['condition-2', 'confirm-1']) {
      assert.equal(drive(s, id, { confirm: () => { asked.push(id); return true; } }).done, true, id);
    }
    assert.deepEqual(asked, [], '本次新增且无边：免确认');
    assert.deepEqual(ids(s.document.value.graph).filter((i) => !ids(g0).includes(i)), ['join-1']);
    assert.equal(s.document.value.experts.find((e) => e.name === 'kb-agent').max_steps, 3);
    assert.equal(s.dirty.value, true);
    assert.equal(drive(s, 'join-1').done, true);
    assert.equal(s.dirty.value, true, '最大步数改动仍在');
  });

  it('TC-FE-R27-E04 旅程 D：结构 / 默认专家 / 多选 / 查看档的全部拒绝路径——草稿与“未保存”始终不变（US-002 AC-002-04/05、US-006、US-007、US-005 AC-005-07）', () => {
    const s = loaded();
    const base = snap(s);
    const doc = s.document.value;
    assert.deepEqual(NR.decideDeleteKey(key({ selectedNodeIds: ['route-1', 'join-9'] }), doc.graph).text, '请选中单个节点后再删除');
    assert.equal(NR.decideDeleteKey(key({ readonly: true, selectedNodeIds: ['route-1'] }), doc.graph).action, 'ignore');
    for (const id of ['start', 'end', 'kb-agent']) {
      const dec = NR.decideDeleteKey(key({ selectedNodeIds: [id] }), doc.graph);
      assert.equal(dec.action, 'request');
      const res = drive(s, dec.nodeId);
      assert.equal(res.done, false);
      assert.match(res.why, /开始 \/ 结束节点不可删除|默认专家不能删除，请先指定其他默认专家/);
    }
    assert.equal(snap(s), base);
    assert.equal(s.dirty.value, false);
    assert.equal(drive(s, 'route-1', { readonly: true }).done, false);
    assert.equal(s.canUndo.value, false);
    // 删除路由节点是允许的（保存时才由服务端判定默认专家不可达）
    assert.equal(drive(s, 'route-1').done, true);
    assert.equal(dangling(s.document.value.graph).length, 0);
    assert.equal(s.document.value.route.default_expert, 'kb-agent', '全局路由参数不因删除而变');
  });

  it('TC-FE-R27-E05 旅程 E：删除后保存成功（markSaved）→ 撤销失效、基线更新；再重新载入 → 无撤销（US-010 AC-010-04、US-009 AC-009-03）', () => {
    const s = loaded({ 'billing-agent': { main: 'x' } });
    drive(s, 'condition-1');
    assert.equal(s.dirty.value, true);
    const payload = s.toPublishPayload();
    assert.equal(ids(payload.document.graph).includes('condition-1'), false);
    s.markSaved(8);
    assert.equal(s.baseVersion.value, 8);
    assert.equal(s.dirty.value, false);
    assert.equal(s.canUndo.value, false);
    assert.equal(s.isBaselineNode('condition-1'), false, '已保存删除后，该节点不再属于基线');
    assert.deepEqual(s.promptPatch.value, {});
  });
});
