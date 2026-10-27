<script setup lang="ts">
/** @module MOD-R26-20  保存前试运行：用草稿配置对话；回答标注“试运行”；校验错误原样展示。 */
import { ref } from 'vue';

import { ApiClientError, type ApiClient, type PublishPayload, type ValidationErrorItem } from '../../api/client';

const props = defineProps<{ client: ApiClient; getDraftPayload: () => PublishPayload; disabled: boolean }>();
const query = ref('');
const answer = ref('');
const busy = ref(false);
const errors = ref<ValidationErrorItem[]>([]);
const notice = ref('');
const sessionId = `t${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;

async function run(): Promise<void> {
  if (!query.value.trim() || busy.value) return;
  busy.value = true;
  answer.value = '';
  errors.value = [];
  notice.value = '';
  try {
    await props.client.trialStream(props.getDraftPayload(), query.value.trim(), sessionId, (ev) => {
      if (ev.kind === 'content') answer.value += ev.data;
      else if (ev.kind === 'error') notice.value = ev.data;
      else if (ev.kind === 'confirmation_required') notice.value = '该图含人工确认节点；试运行不支持续跑确认。';
    });
  } catch (err) {
    if (err instanceof ApiClientError) {
      const items = (err.details.items as ValidationErrorItem[] | undefined) ?? [];
      if (items.length) errors.value = items;
      else notice.value = err.status === 429 ? '试运行繁忙，请稍后再试' : err.message;
    } else {
      notice.value = '试运行失败';
    }
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div>
    <p class="hint">试运行使用当前画布上的草稿配置，不改变在用版本，也不进入正式会话。</p>
    <el-input v-model="query" :disabled="disabled" placeholder="输入一个问题" @keyup.enter="run" />
    <el-button class="gap" :loading="busy" :disabled="disabled" @click="run">试运行</el-button>
    <ul v-if="errors.length"><li v-for="e in errors" :key="`${e.path}:${e.code}`"><code>{{ e.path }}</code> [{{ e.code }}] {{ e.message }}</li></ul>
    <p v-if="notice" class="hint">{{ notice }}</p>
    <div v-if="answer" class="answer"><el-tag size="small" type="warning">试运行</el-tag><pre>{{ answer }}</pre></div>
  </div>
</template>

<style scoped>
.gap { margin-top: 8px; }
.answer pre { white-space: pre-wrap; word-break: break-all; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
