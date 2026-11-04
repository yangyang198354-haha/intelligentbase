/**
 * @module MOD-R28-17
 * @implements IFC-R28-027 “加入 / 移除顾问”的草稿变换（纯函数；无 DOM、无 Vue 依赖，node:test 可离线加载）。
 *
 * 只作用于草稿副本、不发请求；保存走既有“预检 → 差异清单 → 保存并生效”，服务端 `validate_graph`
 * 仍是唯一裁决者。运行期只 import ./graphModel，其余均为 import type。
 */

import type { BuiltinAgentDto, DefinitionDocumentV2, GraphDto, GraphEdgeDto, GraphNodeDto } from '../../api/client';
import { nextEdgeId } from './graphModel';

export const ADVISOR_ID = 'advisor';
const ELSE = '__else__';

export interface AdvisorPlanResult {
  doc: DefinitionDocumentV2;
  graph: GraphDto;
  promptPatch: { expert: string; main: string } | null;
  wired: boolean;
  message: string;
}

/** experts 含 name==='advisor' && is_delegating && status!=='disabled'（顾问模式的唯一判据）。 */
export function hasAdvisor(doc: DefinitionDocumentV2): boolean {
  return doc.experts.some((e) => e.name === ADVISOR_ID && e.is_delegating === true && (e.status ?? 'active') !== 'disabled');
}

function withGraph(doc: DefinitionDocumentV2, graph: GraphDto): DefinitionDocumentV2 {
  return { ...doc, graph };
}

/**
 * 规范形态（可自动接线）：恰一个开始 / 结束 / 路由节点；除它们外只有 agent 节点；
 * 每个 agent 恰有一条出边且指向结束；路由有 __else__ 出边，且默认专家有一条以其名为分支键的路由边。
 */
function canonicalShape(doc: DefinitionDocumentV2, graph: GraphDto): { route: GraphNodeDto; end: GraphNodeDto } | null {
  const starts = graph.nodes.filter((n) => n.kind === 'start');
  const ends = graph.nodes.filter((n) => n.kind === 'end');
  const routes = graph.nodes.filter((n) => n.kind === 'route');
  if (starts.length !== 1 || ends.length !== 1 || routes.length !== 1) return null;
  const route = routes[0];
  const end = ends[0];
  if (graph.nodes.some((n) => !['start', 'end', 'route', 'agent'].includes(n.kind))) return null;
  for (const n of graph.nodes.filter((x) => x.kind === 'agent')) {
    const outs = graph.edges.filter((e) => e.source === n.id);
    if (outs.length !== 1 || outs[0].target !== end.id || outs[0].branch_key) return null;
  }
  const routeOuts = graph.edges.filter((e) => e.source === route.id);
  if (!routeOuts.some((e) => e.branch_key === ELSE)) return null;
  const def = doc.route.default_expert;
  if (!routeOuts.some((e) => e.branch_key === def && e.target === def)) return null;
  return { route, end };
}

/** 追加顾问专家（status active、空授权）；规范形态自动接线，否则放入未连线节点且 wired=false 并给出提示。已存在 ⇒ 原样返回。 */
export function addAdvisor(doc: DefinitionDocumentV2, graph: GraphDto, builtin: BuiltinAgentDto): AdvisorPlanResult {
  if (hasAdvisor(doc)) {
    return { doc: withGraph(doc, graph), graph, promptPatch: null, wired: true, message: '该项目已加入顾问' };
  }
  const expert = { ...builtin.expert, name: ADVISOR_ID, status: 'active' as const, is_delegating: true, is_default: false };
  const grant = { expert_name: ADVISOR_ID, tool_names: [...builtin.default_tool_grants], param_values: [] };
  const baseDoc: DefinitionDocumentV2 = {
    ...doc,
    experts: [...doc.experts, expert],
    tool_grants: [...doc.tool_grants.filter((g) => g.expert_name !== ADVISOR_ID), grant],
  };
  const prompt = { expert: ADVISOR_ID, main: builtin.prompt_main };
  const shape = canonicalShape(doc, graph);
  const placed = graph.nodes.some((n) => n.id === ADVISOR_ID);
  if (!shape || placed) {
    // 非规范形态：不猜测，只放入一个未连线的顾问节点（保存时服务端会提示不可达，须手工连线）
    const maxX = graph.nodes.reduce((m, n) => Math.max(m, n.x), 0);
    const node: GraphNodeDto = placed
      ? (graph.nodes.find((n) => n.id === ADVISOR_ID) as GraphNodeDto)
      : { id: ADVISOR_ID, kind: 'agent', x: maxX / 2, y: 40, expert: ADVISOR_ID, input_mode: 'with_upstream' };
    const g: GraphDto = { nodes: placed ? graph.nodes : [...graph.nodes, node], edges: graph.edges };
    return {
      doc: withGraph(baseDoc, g),
      graph: g,
      promptPatch: prompt,
      wired: false,
      message:
        '已加入顾问，但当前编排图不是标准形态，未自动连线。请手工连线：各 agent → 顾问、路由“否则”分支 → 顾问、顾问 → 结束。',
    };
  }
  const { route, end } = shape;
  const advisor: GraphNodeDto = {
    id: ADVISOR_ID, kind: 'agent', x: end.x, y: end.y, expert: ADVISOR_ID, input_mode: 'with_upstream',
  };
  const movedEnd: GraphNodeDto = { ...end, x: end.x + 230 };
  const nodes = graph.nodes.map((n) => (n.id === end.id ? movedEnd : n)).concat(advisor);
  // 叶子 agent → 结束  改为  agent → 顾问；路由 __else__ → 顾问
  const edges: GraphEdgeDto[] = graph.edges.map((e) => {
    if (e.target === end.id && graph.nodes.find((n) => n.id === e.source)?.kind === 'agent') return { ...e, target: ADVISOR_ID };
    if (e.source === route.id && e.branch_key === ELSE) return { ...e, target: ADVISOR_ID };
    return e;
  });
  const g: GraphDto = { nodes, edges };
  g.edges = [...g.edges, { id: nextEdgeId(g), source: ADVISOR_ID, target: end.id }];
  return {
    doc: withGraph(baseDoc, g),
    graph: g,
    promptPatch: prompt,
    wired: true,
    message: '已加入顾问并自动连线（未保存）。保存并生效后，新问题将先经顾问理解、再委托检索、最后由顾问统一作答。',
  };
}

/**
 * 删除顾问专家 / 授权 / 节点及其边；叶子 agent → 结束 恢复；路由 __else__ 回指默认专家。
 * 顾问为默认专家 ⇒ 不可移除（message 说明）。
 */
export function removeAdvisor(doc: DefinitionDocumentV2, graph: GraphDto): AdvisorPlanResult {
  const unchanged = (message: string): AdvisorPlanResult => ({
    doc: withGraph(doc, graph), graph, promptPatch: null, wired: true, message,
  });
  const advisor = doc.experts.find((e) => e.name === ADVISOR_ID);
  if (!advisor) return unchanged('该项目未加入顾问');
  if (advisor.is_default === true) return unchanged('顾问是默认专家，不能移除；请先指定其他默认专家');
  const end = graph.nodes.find((n) => n.kind === 'end');
  const defaultId = doc.route.default_expert;
  const hasDefaultNode = graph.nodes.some((n) => n.id === defaultId);
  const routeIds = new Set(graph.nodes.filter((n) => n.kind === 'route').map((n) => n.id));
  const restored: GraphEdgeDto[] = [];
  const kept: GraphEdgeDto[] = [];
  for (const e of graph.edges) {
    if (e.source === ADVISOR_ID) continue; // 顾问的出边（→ 结束）随节点删除
    if (e.target !== ADVISOR_ID) {
      kept.push(e);
      continue;
    }
    const srcKind = graph.nodes.find((n) => n.id === e.source)?.kind;
    if (srcKind === 'agent' && end) {
      restored.push({ ...e, target: end.id }); // 叶子 agent → 结束 恢复
    } else if (routeIds.has(e.source) && e.branch_key === ELSE && hasDefaultNode) {
      restored.push({ ...e, target: defaultId }); // 路由 __else__ 回指默认专家
    } // 其他来源（条件 / 汇聚等）无法无歧义恢复：随顾问一并去掉，由保存校验提示
  }
  const nodes = graph.nodes.filter((n) => n.id !== ADVISOR_ID);
  const g: GraphDto = { nodes, edges: [...kept, ...restored] };
  const nextDoc: DefinitionDocumentV2 = {
    ...doc,
    experts: doc.experts.filter((e) => e.name !== ADVISOR_ID),
    tool_grants: doc.tool_grants.filter((x) => x.expert_name !== ADVISOR_ID),
    graph: g,
  };
  return {
    doc: nextDoc,
    graph: g,
    promptPatch: null,
    wired: true,
    message: '已移除顾问并恢复直连结束（未保存）。保存并生效后，其提示词文件将从项目目录移除；可在“版本历史”中回滚找回。',
  };
}
