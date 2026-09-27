/**
 * @module MOD-IB-24
 * @implements IFC-IB-259 类型化 API 客户端（`client.ts`；module_design 中名为 `apiClient.ts`，
 *             同一契约的路径写法差异，见 implementation_plan §8 偏差 D-09）
 *             IFC-IB-283（R2）`fetchFileImage` / `fileImageUrl`：页面图字节取用
 *             IFC-IB-294 / 295（R7）`definitionConfig` / `saveDefinition`：定义文档读写
 * @depends MOD-IB-23（HTTP / SSE 契约，**仅**契约，不 import 任何后端模块）
 * @author software-developer
 *
 * 类型化 HTTP 客户端 —— 前端与后端之间**唯一**的通信入口（IC-IB-01 的落点）。
 *
 * ## IC-IB-01：为什么必须「统一走封装层 + 显式 Authorization」
 *
 * FreeArk 上次的教训很具体：某些页面直接 `import axios from 'axios'` 裸用，靠浏览器
 * 自动携带的 `sessionid` Cookie 完成认证。这类页面对「认证方式」这件事**没有任何显式表达**，
 * 于是：
 *
 *   1. 任何人改动后端的认证配置（例如移除 `SessionAuthentication`），这些页面会**静默 401**，
 *      表现为「页面白屏但控制台没有报错」—— 排查成本极高；
 *   2. 无法审计「哪些页面依赖哪种认证」，安全评审时看不到依赖关系；
 *   3. 一旦后端把令牌改为经 `Authorization` 头传递（本项目就是这样），裸 axios 页面
 *      会因为**不再有 Cookie** 而全部失效。
 *
 * 因此本客户端把认证**显式化**：每个请求都在这里拼上 `Authorization: Bearer <token>`，
 * 页面上不存在第二处拼接令牌的代码。令牌存 `sessionStorage`，不进 URL、不进 Cookie。
 *
 * ## 为什么不用 `EventSource` 读 SSE
 *
 * `EventSource` **不能**设置自定义请求头，只能靠 `withCredentials`（Cookie）或查询串
 * 传凭据 —— 而本项目的 SSE 恰好禁止查询串传令牌（`?token=` 会被后端 400），
 * 且不依赖 Cookie。故改用 `fetch` + `ReadableStream` 手动解析 SSE 帧。
 * 代价是要自己处理「帧可能被 TCP 分片切断」——`parseSseStream` 因此做了跨 chunk 缓冲。
 */

/** 与后端 `DocumentRecord` 序列化字段**逐字段对齐**（后端 `ibweb/serializers.py`）。 */
export type DocumentRecord = {
  doc_id: string;
  kb_id: string;
  doc_name: string;
  ext: string;
  size_bytes: number;
  content_sha256: string;
  status: 'pending' | 'parsing' | 'indexed' | 'failed';
  error_code: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type DeleteReport = {
  vectors_deleted: number;
  blob_deleted: boolean;
  ledger_deleted: boolean;
};

export type RebuildJob = { job_id: string; state: string };

export type RebuildProgress = {
  job_id: string;
  state: string;
  indexed: number;
  failed: number;
  pending: number;
  done: boolean;
};

export type HealthStatus = { ok: boolean; detail: string; latency_ms: number | null };

export type EgressDescriptor = {
  remote: boolean;
  endpoint_host: string;
  data_categories: string[];
};

export type HealthzDeps = {
  qdrant: HealthStatus;
  embed: HealthStatus;
  llm: HealthStatus;
  egress: EgressDescriptor;
};

/** SSE 事件类型（与后端 `StreamEventKind` 枚举值一致）。 */
export type StreamEventKind =
  | 'reasoning'
  | 'content'
  | 'degraded'
  | 'related_images'
  | 'error'
  | 'done';

export type StreamEvent = { kind: StreamEventKind; data: string };

/**
 * `related_images` 事件的载荷条目（IFC-IB-282 / 283；与后端 `RelatedImageItem` 逐字段对齐）。
 *
 * **只有路径，没有字节**：载荷里出现 base64 会让每个事件都背上几百 KB（撑爆 SSE 帧、
 * 同一张图被多次重复传输）。字节一律按需经 `url_path` 取。
 */
export type RelatedImageItem = {
  image_id: string;
  doc_id: string;
  doc_name: string;
  page_or_section: string;
  url_path: string;
};

export type RelatedImagesPayload = { images: RelatedImageItem[] };

export type FileListEnvelope = { items: DocumentRecord[]; total: number };

/**
 * R7 定义文档类型（IFC-IB-294 / 295；与后端 `ibweb/serializers.py` **逐字段对齐**）。
 *
 * 定义文档是「专家 / 路由 / 编排 / 工具授权」的**唯一真源**：前端只**呈现**与**按白名单编辑**，
 * 绝不另存一份（视图侧零持久化，ADR-14）。
 */
export type ExpertSpecInput = {
  name: string;
  cn_label: string;
  keywords: string[];
  exemplars: string[];
  is_data_expert: boolean;
  fallback_prompt: string;
  is_delegating: boolean;
  is_default: boolean;
};

export type RouteSpecInput = {
  tau: number;
  margin: number;
  max_expert_steps: number;
  default_expert: string;
};

/** `branch_map` 为**有序** `[branch_key, target_node]` 序列（保序，供界面判定可达性）。 */
export type ConditionalEdgeSpec = { from_node: string; branch_map: [string, string][] };

export type OrchestrationSpecInput = {
  nodes: string[];
  conditional_edges: ConditionalEdgeSpec[];
};

export type ToolGrantSpec = { expert_name: string; tool_names: string[] };

export type DefinitionDocument = {
  schema_version: number;
  project_id: string;
  content_hash: string;
  experts: ExpertSpecInput[];
  route: RouteSpecInput;
  orchestration: OrchestrationSpecInput;
  tool_grants: ToolGrantSpec[];
  updated_at: string;
};

export type DerivedViewSummary = {
  capability_digest: string;
  expert_names: string[];
  nodes: string[];
  conditional_edges: ConditionalEdgeSpec[];
};

export type ValidationErrorItem = { path: string; code: string; message: string };

export type SaveResult = {
  ok: boolean;
  content_hash: string;
  conflict: boolean;
  errors: ValidationErrorItem[];
};

export type DefinitionConfigEnvelope = {
  document: DefinitionDocument;
  derived: DerivedViewSummary;
  /** 可编辑字段白名单（IFC-IB-292）：白名单外的字段界面**不得写入**。 */
  editable_fields: string[];
  /**
   * R7 配置**键名**（IFC-IB-297）。
   * 只有键名，**没有值** —— 凭据 / 路径值一律不回显（AC-IB-17-05）。
   */
  config_key_names: string[];
};

/**
 * 页面图端点的站内相对路径（IFC-IB-283）。
 *
 * 与后端 `ib.streaming.IMAGE_ENDPOINT_TEMPLATE` 是**同一个字面量形状**；`url_path` 字段
 * 由服务端按它生成，正常情况下前端直接使用该字段，本函数只用于「凭 (doc_id, image_id)
 * 自行拼路径」的场景（例如重试）。
 */
export function fileImageUrl(docId: string, imageId: string): string {
  return `/api/files/${encodeURIComponent(docId)}/images/${encodeURIComponent(imageId)}`;
}

export type ApiError = { status: number; code: string; message: string };

const TOKEN_KEY = 'ib_token';

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  /**
   * 后端错误体里 `error` 对象的**结构化细节**（如 `PUT` 的逐条 `items`、`409` 的 `receipt`）。
   * 供界面给出可读回执（IFC-IB-295）；不含任何凭据值（后端保证）。
   */
  readonly details: Record<string, unknown>;

  constructor({ status, code, message }: ApiError, details: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class ApiClient {
  private readonly baseUrl: string;

  /**
   * 用显式字段赋值而不是参数属性（`constructor(private readonly baseUrl: string)`）：
   * 参数属性是**不可擦除**的 TS 语法，Node 的类型擦除（`--experimental-strip-types`）
   * 无法处理它，`import` 整个模块会直接报错 —— 而本文件需要能被离线自检脚本直接导入
   * （见 `scripts/sse_parser_selfcheck.ts`，用于真跑 SSE 分帧逻辑）。副作用是这行也更
   * 容易被 `grep` 到。
   */
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  // ------------------------------------------------------------------ //
  // 令牌
  // ------------------------------------------------------------------ //

  get token(): string {
    // 只读 `sessionStorage`：不进 URL、不进 Cookie、不落 `localStorage`。
    return sessionStorage.getItem(TOKEN_KEY) ?? '';
  }

  setToken(token: string): void {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  }

  clearToken(): void {
    sessionStorage.removeItem(TOKEN_KEY);
  }

  private headers(extra?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = { Accept: 'application/json', ...extra };
    const token = this.token;
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
  }

  // ------------------------------------------------------------------ //
  // 通用请求（错误统一翻成 ApiClientError）
  // ------------------------------------------------------------------ //

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: this.headers(init.headers as Record<string, string> | undefined),
    });
    return this.decode<T>(response);
  }

  private async decode<T>(response: Response): Promise<T> {
    const text = await response.text();
    if (!response.ok) {
      // 后端错误体固定为 `{"error": {"code","message"}}`；解析失败时给出通用文案，
      // **不把响应原文塞进 Error.message**（可能是框架的 HTML 错误页，会污染界面）。
      let code = 'http_error';
      let message = `请求失败（HTTP ${response.status}）`;
      let details: Record<string, unknown> = {};
      try {
        const parsed = JSON.parse(text);
        if (parsed?.error?.code) code = String(parsed.error.code);
        if (parsed?.error?.message) message = String(parsed.error.message);
        if (parsed?.error && typeof parsed.error === 'object') {
          details = parsed.error as Record<string, unknown>;
        }
      } catch {
        /* 保持通用文案 */
      }
      if (response.status === 401) {
        // 令牌失效即清除，避免界面持续以无效令牌重试
        this.clearToken();
      }
      throw new ApiClientError({ status: response.status, code, message }, details);
    }
    return (text ? JSON.parse(text) : null) as T;
  }

  // ------------------------------------------------------------------ //
  // IFC-IB-242 / 243 / 244 / 245：文件管理
  // ------------------------------------------------------------------ //

  listFiles(params: { page?: number; page_size?: number; status?: string } = {}): Promise<FileListEnvelope> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));
    if (params.status) query.set('status', params.status);
    const suffix = query.toString() ? `?${query.toString()}` : '';
    return this.request<FileListEnvelope>(`/api/files${suffix}`);
  }

  uploadFile(file: File, kbId: string): Promise<DocumentRecord> {
    const body = new FormData();
    // 字段名与后端 `UploadInputSerializer` + `request.FILES['file']` 逐字对齐
    body.append('kb_id', kbId);
    body.append('file', file);
    // **不设置 Content-Type**：交给浏览器带 boundary 生成 multipart/form-data
    return this.request<DocumentRecord>('/api/files', { method: 'POST', body });
  }

  deleteFile(docId: string): Promise<DeleteReport> {
    return this.request<DeleteReport>(`/api/files/${encodeURIComponent(docId)}`, { method: 'DELETE' });
  }

  retryFile(docId: string): Promise<DocumentRecord> {
    return this.request<DocumentRecord>(`/api/files/${encodeURIComponent(docId)}/retry`, {
      method: 'POST',
    });
  }

  // ------------------------------------------------------------------ //
  // IFC-IB-246：重建
  // ------------------------------------------------------------------ //

  startRebuild(): Promise<RebuildJob> {
    return this.request<RebuildJob>('/api/rebuild', { method: 'POST' });
  }

  rebuildProgress(jobId: string): Promise<RebuildProgress> {
    return this.request<RebuildProgress>(`/api/rebuild/${encodeURIComponent(jobId)}`);
  }

  // ------------------------------------------------------------------ //
  // IFC-IB-248 / 249：健康检查
  // ------------------------------------------------------------------ //

  health(): Promise<{ ok: boolean }> {
    return this.request<{ ok: boolean }>('/healthz');
  }

  healthDeps(): Promise<HealthzDeps> {
    return this.request<HealthzDeps>('/healthz/deps');
  }

  // ------------------------------------------------------------------ //
  // IFC-IB-294 / 295：定义文档（单一真源）读写
  // ------------------------------------------------------------------ //

  /**
   * 读取定义文档 + 派生视图摘要 + 可编辑白名单 + 配置键名（IFC-IB-294）。
   *
   * `503` 表示定义文档当前不可读（fail-closed）—— 界面应显示「配置不可用」而**不是**空表单；
   * 后端刻意**不返回空文档**，因为空文档会被误当成「真源就是这么空的」。
   */
  definitionConfig(): Promise<DefinitionConfigEnvelope> {
    return this.request<DefinitionConfigEnvelope>('/api/config/definition');
  }

  /**
   * 原子写回定义文档（IFC-IB-295）。
   *
   * `expectedContentHash` 传当前文档的 `content_hash` 以启用**乐观并发**；服务端不一致时
   * 返回 `409`（抛 `ApiClientError`，`details.receipt` 为可读冲突回执），界面须提示用户
   * 重新载入 —— 绝不静默覆盖他人改动。
   */
  saveDefinition(
    document: DefinitionDocument,
    expectedContentHash?: string | null,
  ): Promise<SaveResult> {
    return this.request<SaveResult>('/api/config/definition', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expected_content_hash: expectedContentHash ?? null, document }),
    });
  }

  // ------------------------------------------------------------------ //
  // IFC-IB-283：页面图字节
  // ------------------------------------------------------------------ //

  /**
   * 取页面图字节，返回可直接给 `<img src>` 用的 `blob:` URL。
   *
   * ## 为什么不能直接 `<img :src="url_path">`
   *
   * 图片端点与其它端点一样要求 `Authorization` 头，而浏览器对 `<img>` 发出的请求
   * **不携带自定义请求头**。三条路都不可走：
   *   1. 把令牌塞进查询串 —— 后端会直接 400（`?token=` 会被访问日志完整打印，FreeArk 已泄露过一次）；
   *   2. 把令牌写进 Cookie —— 本客户端刻意不依赖 Cookie 认证（见文件头 IC-IB-01）；
   *   3. 让图片端点免鉴权 —— 那等于把知识库里的图对全网开放。
   * 因此只能经本客户端显式 fetch 字节，再转成 `blob:` URL。**这是 IC-IB-01 在图片上的落点**：
   * 页面里不得出现第二处拼令牌的代码。
   *
   * ## 失败语义
   *
   * `403` / `404` / `503` 一律抛 `ApiClientError`，由调用方**静默隐藏**该缩略图
   * （IFC-IB-284：不弹错、不中断流、不追加降级文案 —— 降级文案只对 `degraded` 事件负责）。
   * `blob:` URL 的所有权归调用方，**用完须 `URL.revokeObjectURL`**，否则整页图片会常驻内存。
   */
  async fetchFileImage(docId: string, imageId: string, signal?: AbortSignal): Promise<string> {
    const response = await fetch(`${this.baseUrl}${fileImageUrl(docId, imageId)}`, {
      method: 'GET',
      headers: this.headers({ Accept: 'image/*' }),
      signal,
    });
    if (!response.ok) {
      // `decode` 对非 2xx 必定抛 ApiClientError；其后的 throw 只为满足类型收敛，不会执行。
      await this.decode(response);
      throw new ApiClientError({ status: response.status, code: 'image_error', message: '图片不可得' });
    }
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  }

  // ------------------------------------------------------------------ //
  // IFC-IB-247：SSE 问答流
  // ------------------------------------------------------------------ //

  /**
   * 发起一轮问答，逐事件回调。
   *
   * `signal` 让调用方在组件卸载/用户取消时中断 —— 不加会在导航后留下一个未关闭的
   * `ReadableStream`（服务端线程继续跑到 60s 超时，白白占用一个 Waitress 线程）。
   */
  async chatStream(
    query: string,
    sessionId: string,
    onEvent: (event: StreamEvent) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const query$ = new URLSearchParams();
    query$.set('q', query);
    query$.set('session_id', sessionId || 'default');
    const response = await fetch(`${this.baseUrl}/api/chat/stream?${query$.toString()}`, {
      method: 'GET',
      headers: this.headers({ Accept: 'text/event-stream' }),
      signal,
    });
    if (!response.ok) {
      await this.decode(response); // 抛 ApiClientError（含 400/401/403 的中文提示）
      return;
    }
    if (!response.body) {
      throw new ApiClientError({ status: 0, code: 'no_body', message: '流式响应缺少响应体' });
    }
    for await (const frame of parseSseStream(response.body)) {
      onEvent(frame);
      if (frame.kind === 'done') return;
    }
  }
}

/**
 * 解析 SSE 字节流为事件序列。
 *
 * 关键点：**跨 chunk 缓冲**。SSE 帧可能被 TCP 分片切成两半（一个大 `content` 事件尤其
 * 容易被切开），若对每个 chunk 单独解析，会丢掉半截 JSON —— 表现为「偶尔答到一半断掉」，
 * 且刷新一次就好了，最难复现的一类缺陷。
 */
export async function* parseSseStream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<StreamEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE 以空行分隔帧；`\r\n\r\n` 与 `\n\n` 都接受（不同代理会改写换行）
      let boundary = findBoundary(buffer);
      while (boundary !== null) {
        const raw = buffer.slice(0, boundary.start);
        buffer = buffer.slice(boundary.end);
        const event = parseFrame(raw);
        if (event) yield event;
        boundary = findBoundary(buffer);
      }
    }
    if (buffer.trim()) {
      const event = parseFrame(buffer);
      if (event) yield event;
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * 找下一帧边界的**哨兵必须是 `null`，不能是 `-1`**。
 *
 * 这里踩过一次真实的坑：原先返回 `{start,end} | -1`，调用处写 `while (boundary >= 0)`。
 * 对象与数字比较恒为 `false`（`{...} >= 0` → JS 先 `ToPrimitive` 再比，结果为 `NaN` 比较
 * → `false`），于是**循环体一次也不执行**：整条流被缓到最后一次性 `parseFrame`，
 * 多帧被拼成**一个**事件，`kind` 取最后一帧（永远是 `done`），`data` 是所有负载的拼接。
 * 后果是「正文全丢、页面空着但不报错」—— 最像「后端没返回」的那种假象。
 * 这个缺陷被 `scripts/sse_parser_selfcheck.mts` 的跨 chunk 用例抓出（该脚本因此保留）。
 */
function findBoundary(buffer: string): { start: number; end: number } | null {
  const lf = buffer.indexOf('\n\n');
  const crlf = buffer.indexOf('\r\n\r\n');
  if (lf < 0 && crlf < 0) return null;
  if (crlf >= 0 && (lf < 0 || crlf < lf)) return { start: crlf, end: crlf + 4 };
  return { start: lf, end: lf + 2 };
}

function parseFrame(raw: string): StreamEvent | null {
  let kind = 'message';
  const dataLines: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    if (line.startsWith(':')) continue; // 注释/心跳
    if (line.startsWith('event:')) kind = line.slice(6).trim();
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''));
  }
  if (kind === 'message' && dataLines.length === 0) return null;
  return { kind: kind as StreamEventKind, data: dataLines.join('\n') };
}

/** 默认单例（页面优先经 `inject` 取，便于测试替换）。 */
export const apiClient = new ApiClient();
