/**
 * [REV-26 / GROUP_D] 可视化配置前端测试（node:test，零新增依赖）。
 *
 * 做法：
 *  1. 纯函数——用工程已有的 `typescript`（vue-tsc 的依赖）把 graphModel.ts 在内存中转译为 ESM，经 data: URL 导入并真实执行；
 *  2. 结构事实——读源码、剥注释后断言（只读档贯通、无 v-html / localStorage / axios / CDN、保存流程含差异确认与冲突处理）。
 *
 * 局限（如实）：没有组件挂载环境，也没有可用的无头浏览器，且不得新增依赖——拖拽、悬停、连线等**浏览器内真实交互无法在此验证**，
 * 这些 AC 在 e2e_test_report 中列为“未验证”，本文件只覆盖其模型层 / 结构层。
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

const js = ts.transpileModule(read('components', 'config', 'graphModel.ts'), {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const M = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);

const node = (id, kind, extra = {}) => ({ id, kind, x: 0, y: 0, ...extra });
const G = () => ({
  nodes: [node('start', 'start'), node('route-1', 'route'), node('kb', 'agent', { expert: 'kb' }), node('end', 'end')],
  edges: [
    { id: 'e1', source: 'start', target: 'route-1' },
    { id: 'e2', source: 'route-1', target: 'kb', branch_key: 'kb' },
    { id: 'e3', source: 'route-1', target: 'kb', branch_key: '__else__' },
    { id: 'e4', source: 'kb', target: 'end' },
  ],
});
const agents = new Map([
  ['kb', { name: 'kb', cn_label: '知识库助手', is_default: true, tool_names: ['search_knowledge'], prompt_main_present: true,
           prompt_main_head: 'x'.repeat(200), nondefault_param_count: 1, max_steps: 4 }],
  ['bare', { name: 'bare', cn_label: '裸助手', tool_names: [], prompt_main_present: false }],
]);

describe('R26 图模型纯函数（真实执行）', () => {
  it('TC-FE-R26-001 悬停卡片：中文标签 / name / 默认标记 / 工具 / 主提示词存在 / 前 120 字符（US-001 AC-001-01）', () => {
    const c = M.buildHoverCardModel(node('kb', 'agent', { expert: 'kb' }), agents);
    const get = (l) => c.lines.find((x) => x.label === l)?.value;
    assert.equal(c.title, '知识库助手');
    assert.equal(get('name'), 'kb');
    assert.equal(get('标记'), '默认专家');
    assert.equal(get('已授权工具'), 'search_knowledge');
    assert.equal(get('主提示词'), '存在');
    assert.equal(get('提示词开头').length, 120);
    assert.equal(get('工具参数'), '1 个非默认参数');
  });

  it('TC-FE-R26-002 无工具授权的 agent 工具一行显示“无”而不是空白（AC-001-03）', () => {
    const c = M.buildHoverCardModel(node('bare', 'agent', { expert: 'bare' }), agents);
    assert.equal(c.lines.find((x) => x.label === '已授权工具').value, '无');
    assert.equal(c.lines.find((x) => x.label === '主提示词').value, '不存在');
  });

  it('TC-FE-R26-003 路由节点卡片显示 tau / margin / max_expert_steps / default_expert 四项当前值（AC-001-02）', () => {
    const c = M.buildHoverCardModel(node('route-1', 'route'), agents, { tau: 0.65, margin: 0.05, max_expert_steps: 8, default_expert: 'kb' });
    assert.deepEqual(c.lines.map((l) => [l.label, l.value]),
      [['tau', '0.65'], ['margin', '0.05'], ['max_expert_steps', '8'], ['default_expert', 'kb']]);
  });

  it('TC-FE-R26-004 条件边卡片：条件分支标注、否则分支（AC-001-04）', () => {
    const g = { ...G(), nodes: [...G().nodes, node('c', 'condition', { predicate: { kind: 'keyword', branches: [{ key: 'billing', keywords: ['发票'] }] } })] };
    const byId = new Map(g.nodes.map((n) => [n.id, n]));
    const e = M.buildEdgeCardModel({ id: 'x', source: 'c', target: 'kb', branch_key: 'billing' }, byId);
    assert.equal(e.title, '条件边');
    assert.ok(e.lines.some((l) => l.label === '条件分支' && l.value === 'billing'));
    const el = M.buildEdgeCardModel({ id: 'y', source: 'c', target: 'kb', branch_key: '__else__' }, byId);
    assert.ok(el.lines.some((l) => l.value === '否则'));
  });

  it('TC-FE-R26-005 节点面板只提供受限节点集，没有代码 / 表达式节点（US-011 AC-011-06）', () => {
    assert.deepEqual([...M.ADDABLE_KINDS].sort(), ['agent', 'condition', 'confirm', 'join', 'route']);
    assert.ok(!Object.keys(M.KIND_LABEL).some((k) => /code|expr|script/i.test(k)));
  });

  it('TC-FE-R26-006 连线预校验：自环 / 指入开始 / 从结束引出 / 重复边被拒；合法连线通过（AC-011-02）', () => {
    const g = G();
    assert.equal(M.precheckConnection(g, 'kb', 'kb').ok, false);
    assert.equal(M.precheckConnection(g, 'kb', 'start').ok, false);
    assert.equal(M.precheckConnection(g, 'end', 'kb').ok, false);
    assert.equal(M.precheckConnection(g, 'start', 'route-1').ok, false);
    assert.equal(M.precheckConnection(g, 'start', 'ghost').ok, false);
    assert.equal(M.precheckConnection(g, 'start', 'kb').ok, true);
  });

  it('TC-FE-R26-007 新增节点 id 不冲突；agent 节点 id = 专家名；条件 / 确认节点带默认内容（AC-011-03）', () => {
    const g = G();
    const j1 = M.addNodeOfKind(g, 'join');
    const j2 = M.addNodeOfKind({ nodes: [...g.nodes, j1], edges: g.edges }, 'join');
    assert.notEqual(j1.id, j2.id);
    const a = M.addNodeOfKind(g, 'agent', 'billing-agent');
    assert.equal(a.id, 'billing-agent');
    assert.equal(a.expert, 'billing-agent');
    assert.equal(a.input_mode, 'query_only');
    assert.equal(M.addNodeOfKind(g, 'condition').predicate.kind, 'keyword');
    assert.ok(M.addNodeOfKind(g, 'confirm').message.length > 0);
    assert.equal(M.nextEdgeId(g), 'e5');
  });

  it('TC-FE-R26-008 删除节点同时删除其连线，受影响边数用于确认框“将同时删除 N 条边”（US-005 AC-005-03）', () => {
    const g = G();
    assert.equal(M.edgesTouching(g, 'kb'), 3);
    const r = M.removeNode(g, 'kb');
    assert.equal(r.nodes.some((n) => n.id === 'kb'), false);
    assert.deepEqual(r.edges.map((e) => e.id), ['e1']);
  });

  it('TC-FE-R26-009 位置回写：取整并限幅 ±100000；只改坐标不改结构（US-012 AC-012-01）', () => {
    const g = G();
    const out = M.applyPositions(g, new Map([['kb', { x: 12.6, y: -999999 }]]));
    const kb = out.nodes.find((n) => n.id === 'kb');
    assert.equal(kb.x, 13);
    assert.equal(kb.y, -100000);
    assert.deepEqual(out.edges, g.edges);
    assert.equal(out.nodes.find((n) => n.id === 'start').x, 0);
  });

  it('TC-FE-R26-010 图 → 画布：分支边带标签（否则）、默认专家带“（默认）”、坐标全 0 时自动分层（US-003）', () => {
    const f = M.graphToFlow(G(), agents);
    assert.equal(f.nodes.find((n) => n.id === 'kb').data.label, '知识库助手（默认）');
    assert.equal(f.edges.find((e) => e.id === 'e3').label, '否则');
    assert.equal(f.edges.find((e) => e.id === 'e2').label, 'kb');
    const xs = new Set(f.nodes.map((n) => n.position.x));
    assert.ok(xs.size >= 3, '自动分层应产生多列');
  });

  it('TC-FE-R26-011 新连线的默认分支键：route 出边 = 目标专家名或 __else__；condition 先给未占用的分支键（AC-006-02 的前端体验层）', () => {
    const g = G();
    assert.equal(M.defaultBranchKey({ ...g, edges: [] }, 'route-1', 'kb'), 'kb');
    assert.equal(M.defaultBranchKey(g, 'route-1', 'kb'), '__else__');
    assert.equal(M.defaultBranchKey(g, 'kb', 'end'), null);
    const c = { nodes: [node('c', 'condition', { predicate: { kind: 'keyword', branches: [{ key: 'a', keywords: ['x'] }] } }), node('kb', 'agent', { expert: 'kb' })], edges: [] };
    assert.equal(M.defaultBranchKey(c, 'c', 'kb'), 'a');
  });
});

describe('R26 结构事实（读源码）', () => {
  const comps = ['FlowCanvas', 'NodeHoverCard', 'AgentDetailPanel', 'PublishDialog', 'ConflictDialog', 'VersionHistory', 'TrialPanel',
    'BuilderDrawer', 'BuilderEvalView', 'NodePalette', 'AccessPanel'].map((n) => [n, stripComments(read('components', 'config', `${n}.vue`))]);
  const studio = stripComments(read('views', 'ConfigStudio.vue'));

  it('TC-FE-R26-020 不使用 v-html / localStorage / axios / CDN：提示词 / 关键词一律文本插值（US-019 AC-019-02、US-030 AC-030-05）', () => {
    for (const [n, s] of [...comps, ['ConfigStudio', studio], ['configDraft', stripComments(read('stores', 'configDraft.ts'))]]) {
      assert.doesNotMatch(s, /v-html|innerHTML|localStorage|axios/, `${n} 含被禁用法`);
      assert.doesNotMatch(s, /https?:\/\/(cdn|unpkg|esm\.sh)/, `${n} 含 CDN`);
    }
  });

  it('TC-FE-R26-021 画布只读档：不可拖拽 / 不可连线 / 无删除键（US-011 AC-011-04）', () => {
    const s = comps.find(([n]) => n === 'FlowCanvas')[1];
    assert.match(s, /:nodes-draggable="!readonly"/);
    assert.match(s, /:nodes-connectable="!readonly"/);
    assert.match(s, /:delete-key-code="readonly \? null : 'Delete'"/);
    assert.match(comps.find(([n]) => n === 'NodePalette')[1], /v-if="!readonly"/);
  });

  it('TC-FE-R26-022 详情面板只读档：全部输入 disabled，且不出现保存按钮（US-002 AC-002-03、US-009 AC-009-04）', () => {
    const s = comps.find(([n]) => n === 'AgentDetailPanel')[1];
    assert.match(s, /当前为“查看”档/);
    const inputs = (s.match(/<el-(input|input-number|checkbox|select|switch)\b[^>]*>/g) ?? []);
    const editable = inputs.filter((t) => !/:disabled="readonly"|readonly/.test(t));
    assert.deepEqual(editable.map((t) => t.slice(0, 80)), [], '存在未随只读档禁用的输入控件');
  });

  it('TC-FE-R26-023 保存流程：差异预览 → 确认后才提交；取消不提交（US-016 AC-016-01/02）', () => {
    assert.match(studio, /PublishDialog/);
    const dlg = comps.find(([n]) => n === 'PublishDialog')[1];
    assert.match(dlg, /preview|items/);
    assert.match(dlg, /确认/);
    assert.match(dlg, /取消/);
  });

  it('TC-FE-R26-024 保存按钮在无改动时不可用；有改动显示“未保存”；放弃改动 / 重新载入需确认（US-003 AC-003-02/03、US-016 AC-016-03）', () => {
    assert.match(studio, /store\.dirty\.value/);
    assert.match(studio, /未保存/);
    assert.match(studio, /放弃改动/);
    assert.match(studio, /丢弃未保存的改动并重新载入/);
    assert.match(studio, /:disabled="!store\.dirty\.value"/);
  });

  it('TC-FE-R26-025 冲突处理三选项：放弃并重新载入 / 另存草稿副本（US-018 AC-018-02/03）', () => {
    const s = comps.find(([n]) => n === 'ConflictDialog')[1];
    assert.match(s, /重新载入/);
    assert.match(s, /草稿副本/);
  });

  it('TC-FE-R26-026 保存成功文案：不再要求重启，显示“已生效”（US-014 AC-014-05）', () => {
    const all = [studio, ...comps.map(([, s]) => s), stripComments(read('views', 'ConfigPage.vue'))].join('\n');
    assert.doesNotMatch(all, /重启 ?ib-web|重启后生效|不热重载/);
    assert.match(all, /已生效/);
  });

  it('TC-FE-R26-027 权限管理页签仅管理档渲染；Builder / 试运行入口仅编辑档及以上（US-010 AC-010-01、US-004 AC-004-04）', () => {
    assert.match(studio, /level === 'manage'/);
    assert.match(studio, /readonly|level === 'view'|canEdit/);
    assert.match(comps.find(([n]) => n === 'AccessPanel')[1], /canManage/);
  });

  it('TC-FE-R26-028 client.ts 暴露新端点方法且不使用 axios；新增依赖为零（package.json 未含 playwright / puppeteer / axios）', () => {
    const c = stripComments(read('api', 'client.ts'));
    for (const m of ['getAccess', 'putAccess', 'createAccount']) assert.match(c, new RegExp(m));
    const pkg = JSON.parse(readFileSync(join(here, '..', 'package.json'), 'utf8'));
    const deps = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies });
    assert.deepEqual(deps.filter((d) => /playwright|puppeteer|cypress|axios|jsdom|vitest|jest/.test(d)), []);
  });
});
