<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-257（消费 IFC-IB-247：SSE 问答流；渲染 content / degraded）
 *             IFC-IB-284（R2）`related_images` 缩略图行（该轮回答**下方**；点击经 IFC-IB-283 取原图）
 * @author software-developer
 *
 * 知识问答页。
 *
 * ## `degraded` 的界面义务（AC-IB-14-01）
 *
 * 降级**必须让用户看见**：检索不可用时后端仍会 fail-open 继续作答（基于模型通用知识），
 * 若不提示，用户会把「没有依据的回答」当成「有依据的回答」——这是本系统最危险的一种
 * 误导。因此 `degraded` 事件到达时立刻显示醒目横幅，且横幅**在正文之前**（后端保证
 * 顺序：`reasoning → degraded → content → done`），正文在视觉上始终带着这个限定语。
 *
 * 同时刻意区分两件事（AC-IB-14-02）：
 *   - `degraded`=true  → 「当前未接入知识资料库」（检索故障，回答无依据）
 *   - `degraded`=false 且无命中 → 后端正常作答（属正常结果，不误报为故障）
 * 前端只据事件驱动，不做二次判断，避免把「知识库为空」误告成「服务故障」。
 *
 * ## 正文为什么不解析 Markdown
 *
 * 用 `v-html` 渲染模型输出会把「模型生成的内容」直接当 HTML 执行 —— 模型输出受检索
 * 到的文档影响，而文档是外部上传的，等于把 XSS 通道开到了知识库里。故正文一律走
 * 文本插值 + `white-space: pre-wrap`（保留换行与缩进，不解释标签）。若日后确需富文本，
 * 应引入渲染后消毒（DOMPurify）而非直接 `v-html`。
 *
 * ## R2：`related_images` 缩略图行（IFC-IB-284）
 *
 * 四条硬约束，逐条对应契约：
 *
 * 1. **位置**：只能渲染在**该轮回答的下方**，作为独立的一行；**绝不插入正文中间**、
 *    **绝不改写 `content` 文本**。理由：缩略图一旦混进正文，`content` 就不再是服务端
 *    给出的那份文本 —— 前端开始「创作」内容，而回答的可审计性（服务端返回什么、用户看到什么）
 *    也随之丧失。
 * 2. **顺序**：载荷顺序即渲染顺序（服务端按 `page_or_section` 升序给出），**前端不重排**。
 * 3. **降级**：取图失败 / `403` / `404` / `503` → **静默隐藏该缩略图**（不弹错、不中断流、
 *    不追加降级文案）。降级文案**只对 `degraded` 事件负责**：若两种语义共用同一个观察点，
 *    用户与运维都无法从界面区分「知识库没接上」与「某张图丢了」。
 * 4. **取图纪律**：只能经 `ApiClient`（IC-IB-01）。`<img :src="url_path">` 不带
 *    `Authorization` 头，会被后端 401/403，故必须经客户端取字节再转 `blob:` URL
 *    （见 `client.ts::fetchFileImage` 的三条排除理由）。
 *
 * 「缩略图」与「原图」是**同一份字节**：后端只有一个图片端点（IFC-IB-283），界面上的
 * 大小差异纯粹是 CSS。因此点击就是打开这张字节本身，无需第二次请求，也不会出现
 * 「缩略图与原图不一致」这类只有两个端点才会有的漂移。
 */
import { onBeforeUnmount, ref } from 'vue';

import {
  ApiClientError,
  type ApiClient,
  type ConfirmationPrompt,
  type RelatedImageItem,
  type StreamEvent,
} from '../api/client';

const props = defineProps<{ client: ApiClient }>();
const emit = defineEmits<{ (e: 'unauthorized'): void }>();

/** 一张关联图在界面里的状态（`objectUrl` 为空即「尚未取到或已失败」→ 不渲染）。 */
type TurnImage = {
  imageId: string;
  docId: string;
  docName: string;
  pageOrSection: string;
  objectUrl: string;
  failed: boolean;
};

type Turn = {
  query: string;
  answer: string;
  reasoning: string[];
  degraded: string;
  images: TurnImage[];
  error: string;
  streaming: boolean;
  /** R8（IFC-IB-308）：待确认中间态（独立区域呈现）。非空即「**未完成**、等待用户决策」。 */
  confirmation: ConfirmationPrompt | null;
  /** 决策是否已回传（回传后确认区不再接受二次点击，改由续跑流驱动）。 */
  decided: boolean;
};

/** 已创建的 `blob:` URL（卸载时统一释放 —— 不释放会让整页图片常驻内存）。 */
const createdUrls = new Set<string>();

const query = ref('');
// FND-R11-01 / AC-IB-20-01：**不得**预填字面量 'default' —— 预填等于「用户没填也照发」，
// 与后端「缺会话标识即显式 4xx」的纪律自相矛盾（且多标签页会静默共用一个会话）。
// 留空由用户在下方输入；`client.chatStream/chatResume` 对空标识提前拒绝并给出可读回执。
const sessionId = ref('');
const turns = ref<Turn[]>([]);
const showReasoning = ref(true);

/** 当前进行中的流的取消句柄；同时只允许一轮在飞。 */
let controller: AbortController | null = null;

function currentTurn(): Turn | undefined {
  return turns.value.find((t) => t.streaming);
}

function describe(err: unknown): string {
  if (err instanceof ApiClientError) {
    if (err.status === 401) {
      emit('unauthorized');
      return '登录状态已失效，请重新填写访问令牌。';
    }
    if (err.status === 403) return '当前令牌无权访问该项目。';
    if (err.status === 503) return '服务暂时不可用，请稍后重试。';
    return err.message;
  }
  if (err instanceof DOMException && err.name === 'AbortError') return '';
  return '无法连接服务，请确认后端已启动（waitress 监听 127.0.0.1:18080）。';
}

function apply(turn: Turn, event: StreamEvent): void {
  switch (event.kind) {
    case 'reasoning':
      // 进度类信息折叠展示：它含内部分工线索的措辞由后端保证不外泄（AC-IB-09-03）
      if (event.data) turn.reasoning.push(event.data);
      break;
    case 'content':
      turn.answer += event.data;
      break;
    case 'degraded': {
      // 后端负载形如 {"reason": "...", "hint": "当前未接入知识资料库，以下回答基于通用知识。"}
      // 解析失败时**仍要提示**：宁可显示泛化文案，也不静默吞掉降级信号。
      let hint = '当前未接入知识资料库，以下回答基于通用知识。';
      try {
        const parsed = JSON.parse(event.data);
        if (parsed?.hint) hint = String(parsed.hint);
        else if (parsed?.reason) hint = `当前未接入知识资料库（${parsed.reason}），以下回答基于通用知识。`;
      } catch {
        if (event.data) hint = event.data;
      }
      turn.degraded = hint;
      break;
    }
    case 'error':
      turn.error = event.data || '服务暂时不可用，请稍后重试。';
      break;
    case 'related_images':
      // IFC-IB-282：载荷形如 {"images":[{image_id, doc_id, doc_name, page_or_section, url_path}]}
      // 结构与后端契约一致，故正常解析；**解析失败/结构不符则静默忽略** ——
      // 这里不追加任何降级文案（降级文案只对 degraded 事件负责，见文件头第 3 条）。
      collectImages(turn, event.data);
      break;
    case 'confirmation_required': {
      // IFC-IB-308：确认中间态以**独立区域**呈现，**不并入正文**（`turn.answer` 不被触碰）。
      // 载荷形如 {"gate_id","expert_name","summary"}；解析失败则给可读泛化文案并保留决策能力
      // （宁可显示泛化话术，也不静默吞掉「需要你确认」这件事 —— 那会让界面看起来「已完成」）。
      const prompt = parseConfirmation(event.data);
      if (prompt) {
        turn.confirmation = prompt;
        turn.decided = false;
      } else {
        turn.confirmation = { gate_id: '', expert_name: '', summary: '有一步操作需要你确认后才会继续。' };
        turn.decided = false;
      }
      break;
    }
    case 'done':
      // IFC-IB-308：`done` 只表示**本次流已收束**，不表示「答复已完成」——
      // 若仍挂有待确认中间态，界面必须保持「未完成」外观（见模板 `awaitingDecision`）。
      turn.streaming = false;
      break;
    default:
      break;
  }
}

/** 解析 `confirmation_required` 载荷；结构不符返回 `null`（调用方给泛化文案）。 */
function parseConfirmation(data: string): ConfirmationPrompt | null {
  try {
    const parsed = JSON.parse(data) as Partial<ConfirmationPrompt>;
    if (!parsed || typeof parsed !== 'object' || !parsed.gate_id) return null;
    return {
      gate_id: String(parsed.gate_id),
      expert_name: String(parsed.expert_name ?? ''),
      summary: String(parsed.summary ?? ''),
    };
  } catch {
    return null;
  }
}

/** 该轮是否仍**等待用户决策**（未决策则界面不显示为「已完成」，且不自动继续）。 */
function awaitingDecision(turn: Turn): boolean {
  return !!turn.confirmation && !turn.decided;
}

/** 解析载荷为条目列表；任何异常/结构不符一律当「没有图」（不抛、不提示）。 */
function parseImages(data: string): RelatedImageItem[] {
  try {
    const parsed = JSON.parse(data) as { images?: unknown };
    const list = Array.isArray(parsed?.images) ? parsed.images : [];
    return list.filter(
      (item): item is RelatedImageItem =>
        !!item && typeof item === 'object' && !!(item as RelatedImageItem).image_id && !!(item as RelatedImageItem).doc_id,
    );
  } catch {
    return [];
  }
}

/** 收集该轮的关联图并**立即取字节**（取不到就静默隐藏，见 `loadImage`）。 */
function collectImages(turn: Turn, data: string): void {
  for (const item of parseImages(data)) {
    // 同一条目重复到达（重连/重放）不重复渲染；顺序即到达顺序（**不重排**）
    if (turn.images.some((existing) => existing.imageId === item.image_id)) continue;
    const image: TurnImage = {
      imageId: item.image_id,
      docId: item.doc_id,
      docName: item.doc_name ?? '',
      pageOrSection: item.page_or_section ?? '',
      objectUrl: '',
      failed: false,
    };
    turn.images.push(image);
    void loadImage(image);
  }
}

/** 取图；失败一律 `failed = true`（渲染层据此隐藏该缩略图，不弹错、不中断流）。 */
async function loadImage(image: TurnImage): Promise<void> {
  try {
    const objectUrl = await props.client.fetchFileImage(image.docId, image.imageId);
    image.objectUrl = objectUrl;
    createdUrls.add(objectUrl);
  } catch {
    image.failed = true;
  }
}

/** 该轮**可渲染**的缩略图（按载荷顺序；失败或未取到的条目不出现在界面上）。 */
function visibleImages(turn: Turn): TurnImage[] {
  return turn.images.filter((image) => !!image.objectUrl && !image.failed);
}

/** 点击缩略图：打开这张字节本身（同一份来自 IFC-IB-283 的字节，见文件头末段）。 */
function openOriginal(image: TurnImage): void {
  if (image.objectUrl) window.open(image.objectUrl, '_blank', 'noopener');
}

async function ask(): Promise<void> {
  const text = query.value.trim();
  if (!text || controller) return;
  const turn: Turn = {
    query: text,
    answer: '',
    reasoning: [],
    degraded: '',
    images: [],
    error: '',
    streaming: true,
    confirmation: null,
    decided: false,
  };
  turns.value.push(turn);
  query.value = '';
  controller = new AbortController();
  try {
    await props.client.chatStream(text, sessionId.value, (event) => apply(turn, event), controller.signal);
  } catch (err) {
    if (!(err instanceof DOMException && err.name === 'AbortError')) {
      turn.error = describe(err);
    }
  } finally {
    turn.streaming = false;
    controller = null;
  }
}

/**
 * 回传确认决策并续跑（IFC-IB-308 / IFC-IB-307）。
 *
 * **只能由用户显式点击触发**（不做任何自动继续）：未决策前界面保持「未完成」，
 * 且**不自动重跑**（AC-IB-20-04）。`403`/`404`/`409`/`503` 由 `describe` 翻成可读回执
 * （如「会话已失效，请重新发起或重新确认」），**不静默丢弃**（AC-IB-20-05 / 20-06）。
 */
async function decide(turn: Turn, approved: boolean): Promise<void> {
  const prompt = turn.confirmation;
  if (!prompt || !prompt.gate_id || controller) return;
  turn.decided = true;
  turn.error = '';
  turn.streaming = true;
  controller = new AbortController();
  try {
    await props.client.chatResume(
      sessionId.value,
      { gate_id: prompt.gate_id, approved },
      (event) => apply(turn, event),
      controller.signal,
    );
  } catch (err) {
    if (!(err instanceof DOMException && err.name === 'AbortError')) {
      // 恢复失败（403/404/409/503）：给出可读回执，**不自动重跑**（AC-IB-20-05 / 20-06）
      turn.error = describe(err);
    }
  } finally {
    // 无论批准或拒绝，本次未决呈现都已了结：清空待确认区（拒绝/失败时由 error 区承接）。
    turn.confirmation = null;
    turn.decided = false;
    turn.streaming = false;
    controller = null;
  }
}

function stop(): void {
  controller?.abort();
  controller = null;
  const turn = currentTurn();
  if (turn) turn.streaming = false;
}

onBeforeUnmount(() => {
  // 组件卸载即中断：否则服务端的同步 WSGI 线程会把这个连接跑到底（最长 60s），
  // 白白占住一个 Waitress worker。
  controller?.abort();
  controller = null;
  // 释放已创建的 blob URL（不释放则图片字节随组件生命周期一起常驻内存）
  for (const url of createdUrls) URL.revokeObjectURL(url);
  createdUrls.clear();
});
</script>

<template>
  <section class="page">
    <h2>知识问答</h2>

    <form class="ask" @submit.prevent="ask">
      <input
        v-model="query"
        type="text"
        placeholder="输入问题，例如：本项目的验收标准是什么？"
        aria-label="问题"
        :disabled="!!controller"
      />
      <button v-if="!controller" type="submit" :disabled="!query.trim()">提问</button>
      <button v-else type="button" class="stop" @click="stop">停止</button>
    </form>

    <p class="hint">
      会话标识
      <input
        v-model="sessionId"
        class="session"
        type="text"
        placeholder="必填，如 s1"
        aria-label="会话标识"
      />
      （多轮上下文按此标识隔离；回答经云端模型生成，问题文本与检索片段会外发，见部署说明）
    </p>

    <article v-for="(turn, index) in turns" :key="index" class="turn">
      <p class="question">{{ turn.query }}</p>

      <!-- 降级横幅：置于正文之前，正文始终带着这个限定语 -->
      <p v-if="turn.degraded" class="degraded" role="status">{{ turn.degraded }}</p>

      <details v-if="turn.reasoning.length" :open="showReasoning" class="reasoning">
        <summary>处理过程（{{ turn.reasoning.length }} 步）</summary>
        <p v-for="(line, i) in turn.reasoning" :key="i">{{ line }}</p>
      </details>

      <pre v-if="turn.answer" class="answer">{{ turn.answer }}</pre>
      <p v-else-if="turn.streaming" class="hint">生成中…</p>

      <!-- IFC-IB-284：缩略图行**在该轮回答下方**（独立一行，绝不插入正文中间）。
           顺序即载荷顺序（不重排）；取图失败的条目已被 visibleImages 滤掉（静默隐藏）。 -->
      <div v-if="visibleImages(turn).length" class="thumbs">
        <button
          v-for="image in visibleImages(turn)"
          :key="image.imageId"
          type="button"
          class="thumb"
          :title="`${image.docName || '文档'} · ${image.pageOrSection}`"
          :aria-label="`查看原图：${image.docName || '文档'} ${image.pageOrSection}`"
          @click="openOriginal(image)"
        >
          <img :src="image.objectUrl" :alt="`${image.docName} ${image.pageOrSection}`" loading="lazy" />
        </button>
      </div>

      <p v-if="turn.error" class="error" role="alert">{{ turn.error }}</p>

      <!-- R8（IFC-IB-308）：确认中间态**独立区域**呈现（与答复片段视觉可区分、**不并入正文**）。
           只能由用户显式点击决策；未决策前**不自动继续**，且该轮**不显示为「已完成」**。 -->
      <div v-if="awaitingDecision(turn)" class="confirm" role="alertdialog" aria-live="assertive">
        <p class="confirm-title">有一步操作需要你确认</p>
        <p class="confirm-summary">
          {{ turn.confirmation?.summary || '请确认是否继续执行该操作。' }}
        </p>
        <div class="confirm-actions">
          <button type="button" class="approve" @click="decide(turn, true)">同意并继续</button>
          <button type="button" class="reject" @click="decide(turn, false)">拒绝</button>
        </div>
      </div>

      <!-- 仅当**不在待确认态**且本轮已收束时才标记完成（待确认态下绝不显示「已完成」）。 -->
      <p
        v-if="!turn.streaming && !awaitingDecision(turn) && !!turn.answer && !turn.error"
        class="done-mark"
      >
        本轮已完成
      </p>
    </article>

    <p v-if="!turns.length" class="hint">还没有提问。回答会标注是否接入知识资料库。</p>
  </section>
</template>

<style scoped>
.page {
  padding-top: 16px;
}
.ask {
  display: flex;
  gap: 8px;
  margin: 12px 0 4px;
}
.ask input {
  flex: 1;
  padding: 8px;
  border: 1px solid #d8dee4;
  border-radius: 6px;
}
button {
  padding: 6px 14px;
  border: 1px solid #0969da;
  background: #0969da;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
}
button.stop {
  background: #fff;
  color: #cf222e;
  border-color: #cf222e;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.turn {
  border-top: 1px solid #eaeef2;
  padding: 16px 0;
}
.question {
  font-weight: 600;
  margin: 0 0 8px;
}
.answer {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  margin: 8px 0;
  background: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
}
.degraded {
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 6px;
  padding: 8px 12px;
  margin: 0 0 8px;
}
.thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0 0;
}
.thumb {
  padding: 0;
  border: 1px solid #d8dee4;
  background: #fff;
  border-radius: 6px;
  cursor: zoom-in;
  overflow: hidden;
  line-height: 0;
}
.thumb img {
  display: block;
  width: 96px;
  height: 96px;
  object-fit: cover;
}
.error {
  background: #ffebe9;
  border: 1px solid #cf222e;
  border-radius: 6px;
  padding: 8px 12px;
  color: #cf222e;
}
.reasoning {
  font-size: 13px;
  color: #57606a;
  margin: 8px 0;
}
.reasoning pre {
  white-space: pre-wrap;
  font-family: inherit;
}
.hint {
  color: #57606a;
  font-size: 13px;
}
.session {
  width: 120px;
  padding: 3px 6px;
  border: 1px solid #d8dee4;
  border-radius: 4px;
}
/* R8（IFC-IB-308）：确认区与答复区**视觉可区分**（独立边框/底色，绝不与正文混排）。 */
.confirm {
  border: 1px solid #d4a72c;
  background: #fff8c5;
  border-radius: 6px;
  padding: 12px;
  margin: 8px 0;
}
.confirm-title {
  font-weight: 600;
  margin: 0 0 6px;
}
.confirm-summary {
  margin: 0 0 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
.confirm-actions {
  display: flex;
  gap: 8px;
}
.confirm-actions .reject {
  background: #fff;
  color: #cf222e;
  border-color: #cf222e;
}
.done-mark {
  color: #57606a;
  font-size: 12px;
  margin: 8px 0 0;
}
</style>
