<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-258（消费 IFC-IB-246：启动重建 + 查询进度）
 * @author software-developer
 *
 * 索引重建页。
 *
 * ## 重建是「先建新版、原子切换、可回滚」，界面必须说清楚
 *
 * 重建期间读路径**仍走旧 collection**（服务不中断，内容非最新）；只有全部文档成功
 * 才切换 active version。因此：
 *   - 界面明确写「重建期间问答可正常使用，读到的是重建前的内容」，避免运维以为要停服；
 *   - `failed > 0` 时给出「本次不会切换版本，旧版本继续服务」的说明 —— 否则用户看到
 *     「失败 N」会以为线上已经坏了（实际是**未切换**，线上完好）。
 *
 * ## 轮询为何是 2 秒且必停
 *
 * 重建是长任务（分钟级）。轮询间隔过小会持续占住 Waitress 线程（同步 WSGI），
 * 而重建期间恰是 IO 密集期；`done` 到达即停止，且组件卸载时清掉定时器，避免
 * 离开页面后仍在打后端。
 */
import { computed, onBeforeUnmount, ref } from 'vue';

import { ApiClientError, type ApiClient, type RebuildProgress } from '../api/client';

const props = defineProps<{ client: ApiClient }>();
const emit = defineEmits<{ (e: 'unauthorized'): void }>();

const jobId = ref('');
const progress = ref<RebuildProgress | null>(null);
const starting = ref(false);
const error = ref('');

const STATE_LABEL: Record<string, string> = {
  planned: '已规划',
  running: '进行中',
  done: '已完成',
  failed: '失败',
  cancelled: '已取消',
};

const total = computed(() => {
  const p = progress.value;
  return p ? p.indexed + p.failed + p.pending : 0;
});

const percent = computed(() => {
  const p = progress.value;
  if (!p || total.value === 0) return 0;
  return Math.round(((p.indexed + p.failed) / total.value) * 100);
});

let timer: number | null = null;

function stopPolling(): void {
  if (timer !== null) {
    window.clearTimeout(timer);
    timer = null;
  }
}

onBeforeUnmount(stopPolling);

function describe(err: unknown): string {
  if (err instanceof ApiClientError) {
    if (err.status === 401) {
      emit('unauthorized');
      return '登录状态已失效，请重新填写访问令牌。';
    }
    if (err.status === 403) return '当前令牌无权操作该项目。';
    if (err.status === 409) return '已有一个重建任务在进行中，请等待其结束。';
    if (err.status === 503) return '服务暂时不可用，请稍后重试。';
    return err.message;
  }
  return '无法连接服务，请确认后端已启动（waitress 监听 127.0.0.1:18080）。';
}

async function poll(): Promise<void> {
  if (!jobId.value) return;
  try {
    const result = await props.client.rebuildProgress(jobId.value);
    progress.value = result;
    if (result.done) {
      stopPolling();
      return;
    }
  } catch (err) {
    error.value = describe(err);
    stopPolling();
    return;
  }
  timer = window.setTimeout(poll, 2000);
}

async function start(): Promise<void> {
  starting.value = true;
  error.value = '';
  progress.value = null;
  stopPolling();
  try {
    const job = await props.client.startRebuild();
    jobId.value = job.job_id;
    await poll();
  } catch (err) {
    error.value = describe(err);
  } finally {
    starting.value = false;
  }
}
</script>

<template>
  <section class="page">
    <h2>索引重建</h2>

    <p class="hint">
      重建会把全部资料按当前解析/切分/向量化配置重新入库：先建新版本集合，逐文档重写，
      全部成功后才原子切换。重建期间问答可正常使用，读到的是重建前的内容。
    </p>

    <button type="button" :disabled="starting || (!!progress && !progress.done)" @click="start">
      {{ starting ? '启动中…' : '开始重建' }}
    </button>

    <p v-if="error" class="error" role="alert">{{ error }}</p>

    <div v-if="progress" class="status">
      <p>
        任务 <code>{{ progress.job_id }}</code>
        —— {{ STATE_LABEL[progress.state] ?? progress.state }}
      </p>

      <div class="bar"><span :style="{ width: percent + '%' }" /></div>
      <p class="hint">
        已入库 {{ progress.indexed }} / 失败 {{ progress.failed }} / 待处理 {{ progress.pending }}
        （共 {{ total }}，{{ percent }}%）
      </p>

      <p v-if="progress.failed > 0" class="warn">
        有 {{ progress.failed }} 个文档重建失败：本次**不会**切换版本，旧版本继续对外服务，
        线上内容不受影响。请先在「资料管理」页修复失败文档后重新发起重建。
      </p>
      <p v-else-if="progress.done" class="ok">
        全部文档重建成功，新版本已生效。旧版本集合保留一个回滚窗口，确认无误后可人工删除。
      </p>
    </div>
  </section>
</template>

<style scoped>
.page {
  padding-top: 16px;
}
button {
  padding: 8px 16px;
  border: 1px solid #0969da;
  background: #0969da;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.status {
  margin-top: 16px;
}
.bar {
  height: 10px;
  background: #eaeef2;
  border-radius: 5px;
  overflow: hidden;
}
.bar span {
  display: block;
  height: 100%;
  background: #0969da;
  transition: width 0.3s ease;
}
.hint {
  color: #57606a;
  font-size: 13px;
}
.warn {
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 6px;
  padding: 8px 12px;
}
.ok {
  background: #dafbe1;
  border: 1px solid #1a7f37;
  border-radius: 6px;
  padding: 8px 12px;
  color: #1a7f37;
}
.error {
  background: #ffebe9;
  border: 1px solid #cf222e;
  border-radius: 6px;
  padding: 8px 12px;
  color: #cf222e;
}
code {
  background: #f6f8fa;
  padding: 1px 5px;
  border-radius: 4px;
}
</style>
