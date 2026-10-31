<script setup lang="ts">
/**
 * @module MOD-R26-19
 * @implements REQ-FUNC-002/005/006/007/008/009 详情面板：提示词全文（只读 / 可编辑取决于档位）、关键词、
 *             工具授权与参数、知识范围、最大步数、停用 / 删除（默认专家受保护）、路由参数。
 * 提示词一律在 <textarea> / 文本插值中展示，不执行；只读档没有任何保存控件。
 */
import { ref, watch } from 'vue';

import type { ApiClient, ConfigCatalogDto, DefinitionDocumentV2, GraphNodeDto } from '../../api/client';
import { DEFAULT_EXPERT_HINT } from './nodeRemoval'; // MOD-R27-05

const props = defineProps<{
  client: ApiClient;
  doc: DefinitionDocumentV2;
  catalog: ConfigCatalogDto | null;
  node: GraphNodeDto | null;
  readonly: boolean;
  promptPatch: Record<string, { main?: string | null; fallback?: string | null }>;
}>();
const emit = defineEmits<{
  (e: 'change', doc: DefinitionDocumentV2): void;
  (e: 'prompt', expert: string, layer: 'main' | 'fallback', text: string): void;
  (e: 'remove-agent', nodeId: string): void;
  (e: 'request-remove', nodeId: string): void;
  (e: 'update-node', node: GraphNodeDto): void;
}>();

type Layers = { main: string | null; fallback: string | null; source: string };
const layers = ref<Layers>({ main: null, fallback: null, source: '' });
const loadErr = ref('');

const expert = () => props.doc.experts.find((e) => e.name === (props.node?.expert ?? props.node?.id));

async function loadPrompts(): Promise<void> {
  const e = expert();
  layers.value = { main: null, fallback: null, source: '' };
  loadErr.value = '';
  if (!e || props.node?.kind !== 'agent') return;
  const patch = props.promptPatch[e.name] ?? {};
  for (const layer of ['main', 'fallback'] as const) {
    if (patch[layer] != null) {
      layers.value[layer] = patch[layer] as string;
      continue;
    }
    try {
      layers.value[layer] = (await props.client.promptLayer(e.name, layer)).content;
    } catch {
      layers.value[layer] = null; // 404 = 该层文件不存在
    }
  }
  const l = layers.value;
  layers.value.source = l.main?.trim() ? '生效来源：项目目录 main' : l.fallback?.trim() ? '生效来源：项目目录 fallback' : '两层皆缺（无法装配）';
}
watch(() => props.node?.id, loadPrompts, { immediate: true });

function patchExpert(fn: (e: NonNullable<ReturnType<typeof expert>>) => void): void {
  const copy = JSON.parse(JSON.stringify(props.doc)) as DefinitionDocumentV2;
  const e = copy.experts.find((x) => x.name === (props.node?.expert ?? props.node?.id));
  if (!e) return;
  fn(e);
  emit('change', copy);
}
function grantOf(copy: DefinitionDocumentV2, name: string) {
  let g = copy.tool_grants.find((x) => x.expert_name === name);
  if (!g) {
    g = { expert_name: name, tool_names: [], param_values: [] };
    copy.tool_grants.push(g);
  }
  return g;
}
function hasTool(tool: string): boolean {
  const e = expert();
  return !!props.doc.tool_grants.find((g) => g.expert_name === e?.name)?.tool_names.includes(tool);
}
function toggleTool(tool: string, on: boolean): void {
  const copy = JSON.parse(JSON.stringify(props.doc)) as DefinitionDocumentV2;
  const name = props.node?.expert ?? props.node?.id ?? '';
  const g = grantOf(copy, name);
  g.tool_names = on ? [...new Set([...g.tool_names, tool])] : g.tool_names.filter((t) => t !== tool);
  if (!on) g.param_values = (g.param_values ?? []).filter((p) => !p.name.startsWith(`${tool}.`));
  emit('change', copy);
}
function paramsFor(tool: string) {
  return (props.catalog?.tool_param_specs ?? []).filter((s) => s.name.startsWith(`${tool}.`));
}
function paramValue(specName: string): string {
  const name = expert()?.name;
  return props.doc.tool_grants.find((g) => g.expert_name === name)?.param_values?.find((p) => p.name === specName)?.value ?? '';
}
function setParam(specName: string, value: string): void {
  const copy = JSON.parse(JSON.stringify(props.doc)) as DefinitionDocumentV2;
  const g = grantOf(copy, props.node?.expert ?? props.node?.id ?? '');
  g.param_values = (g.param_values ?? []).filter((p) => p.name !== specName);
  if (value !== '') g.param_values.push({ name: specName, value });
  emit('change', copy);
}
function setRoute(key: 'tau' | 'margin' | 'max_expert_steps', value: number): void {
  const copy = JSON.parse(JSON.stringify(props.doc)) as DefinitionDocumentV2;
  (copy.route as Record<string, unknown>)[key] = value;
  emit('change', copy);
}
function setDefault(): void {
  const copy = JSON.parse(JSON.stringify(props.doc)) as DefinitionDocumentV2;
  const name = props.node?.expert ?? props.node?.id;
  copy.route.default_expert = name ?? '';
  for (const e of copy.experts) e.is_default = e.name === name;
  emit('change', copy);
}
function toggleFolder(id: string, on: boolean): void {
  patchExpert((e) => {
    const cur = new Set(e.knowledge_scope?.folder_ids ?? []);
    if (on) cur.add(id);
    else cur.delete(id);
    e.knowledge_scope = { mode: 'folders', folder_ids: [...cur] };
  });
}
function setScopeAll(all: boolean): void {
  patchExpert((e) => {
    e.knowledge_scope = all ? { mode: 'all', folder_ids: [] } : { mode: 'folders', folder_ids: e.knowledge_scope?.folder_ids ?? [] };
  });
}
function onPrompt(layer: 'main' | 'fallback', text: string): void {
  layers.value[layer] = text;
  emit('prompt', expert()?.name ?? '', layer, text);
}
</script>

<template>
  <div class="detail">
    <!-- 路由节点：全局路由参数 -->
    <template v-if="node?.kind === 'route'">
      <h4>路由参数</h4>
      <el-form label-width="150px" size="small">
        <el-form-item label="tau"><el-input-number :model-value="doc.route.tau" :min="0" :max="1" :step="0.01" :disabled="readonly" @change="(v: number) => setRoute('tau', v)" /></el-form-item>
        <el-form-item label="margin"><el-input-number :model-value="doc.route.margin" :min="0" :max="1" :step="0.01" :disabled="readonly" @change="(v: number) => setRoute('margin', v)" /></el-form-item>
        <el-form-item label="max_expert_steps"><el-input-number :model-value="doc.route.max_expert_steps" :min="1" :max="64" :disabled="readonly" @change="(v: number) => setRoute('max_expert_steps', v)" /></el-form-item>
      </el-form>
      <p class="hint">分类器 temperature 不可配置。</p>
      <div v-if="!readonly" class="actions">
        <el-button size="small" type="danger" plain @click="emit('request-remove', node.id)">删除节点</el-button>
      </div>
    </template>

    <!-- agent 节点 -->
    <template v-else-if="node?.kind === 'agent' && expert()">
      <h4>{{ expert()?.cn_label }}（{{ expert()?.name }}）</h4>
      <p v-if="readonly" class="hint">当前为“查看”档：以下内容只读。</p>
      <el-form label-width="110px" size="small">
        <el-form-item label="中文标签"><el-input :model-value="expert()?.cn_label" :disabled="readonly" @update:model-value="(v: string) => patchExpert((e) => (e.cn_label = v))" /></el-form-item>
        <el-form-item label="关键词"><el-input :model-value="(expert()?.keywords ?? []).join(', ')" :disabled="readonly" placeholder="逗号分隔" @change="(v: string) => patchExpert((e) => (e.keywords = v.split(/[,，]/).map((s) => s.trim()).filter(Boolean)))" /></el-form-item>
        <el-form-item label="最大步数"><el-input-number :model-value="expert()?.max_steps ?? 4" :min="1" :max="8" :disabled="readonly" @change="(v: number) => patchExpert((e) => (e.max_steps = v))" /></el-form-item>
        <el-form-item label="工具授权">
          <div class="tools">
            <div v-for="t in catalog?.available_tools ?? []" :key="t">
              <el-checkbox :model-value="hasTool(t)" :disabled="readonly" @change="(v: boolean) => toggleTool(t, v)">{{ t }}</el-checkbox>
              <div v-if="hasTool(t)" class="params">
                <label v-for="s in paramsFor(t)" :key="s.name">
                  {{ s.name }}
                  <el-input :model-value="paramValue(s.name)" size="small" :disabled="readonly" :placeholder="`默认 ${s.default}${s.minimum != null ? `，范围 ${s.minimum}~${s.maximum}` : ''}`" @change="(v: string) => setParam(s.name, v)" />
                </label>
              </div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="知识范围">
          <el-radio-group :model-value="expert()?.knowledge_scope?.mode ?? 'all'" :disabled="readonly" @change="(v: string) => setScopeAll(v === 'all')">
            <el-radio value="all">项目全部资料</el-radio>
            <el-radio value="folders">仅所选目录</el-radio>
          </el-radio-group>
          <div v-if="(expert()?.knowledge_scope?.mode ?? 'all') === 'folders'" class="tools">
            <el-checkbox v-for="f in catalog?.folders ?? []" :key="f.folder_id" :model-value="(expert()?.knowledge_scope?.folder_ids ?? []).includes(f.folder_id)" :disabled="readonly" @change="(v: boolean) => toggleFolder(f.folder_id, v)">{{ f.path }}</el-checkbox>
            <span v-if="!(catalog?.folders ?? []).length" class="hint">项目暂无资料目录（范围为空 = 检索 0 命中）</span>
          </div>
        </el-form-item>
        <el-form-item label="输入方式">
          <el-select :model-value="node.input_mode ?? 'query_only'" :disabled="readonly" @change="(v: 'query_only' | 'with_upstream') => emit('update-node', { ...node!, input_mode: v })">
            <el-option value="query_only" label="仅用户问题" />
            <el-option value="with_upstream" label="含上游材料（只读）" />
          </el-select>
        </el-form-item>
      </el-form>

      <h5>提示词 <span class="hint">{{ layers.source }}</span></h5>
      <p v-if="layers.main === null" class="hint">主提示词：文件不存在</p>
      <el-input type="textarea" :rows="7" :model-value="layers.main ?? ''" :readonly="readonly" placeholder="主提示词" @update:model-value="(v: string) => onPrompt('main', v)" />
      <el-input type="textarea" class="gap" :rows="3" :model-value="layers.fallback ?? ''" :readonly="readonly" placeholder="兜底提示词" @update:model-value="(v: string) => onPrompt('fallback', v)" />
      <p v-if="loadErr" class="hint">{{ loadErr }}</p>

      <div v-if="!readonly" class="actions">
        <el-button size="small" :disabled="expert()?.is_default" @click="setDefault">设为默认专家</el-button>
        <el-button size="small" type="danger" :disabled="expert()?.is_default" @click="emit('remove-agent', node.id)">删除 agent</el-button>
        <el-button size="small" type="danger" plain :disabled="expert()?.is_default" @click="emit('request-remove', node.id)">删除节点</el-button>
        <span class="hint">“删除节点”仅从画布移除，agent 的定义与提示词保留</span>
        <span v-if="expert()?.is_default" class="hint">{{ DEFAULT_EXPERT_HINT }}</span>
      </div>
    </template>

    <!-- 条件 / 确认节点 -->
    <template v-else-if="node?.kind === 'condition'">
      <h4>条件分支</h4>
      <el-select :model-value="node.predicate?.kind" :disabled="readonly" @change="(v: 'keyword' | 'upstream_degraded') => emit('update-node', { ...node!, predicate: { kind: v, branches: v === 'keyword' ? (node!.predicate?.branches?.length ? node!.predicate!.branches : [{ key: 'a', keywords: ['关键词'] }]) : [] } })">
        <el-option value="keyword" label="关键词" />
        <el-option value="upstream_degraded" label="上游降级" />
      </el-select>
      <div v-for="(b, i) in node.predicate?.branches ?? []" :key="i" class="params">
        <el-input size="small" :model-value="b.key" :disabled="readonly" placeholder="分支键" @change="(v: string) => emit('update-node', { ...node!, predicate: { kind: 'keyword', branches: node!.predicate!.branches.map((x, j) => (j === i ? { ...x, key: v } : x)) } })" />
        <el-input size="small" :model-value="b.keywords.join(', ')" :disabled="readonly" placeholder="关键词，逗号分隔" @change="(v: string) => emit('update-node', { ...node!, predicate: { kind: 'keyword', branches: node!.predicate!.branches.map((x, j) => (j === i ? { ...x, keywords: v.split(/[,，]/).map((s) => s.trim()).filter(Boolean) } : x)) } })" />
      </div>
      <p class="hint">无表达式 / 代码；出边需配置分支键，并有“否则”分支。</p>
      <div v-if="!readonly" class="actions">
        <el-button size="small" type="danger" plain @click="emit('request-remove', node.id)">删除节点</el-button>
      </div>
    </template>
    <template v-else-if="node?.kind === 'confirm'">
      <h4>人工确认</h4>
      <el-input :model-value="node.message" :disabled="readonly" maxlength="200" @change="(v: string) => emit('update-node', { ...node!, message: v })" />
      <p class="hint">挂起状态仅在进程内保留，服务重启后需重新提问。</p>
      <div v-if="!readonly" class="actions">
        <el-button size="small" type="danger" plain @click="emit('request-remove', node.id)">删除节点</el-button>
      </div>
    </template>
    <template v-else-if="node?.kind === 'join'">
      <h4>汇聚</h4>
      <p class="hint">汇聚节点等待多路上游完成后再继续，无可配置项。</p>
      <div v-if="!readonly" class="actions">
        <el-button size="small" type="danger" plain @click="emit('request-remove', node.id)">删除节点</el-button>
      </div>
    </template>
    <template v-else-if="node?.kind === 'start' || node?.kind === 'end'">
      <h4>{{ node.kind === 'start' ? '开始' : '结束' }}</h4>
      <p class="hint">开始 / 结束节点不可删除</p>
    </template>
    <p v-else class="hint">点击画布上的节点查看或编辑其配置。</p>
  </div>
</template>

<style scoped>
.detail {
  font-size: 13px;
}
.tools {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.params {
  margin-left: 22px;
  display: grid;
  gap: 4px;
}
.gap {
  margin-top: 8px;
}
.actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  align-items: center;
}
.hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
