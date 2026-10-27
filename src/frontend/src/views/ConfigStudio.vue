<script setup lang="ts">
/**
 * @module MOD-R26-21
 * @implements REQ-FUNC-001~003/011/014~017/023 编排画布页壳：动态图 + 悬停卡片 + 详情面板 + Agent Builder +
 *             保存并生效（先看差异再确认）+ 版本历史 / 回滚 + 试运行。
 * 保存成功提示“已生效（版本 N）”，不再出现“重启后生效”。视图侧零持久化：草稿只在内存，
 * 离开前可“另存为服务端草稿副本”。
 */
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';

import {
  ApiClientError,
  type ApiClient,
  type ConfigCatalogDto,
  type ConfigStatusDto,
  type ConflictReceiptDto,
  type DiffItemDto,
  type GraphDto,
  type GraphNodeDto,
  type NodeKind,
  type ValidationErrorItem,
} from '../api/client';
import type { AgentDraftDto } from '../api/builderTypes';
import AccessPanel from '../components/config/AccessPanel.vue';
import AgentDetailPanel from '../components/config/AgentDetailPanel.vue';
import BuilderDrawer from '../components/config/BuilderDrawer.vue';
import ConflictDialog from '../components/config/ConflictDialog.vue';
import FlowCanvas from '../components/config/FlowCanvas.vue';
import NodePalette from '../components/config/NodePalette.vue';
import PublishDialog from '../components/config/PublishDialog.vue';
import TrialPanel from '../components/config/TrialPanel.vue';
import VersionHistory from '../components/config/VersionHistory.vue';
import { addNodeOfKind, edgesTouching, removeNode, type AgentInfo } from '../components/config/graphModel';
import { createConfigDraft } from '../stores/configDraft';

const props = defineProps<{ client: ApiClient }>();

const store = createConfigDraft();
const status = ref<ConfigStatusDto | null>(null);
const catalog = ref<ConfigCatalogDto | null>(null);
const phase = ref<'loading' | 'ready' | 'unavailable' | 'forbidden'>('loading');
const banner = ref('');
const selectedId = ref<string | null>(null);
const tab = ref('detail');
const builderOpen = ref(false);

const level = computed(() => status.value?.level ?? 'view');
const readonly = computed(() => level.value === 'view');
const graph = computed<GraphDto>(() => store.document.value?.graph ?? { nodes: [], edges: [] });
const selectedNode = computed<GraphNodeDto | null>(() => graph.value.nodes.find((n) => n.id === selectedId.value) ?? null);

const agents = computed(() => {
  const m = new Map<string, AgentInfo>();
  const doc = store.document.value;
  if (!doc) return m;
  for (const e of doc.experts) {
    const grant = doc.tool_grants.find((g) => g.expert_name === e.name);
    const sum = catalog.value?.agents.find((a) => a.name === e.name);
    m.set(e.name, {
      name: e.name, cn_label: e.cn_label, is_default: e.is_default, status: e.status, keywords: e.keywords,
      tool_names: grant?.tool_names ?? [], nondefault_param_count: grant?.param_values?.length ?? 0,
      prompt_main_present: sum?.prompt_main_present, prompt_main_head: sum?.prompt_main_head,
      max_steps: e.max_steps ?? null,
    });
  }
  return m;
});

async function load(): Promise<void> {
  phase.value = 'loading';
  banner.value = '';
  try {
    const [st, env, cat] = await Promise.all([props.client.configStatus(), props.client.definitionConfigV2(), props.client.configCatalog()]);
    status.value = st;
    catalog.value = cat;
    store.load(env.document as never, env.version, env.graph);
    selectedId.value = null;
    phase.value = 'ready';
  } catch (err) {
    phase.value = err instanceof ApiClientError && err.status === 403 ? 'forbidden' : 'unavailable';
    banner.value = err instanceof ApiClientError ? err.message : '配置载入失败';
  }
}
function reloadWithConfirm(): void {
  if (store.dirty.value && !window.confirm('丢弃未保存的改动并重新载入？')) return;
  void load();
}
function discard(): void {
  store.discard();
  selectedId.value = null;
}

// ---- 画布操作 ----
function setGraph(g: GraphDto): void {
  store.setGraph(g);
}
function onAddNode(kind: NodeKind): void {
  const doc = store.document.value;
  if (!doc) return;
  if (kind === 'agent') {
    const placed = new Set(graph.value.nodes.map((n) => n.expert ?? n.id));
    const free = doc.experts.find((e) => !placed.has(e.name) && (e.status ?? 'active') === 'active');
    if (!free) {
      ElMessage.info('没有尚未上图的 agent，请用 Agent Builder 创建新 agent');
      return;
    }
    setGraph({ nodes: [...graph.value.nodes, addNodeOfKind(graph.value, 'agent', free.name)], edges: graph.value.edges });
    return;
  }
  setGraph({ nodes: [...graph.value.nodes, addNodeOfKind(graph.value, kind)], edges: graph.value.edges });
}
function onUpdateNode(n: GraphNodeDto): void {
  setGraph({ nodes: graph.value.nodes.map((x) => (x.id === n.id ? n : x)), edges: graph.value.edges });
}
function onRemoveAgent(name: string): void {
  const doc = store.document.value;
  if (!doc) return;
  const n = edgesTouching(graph.value, name);
  if (n > 0 && !window.confirm(`将同时删除 ${n} 条边，继续？`)) return;
  const g = removeNode(graph.value, name);
  store.document.value = {
    ...doc,
    experts: doc.experts.filter((e) => e.name !== name),
    tool_grants: doc.tool_grants.filter((x) => x.expert_name !== name),
    graph: g,
  };
  selectedId.value = null;
}
function onBuilderAdd(d: AgentDraftDto): void {
  const doc = store.document.value;
  if (!doc) return;
  const scope = d.knowledge_folder_ids.length ? { mode: 'folders' as const, folder_ids: d.knowledge_folder_ids } : { mode: 'all' as const, folder_ids: [] };
  const expert = {
    name: d.name, cn_label: d.cn_label, keywords: d.keywords, exemplars: d.exemplars, is_data_expert: d.is_data_expert,
    is_delegating: d.is_delegating, is_default: false, status: 'active' as const, max_steps: d.max_steps, knowledge_scope: scope,
  };
  const grant = { expert_name: d.name, tool_names: d.tool_names, param_values: d.tool_params.map(([name, value]) => ({ name, value: String(value) })) };
  const node = addNodeOfKind(graph.value, 'agent', d.name);
  store.document.value = {
    ...doc,
    experts: [...doc.experts, expert],
    tool_grants: [...doc.tool_grants, grant],
    graph: { nodes: [...graph.value.nodes, node], edges: graph.value.edges },
  };
  store.setPrompt(d.name, 'main', d.main_prompt);
  store.setPrompt(d.name, 'fallback', d.fallback_prompt);
  selectedId.value = d.name;
  tab.value = 'detail';
  ElMessage.success('已加入画布（未保存）。请把它连入路由与结束节点后再“保存并生效”。');
}

// ---- 保存并生效 ----
const dialog = ref(false);
const diffItems = ref<DiffItemDto[]>([]);
const layoutOnly = ref(false);
const diffErrors = ref<ValidationErrorItem[]>([]);
const busy = ref(false);
const receipt = ref<ConflictReceiptDto | null>(null);

function explain(err: unknown): void {
  if (err instanceof ApiClientError) {
    if (err.status === 403) banner.value = `权限不足：需要“${String(err.details.required_level ?? 'edit')}”档`;
    else banner.value = err.message;
  } else {
    banner.value = '操作失败';
  }
}
async function startSave(): Promise<void> {
  banner.value = '';
  busy.value = true;
  try {
    const p = await props.client.publishPreview(store.baseVersion.value, store.toPublishPayload());
    diffItems.value = p.items;
    layoutOnly.value = p.layout_only;
    diffErrors.value = p.errors;
    dialog.value = true;
  } catch (err) {
    if (err instanceof ApiClientError && err.code === 'conflict') receipt.value = err.details.receipt as ConflictReceiptDto;
    else if (err instanceof ApiClientError && err.code === 'validation_error') {
      diffItems.value = [];
      diffErrors.value = (err.details.items as ValidationErrorItem[]) ?? [];
      dialog.value = true;
    } else explain(err);
  } finally {
    busy.value = false;
  }
}
async function confirmSave(message?: string): Promise<void> {
  busy.value = true;
  try {
    const r = await props.client.publish(store.baseVersion.value, store.toPublishPayload(), message);
    dialog.value = false;
    ElMessage.success(`已生效（版本 ${r.version}）`);
    await load();
  } catch (err) {
    if (err instanceof ApiClientError && err.code === 'conflict') {
      dialog.value = false;
      receipt.value = err.details.receipt as ConflictReceiptDto;
    } else if (err instanceof ApiClientError && err.code === 'validation_error') {
      diffErrors.value = (err.details.items as ValidationErrorItem[]) ?? [];
    } else if (err instanceof ApiClientError && err.code === 'apply_failed') {
      dialog.value = false;
      banner.value = `应用失败，当前仍使用版本 ${status.value?.version ?? ''}：${err.message}（错误码 ${err.code}）`;
    } else {
      dialog.value = false;
      explain(err);
    }
  } finally {
    busy.value = false;
  }
}
async function saveAsDraft(): Promise<void> {
  try {
    await props.client.saveDraft(`草稿 ${new Date().toLocaleString()}`, store.baseVersion.value, store.toPublishPayload());
    ElMessage.success('已另存为草稿副本（不影响在用版本）');
    receipt.value = null;
    await load();
  } catch (err) {
    explain(err);
  }
}
async function adopt(): Promise<void> {
  try {
    const r = await props.client.adoptDrift(store.baseVersion.value);
    ElMessage.success(`已采纳文件态为版本 ${r.version}`);
    await load();
  } catch (err) {
    explain(err);
  }
}
async function onRolledBack(): Promise<void> {
  await load();
}

onMounted(load);
</script>

<template>
  <section class="studio">
    <header class="bar">
      <h3>编排画布</h3>
      <span v-if="status">当前版本 {{ status.version }} · 权限档位：{{ { view: '查看', edit: '编辑', manage: '管理' }[status.level] }}</span>
      <el-tag v-if="store.dirty.value" type="warning" size="small">未保存</el-tag>
      <span class="spacer" />
      <el-button size="small" @click="reloadWithConfirm">重新载入</el-button>
      <el-button size="small" :disabled="!store.dirty.value" @click="discard">放弃改动</el-button>
      <el-button v-if="!readonly" size="small" @click="builderOpen = true">Agent Builder</el-button>
      <el-button v-if="!readonly" size="small" type="primary" :loading="busy" :disabled="!store.dirty.value" @click="startSave">保存并生效</el-button>
    </header>

    <el-alert v-if="status?.apply_state === 'apply_failed'" type="error" :closable="false" title="新配置应用失败，当前仍使用上一个成功版本" />
    <el-alert v-if="status?.drift" type="warning" :closable="false" title="检测到配置文件被绕过系统直接修改（漂移）；运行中仍使用已发布版本">
      <el-button v-if="level === 'manage'" size="small" @click="adopt">采纳文件态为新版本</el-button>
    </el-alert>
    <el-alert v-if="status?.legacy" type="info" :closable="false" title="该项目仍是旧形态配置；首次保存会自动升级为自由画布，并先存一份升级前基线版本。" />
    <p v-if="banner" class="banner">{{ banner }}</p>
    <p v-if="phase === 'loading'">载入中…</p>
    <p v-else-if="phase === 'forbidden'" class="banner">当前账号无权查看本项目的配置。</p>
    <p v-else-if="phase === 'unavailable'" class="banner">配置当前不可用（服务端 fail-closed，不返回空配置）。</p>

    <div v-if="phase === 'ready' && store.document.value" class="body">
      <div class="left">
        <NodePalette :readonly="readonly" @add-node="onAddNode" />
        <FlowCanvas
          :graph="graph"
          :readonly="readonly"
          :agents="agents"
          :route="store.document.value.route"
          @update:graph="setGraph"
          @select-node="(id: string) => { selectedId = id; tab = 'detail'; }"
          @notice="(t: string) => (banner = t)"
        />
        <p class="hint">鼠标悬停节点或边可查看其配置；点击节点在右侧查看 / 编辑详情与提示词。{{ readonly ? '（查看档：只读）' : '' }}</p>
      </div>
      <div class="right">
        <el-tabs v-model="tab">
          <el-tab-pane label="详情" name="detail">
            <AgentDetailPanel
              :client="client"
              :doc="store.document.value"
              :catalog="catalog"
              :node="selectedNode"
              :readonly="readonly"
              :prompt-patch="store.promptPatch.value"
              @change="(d) => (store.document.value = d)"
              @prompt="(e, l, t) => store.setPrompt(e, l, t)"
              @remove-agent="onRemoveAgent"
              @update-node="onUpdateNode"
            />
          </el-tab-pane>
          <el-tab-pane label="版本历史" name="versions" lazy>
            <VersionHistory :client="client" :level="level" :head-version="status?.version ?? 0" @rolled-back="onRolledBack" />
          </el-tab-pane>
          <el-tab-pane v-if="level === 'manage'" label="权限管理" name="access" lazy>
            <AccessPanel :client="client" :level="level" />
          </el-tab-pane>
          <el-tab-pane v-if="!readonly" label="试运行" name="trial" lazy>
            <TrialPanel :client="client" :get-draft-payload="store.toPublishPayload" :disabled="readonly" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <PublishDialog :visible="dialog" :items="diffItems" :layout-only="layoutOnly" :errors="diffErrors" :busy="busy" @confirm="confirmSave" @cancel="dialog = false" />
    <ConflictDialog :visible="receipt !== null" :receipt="receipt" @reload="() => { receipt = null; void load(); }" @save-draft="saveAsDraft" @close="receipt = null" />
    <BuilderDrawer :visible="builderOpen" :client="client" :doc="store.document.value" :catalog="catalog" @add-to-canvas="onBuilderAdd" @close="builderOpen = false" />
  </section>
</template>

<style scoped>
.bar { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.spacer { flex: 1; }
.body { display: grid; grid-template-columns: minmax(0, 3fr) minmax(320px, 2fr); gap: 14px; }
.banner { color: var(--el-color-danger); }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
