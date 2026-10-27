<script setup lang="ts">
/**
 * @module MOD-R26-19
 * @implements REQ-FUNC-001/003/011/012 可编辑编排画布（悬停卡片、拖拽、连线、删边）
 * 只读档（readonly）：节点不可拖拽、无连线句柄。悬停卡片一律文本插值（不使用富文本注入）。
 */
import { VueFlow, type Connection, type EdgeChange, type NodeDragEvent, type NodeMouseEvent, type EdgeMouseEvent } from '@vue-flow/core';
import { computed, ref } from 'vue';

import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';

import type { GraphDto } from '../../api/client';
import NodeHoverCard from './NodeHoverCard.vue';
import {
  applyPositions,
  buildEdgeCardModel,
  buildHoverCardModel,
  defaultBranchKey,
  graphToFlow,
  nextEdgeId,
  precheckConnection,
  type AgentInfo,
  type HoverCardModel,
} from './graphModel';

const props = defineProps<{
  graph: GraphDto;
  readonly: boolean;
  agents: Map<string, AgentInfo>;
  route?: { tau: number; margin: number; max_expert_steps: number; default_expert: string };
}>();
const emit = defineEmits<{
  (e: 'update:graph', g: GraphDto): void;
  (e: 'select-node', id: string): void;
  (e: 'select-edge', id: string): void;
  (e: 'notice', text: string): void;
}>();

const flow = computed(() => graphToFlow(props.graph, props.agents));
const card = ref<HoverCardModel | null>(null);
const cardPos = ref({ x: 0, y: 0 });

function place(ev: MouseEvent): void {
  const host = (ev.currentTarget as HTMLElement | null)?.closest('.flow-host') as HTMLElement | null;
  const r = host?.getBoundingClientRect();
  cardPos.value = { x: ev.clientX - (r?.left ?? 0) + 14, y: ev.clientY - (r?.top ?? 0) + 14 };
}
function onNodeEnter({ node, event }: NodeMouseEvent): void {
  const n = props.graph.nodes.find((x) => x.id === node.id);
  if (!n) return;
  card.value = buildHoverCardModel(n, props.agents, props.route);
  place(event as MouseEvent);
}
function onEdgeEnter({ edge, event }: EdgeMouseEvent): void {
  const e = props.graph.edges.find((x) => x.id === edge.id);
  if (!e) return;
  card.value = buildEdgeCardModel(e, new Map(props.graph.nodes.map((n) => [n.id, n])));
  place(event as MouseEvent);
}
function hide(): void {
  card.value = null;
}

function onDragStop({ node }: NodeDragEvent): void {
  if (props.readonly) return;
  emit('update:graph', applyPositions(props.graph, new Map([[node.id, node.position]])));
}

function onConnect(c: Connection): void {
  if (props.readonly) return;
  const chk = precheckConnection(props.graph, c.source, c.target);
  if (!chk.ok) {
    emit('notice', chk.reason ?? '连线不合法');
    return;
  }
  const edge = {
    id: nextEdgeId(props.graph),
    source: c.source,
    target: c.target,
    branch_key: defaultBranchKey(props.graph, c.source, c.target),
  };
  emit('update:graph', { nodes: props.graph.nodes, edges: [...props.graph.edges, edge] });
}

function onEdgesChange(changes: EdgeChange[]): void {
  if (props.readonly) return;
  const gone = new Set(changes.filter((c) => c.type === 'remove').map((c) => (c as { id: string }).id));
  if (gone.size === 0) return;
  emit('update:graph', { nodes: props.graph.nodes, edges: props.graph.edges.filter((e) => !gone.has(e.id)) });
}
</script>

<template>
  <div class="flow-host" @mouseleave="hide">
    <VueFlow
      :nodes="flow.nodes.map((n) => ({ ...n, deletable: false }))"
      :edges="flow.edges"
      :nodes-draggable="!readonly"
      :nodes-connectable="!readonly"
      :elements-selectable="true"
      :delete-key-code="readonly ? null : 'Delete'"
      fit-view-on-init
      @node-mouse-enter="onNodeEnter"
      @node-mouse-leave="hide"
      @edge-mouse-enter="onEdgeEnter"
      @edge-mouse-leave="hide"
      @node-drag-stop="onDragStop"
      @connect="onConnect"
      @edges-change="onEdgesChange"
      @node-click="({ node }) => emit('select-node', node.id)"
      @edge-click="({ edge }) => emit('select-edge', edge.id)"
    />
    <NodeHoverCard v-if="card" :model="card" :x="cardPos.x" :y="cardPos.y" />
  </div>
</template>

<style scoped>
.flow-host {
  position: relative;
  height: 460px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
}
:deep(.graph-agent) {
  border: 2px solid var(--el-color-primary);
}
:deep(.graph-start),
:deep(.graph-end) {
  border-style: dashed;
}
:deep(.graph-route),
:deep(.graph-condition),
:deep(.graph-join),
:deep(.graph-confirm) {
  background: var(--el-fill-color-light);
}
</style>
