<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-296（R7 可视化配置页约束；REQ-FUNC-IB-25 主 / IB-26 并列主）
 *             IFC-IB-354（REV-16-2 提示词分层编辑器 + 工具授权勾选 + 工具参数）
 *             IFC-IB-363（REV-16-4 内存态非静默提示：任一 store == "memory" 即提示）
 * @depends MOD-IB-23（IFC-IB-294 / 295 / 352 / 362；**仅** HTTP 契约，不 import 任何后端模块）
 * @author software-developer
 *
 * 可视化配置页：定义文档（专家 / 路由 / 编排 / 工具授权）的**只读图渲染** + **白名单表单**。
 *
 * ## REV-16-2：三个编辑域，各有其真源（ADR-15-R1 / ADR-29 / ADR-30 / ADR-32）
 *
 *   - **定义文档域**（专家 / 路由 / 编排 / 工具授权 / 参数取值）：真源 = 服务端定义文档，
 *     经 `GET|PUT /api/config/definition`（既有白名单表单）。
 *   - **提示词域**（主 / 兜底分层）：真源 = **独立提示词目录**，经 `GET|PUT /api/config/prompts/...`
 *     （IFC-IB-352）。两域在**装配期**按专家 `name` 合并，故本页**不**把提示词塞进定义文档草稿。
 *   - **回退链可见**：主缺失时必须让用户看见「当前生效 = 兜底」（`resolved_from`），
 *     否则「主提示词存了却没生效」会被误判为保存失败（US-IB-30）。
 *
 * ## 生效口径显式提示（ADR-32 / C-IB-40，强制）
 *
 * 保存成功后**必须**提示「保存成功；重启 `ib-web` / `ib-worker` 后生效」—— 保存只做原子落盘，
 * **不**热重载、**不**在运行期重编译编排图。界面不得暗示「即时生效」。
 *
 * ## 视图侧零持久化（ADR-14 强制约束①②）
 *
 * 本页**不**用 `localStorage` / `IndexedDB` / 独立后端表保存任何内容。唯一真源是服务端定义
 * 文档；本页只持有从 `GET /api/config/definition` 取回的**内存草稿**，且：
 *   - 未提交草稿在界面显式标注「未提交（可丢弃）」；
 *   - **不得**作为下次载入源（每次进入本页都重新 `definitionConfig()` 以文档为准刷新）。
 *
 * ## 白名单制 + 拓扑不可编辑（REQ-FUNC-IB-26）
 *
 * 只渲染 / 只提交白名单（`envelope.editable_fields`）内字段。**不提供**运行期增删图节点、
 * 改变拓扑或编辑条件边存在性的入口 —— 编排图**只读**渲染（IFC-IB-296）。
 *
 * ## 本地打包，无 CDN（IFC-IB-296 / AC-IB-17-06）
 *
 * 图可视化库 `@vue-flow/core` 及其样式经**构建打包**（见 `package.json`），运行期**不**从
 * 任何 CDN 拉取，数据不出本机。
 *
 * ## 凭据不回显（AC-IB-17-05）
 *
 * `config_key_names` 只展示**键名**，不展示任何值 / 掩码 / 前缀；定义文档本就不承载凭据。
 */
import { VueFlow, type Edge, type Node } from '@vue-flow/core';
import { computed, onMounted, ref } from 'vue';

import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';

import {
  ApiClientError,
  type DefinitionConfigEnvelope,
  type DefinitionDocument,
  type PromptExpertEntry,
  type PromptLayer,
  type PromptListEnvelope,
  type StorageState,
  type ToolParamSpec,
  type ToolGrantSpec,
} from '../api/client';
import type { ApiClient } from '../api/client';

const props = defineProps<{ client: ApiClient }>();
const emit = defineEmits<{ (e: 'unauthorized'): void }>();

type Phase = 'loading' | 'ready' | 'unavailable' | 'forbidden';

const phase = ref<Phase>('loading');
const envelope = ref<DefinitionConfigEnvelope | null>(null);
/** 内存草稿（**唯一真源**仍是服务端文档；草稿从不落盘、从不作为载入源）。 */
const draft = ref<DefinitionDocument | null>(null);
const dirty = ref(false);
const saving = ref(false);
const banner = ref('');
const errorItems = ref<{ path: string; code: string; message: string }[]>([]);
/** 乐观并发基线：提交时携带，服务端不一致即 409（**不静默覆盖**）。 */
const baseHash = ref('');

const editable = computed<Set<string>>(() => new Set(envelope.value?.editable_fields ?? []));
const canEdit = (field: string): boolean => editable.value.has(field);

const keyNames = computed<string[]>(() => envelope.value?.config_key_names ?? []);

// --------------------------------------------------------------------------- //
// 编排图（只读）渲染
//
// 两类边**缺一不可**：**普通边**（无条件转移，如 `expert → gate → aggregate`）与
// **条件边**（按分支键择一，如 `route → expert / general`）。只画条件边时，`gate` /
// `aggregate` 这类只靠普通边相连的节点会渲染成孤立方块 —— 看着像断链，其实拓扑是通的。
//
// 节点坐标**按拓扑分层算**，不再按数组下标摆：下标顺序与拓扑无关，图一有分支/汇合，
// 边就会横穿画面（`general → aggregate` 会从 `gate` 上方掠过）。
// --------------------------------------------------------------------------- //

const X_GAP = 190;
const Y_GAP = 90;

/**
 * 拓扑分层布局（Kahn 最长路径）。纯函数。
 *
 * 入度为 0 的节点落在第 0 层，其余节点取「所有前驱层号的最大值 + 1」；同层节点垂直并排、
 * 以该层中线对齐。成环时剩余节点挂在最大层之后 —— 拓扑运行期不可编辑，界面不必为不可达图
 * 做特殊表达，但**不能**因此死循环或丢节点。
 */
function layeredPositions(
  names: string[],
  links: [string, string][],
): Map<string, { x: number; y: number }> {
  const rank = new Map<string, number>(names.map((n) => [n, 0]));
  const indegree = new Map<string, number>(names.map((n) => [n, 0]));
  const outgoing = new Map<string, string[]>(names.map((n) => [n, []]));
  for (const [from, to] of links) {
    if (from === to || !rank.has(from) || !rank.has(to)) continue;
    outgoing.get(from)!.push(to);
    indegree.set(to, (indegree.get(to) ?? 0) + 1);
  }

  const settled = new Set<string>();
  const queue = names.filter((n) => (indegree.get(n) ?? 0) === 0);
  for (const n of queue) settled.add(n);
  while (queue.length > 0) {
    const node = queue.shift() as string;
    for (const next of outgoing.get(node) ?? []) {
      rank.set(next, Math.max(rank.get(next) ?? 0, (rank.get(node) ?? 0) + 1));
      indegree.set(next, (indegree.get(next) ?? 0) - 1);
      if ((indegree.get(next) ?? 0) === 0 && !settled.has(next)) {
        settled.add(next);
        queue.push(next);
      }
    }
  }

  let tail = names.reduce((max, n) => Math.max(max, rank.get(n) ?? 0), 0);
  for (const node of names) {
    if (!settled.has(node)) {
      tail += 1;
      rank.set(node, tail);
    }
  }

  const byRank = new Map<number, string[]>();
  for (const node of names) {
    const r = rank.get(node) ?? 0;
    const bucket = byRank.get(r);
    if (bucket) bucket.push(node);
    else byRank.set(r, [node]);
  }

  const positions = new Map<string, { x: number; y: number }>();
  for (const [r, members] of byRank) {
    const offset = ((members.length - 1) * Y_GAP) / 2;
    members.forEach((node, i) => {
      positions.set(node, { x: r * X_GAP, y: i * Y_GAP - offset });
    });
  }
  return positions;
}

/** 定义文档声明的**真实**节点（合成端点不在此列）。 */
const declaredNodes = computed<string[]>(() => envelope.value?.derived.nodes ?? []);

/** 图的全部连线：普通边 + 条件边的每个分支（仅供分层用，不区分线型）。 */
const graphLinks = computed<[string, string][]>(() => {
  const links: [string, string][] = [];
  for (const e of envelope.value?.derived.edges ?? []) links.push([e.from_node, e.to_node]);
  for (const ce of envelope.value?.derived.conditional_edges ?? []) {
    for (const [, target] of ce.branch_map) links.push([ce.from_node, target]);
  }
  return links;
});

/** 节点集合 = 声明节点 ∪ 只出现在边端点里的合成端点（`START` / `END`）。 */
const graphNodeNames = computed<string[]>(() => {
  const declared = declaredNodes.value;
  const seen = new Set(declared);
  const extra: string[] = [];
  for (const [from, to] of graphLinks.value) {
    for (const name of [from, to]) {
      if (!seen.has(name)) {
        seen.add(name);
        extra.push(name);
      }
    }
  }
  return [...declared, ...extra];
});

/** 编排图**只读**渲染：节点 + 普通边（实线）+ 条件边（虚线带分支标签）。 */
const graphNodes = computed<Node[]>(() => {
  const names = graphNodeNames.value;
  const declared = new Set(declaredNodes.value);
  const positions = layeredPositions(names, graphLinks.value);
  return names.map((name) => ({
    id: name,
    position: positions.get(name) ?? { x: 0, y: 0 },
    data: { label: name },
    // 合成端点单独一个 class：它不是可编排节点，只是图的入口 / 出口。
    class: declared.has(name) ? '' : 'graph-endpoint',
    draggable: false,
    connectable: false,
  }));
});

const graphEdges = computed<Edge[]>(() => {
  const edges: Edge[] = [];
  // 普通边：实线、无标签 —— 无条件转移，不存在「走哪条分支」的问题。
  for (const e of envelope.value?.derived.edges ?? []) {
    edges.push({
      id: `plain:${e.from_node}->${e.to_node}`,
      source: e.from_node,
      target: e.to_node,
      animated: false,
    });
  }
  // 条件边：虚线 + 分支标签 —— 与普通边必须在视觉上可区分，否则看不出哪条是「择一」。
  for (const ce of envelope.value?.derived.conditional_edges ?? []) {
    for (const [branchKey, target] of ce.branch_map) {
      edges.push({
        id: `cond:${ce.from_node}->${target}:${branchKey}`,
        source: ce.from_node,
        target,
        label: branchKey,
        style: { strokeDasharray: '5 3' },
        animated: false,
      });
    }
  }
  return edges;
});

async function load(): Promise<void> {
  phase.value = 'loading';
  banner.value = '';
  errorItems.value = [];
  try {
    const data = await props.client.definitionConfig();
    envelope.value = data;
    draft.value = structuredClone(data.document);
    baseHash.value = data.document.content_hash;
    dirty.value = false;
    phase.value = 'ready';
  } catch (err) {
    if (err instanceof ApiClientError) {
      if (err.status === 401) {
        emit('unauthorized');
        return;
      }
      if (err.status === 403) {
        phase.value = 'forbidden';
        banner.value = err.message;
        return;
      }
      // 503（fail-closed）：定义文档不可读 —— 显式显示「不可用」，绝不显示空表单。
      phase.value = 'unavailable';
      banner.value = err.message;
      return;
    }
    phase.value = 'unavailable';
    banner.value = '定义文档载入失败';
  }
}

onMounted(() => {
  void load();
  void loadPrompts();
  void loadStorageState();
});

function markDirty(): void {
  dirty.value = true;
  banner.value = '';
  errorItems.value = [];
}

function splitList(text: string): string[] {
  return text
    .split(/[,，\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function joinList(items: string[]): string {
  return items.join(', ');
}

function grantFor(expertName: string): string {
  const grant = draft.value?.tool_grants.find((g) => g.expert_name === expertName);
  return grant ? joinList(grant.tool_names) : '';
}

// --------------------------------------------------------------------------- //
// REV-16-2：工具授权**勾选** + 工具参数取值（ADR-30 / IFC-IB-350）
//
// 勾选**只作用于既有工具集合**（名单由后端 `available_tools` 给出，与装配期校验同源），
// 不新增工具本体。参数取值以**限定名**（`<tool>.<param>`）存入定义文档，与后端规格同键，
// 避免「同名参数跨工具串味」。
// --------------------------------------------------------------------------- //

function grantOf(expertName: string): ToolGrantSpec | undefined {
  return draft.value?.tool_grants.find((g) => g.expert_name === expertName);
}

/** 勾选清单 = 既有工具 ∪ 文档里已勾（后者防「后端名单缺项」把既有授权渲染丢）。 */
function grantChecklist(expertName: string): string[] {
  const granted = grantOf(expertName)?.tool_names ?? [];
  const names = [...availableTools.value];
  for (const t of granted) if (!names.includes(t)) names.push(t);
  return names;
}

function isToolGranted(expertName: string, tool: string): boolean {
  return (grantOf(expertName)?.tool_names ?? []).includes(tool);
}

function toggleTool(expertName: string, tool: string, checked: boolean): void {
  if (!draft.value) return;
  let grant = grantOf(expertName);
  if (!grant) {
    grant = { expert_name: expertName, tool_names: [], param_values: [] };
    draft.value.tool_grants.push(grant);
  }
  const set = new Set(grant.tool_names);
  if (checked) set.add(tool);
  else set.delete(tool);
  grant.tool_names = [...set];
  // 既无授权也无参数的条目**不留空壳**（否则白名单校验会收到无意义条目）。
  if (!grant.tool_names.length && !(grant.param_values ?? []).length) {
    draft.value.tool_grants = draft.value.tool_grants.filter((g) => g !== grant);
  }
  markDirty();
}

function bareParam(qualified: string): string {
  const dot = qualified.indexOf('.');
  return dot < 0 ? qualified : qualified.slice(dot + 1);
}

function paramsForTool(tool: string): ToolParamSpec[] {
  return toolParamSpecs.value.filter((s) => s.name.startsWith(`${tool}.`));
}

function paramValueOf(expertName: string, qualified: string): string {
  const pv = grantOf(expertName)?.param_values?.find((p) => p.name === qualified);
  return pv?.value ?? '';
}

function setParamValue(expertName: string, qualified: string, value: string): void {
  if (!draft.value) return;
  let grant = grantOf(expertName);
  if (!grant) {
    grant = { expert_name: expertName, tool_names: [], param_values: [] };
    draft.value.tool_grants.push(grant);
  }
  if (!grant.param_values) grant.param_values = [];
  const existing = grant.param_values.find((p) => p.name === qualified);
  if (value.trim() === '') {
    // 清空 ⇒ 移除该取值（回落工具自身默认；不写空串冒充「已配置」）。
    grant.param_values = grant.param_values.filter((p) => p.name !== qualified);
  } else if (existing) {
    existing.value = value;
  } else {
    grant.param_values.push({ name: qualified, value });
  }
  markDirty();
}

function setDefaultExpert(name: string): void {
  if (!draft.value) return;
  for (const e of draft.value.experts) e.is_default = e.name === name;
  draft.value.route.default_expert = name;
  markDirty();
}

function addExpert(): void {
  if (!draft.value) return;
  // 仅新增**专家集合**成员（REQ-FUNC-IB-26：专家集合可编辑）；**不**新增图节点（拓扑不可编辑）。
  const names = new Set(draft.value.experts.map((e) => e.name));
  let idx = 1;
  let name = 'new-expert';
  while (names.has(name)) name = `new-expert-${++idx}`;
  draft.value.experts.push({
    name,
    cn_label: '新专家',
    keywords: [],
    exemplars: [],
    is_data_expert: false,
    fallback_prompt: '请填写该专家的兜底提示。',
    is_delegating: false,
    is_default: false,
  });
  markDirty();
}

function removeExpert(name: string): void {
  if (!draft.value) return;
  draft.value.experts = draft.value.experts.filter((e) => e.name !== name);
  draft.value.tool_grants = draft.value.tool_grants.filter((g) => g.expert_name !== name);
  markDirty();
}

async function save(): Promise<void> {
  if (!draft.value || saving.value) return;
  saving.value = true;
  banner.value = '';
  errorItems.value = [];
  try {
    const result = await props.client.saveDefinition(draft.value, baseHash.value);
    baseHash.value = result.content_hash;
    dirty.value = false;
    await load(); // **以文档为准**刷新（AC-IB-17-03），绝不用陈旧视图反向覆盖
    banner.value = '已保存。专家 / 路由 / 编排变更自**下次装配**生效（图编译一次常驻）。';
  } catch (err) {
    if (err instanceof ApiClientError) {
      if (err.status === 401) {
        emit('unauthorized');
        return;
      }
      if (err.status === 409) {
        banner.value = '定义文档已被他处修改（409 冲突）；已保留你的草稿，请重新载入后再提交。';
        return;
      }
      if (err.status === 400) {
        const items = (err.details.items as { path: string; code: string; message: string }[]) ?? [];
        errorItems.value = items;
        banner.value = items.length ? '校验不通过（服务端为唯一裁决者）：' : err.message;
        return;
      }
      banner.value = err.message;
      return;
    }
    banner.value = '保存失败';
  } finally {
    saving.value = false;
  }
}

// --------------------------------------------------------------------------- //
// REV-16-2：提示词域（独立提示词目录）—— 分层编辑器（IFC-IB-352 / 354）
//
// 与定义文档域**各自独立的草稿 / 基线哈希**：两域真源不同、合并发生在装配期，混用草稿会把
// 「提示词保存」误判成「文档冲突」。
//
// 视图侧仍**零持久化**：只持有内存草稿；每次进页从服务端重新拉取（含各层正文与哈希）。
// --------------------------------------------------------------------------- //

type LayerTexts = { main: string; fallback: string };

/** 分层顺序（与后端 `_PROMPT_LAYERS` 同序）：主在前、兜底在后。 */
const PROMPT_LAYERS: PromptLayer[] = ['main', 'fallback'];

const promptEnvelope = ref<PromptListEnvelope | null>(null);
const promptPhase = ref<Phase>('loading');
const promptTexts = ref<Record<string, LayerTexts>>({});
/** 乐观并发基线（逐专家逐层）：PUT 时携带，服务端不一致即 409（不静默覆盖）。 */
const promptHashes = ref<Record<string, LayerTexts>>({});
const promptDirty = ref<Record<string, boolean>>({});
const promptSaving = ref(false);
const promptBanner = ref('');
const promptErrors = ref<{ path: string; code: string; message: string }[]>([]);

// --------------------------------------------------------------------------- //
// REV-16-4（IFC-IB-361 / 362 / 363）：存储态**非静默**提示
//
// 「配置仅内存生效、不跨重启保留」必须**显式渲染**（不得静默）。单一来源 = 服务端
// 装配期**实际选用**的存储实现（`GET /api/config/storage-state`，ADR-35）——
// 本页**不**从任何环境变量自行推断存储态（否则「实际跑在内存替身」与「界面自称文件态」
// 可能不一致，正是 GAP-R16-03 要消除的静默失效）。
// --------------------------------------------------------------------------- //

const storageState = ref<StorageState | null>(null);
const storageBanner = ref('');

/** 任一域为 `memory` ⇒ 必须提示（IFC-IB-363 / AC-IB-33-02）。 */
const memoryNotice = computed<boolean>(() => {
  const s = storageState.value;
  if (s === null) return false;
  return s.definition_store === 'memory' || s.prompt_store === 'memory';
});

/** 处于内存态的域（用于提示文案；**不含**任何路径值 / 键值）。 */
const memoryDomains = computed<string>(() => {
  const s = storageState.value;
  if (s === null) return '';
  const parts: string[] = [];
  if (s.definition_store === 'memory') parts.push('定义文档');
  if (s.prompt_store === 'memory') parts.push('提示词');
  return parts.join(' / ');
});

async function loadStorageState(): Promise<void> {
  storageBanner.value = '';
  try {
    storageState.value = await props.client.storageState();
  } catch (err) {
    // fail-closed：读不到存储态**绝不**静默当作「文件态」——给出一条显式提示。
    storageState.value = null;
    if (err instanceof ApiClientError && err.status === 401) {
      emit('unauthorized');
      return;
    }
    storageBanner.value = err instanceof ApiClientError ? err.message : '存储态读取失败';
  }
}

const promptExperts = computed<PromptExpertEntry[]>(() => promptEnvelope.value?.experts ?? []);
const availableTools = computed<string[]>(() => promptEnvelope.value?.available_tools ?? []);
const toolParamSpecs = computed<ToolParamSpec[]>(() => promptEnvelope.value?.tool_param_specs ?? []);
const promptKeyNames = computed<string[]>(() => promptEnvelope.value?.config_key_names ?? []);

function layerText(expertName: string, layer: PromptLayer): string {
  return promptTexts.value[expertName]?.[layer] ?? '';
}

function isPromptDirty(expertName: string, layer: PromptLayer): boolean {
  return Boolean(promptDirty.value[`${expertName}:${layer}`]);
}

function setPromptText(expertName: string, layer: PromptLayer, value: string): void {
  const current = promptTexts.value[expertName] ?? { main: '', fallback: '' };
  current[layer] = value;
  promptTexts.value[expertName] = current;
  promptDirty.value = { ...promptDirty.value, [`${expertName}:${layer}`]: true };
  promptBanner.value = '';
  promptErrors.value = [];
}

/**
 * 回退链的**当前生效层**（US-IB-30）：主 > 兜底文件 > 定义文档兜底。
 *
 * 必须可见 —— 只显示两个文本框时，用户存了主提示词却因未保存兜底而「看不出哪层在生效」。
 */
function resolvedFrom(expertName: string): string {
  const entry = promptExperts.value.find((e) => e.name === expertName);
  if (!entry) return '';
  if (entry.layers.main.exists) return 'main_file';
  if (entry.layers.fallback.exists) return 'fallback_file';
  return 'definition_doc_fallback';
}

const RESOLVED_LABEL: Record<string, string> = {
  main_file: '当前生效 = 主提示词',
  fallback_file: '主提示词缺失，当前生效 = 兜底提示词',
  definition_doc_fallback: '提示词目录无该专家，当前生效 = 定义文档兜底',
};

async function loadPrompts(): Promise<void> {
  promptPhase.value = 'loading';
  promptBanner.value = '';
  promptErrors.value = [];
  try {
    const data = await props.client.promptList();
    promptEnvelope.value = data;
    const texts: Record<string, LayerTexts> = {};
    const hashes: Record<string, LayerTexts> = {};
    for (const entry of data.experts) {
      const text: LayerTexts = { main: '', fallback: '' };
      const hash: LayerTexts = { main: '', fallback: '' };
      for (const layer of PROMPT_LAYERS) {
        const meta = entry.layers[layer];
        hash[layer] = meta?.content_hash ?? '';
        if (meta?.exists) {
          try {
            const got = await props.client.promptLayer(entry.name, layer);
            text[layer] = got.content;
            hash[layer] = got.content_hash;
          } catch {
            // 单层读取失败按空处理：**不臆造正文**（空文本框 + 下方错误提示）。
          }
        }
      }
      texts[entry.name] = text;
      hashes[entry.name] = hash;
    }
    promptTexts.value = texts;
    promptHashes.value = hashes;
    promptDirty.value = {};
    promptPhase.value = 'ready';
  } catch (err) {
    if (err instanceof ApiClientError) {
      if (err.status === 401) {
        emit('unauthorized');
        return;
      }
      // 404（可视化配置总开关关闭）/ 503（fail-closed）→ 显式「不可用」，绝不显示空编辑器。
      promptPhase.value = 'unavailable';
      promptBanner.value = err.message;
      return;
    }
    promptPhase.value = 'unavailable';
    promptBanner.value = '提示词域载入失败';
  }
}

async function savePromptLayer(expertName: string, layer: PromptLayer): Promise<void> {
  if (promptSaving.value) return;
  promptSaving.value = true;
  promptBanner.value = '';
  promptErrors.value = [];
  try {
    const result = await props.client.savePromptLayer(
      expertName,
      layer,
      layerText(expertName, layer),
      promptHashes.value[expertName]?.[layer] ?? '',
    );
    if (!result.saved) {
      if (result.conflict) {
        promptBanner.value =
          '该层已被他处修改（409 冲突）；已保留你的草稿，请重新载入后再提交。';
        return;
      }
      promptErrors.value = result.errors.map((e) => ({
        path: e.path,
        code: e.code,
        message: e.message,
      }));
      promptBanner.value = promptErrors.value.length
        ? '提示词校验不通过（服务端为唯一裁决者）：'
        : '提示词未保存';
      return;
    }
    const hash = promptHashes.value[expertName] ?? { main: '', fallback: '' };
    hash[layer] = result.content_hash;
    promptHashes.value[expertName] = hash;
    promptDirty.value = { ...promptDirty.value, [`${expertName}:${layer}`]: false };
    // **生效口径显式提示（强制）**：保存只原子落盘，重启后装配期才重新合并（ADR-32 / C-IB-40）。
    promptBanner.value = '保存成功；重启 `ib-web` / `ib-worker` 后生效（保存仅原子落盘，不热重载）。';
  } catch (err) {
    if (err instanceof ApiClientError) {
      if (err.status === 401) {
        emit('unauthorized');
        return;
      }
      if (err.status === 403) {
        promptBanner.value = '当前主体无配置管理权限（403）。';
        return;
      }
      if (err.status === 404) {
        promptBanner.value = '该专家或提示词层不存在。';
        return;
      }
      promptBanner.value = err.message;
      return;
    }
    promptBanner.value = '提示词保存失败';
  } finally {
    promptSaving.value = false;
  }
}
</script>

<template>
  <section class="config">
    <header class="bar">
      <h2>可视化配置（定义文档 · 单一真源）</h2>
      <button type="button" :disabled="saving" @click="load">重新载入</button>
    </header>

    <!-- REV-16-4（IFC-IB-363）：内存态**非静默**提示（任一 store == "memory"）。 -->
    <p v-if="memoryNotice" class="notice notice-warn">
      注意：{{ memoryDomains }}配置**仅内存生效、不跨重启保留** ——
      服务重启后重新装配将回到种子默认（未配置文件存储路径）。保存与生效口径不变：
      保存仅原子落盘，需**重启服务重新装配**后生效（不热重载）。
    </p>
    <p v-else-if="storageBanner" class="notice notice-warn">
      存储态读取失败（fail-closed，**不静默当作文件态**）：{{ storageBanner }}
    </p>

    <p v-if="banner" class="notice">{{ banner }}</p>
    <ul v-if="errorItems.length" class="errors">
      <li v-for="item in errorItems" :key="`${item.path}:${item.code}`">
        <code>{{ item.path }}</code> [{{ item.code }}] {{ item.message }}
      </li>
    </ul>

    <p v-if="phase === 'unavailable'" class="blocked">
      定义文档当前不可读（服务端 fail-closed：为满足单一真源纪律，**不返回空文档**）。
      请检查部署端定义文档路径后重试。
    </p>
    <p v-else-if="phase === 'forbidden'" class="blocked">当前主体无配置管理权限（403）。</p>
    <p v-else-if="phase === 'loading'">载入中…</p>

    <template v-if="phase === 'ready' && draft">
      <p v-if="dirty" class="draft-flag">草稿未提交（可丢弃）—— 本页不保存任何内容，唯一真源是服务端定义文档。</p>

      <h3>编排图（只读）</h3>
      <p class="hint">
        节点与边由定义文档派生，**运行期不可编辑**（无增删节点 / 改边入口）。
        拓扑变更路径 = 改定义文档 → 装配期校验 → 重新编译。
      </p>
      <p class="legend">
        <span class="legend-item"><span class="legend-line solid"></span>普通边（无条件转移）</span>
        <span class="legend-item"><span class="legend-line dashed"></span>条件边（按分支键择一）</span>
        <span class="legend-item"><span class="legend-box"></span>START / END（合成端点，非可编排节点）</span>
      </p>
      <div class="graph">
        <VueFlow
          :nodes="graphNodes"
          :edges="graphEdges"
          :nodes-draggable="false"
          :nodes-connectable="false"
          :elements-selectable="false"
          fit-view-on-init
        />
      </div>

      <h3>路由参数</h3>
      <div class="grid">
        <label>
          语义阈值 tau
          <input
            v-model.number="draft.route.tau"
            type="number"
            step="0.01"
            :disabled="!canEdit('route.tau')"
            @change="markDirty"
          />
        </label>
        <label>
          并列裕度 margin
          <input
            v-model.number="draft.route.margin"
            type="number"
            step="0.01"
            :disabled="!canEdit('route.margin')"
            @change="markDirty"
          />
        </label>
        <label>
          专家步数上限
          <input
            v-model.number="draft.route.max_expert_steps"
            type="number"
            min="1"
            :disabled="!canEdit('route.max_expert_steps')"
            @change="markDirty"
          />
        </label>
      </div>

      <h3>专家集合</h3>
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>中文标签</th>
            <th>关键词</th>
            <th>示例句</th>
            <th>数据专家</th>
            <th>可委托</th>
            <th>默认</th>
            <th>工具授权</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="expert in draft.experts" :key="expert.name">
            <td>
              <input
                v-model="expert.name"
                :disabled="!canEdit('experts[].name')"
                @change="markDirty"
              />
            </td>
            <td>
              <input
                v-model="expert.cn_label"
                :disabled="!canEdit('experts[].cn_label')"
                @change="markDirty"
              />
            </td>
            <td>
              <input
                :value="joinList(expert.keywords)"
                :disabled="!canEdit('experts[].keywords')"
                @change="((expert.keywords = splitList(($event.target as HTMLInputElement).value)), markDirty())"
              />
            </td>
            <td>
              <input
                :value="joinList(expert.exemplars)"
                :disabled="!canEdit('experts[].exemplars')"
                @change="((expert.exemplars = splitList(($event.target as HTMLInputElement).value)), markDirty())"
              />
            </td>
            <td>
              <input
                v-model="expert.is_data_expert"
                type="checkbox"
                :disabled="!canEdit('experts[].is_data_expert')"
                @change="markDirty"
              />
            </td>
            <td>
              <input
                v-model="expert.is_delegating"
                type="checkbox"
                :disabled="!canEdit('experts[].is_delegating')"
                @change="markDirty"
              />
            </td>
            <td>
              <input
                type="radio"
                name="default-expert"
                :checked="expert.is_default"
                :disabled="!canEdit('experts[].is_default')"
                @change="setDefaultExpert(expert.name)"
              />
            </td>
            <td>
              <span v-if="!canEdit('tool_grants[].tool_names')">{{ grantFor(expert.name) }}</span>
              <template v-else>
                <label
                  v-for="tool in grantChecklist(expert.name)"
                  :key="`${expert.name}:${tool}`"
                  class="tool-check"
                >
                  <input
                    type="checkbox"
                    :checked="isToolGranted(expert.name, tool)"
                    @change="
                      toggleTool(
                        expert.name,
                        tool,
                        ($event.target as HTMLInputElement).checked,
                      )
                    "
                  />
                  {{ tool }}
                </label>
              </template>
            </td>
            <td>
              <button type="button" class="link" @click="removeExpert(expert.name)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <button type="button" @click="addExpert">添加专家</button>

      <h3>工具参数（既有工具的可配参数；留空即用工具默认）</h3>
      <p class="hint">
        参数规格由**既有工具声明**派生（不新增工具本体）。取值随定义文档保存，
        **调用方显式实参优先**；重启后装配期注入生效。
      </p>
      <div v-for="expert in draft.experts" :key="`tp-${expert.name}`" class="tool-params">
        <strong>{{ expert.name }}</strong>
        <span v-if="!grantChecklist(expert.name).length" class="hint">（无既有工具）</span>
        <div
          v-for="tool in grantChecklist(expert.name).filter((t) => paramsForTool(t).length)"
          :key="`tp-${expert.name}-${tool}`"
          class="tool-param-group"
        >
          <span class="tool-param-tool">{{ tool }}</span>
          <label v-for="spec in paramsForTool(tool)" :key="spec.name" class="tool-param">
            {{ bareParam(spec.name) }}
            <select
              v-if="spec.choices && spec.choices.length"
              :value="paramValueOf(expert.name, spec.name)"
              :disabled="!canEdit('tool_grants[].param_values')"
              @change="setParamValue(expert.name, spec.name, ($event.target as HTMLSelectElement).value)"
            >
              <option value="">（工具默认：{{ spec.default || '无' }}）</option>
              <option v-for="choice in spec.choices" :key="choice" :value="choice">
                {{ choice }}
              </option>
            </select>
            <input
              v-else-if="spec.type === 'bool'"
              type="checkbox"
              :checked="paramValueOf(expert.name, spec.name) === 'true'"
              :disabled="!canEdit('tool_grants[].param_values')"
              @change="
                setParamValue(
                  expert.name,
                  spec.name,
                  ($event.target as HTMLInputElement).checked ? 'true' : 'false',
                )
              "
            />
            <input
              v-else-if="spec.type === 'int' || spec.type === 'float'"
              type="number"
              :step="spec.type === 'int' ? '1' : 'any'"
              :min="spec.minimum ?? undefined"
              :max="spec.maximum ?? undefined"
              :placeholder="spec.default"
              :value="paramValueOf(expert.name, spec.name)"
              :disabled="!canEdit('tool_grants[].param_values')"
              @change="setParamValue(expert.name, spec.name, ($event.target as HTMLInputElement).value)"
            />
            <input
              v-else
              type="text"
              :placeholder="spec.default"
              :value="paramValueOf(expert.name, spec.name)"
              :disabled="!canEdit('tool_grants[].param_values')"
              @change="setParamValue(expert.name, spec.name, ($event.target as HTMLInputElement).value)"
            />
          </label>
        </div>
      </div>

      <h3>定义文档兜底提示（终级回退：提示词目录两层皆缺时生效）</h3>
      <div v-for="expert in draft.experts" :key="`p-${expert.name}`" class="prompt">
        <label>
          {{ expert.name }}
          <textarea
            v-model="expert.fallback_prompt"
            :disabled="!canEdit('experts[].fallback_prompt')"
            rows="3"
            @change="markDirty"
          />
        </label>
      </div>

      <h3>提示词分层（独立提示词目录 · 与定义文档分属两个真源）</h3>
      <p v-if="promptPhase === 'unavailable'" class="blocked">
        提示词域当前不可用（可视化配置总开关关闭或服务端 fail-closed）。请检查部署后重试。
      </p>
      <p v-else-if="promptPhase === 'loading'">提示词载入中…</p>
      <template v-else-if="promptEnvelope">
        <p class="hint">
          主提示词可缺、兜底不得缺；主缺失时**自动回退兜底**。保存**不热重载** ——
          重启 <code>ib-web</code> / <code>ib-worker</code> 后装配期才重新合并生效（ADR-32）。
        </p>
        <p class="hint">
          目录口径：<code>{{ promptEnvelope.layout.file_pattern }}</code>（
          {{ promptEnvelope.layout.naming_rule }}）
        </p>
        <p v-if="promptBanner" class="notice">{{ promptBanner }}</p>
        <ul v-if="promptErrors.length" class="errors">
          <li v-for="item in promptErrors" :key="`${item.path}:${item.code}`">
            <code>{{ item.path }}</code> [{{ item.code }}] {{ item.message }}
          </li>
        </ul>
        <div v-for="expert in promptExperts" :key="`pl-${expert.name}`" class="prompt">
          <div class="prompt-head">
            <strong>{{ expert.cn_label || expert.name }}</strong>
            <code>{{ expert.name }}</code>
            <span class="resolved">{{ RESOLVED_LABEL[resolvedFrom(expert.name)] }}</span>
          </div>
          <label v-for="layer in PROMPT_LAYERS" :key="`${expert.name}:${layer}`">
            {{ layer === 'main' ? '主提示词' : '兜底提示词' }}
            <span v-if="isPromptDirty(expert.name, layer)" class="draft-flag-inline">未保存</span>
            <span v-else-if="!expert.layers[layer].exists" class="hint">（文件不存在）</span>
            <textarea
              :value="layerText(expert.name, layer)"
              rows="3"
              @input="
                setPromptText(expert.name, layer, ($event.target as HTMLTextAreaElement).value)
              "
            />
            <button
              type="button"
              :disabled="promptSaving || !isPromptDirty(expert.name, layer)"
              @click="savePromptLayer(expert.name, layer)"
            >
              保存{{ layer === 'main' ? '主' : '兜底' }}提示词
            </button>
          </label>
        </div>
        <h3>提示词配置键（只登记键名，不回显值）</h3>
        <ul class="keys">
          <li v-for="key in promptKeyNames" :key="`pk-${key}`"><code>{{ key }}</code></li>
        </ul>
      </template>

      <h3>配置键（只登记键名，不回显值）</h3>
      <ul class="keys">
        <li v-for="key in keyNames" :key="key"><code>{{ key }}</code></li>
      </ul>

      <div class="actions">
        <button type="button" :disabled="saving" @click="save">保存并回写</button>
        <span class="hint">服务端校验器（IFC-IB-290）为唯一裁决者；界面预校验仅作提示。</span>
      </div>
    </template>
  </section>
</template>

<style scoped>
.config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
h3 {
  margin: 12px 0 4px;
}
.hint {
  color: #57606a;
  font-size: 13px;
}
.notice {
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 6px;
  padding: 8px 12px;
}
/* REV-16-4（IFC-IB-363）：常驻的内存态提示 —— 虚线边框与保存提示条区分，表明「状态」而非「一次性反馈」。 */
.notice-warn {
  border-style: dashed;
  font-weight: 600;
}
.draft-flag {
  background: #ddf4ff;
  border: 1px solid #0969da;
  border-radius: 6px;
  padding: 8px 12px;
  color: #0969da;
}
.errors {
  background: #ffebe9;
  border: 1px solid #cf222e;
  border-radius: 6px;
  padding: 8px 12px 8px 28px;
  color: #cf222e;
}
.blocked {
  background: #fff1e5;
  border: 1px solid #bc4c00;
  border-radius: 6px;
  padding: 8px 12px;
}
.graph {
  height: 280px;
  border: 1px solid #d8dee4;
  border-radius: 6px;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin: 0 0 8px;
  font-size: 12px;
  color: #57606a;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.legend-line {
  display: inline-block;
  width: 26px;
  border-top: 2px solid #6b7280;
}
.legend-line.dashed {
  border-top-style: dashed;
}
.legend-box {
  display: inline-block;
  width: 16px;
  height: 12px;
  border: 1px dashed #6b7280;
  border-radius: 3px;
}
/* 节点元素由 Vue Flow 在运行期创建，scoped 样式需经 :deep 才能命中自定义 class。 */
.graph :deep(.graph-endpoint) {
  border-style: dashed;
  background: #f6f8fa;
  color: #57606a;
}
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.grid label {
  display: flex;
  flex-direction: column;
  font-size: 13px;
  gap: 4px;
}
table {
  border-collapse: collapse;
  width: 100%;
}
th,
td {
  border: 1px solid #d8dee4;
  padding: 4px 6px;
  font-size: 13px;
}
th {
  background: #f6f8fa;
}
td input {
  width: 100%;
}
.prompt label {
  display: flex;
  flex-direction: column;
  font-size: 13px;
  gap: 4px;
}
.prompt textarea {
  width: 100%;
}
.prompt-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.resolved {
  background: #ddf4ff;
  border-radius: 4px;
  padding: 1px 6px;
  color: #0969da;
}
.draft-flag-inline {
  color: #bc4c00;
  font-size: 12px;
}
.tool-check {
  display: block;
  font-size: 13px;
  white-space: nowrap;
}
.tool-params {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}
.tool-param-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding-left: 12px;
}
.tool-param-tool {
  font-size: 12px;
  color: #57606a;
}
.tool-param {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}
.keys code {
  background: #f6f8fa;
  border-radius: 4px;
  padding: 1px 6px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}
button.link {
  background: none;
  border: none;
  color: #cf222e;
  cursor: pointer;
}
</style>
