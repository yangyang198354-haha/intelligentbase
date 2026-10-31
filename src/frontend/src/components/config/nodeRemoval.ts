/**
 * @module MOD-R27-01
 * @implements IFC-R27-001~006、009a 节点删除纯逻辑（Delete 键判定、删除可行性、确认规则与文案、
 *             两种移除的草稿变换、未上图 agent 列表、撤销状态机）。无 DOM、无 Vue 依赖；
 *             运行期仅 import ./graphModel，其余均为 import type，可由 node:test 离线加载。
 */

import type { DefinitionDocumentV2, GraphDto, NodeKind, PromptPatch } from '../../api/client';
import { ADDABLE_KINDS, edgesTouching, removeNode } from './graphModel';

/** 可删类型 = ADDABLE_KINDS（route / agent / condition / join / confirm）；start / end 为结构节点。 */
export const REMOVABLE_KINDS: readonly NodeKind[] = ADDABLE_KINDS;
export const STRUCTURAL_REMOVE_HINT = '开始 / 结束节点不可删除';
export const DEFAULT_EXPERT_HINT = '默认专家不能删除，请先指定其他默认专家';
export const MULTI_SELECT_HINT = '请选中单个节点后再删除';

/** 草稿的“可被删除操作改变的部分”：文档 + 提示词补丁（与 configDraft 快照口径一致）。 */
export interface DraftState {
  document: DefinitionDocumentV2;
  promptPatch: PromptPatch;
}
export type RemovalMode = 'canvas' | 'definition';

export interface KeyTargetLike {
  nodeName?: string;
  hasAttribute?: (n: string) => boolean;
  closest?: (sel: string) => unknown;
}

// ---- IFC-R27-001 ----
export function isEditableTarget(target: KeyTargetLike | null): boolean {
  if (!target) return false;
  const name = typeof target.nodeName === 'string' ? target.nodeName.toUpperCase() : '';
  if (name === 'INPUT' || name === 'SELECT' || name === 'TEXTAREA') return true;
  if (typeof target.hasAttribute === 'function' && target.hasAttribute('contenteditable')) return true;
  if (typeof target.closest === 'function') {
    return !!target.closest('.nokey, .el-overlay, .el-drawer, [role="dialog"]');
  }
  return false;
}

// ---- IFC-R27-002 ----
export interface DeleteKeyInput {
  key: string;
  ctrlKey: boolean;
  metaKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
  readonly: boolean;
  target: KeyTargetLike | null;
  selectedNodeIds: readonly string[];
  selectedEdgeIds: readonly string[];
}
export type DeleteKeyDecision =
  | { action: 'ignore' }
  | { action: 'hint'; text: string }
  | { action: 'request'; nodeId: string };

export function decideDeleteKey(input: DeleteKeyInput, _graph: GraphDto): DeleteKeyDecision {
  if (input.key !== 'Delete') return { action: 'ignore' };
  if (input.readonly) return { action: 'ignore' };
  if (input.ctrlKey || input.metaKey || input.altKey || input.shiftKey) return { action: 'ignore' };
  if (isEditableTarget(input.target)) return { action: 'ignore' };
  if (input.selectedNodeIds.length === 0) return { action: 'ignore' };
  if (input.selectedNodeIds.length + input.selectedEdgeIds.length > 1) {
    return { action: 'hint', text: MULTI_SELECT_HINT };
  }
  return { action: 'request', nodeId: input.selectedNodeIds[0] };
}

// ---- IFC-R27-003 ----
export interface RemovalVerdict {
  ok: boolean;
  reason?: string;
}

export function removalVerdict(
  doc: DefinitionDocumentV2,
  graph: GraphDto,
  nodeId: string,
  _mode: RemovalMode,
): RemovalVerdict {
  const node = graph.nodes.find((n) => n.id === nodeId);
  if (!node) return { ok: false, reason: '节点不存在' };
  if (node.kind === 'start' || node.kind === 'end') return { ok: false, reason: STRUCTURAL_REMOVE_HINT };
  if (node.kind === 'agent') {
    const name = node.expert ?? node.id;
    if (doc.experts.find((e) => e.name === name)?.is_default === true) {
      return { ok: false, reason: DEFAULT_EXPERT_HINT };
    }
  }
  return { ok: true };
}

// ---- IFC-R27-004 ----
export interface ConfirmPlan {
  needConfirm: boolean;
  edgeCount: number;
  text: string;
}

export function planConfirm(
  graph: GraphDto,
  nodeId: string,
  isBaselineNode: boolean,
  mode: RemovalMode,
  label: string,
): ConfirmPlan {
  const edgeCount = edgesTouching(graph, nodeId);
  const kind = graph.nodes.find((n) => n.id === nodeId)?.kind;
  if (mode === 'definition') {
    const edgePart = edgeCount > 0 ? `，并同时删除 ${edgeCount} 条边` : '';
    return {
      needConfirm: true,
      edgeCount,
      text:
        `确认删除 agent「${label}」（${nodeId}）？将移除其定义与工具授权${edgePart}。` +
        '保存并生效后，其提示词文件将从项目目录移除；历史会话不受影响，也可在“版本历史”中回滚找回。' +
        '若只想把它从画布拿掉并保留定义，请取消后改用“删除节点”。',
    };
  }
  const edgePart = edgeCount > 0 ? `将同时删除 ${edgeCount} 条边。` : '';
  const text =
    kind === 'agent'
      ? `确认将 agent「${label}」从画布移除？${edgePart}其定义、工具授权与提示词草稿保留，之后可点击节点面板的“agent”按钮重新放回画布。`
      : `确认删除${label}节点「${nodeId}」？${edgePart}`;
  return { needConfirm: edgeCount > 0 || isBaselineNode, edgeCount, text };
}

// ---- IFC-R27-005 ----
export function dropPromptPatch(patch: PromptPatch, expert: string): PromptPatch {
  if (!Object.prototype.hasOwnProperty.call(patch, expert)) return patch;
  const next: PromptPatch = {};
  for (const k of Object.keys(patch)) {
    if (k !== expert) next[k] = patch[k];
  }
  return next;
}

/** 仅从画布移除：只去掉节点与相连边；experts / tool_grants / promptPatch 原样保留。 */
export function removeFromCanvas(state: DraftState, nodeId: string): DraftState {
  const graph = removeNode(state.document.graph as GraphDto, nodeId);
  return { document: { ...state.document, graph }, promptPatch: state.promptPatch };
}

/** 删除 agent 定义：节点 + 相连边 + experts 条目 + tool_grants 条目 + promptPatch[expert]。 */
export function deleteAgentDefinition(state: DraftState, nodeId: string): DraftState {
  const graph = state.document.graph as GraphDto;
  const node = graph.nodes.find((n) => n.id === nodeId);
  if (!node || node.kind !== 'agent') return removeFromCanvas(state, nodeId);
  const expert = node.expert ?? node.id;
  const doc = state.document;
  return {
    document: {
      ...doc,
      experts: doc.experts.filter((e) => e.name !== expert),
      tool_grants: doc.tool_grants.filter((g) => g.expert_name !== expert),
      graph: removeNode(graph, nodeId),
    },
    promptPatch: dropPromptPatch(state.promptPatch, expert),
  };
}

// ---- IFC-R27-006 ----
export function unplacedAgents(
  doc: DefinitionDocumentV2,
  graph: GraphDto,
): { name: string; cn_label: string }[] {
  const placed = new Set(graph.nodes.map((n) => n.expert ?? n.id));
  return doc.experts
    .filter((e) => !placed.has(e.name) && (e.status ?? 'active') === 'active')
    .map((e) => ({ name: e.name, cn_label: e.cn_label }));
}

// ---- IFC-R27-009a ----
export interface RemovalUndoSlot {
  label: string;
  before: string;
  after: string;
}
export function recordRemoval(label: string, before: string, after: string): RemovalUndoSlot {
  return { label, before, after };
}
export function undoAvailable(slot: RemovalUndoSlot | null, currentSnapshot: string): boolean {
  return slot !== null && slot.after === currentSnapshot;
}
export function restoreFrom(slot: RemovalUndoSlot): DraftState {
  const parsed = JSON.parse(slot.before) as { d: DefinitionDocumentV2; p: PromptPatch };
  return { document: parsed.d, promptPatch: parsed.p };
}
