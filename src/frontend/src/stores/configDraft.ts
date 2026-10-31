/**
 * @module MOD-R26-18
 * @implements IFC-R26-182 配置草稿 store（手写，沿用 stores/*.ts 风格，无新库）
 *
 * 持有：服务端基线版本 `baseVersion`、文档草稿 `document`、提示词补丁 `promptPatch`、`dirty`。
 * 视图侧零持久化：不使用浏览器本地存储（ADR-14 约束①②）；唯一真源是服务端。
 */

import { computed, ref } from 'vue';

import type { DefinitionDocumentV2, GraphDto, PromptPatch, PublishPayload } from '../api/client';
import {
  recordRemoval,
  restoreFrom,
  undoAvailable,
  type DraftState,
  type RemovalUndoSlot,
} from '../components/config/nodeRemoval'; // MOD-R27-02：撤销位（纯内存）

export function createConfigDraft() {
  const baseVersion = ref(0);
  const baseline = ref<string>('');
  const document = ref<DefinitionDocumentV2 | null>(null);
  const promptPatch = ref<PromptPatch>({});
  const undoSlot = ref<RemovalUndoSlot | null>(null);

  const snapshotOf = () => JSON.stringify({ d: document.value, p: promptPatch.value });
  const dirty = computed(() => document.value !== null && snapshotOf() !== baseline.value);
  const canUndo = computed(() => undoAvailable(undoSlot.value, snapshotOf()));
  const undoLabel = computed(() => (undoSlot.value ? undoSlot.value.label : ''));

  function load(doc: DefinitionDocumentV2, version: number, graph: GraphDto): void {
    const copy = JSON.parse(JSON.stringify(doc)) as DefinitionDocumentV2;
    copy.schema_version = 2;
    delete (copy as Record<string, unknown>).orchestration; // v2 以 graph 取代固定拓扑；首次保存即升级（服务端先存升级前基线）
    copy.graph = JSON.parse(JSON.stringify(graph)) as GraphDto;
    document.value = copy;
    promptPatch.value = {};
    baseVersion.value = version;
    baseline.value = snapshotOf();
    undoSlot.value = null;
  }

  function discard(): void {
    if (baseline.value) {
      const parsed = JSON.parse(baseline.value) as { d: DefinitionDocumentV2; p: PromptPatch };
      document.value = parsed.d;
      promptPatch.value = parsed.p;
    }
    undoSlot.value = null;
  }

  function markSaved(version: number): void {
    baseVersion.value = version;
    promptPatch.value = {};
    baseline.value = snapshotOf();
    undoSlot.value = null;
  }

  /** 应用一次删除并登记单步撤销（覆盖上一次）。 */
  function applyRemoval(label: string, next: DraftState): void {
    const before = snapshotOf();
    document.value = next.document;
    promptPatch.value = next.promptPatch;
    undoSlot.value = recordRemoval(label, before, snapshotOf());
  }

  /** 撤销位有效（快照仍等于删除后快照）时恢复删除前快照；否则不动。 */
  function undoRemoval(): boolean {
    if (!undoSlot.value || !canUndo.value) return false;
    const prev = restoreFrom(undoSlot.value);
    document.value = prev.document;
    promptPatch.value = prev.promptPatch;
    undoSlot.value = null;
    return true;
  }

  /** 基线（最近一次 load / markSaved）图中是否含该节点 id；基线未载入 → false。 */
  function isBaselineNode(nodeId: string): boolean {
    if (!baseline.value) return false;
    try {
      const parsed = JSON.parse(baseline.value) as { d: DefinitionDocumentV2 | null };
      return !!parsed.d?.graph?.nodes?.some((n) => n.id === nodeId);
    } catch {
      return false;
    }
  }

  function setGraph(graph: GraphDto): void {
    if (document.value) document.value = { ...document.value, graph };
  }

  function setPrompt(expert: string, layer: 'main' | 'fallback', text: string): void {
    promptPatch.value = {
      ...promptPatch.value,
      [expert]: { ...(promptPatch.value[expert] ?? {}), [layer]: text },
    };
  }

  function toPublishPayload(): PublishPayload {
    if (!document.value) throw new Error('配置尚未载入');
    return { document: document.value, prompts: promptPatch.value };
  }

  return {
    baseVersion, document, promptPatch, dirty, load, discard, markSaved, setGraph, setPrompt, toPublishPayload,
    applyRemoval, undoRemoval, canUndo, undoLabel, isBaselineNode,
  };
}

export type ConfigDraftStore = ReturnType<typeof createConfigDraft>;
