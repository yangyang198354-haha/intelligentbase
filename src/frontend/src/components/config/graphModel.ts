/**
 * @module MOD-R26-19
 * @implements IFC-R26-19x 图↔画布模型纯函数（graphToFlow / flowToGraph / buildHoverCardModel / precheckConnection /
 *             layeredPositions / addNodeOfKind）。无 DOM、无框架依赖，可由 node:test 直接离线运行。
 *
 * 前端预校验只为体验；服务端 `validate_graph` 才是唯一裁决者（REQ-FUNC-013）。
 */

import type { GraphDto, GraphEdgeDto, GraphNodeDto, NodeKind } from '../../api/client';

export interface AgentInfo {
  name: string;
  cn_label: string;
  is_default?: boolean;
  status?: string;
  keywords?: string[];
  tool_names?: string[];
  tool_count?: number;
  nondefault_param_count?: number;
  prompt_main_present?: boolean;
  prompt_main_head?: string;
  max_steps?: number | null;
}

export interface HoverCardModel {
  title: string;
  lines: { label: string; value: string }[];
}

export const KIND_LABEL: Record<NodeKind, string> = {
  start: '开始',
  end: '结束',
  route: '路由',
  agent: 'agent',
  condition: '条件分支',
  join: '汇聚',
  confirm: '人工确认',
};

/** 面板可新增的节点类型：开始 / 结束固定存在，故不在列；没有代码 / 表达式节点（AC-011-06）。 */
export const ADDABLE_KINDS: NodeKind[] = ['route', 'agent', 'condition', 'join', 'confirm'];

const ELSE = '__else__';

export function buildHoverCardModel(
  node: GraphNodeDto,
  agents: Map<string, AgentInfo>,
  route?: { tau: number; margin: number; max_expert_steps: number; default_expert: string },
): HoverCardModel {
  const lines: { label: string; value: string }[] = [];
  if (node.kind === 'agent') {
    const a = agents.get(node.expert ?? node.id);
    const title = a ? a.cn_label : node.id;
    lines.push({ label: 'name', value: node.expert ?? node.id });
    if (a?.is_default) lines.push({ label: '标记', value: '默认专家' });
    const tools = a?.tool_names ?? [];
    lines.push({ label: '已授权工具', value: tools.length ? tools.join('、') : '无' });
    if ((a?.nondefault_param_count ?? 0) > 0) {
      lines.push({ label: '工具参数', value: `${a?.nondefault_param_count} 个非默认参数` });
    }
    lines.push({ label: '主提示词', value: a?.prompt_main_present ? '存在' : '不存在' });
    if (a?.prompt_main_present && a.prompt_main_head) {
      lines.push({ label: '提示词开头', value: a.prompt_main_head.slice(0, 120) });
    }
    if (a?.max_steps) lines.push({ label: '最大步数', value: String(a.max_steps) });
    if (node.input_mode === 'with_upstream') lines.push({ label: '输入', value: '含上游材料（只读）' });
    return { title, lines };
  }
  if (node.kind === 'route') {
    if (route) {
      lines.push({ label: 'tau', value: String(route.tau) });
      lines.push({ label: 'margin', value: String(route.margin) });
      lines.push({ label: 'max_expert_steps', value: String(route.max_expert_steps) });
      lines.push({ label: 'default_expert', value: route.default_expert });
    }
    return { title: KIND_LABEL.route, lines };
  }
  if (node.kind === 'condition') {
    const p = node.predicate;
    lines.push({ label: '谓词', value: p?.kind === 'upstream_degraded' ? '上游降级' : '关键词' });
    for (const b of p?.branches ?? []) lines.push({ label: `分支 ${b.key}`, value: b.keywords.join('、') });
    return { title: KIND_LABEL.condition, lines };
  }
  if (node.kind === 'confirm') {
    lines.push({ label: '确认话术', value: node.message ?? '' });
    return { title: KIND_LABEL.confirm, lines };
  }
  return { title: KIND_LABEL[node.kind], lines };
}

export function buildEdgeCardModel(edge: GraphEdgeDto, byId: Map<string, GraphNodeDto>): HoverCardModel {
  const src = byId.get(edge.source);
  const tgt = byId.get(edge.target);
  const lines = [
    { label: '起点', value: edge.source },
    { label: '终点', value: edge.target },
  ];
  if (edge.branch_key) {
    lines.push({
      label: src?.kind === 'condition' ? '条件分支' : '路由分支',
      value: edge.branch_key === ELSE ? '否则' : edge.branch_key,
    });
  }
  return { title: edge.branch_key ? '条件边' : '边', lines: tgt ? lines : lines };
}

/** 新增节点：生成不冲突的 id 与默认位置。agent 节点需调用方指定专家名（id = 专家名）。 */
export function addNodeOfKind(graph: GraphDto, kind: NodeKind, expert?: string): GraphNodeDto {
  const used = new Set(graph.nodes.map((n) => n.id));
  let id = expert ?? '';
  if (!id) {
    let k = 1;
    while (used.has(`${kind}-${k}`)) k += 1;
    id = `${kind}-${k}`;
  }
  const maxX = graph.nodes.reduce((m, n) => Math.max(m, n.x), 0);
  const node: GraphNodeDto = { id, kind, x: maxX / 2, y: 120 + (graph.nodes.length % 4) * 70 };
  if (kind === 'agent') {
    node.expert = id;
    node.input_mode = 'query_only';
  }
  if (kind === 'condition') node.predicate = { kind: 'keyword', branches: [{ key: 'a', keywords: ['关键词'] }] };
  if (kind === 'confirm') node.message = '请确认是否继续';
  return node;
}

export function nextEdgeId(graph: GraphDto): string {
  const used = new Set(graph.edges.map((e) => e.id));
  let k = 1;
  while (used.has(`e${k}`)) k += 1;
  return `e${k}`;
}

/** 连线预校验（仅体验）：不允许指入开始、自环、重复边、从结束引出。 */
export function precheckConnection(
  graph: GraphDto,
  source: string,
  target: string,
): { ok: boolean; reason?: string } {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const s = byId.get(source);
  const t = byId.get(target);
  if (!s || !t) return { ok: false, reason: '节点不存在' };
  if (source === target) return { ok: false, reason: '不能连到自身' };
  if (t.kind === 'start') return { ok: false, reason: '开始节点不能有入边' };
  if (s.kind === 'end') return { ok: false, reason: '结束节点不能有出边' };
  if (graph.edges.some((e) => e.source === source && e.target === target)) {
    return { ok: false, reason: '该连线已存在' };
  }
  return { ok: true };
}

/** 新连线的分支键：route 出边 = 目标 agent 专家名；condition 出边需配置者在面板里补（先给占位的第一个分支键）。 */
export function defaultBranchKey(graph: GraphDto, source: string, target: string): string | null {
  const s = graph.nodes.find((n) => n.id === source);
  const t = graph.nodes.find((n) => n.id === target);
  if (!s) return null;
  if (s.kind === 'route') {
    const taken = graph.edges.some((e) => e.source === source && e.branch_key === (t?.expert ?? t?.id));
    return t?.kind === 'agent' && !taken ? (t.expert ?? t.id) : taken || t?.kind !== 'agent' ? ELSE : null;
  }
  if (s.kind === 'condition') {
    const keys = new Set(graph.edges.filter((e) => e.source === source).map((e) => e.branch_key));
    const free = (s.predicate?.branches ?? []).find((b) => !keys.has(b.key));
    return free ? free.key : keys.has(ELSE) ? null : ELSE;
  }
  return null;
}

export function layeredPositions(graph: GraphDto): Map<string, { x: number; y: number }> {
  const rank = new Map<string, number>(graph.nodes.map((n) => [n.id, 0]));
  for (let pass = 0; pass < graph.nodes.length; pass += 1) {
    let changed = false;
    for (const e of graph.edges) {
      const r = (rank.get(e.source) ?? 0) + 1;
      if (rank.has(e.target) && r > (rank.get(e.target) ?? 0) && r <= graph.nodes.length) {
        rank.set(e.target, r);
        changed = true;
      }
    }
    if (!changed) break;
  }
  const rows = new Map<number, number>();
  const out = new Map<string, { x: number; y: number }>();
  for (const n of graph.nodes) {
    const r = rank.get(n.id) ?? 0;
    const row = rows.get(r) ?? 0;
    rows.set(r, row + 1);
    out.set(n.id, { x: r * 230, y: row * 110 });
  }
  return out;
}

export interface FlowNode {
  id: string;
  position: { x: number; y: number };
  data: { label: string; kind: NodeKind };
  class: string;
}
export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated: boolean;
  style?: Record<string, string>;
}

export function graphToFlow(
  graph: GraphDto,
  agents: Map<string, AgentInfo>,
): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const auto = graph.nodes.every((n) => n.x === 0 && n.y === 0) ? layeredPositions(graph) : null;
  const nodes = graph.nodes.map((n) => {
    const a = n.kind === 'agent' ? agents.get(n.expert ?? n.id) : undefined;
    const label =
      n.kind === 'agent'
        ? `${a?.cn_label ?? n.id}${a?.is_default ? '（默认）' : ''}`
        : KIND_LABEL[n.kind];
    return {
      id: n.id,
      position: auto?.get(n.id) ?? { x: n.x, y: n.y },
      data: { label, kind: n.kind },
      class: `graph-node graph-${n.kind}`,
    };
  });
  const edges = graph.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.branch_key ? (e.branch_key === ELSE ? '否则' : e.branch_key) : undefined,
    animated: false,
    style: e.branch_key ? { strokeDasharray: '6 4' } : undefined,
  }));
  return { nodes, edges };
}

/** 画布节点位置 → 图（只更新坐标；结构变更走 store 的显式操作）。坐标取整，限幅 ±100000。 */
export function applyPositions(graph: GraphDto, pos: Map<string, { x: number; y: number }>): GraphDto {
  const clamp = (v: number) => Math.max(-100000, Math.min(100000, Math.round(v)));
  return {
    nodes: graph.nodes.map((n) => {
      const p = pos.get(n.id);
      return p ? { ...n, x: clamp(p.x), y: clamp(p.y) } : n;
    }),
    edges: graph.edges,
  };
}

/** 删除节点时受影响的边数（确认框文案“将同时删除 N 条边”）。 */
export function edgesTouching(graph: GraphDto, nodeId: string): number {
  return graph.edges.filter((e) => e.source === nodeId || e.target === nodeId).length;
}

export function removeNode(graph: GraphDto, nodeId: string): GraphDto {
  return {
    nodes: graph.nodes.filter((n) => n.id !== nodeId),
    edges: graph.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
  };
}
