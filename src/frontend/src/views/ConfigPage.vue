<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-296（R7 可视化配置页约束；REQ-FUNC-IB-25 主 / IB-26 并列主）
 * @depends MOD-IB-23（IFC-IB-294 / 295；**仅** HTTP 契约，不 import 任何后端模块）
 * @author software-developer
 *
 * 可视化配置页：定义文档（专家 / 路由 / 编排 / 工具授权）的**只读图渲染** + **白名单表单**。
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

/** 编排图**只读**渲染：节点 + 条件边（按 `branch_map` 表达分支可达性）。 */
const graphNodes = computed<Node[]>(() => {
  const names = envelope.value?.derived.nodes ?? [];
  return names.map((name, index) => ({
    id: name,
    position: { x: index * 170, y: index % 2 === 0 ? 40 : 130 },
    data: { label: name },
    draggable: false,
    connectable: false,
  }));
});

const graphEdges = computed<Edge[]>(() => {
  const edges: Edge[] = [];
  for (const ce of envelope.value?.derived.conditional_edges ?? []) {
    for (const [branchKey, target] of ce.branch_map) {
      edges.push({
        id: `${ce.from_node}->${target}:${branchKey}`,
        source: ce.from_node,
        target,
        label: branchKey,
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

onMounted(load);

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

function setGrant(expertName: string, text: string): void {
  if (!draft.value) return;
  const names = splitList(text);
  const existing = draft.value.tool_grants.find((g) => g.expert_name === expertName);
  if (existing) existing.tool_names = names;
  else draft.value.tool_grants.push({ expert_name: expertName, tool_names: names });
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
</script>

<template>
  <section class="config">
    <header class="bar">
      <h2>可视化配置（定义文档 · 单一真源）</h2>
      <button type="button" :disabled="saving" @click="load">重新载入</button>
    </header>

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
        节点与条件边由定义文档派生，**运行期不可编辑**（无增删节点 / 改边入口）。
        拓扑变更路径 = 改定义文档 → 装配期校验 → 重新编译。
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
              <input
                :value="grantFor(expert.name)"
                :disabled="!canEdit('tool_grants[].tool_names')"
                @change="setGrant(expert.name, ($event.target as HTMLInputElement).value)"
              />
            </td>
            <td>
              <button type="button" class="link" @click="removeExpert(expert.name)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <button type="button" @click="addExpert">添加专家</button>

      <h3>兜底提示</h3>
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
