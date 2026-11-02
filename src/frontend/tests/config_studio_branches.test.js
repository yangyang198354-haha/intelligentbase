/**
 * 条件分支编辑 / 连线分支键编辑（graphModel.ts 纯函数 + 面板 / 页面接线结构断言；node:test，零新增依赖）。
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
const js = ts.transpileModule(read('components', 'config', 'graphModel.ts'), {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const M = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);

const node = (id, kind, extra = {}) => ({ id, kind, x: 0, y: 0, ...extra });
const G = () => ({
  nodes: [
    node('start', 'start'),
    node('c', 'condition', { predicate: { kind: 'keyword', branches: [{ key: 'a', keywords: ['报价'] }] } }),
    node('kb', 'agent', { expert: 'kb' }),
    node('biz', 'agent', { expert: 'biz' }),
    node('r', 'route'),
    node('end', 'end'),
  ],
  edges: [
    { id: 'e1', source: 'start', target: 'c' },
    { id: 'e2', source: 'c', target: 'biz', branch_key: 'a' },
    { id: 'e3', source: 'c', target: 'kb', branch_key: '__else__' },
    { id: 'e4', source: 'r', target: 'kb', branch_key: 'kb' },
  ],
});
const cond = (g) => g.nodes.find((n) => n.id === 'c');

describe('条件分支编辑', () => {
  it('添加分支：键取下一个未占用字母，关键词为空；不改原图', () => {
    const g = G();
    const g2 = M.addConditionBranch(g, 'c');
    assert.deepEqual(cond(g2).predicate.branches.map((b) => b.key), ['a', 'b']);
    assert.deepEqual(cond(g2).predicate.branches[1].keywords, []);
    assert.equal(cond(g).predicate.branches.length, 1);
    const g3 = M.addConditionBranch(M.addConditionBranch(g2, 'c'), 'c');
    assert.deepEqual(cond(g3).predicate.branches.map((b) => b.key), ['a', 'b', 'c', 'd']);
  });

  it('添加分支：非关键词谓词 / 非条件节点不变', () => {
    const g = G();
    assert.equal(M.addConditionBranch(g, 'kb'), g);
    const d = { ...g, nodes: g.nodes.map((n) => (n.id === 'c' ? { ...n, predicate: { kind: 'upstream_degraded', branches: [] } } : n)) };
    assert.equal(M.addConditionBranch(d, 'c'), d);
  });

  it('删除分支：同时删掉使用该键的连线；只剩一个分支时不删', () => {
    const g = M.addConditionBranch(G(), 'c');
    const g2 = M.removeConditionBranch(g, 'c', 0);
    assert.deepEqual(cond(g2).predicate.branches.map((b) => b.key), ['b']);
    assert.ok(!g2.edges.some((e) => e.id === 'e2'));
    assert.ok(g2.edges.some((e) => e.id === 'e3'));
    assert.equal(M.removeConditionBranch(g2, 'c', 0), g2);
  });

  it('重命名分支：同步改写该节点的连线，不影响其他节点', () => {
    const r = M.renameConditionBranch(G(), 'c', 0, ' pricing ');
    assert.equal(r.error, undefined);
    assert.equal(cond(r.graph).predicate.branches[0].key, 'pricing');
    assert.equal(r.graph.edges.find((e) => e.id === 'e2').branch_key, 'pricing');
    assert.equal(r.graph.edges.find((e) => e.id === 'e4').branch_key, 'kb');
  });

  it('重命名分支：空 / 超长 / 保留名 / 重复都报错且不改图', () => {
    const g = M.addConditionBranch(G(), 'c');
    for (const bad of ['', '  ', 'x'.repeat(33), '__else__', '__x', 'b']) {
      const r = M.renameConditionBranch(g, 'c', 0, bad);
      assert.ok(r.error, `应拒绝 ${JSON.stringify(bad)}`);
      assert.equal(r.graph, g);
    }
  });

  it('改关键词：中英文逗号分隔、去空白', () => {
    const g = M.setConditionKeywords(G(), 'c', 0, '价格， 费用 ,,报价');
    assert.deepEqual(cond(g).predicate.branches[0].keywords, ['价格', '费用', '报价']);
  });
});

describe('连线分支键', () => {
  it('条件节点出边：选项 = 各分支键 + 否则，被其他连线占用的标 taken', () => {
    const g = M.addConditionBranch(G(), 'c');
    const opts = M.edgeBranchOptions(g, 'e3');
    assert.deepEqual(opts.map((o) => [o.value, o.label, o.taken]), [['a', 'a', true], ['b', 'b', false], ['__else__', '否则', false]]);
  });

  it('上游降级条件：选项 = degraded + 否则', () => {
    const g = G();
    const d = { ...g, nodes: g.nodes.map((n) => (n.id === 'c' ? { ...n, predicate: { kind: 'upstream_degraded', branches: [] } } : n)) };
    assert.deepEqual(M.edgeBranchOptions(d, 'e2').map((o) => o.value), ['degraded', '__else__']);
    // 新连线的默认分支键也能分到 degraded
    assert.equal(M.defaultBranchKey({ ...d, edges: [] }, 'c', 'kb'), 'degraded');
  });

  it('路由出边：选项 = 目标专家名 + 否则；普通边无选项', () => {
    assert.deepEqual(M.edgeBranchOptions(G(), 'e4').map((o) => o.value), ['kb', '__else__']);
    assert.deepEqual(M.edgeBranchOptions(G(), 'e1'), []);
  });

  it('设置边分支键只改目标边', () => {
    const g = M.setEdgeBranchKey(G(), 'e3', 'b');
    assert.equal(g.edges.find((e) => e.id === 'e3').branch_key, 'b');
    assert.equal(g.edges.find((e) => e.id === 'e2').branch_key, 'a');
  });
});

describe('接线（读源码）', () => {
  const panel = read('components', 'config', 'AgentDetailPanel.vue');
  const studio = read('views', 'ConfigStudio.vue');
  it('面板有添加分支 / 删除分支 / 连线分支键下拉，且都受只读档控制', () => {
    assert.match(panel, /<el-button v-if="!readonly"[^>]*@click="onRemoveBranch\(i\)"/);
    assert.match(panel, /<div v-if="!readonly" class="actions">\s*<el-button size="small" @click="onAddBranch">添加分支/);
    assert.match(panel, /<el-select size="small" :model-value="edge\.branch_key \?\? ''" :disabled="readonly"[^>]*@change="onEdgeKey"/);
  });
  it('页面把选中的边和图传给面板，并接 update-graph', () => {
    assert.match(studio, /@select-edge="\(id: string\) => \{ selectedEdgeId = id; selectedId = null;/);
    assert.match(studio, /:edge="selectedEdge"\s*:graph="graph"/);
    assert.match(studio, /@update-graph="setGraph"/);
  });
});
