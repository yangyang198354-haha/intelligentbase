<script setup lang="ts">
/**
 * @module MOD-R26-20
 * @implements REQ-FUNC-004/018~022 Agent Builder：空白表单 / 克隆 / 按需求生成 / 评审并优化已有 agent。
 * 草案只在本组件内存在，点“加入画布”后才进入画布草稿（仍需“保存并生效”）；LLM 不可用时手工入口照常可用。
 */
import { computed, ref } from 'vue';

import { ApiClientError, type ApiClient, type ConfigCatalogDto, type DefinitionDocumentV2 } from '../../api/client';
import type { AdaptationNoteDto, AgentDraftDto, FieldChangeDto, RubricResultDto } from '../../api/builderTypes';
import BuilderEvalView from './BuilderEvalView.vue';

const props = defineProps<{ visible: boolean; client: ApiClient; doc: DefinitionDocumentV2 | null; catalog: ConfigCatalogDto | null }>();
const emit = defineEmits<{ (e: 'add-to-canvas', draft: AgentDraftDto): void; (e: 'close'): void }>();

const mode = ref<'blank' | 'clone' | 'generate' | 'review'>('blank');
const draft = ref<AgentDraftDto | null>(null);
const notes = ref<AdaptationNoteDto[]>([]);
const evalResult = ref<RubricResultDto | null>(null);
const changes = ref<FieldChangeDto[]>([]);
const requirement = ref('');
const instruction = ref('');
const source = ref('');
const busy = ref(false);
const error = ref('');

const blank = (): AgentDraftDto => ({
  name: '', cn_label: '', main_prompt: '', fallback_prompt: '', keywords: [], exemplars: [], is_data_expert: false,
  is_delegating: false, tool_names: [], tool_params: [], knowledge_folder_ids: [], max_steps: 4, source: 'blank',
});
const names = computed(() => new Set((props.doc?.experts ?? []).map((e) => e.name)));
const labels = computed(() => new Set((props.doc?.experts ?? []).map((e) => e.cn_label)));
const problems = computed(() => {
  const d = draft.value;
  const out: string[] = [];
  if (!d) return out;
  if (!d.name.trim()) out.push('name 不能为空');
  else if (names.value.has(d.name)) out.push('name 已存在，请修改');
  if (!d.cn_label.trim()) out.push('中文标签不能为空');
  else if (labels.value.has(d.cn_label)) out.push('中文标签与已有 agent 重复，请修改');
  if (!d.main_prompt.trim()) out.push('主提示词不能为空');
  if (!d.fallback_prompt.trim()) out.push('兜底提示词不能为空');
  return out;
});

function fail(err: unknown, fallback: string): void {
  error.value = err instanceof ApiClientError ? err.message : fallback;
}
async function run<T>(fn: () => Promise<T>, failText: string): Promise<T | null> {
  busy.value = true;
  error.value = '';
  try {
    return await fn();
  } catch (err) {
    fail(err, failText);
    return null;
  } finally {
    busy.value = false;
  }
}

function startBlank(): void {
  mode.value = 'blank';
  draft.value = blank();
  notes.value = [];
  evalResult.value = null;
}
async function startClone(): Promise<void> {
  const src = props.doc?.experts.find((e) => e.name === source.value);
  if (!src) return;
  const grant = props.doc?.tool_grants.find((g) => g.expert_name === src.name);
  const layer = async (l: 'main' | 'fallback') => {
    try {
      return (await props.client.promptLayer(src.name, l)).content;
    } catch {
      return '';
    }
  };
  draft.value = {
    ...blank(), name: '', cn_label: '', source: 'cloned',
    main_prompt: await layer('main'), fallback_prompt: await layer('fallback'),
    keywords: [...src.keywords], exemplars: [...src.exemplars], is_data_expert: src.is_data_expert,
    is_delegating: src.is_delegating, tool_names: [...(grant?.tool_names ?? [])],
    tool_params: (grant?.param_values ?? []).map((p) => [p.name, p.value] as [string, string]),
    knowledge_folder_ids: [...(src.knowledge_scope?.folder_ids ?? [])], max_steps: src.max_steps ?? 4,
  };
}
async function generate(): Promise<void> {
  const r = await run(() => props.client.builderDraft(requirement.value), 'Agent Builder 暂不可用');
  if (r) {
    draft.value = r.draft;
    notes.value = r.notes;
    evalResult.value = r.evaluation;
    changes.value = [];
  }
}
async function evaluate(): Promise<void> {
  if (!draft.value) return;
  const r = await run(() => props.client.builderEvaluate(draft.value as AgentDraftDto), '评审失败');
  if (r) evalResult.value = r.evaluation;
}
async function optimize(): Promise<void> {
  if (!draft.value) return;
  const r = await run(() => props.client.builderOptimize(draft.value as AgentDraftDto, instruction.value || undefined), '优化失败');
  if (r) {
    draft.value = r.draft;
    notes.value = r.notes;
    evalResult.value = r.after;
    changes.value = r.changes;
  }
}
async function review(): Promise<void> {
  const r = await run(() => props.client.builderReviewExisting(source.value, 'optimize', instruction.value || undefined), '评审失败');
  if (r) {
    evalResult.value = r.evaluation;
    changes.value = r.changes;
    if (r.proposal) draft.value = { ...r.proposal, name: '', cn_label: '', source: 'optimized' };
    notes.value = [];
    error.value = r.proposal ? '修订建议已生成。要采纳请为其起一个新的 name 与中文标签后加入画布（不会覆盖线上的原 agent）。' : '';
  }
}
function add(): void {
  if (draft.value && problems.value.length === 0) {
    emit('add-to-canvas', JSON.parse(JSON.stringify(draft.value)) as AgentDraftDto);
    draft.value = null;
    emit('close');
  }
}
const csv = (v: string) => v.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
</script>

<template>
  <el-drawer :model-value="visible" title="Agent Builder" size="560px" @close="emit('close')">
    <el-radio-group v-model="mode" size="small" @change="() => { draft = null; evalResult = null; notes = []; changes = []; error = ''; if (mode === 'blank') startBlank(); }">
      <el-radio-button value="blank">空白表单</el-radio-button>
      <el-radio-button value="clone">克隆已有</el-radio-button>
      <el-radio-button value="generate">按需求生成</el-radio-button>
      <el-radio-button value="review">评审并优化已有</el-radio-button>
    </el-radio-group>

    <div class="section">
      <template v-if="mode === 'blank'"><el-button size="small" @click="startBlank">开始填写</el-button></template>
      <template v-else-if="mode === 'clone' || mode === 'review'">
        <el-select v-model="source" placeholder="选择已有 agent" size="small">
          <el-option v-for="e in doc?.experts ?? []" :key="e.name" :value="e.name" :label="`${e.cn_label}（${e.name}）`" />
        </el-select>
        <el-button v-if="mode === 'clone'" size="small" :disabled="!source" @click="startClone">以其为起点</el-button>
        <template v-else>
          <el-input v-model="instruction" size="small" placeholder="修改意见（可选）" maxlength="1000" />
          <el-button size="small" :loading="busy" :disabled="!source" @click="review">评审并按意见优化</el-button>
        </template>
      </template>
      <template v-else>
        <el-input v-model="requirement" type="textarea" :rows="3" maxlength="2000" placeholder="用自然语言描述你要的 agent（内容将发往云端模型，请勿包含密钥或敏感资料）" />
        <el-button size="small" type="primary" :loading="busy" :disabled="!requirement.trim()" @click="generate">生成草案</el-button>
        <p class="hint">云端不可用或未配置 Key 时，请改用“空白表单”或“克隆”。</p>
      </template>
    </div>

    <p v-if="error" class="warn">{{ error }}</p>

    <div v-if="draft" class="section">
      <el-form label-width="96px" size="small">
        <el-form-item label="name"><el-input v-model="draft.name" maxlength="48" /></el-form-item>
        <el-form-item label="中文标签"><el-input v-model="draft.cn_label" maxlength="32" /></el-form-item>
        <el-form-item label="主提示词"><el-input v-model="draft.main_prompt" type="textarea" :rows="6" /></el-form-item>
        <el-form-item label="兜底提示词"><el-input v-model="draft.fallback_prompt" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="关键词"><el-input :model-value="draft.keywords.join(', ')" @change="(v: string) => (draft!.keywords = csv(v))" /></el-form-item>
        <el-form-item label="工具">
          <el-checkbox-group v-model="draft.tool_names"><el-checkbox v-for="t in catalog?.available_tools ?? []" :key="t" :value="t">{{ t }}</el-checkbox></el-checkbox-group>
        </el-form-item>
        <el-form-item label="最大步数"><el-input-number v-model="draft.max_steps" :min="1" :max="8" /></el-form-item>
      </el-form>
      <ul v-if="notes.length" class="notes"><li v-for="(n, i) in notes" :key="i">适配说明：{{ n.message }}</li></ul>
      <ul v-if="changes.length"><li v-for="(c, i) in changes" :key="i">{{ c.field }}：{{ c.note }}</li></ul>
      <ul v-if="problems.length" class="warn"><li v-for="p in problems" :key="p">{{ p }}</li></ul>
      <BuilderEvalView v-if="evalResult" :result="evalResult" />
      <div class="actions">
        <el-button v-if="draft.source !== 'blank' && draft.source !== 'cloned'" size="small" :loading="busy" @click="evaluate">重新评审</el-button>
        <el-button v-if="draft.source === 'generated' || draft.source === 'optimized'" size="small" :loading="busy" @click="optimize">按意见优化（单轮）</el-button>
        <el-button type="primary" size="small" :disabled="problems.length > 0" @click="add">加入画布</el-button>
      </div>
      <p class="hint">加入画布后仍需“保存并生效”才会上线；未加入就关闭则不会有任何改动。</p>
    </div>
  </el-drawer>
</template>

<style scoped>
.section { margin-top: 12px; display: grid; gap: 8px; }
.actions { display: flex; gap: 8px; }
.warn { color: var(--el-color-danger); font-size: 12px; }
.notes { color: var(--el-text-color-secondary); font-size: 12px; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
