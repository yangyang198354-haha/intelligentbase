/**
 * @module MOD-IB-24
 * @implements IFC-IB-259 类型化 API 客户端（`client.ts`；module_design 中名为 `apiClient.ts`，
 *             同一契约的路径写法差异，见 implementation_plan §8 偏差 D-09）
 *             IFC-IB-283（R2）`fetchFileImage` / `fileImageUrl`：页面图字节取用
 *             IFC-IB-294 / 295（R7）`definitionConfig` / `saveDefinition`：定义文档读写
 *             IFC-IB-333 / 336（R14）`listProjects` + `headers()` 的 `X-IB-Project` 单一注入点
 *             （含 SSE `chatStream` / `chatResume`，二者同经 `headers()`）
 *             IFC-IB-352（REV-16-2）`promptList` / `promptLayer` / `savePromptLayer`：
 *             独立提示词目录（第二真源）的列表元数据 / 单层读 / 单层原子保存
 *             IFC-IB-359 / 362（REV-16-4）`configAudit` / `storageState`：
 *             配置审计（只读）与存储态（只读，供 IFC-IB-363 非静默提示）
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

/** SSE 事件类型（与后端 `StreamEventKind` 枚举值一致）。
 *
 * R8（IFC-IB-301）：**追加** `confirmation_required`（确认中间态呈递）。既有 6 个取值
 * **一字不动** —— 后端是「追加成员」而非「改集合」，前端取值域是它的超集。
 */
export type StreamEventKind =
  | 'reasoning'
  | 'content'
  | 'degraded'
  | 'related_images'
  | 'error'
  | 'done'
  | 'confirmation_required';

export type StreamEvent = { kind: StreamEventKind; data: string };

/** `confirmation_required` 事件的载荷（IFC-IB-301 / 308；与后端 JSON 对齐）。
 *
 * `summary` 由**接入方**构造（骨架不生成业务话术）；`gate_id` 供决策回传对账
 * （`POST /api/chat/resume` 以它做归属断言，见 `chatResume`）。
 */
export type ConfirmationPrompt = {
  gate_id: string;
  expert_name: string;
  summary: string;
};

/** 决策回传载荷（IFC-IB-301：`ConfirmationDecision`）。 */
export type ConfirmationDecision = { gate_id: string; approved: boolean };

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

/**
 * 普通边（无条件转移）。端点可能是真实节点，也可能是保留合成端点 `START` / `END`
 * —— 后者**不**出现在 `nodes` 里，是图的入口与出口（见后端 `RESERVED_GRAPH_ENDPOINTS`）。
 */
export type EdgeSpec = { from_node: string; to_node: string };

export type OrchestrationSpecInput = {
  nodes: string[];
  conditional_edges: ConditionalEdgeSpec[];
  edges: EdgeSpec[];
};

/** 工具参数取值（IFC-IB-340；`name` 用 `<tool>.<param>` 限定名声明归属工具）。 */
export type ToolParamValue = { name: string; value: string };

export type ToolGrantSpec = {
  expert_name: string;
  tool_names: string[];
  /** REV-16-2 加成式扩展（IFC-IB-340）：工具参数取值；旧文档缺省为空。 */
  param_values?: ToolParamValue[];
};

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
  edges: EdgeSpec[];
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
 * REV-16-2 提示词分层类型（IFC-IB-352 / 354；与后端 `ibweb/views.py` **逐字段对齐**）。
 *
 * 独立提示词目录是**提示词域**的真源（ADR-15-R1）；界面只呈现与编辑，**视图侧零持久化**。
 */
export type PromptLayer = 'main' | 'fallback';

export type PromptLayerMeta = { exists: boolean; content_hash: string };

export type PromptExpertEntry = {
  name: string;
  cn_label: string;
  layers: Record<PromptLayer, PromptLayerMeta>;
  /**
   * 代码内置兜底（REV-17 / ADR-36）：两层文件皆缺时**实际生效**的提示词。
   *
   * **只读** —— 它是代码里的进程常量，界面**不**为它提供写入口（否则又回到「同一语义两个
   * 可写入口」的重叠真源）。此处仅用于让用户看见「兜底到底是什么」。
   */
  builtin_fallback: string;
};

/** 工具参数规格（IFC-IB-340）：由后端从**既有工具声明**派生；界面据此生成控件。 */
export type ToolParamSpec = {
  name: string;
  type: 'int' | 'float' | 'bool' | 'str';
  default: string;
  minimum: number | null;
  maximum: number | null;
  choices: string[] | null;
};

export type PromptListEnvelope = {
  experts: PromptExpertEntry[];
  tool_param_specs: ToolParamSpec[];
  /** **既有**工具名单（ADR-30）：勾选只作用于既有工具集合，不新增工具本体。 */
  available_tools: string[];
  layout: { root_key: string; file_pattern: string; naming_rule: string };
  config_key_names: string[];
};

export type PromptLayerContent = { content: string; content_hash: string };

export type PromptSaveResult = {
  saved: boolean;
  content_hash: string;
  conflict: boolean;
  errors: ValidationErrorItem[];
};

// --------------------------------------------------------------------------- //
// REV-16-4（IFC-IB-356 / 361）：配置审计与存储态
// --------------------------------------------------------------------------- //

/**
 * 存储态（IFC-IB-361；`GET /api/config/storage-state`）。
 *
 * `memory` 表示「**配置仅内存生效、不跨重启保留**」（ADR-35）：`definition_store` /
 * `prompt_store` 为 `memory` 时，配置页**必须显式提示**（IFC-IB-363 非静默提示）。
 * `*_configured` 是「对应键名是否提供了非空值」——只作为补充信息，**不含任何路径值**。
 */
export type StorageState = {
  definition_store: 'memory' | 'file';
  prompt_store: 'memory' | 'file';
  definition_store_configured: boolean;
  prompt_store_configured: boolean;
};

/**
 * 配置审计条目（IFC-IB-356；`GET /api/config/audit`）。
 *
 * **字段白名单**：`changed_field_names` **只含字段名**、`detail_code` **只含字段名 /
 * 错误码** —— 后端**永不**回传任何配置取值（ADR-34）。
 */
export type ConfigAuditEntry = {
  timestamp: string;
  project: string;
  actor: string;
  action: string;
  changed_field_names: string[];
  result: 'saved' | 'rejected';
  detail_code: string | null;
};

export type ConfigAuditEnvelope = { items: ConfigAuditEntry[]; total: number };

// --------------------------------------------------------------------------- //
// R13（IFC-IB-316 ~ 321）：账户 / 会话
// --------------------------------------------------------------------------- //

/** 账户记录（与后端 `AccountSummary` **逐字段对齐**；**不含** `password_hash`）。 */
export type AccountSummary = {
  user_id: string;
  username: string;
  /** `admin` = 全局账户；`ops` = 绑定单项目（等价既有 `manager` 语义）。 */
  role: 'admin' | 'ops';
  project_id: string | null;
  status: 'active' | 'disabled';
  must_change_password: boolean;
};

/**
 * `POST /api/auth/login` 的成功体（IFC-IB-316）。
 *
 * `token` **只在这一处**出现：写进 `sessionStorage` 后立即丢弃，绝不进 URL / Cookie /
 * `localStorage`（令牌进 URL 会被 nginx 访问日志完整记录，FreeArk 已泄露过一次）。
 */
export type LoginResult = {
  token: string;
  expires_at: string;
  must_change_password: boolean;
  user: AccountSummary;
};

/** `GET /api/auth/me`（IFC-IB-318）。 */
export type CurrentUser = {
  user_id: string;
  username: string;
  role: 'admin' | 'ops';
  project_id: string | null;
  must_change_password: boolean;
};

export type AccountListEnvelope = { items: AccountSummary[] };

// --------------------------------------------------------------------------- //
// R14（IFC-IB-333 / 336）：项目上下文
// --------------------------------------------------------------------------- //

/**
 * `GET /api/projects` 的项目条目（IFC-IB-333；与后端**逐字段对齐**）。
 *
 * `is_current` = 该项目是否等于**本请求**的服务端 `effective_project`
 * （admin 未选定当前项目时为全局哨兵，故全部为 `false`）。
 */
export type ProjectSummary = {
  project_id: string;
  name: string;
  is_current: boolean;
};

export type ProjectListEnvelope = { items: ProjectSummary[] };

/**
 * 项目头提供者（IFC-IB-336）：返回要附加到请求头的项目上下文键值对。
 *
 * 由 `app/env.ts` 用 `projectContext`（IFC-IB-335）注入 —— `client.ts` **不** import
 * `stores/project.ts`（否则 `client.ts ← project.ts ← client.ts` 形成 ESM 循环依赖）。
 * 提供者缺省 / 返回空对象时**不注入** `X-IB-Project`（保持 fail-closed）。
 */
export type ProjectHeaderProvider = () => Record<string, string>;

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

/**
 * 客户端配置键（tech_stack §1.4 登记的键名；**只登记键名，不含任何值**）。
 *
 * Vite 只把 `VITE_` 前缀的环境变量暴露给客户端代码，因此登记的 `IB_AUTH_*` 在构建期
 * 对应 `VITE_IB_AUTH_*`（前缀是打包器的暴露机制，不是键名漂移）。未设置时用默认值 ——
 * 这两个键是**可选**的接缝（供接入方改登录路径 / 令牌存储键），不是必填配置。
 *
 * ## 为什么 `import.meta.env` 要防御性取值
 *
 * 本文件需能被**离线自检脚本**直接 `import`（Node 的类型擦除，见文件头 `parseSseStream`
 * 说明与 `scripts/sse_parser_selfcheck.mts`）。Node 下 `import.meta.env` **不存在**
 * （它是 Vite 的注入），直接读属性会 `TypeError` 并令整个模块无法导入 —— 这是本文件
 * 自身契约（可被自检导入）与实际行为的一处落差，故在此显式回退为空对象。
 * Vite 构建期 `import.meta.env` 恒有定义，行为逐位不变。
 */
const ENV: Record<string, string | undefined> = import.meta.env ?? {};
const LOGIN_PATH = ENV.VITE_IB_AUTH_LOGIN_PATH ?? '/api/auth/login';
const TOKEN_KEY = ENV.VITE_IB_AUTH_SESSION_STORAGE_KEY ?? 'ib_token';

/**
 * 401 全局回调（R13）：令牌失效时由 `decode()` 触发，交给会话层跳登录页。
 *
 * 为什么用回调而不是让每个页面各自处理：R1~R12 由 `App.vue` 向每个页面传
 * `@unauthorized` 监听器，**每一个**新页面都要记得接上，漏一个就表现为「这个页面 401 后
 * 白屏」。R13 改为在 `decode()` 这个**唯一**的 401 发生地点回调一次 —— 页面不再负责
 * 「登录态」这件事（页面只负责自己的业务错误）。
 */
let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

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
   * 项目上下文头提供者（IFC-IB-336）。缺省 `null` ⇒ `headers()` **不注入**
   * `X-IB-Project`（fail-closed：未选项目即不泄露）。由 `app/env.ts` 唯一装配。
   */
  private projectHeaderProvider: ProjectHeaderProvider | null = null;

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

  /**
   * 装配项目头提供者（IFC-IB-336 的**唯一**注入点接线）。只在 `app/env.ts` 调用一次。
   *
   * 为什么不把项目作为 `headers()` / 各调用点的参数：那会造出**第二注入点** ——
   * 一旦某个调用点忘记传（例如新增的 SSE 调用），就表现为「该请求静默 fail-closed」。
   * 由提供者中心化取值，`headers()` 是**唯一**决定是否注入的地方。
   */
  setProjectHeaderProvider(provider: ProjectHeaderProvider | null): void {
    this.projectHeaderProvider = provider;
  }

  /** 从提供者取项目头；提供者缺省 / 抛错 ⇒ 空对象（**不注入**，fail-closed）。 */
  private projectHeader(): Record<string, string> {
    if (!this.projectHeaderProvider) return {};
    try {
      return this.projectHeaderProvider() ?? {};
    } catch {
      return {};
    }
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

  /**
   * 请求头构造 —— `X-IB-Project` 的**唯一**注入点（IFC-IB-336）。
   *
   * `chatStream`（`GET /api/chat/stream`）与 `chatResume`（`POST /api/chat/resume`）
   * 均已调用本方法，故扩展此处即**自动覆盖两个 SSE 调用点** —— 调用点**不得**重复拼头。
   * 项目头置于 `extra` 之后，确保其值只来自 `projectContext`（提供者），不被调用点覆盖。
   */
  private headers(extra?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...extra,
      ...this.projectHeader(),
    };
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
        // R13：唯一 401 发生点 → 通知会话层（跳登录页）。登录端点自身的 401 也不例外：
        // 会话层据此清态即可，**不得**在登录页面上再跳转（由会话层判断当前路由）。
        try {
          unauthorizedHandler?.();
        } catch {
          /* 回调失败不得掩盖原始错误 */
        }
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
  // IFC-IB-352：独立提示词目录（第二真源，ADR-15-R1）
  // ------------------------------------------------------------------ //

  /** 读取提示词元数据 + 工具参数规格（**不含正文**）。`503` = 目录不可读（fail-closed）。 */
  promptList(): Promise<PromptListEnvelope> {
    return this.request<PromptListEnvelope>('/api/config/prompts');
  }

  /** 读取单个专家的单层提示词正文 + 语义哈希（`404` = 该层不存在）。 */
  promptLayer(expert: string, layer: PromptLayer): Promise<PromptLayerContent> {
    return this.request<PromptLayerContent>(
      `/api/config/prompts/${encodeURIComponent(expert)}/${layer}`,
    );
  }

  /**
   * 原子保存单层提示词（IFC-IB-352）。
   *
   * `expectedHash` 传该层当前 `content_hash` 以启用**乐观并发**；服务端不一致时返回 `409`
   * （抛 `ApiClientError`），界面须提示重新载入 —— **不静默覆盖**。
   * 保存成功后**不即时生效**（ADR-32：重启服务后重新装配才生效）。
   */
  savePromptLayer(
    expert: string,
    layer: PromptLayer,
    content: string,
    expectedHash?: string | null,
  ): Promise<PromptSaveResult> {
    return this.request<PromptSaveResult>(
      `/api/config/prompts/${encodeURIComponent(expert)}/${layer}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, expected_hash: expectedHash ?? null }),
      },
    );
  }

  // ------------------------------------------------------------------ //
  // REV-16-4（IFC-IB-359 / 362）：配置审计与存储态（**只读**）
  // ------------------------------------------------------------------ //

  /**
   * 读取当前存储态（IFC-IB-362）——**单一来源 = 装配期实际选用的存储实现**。
   *
   * 界面据此判定是否**非静默提示**「配置仅内存生效、不跨重启保留」（IFC-IB-363）。
   * **只读**；`503` = 存储态不可读（fail-closed）——界面不得静默当作「文件态」。
   */
  storageState(): Promise<StorageState> {
    return this.request<StorageState>('/api/config/storage-state');
  }

  /**
   * 读取本项目的配置审计（IFC-IB-359）；承载**成功与失败**两类记录（结果码）。
   *
   * `project_id` **只认服务端结论**（`X-IB-Project` 由 `headers()` 单点注入，ops 恒为自身）。
   * **只读**；`503` = 审计不可读（fail-closed，后端不返回空集合冒充「无记录」）。
   */
  configAudit(limit = 50, offset = 0): Promise<ConfigAuditEnvelope> {
    return this.request<ConfigAuditEnvelope>(
      `/api/config/audit?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`,
    );
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
    const session_id = (sessionId || '').trim();
    // FND-R11-01 / AC-IB-20-01：**不得**回退到字面量 'default' —— 服务端会对缺失的
    // 会话标识显式 4xx。这里提前拦住，避免一次注定失败的往返；且「缺标识」与「显式用
    // default 会话」在前端也必须可区分（否则不同标签页会静默共用一个会话）。
    if (!session_id) {
      throw new ApiClientError({ status: 400, code: 'bad_request', message: '缺少会话标识 session_id' });
    }
    const query$ = new URLSearchParams();
    query$.set('q', query);
    query$.set('session_id', session_id);
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

  /**
   * 回传确认决策并续跑（IFC-IB-307）：`POST /api/chat/resume` → 续跑 SSE。
   *
   * **仅经 `Authorization` 头**（`headers()` 已注入）；请求体只放 `session_id` 与决策，
   * **不放令牌**。`403` / `404` / `409` / `503` 由 `decode()` 翻成可读 `ApiClientError`
   * （含中文提示）—— 调用方据此给出「会话已失效，请重新发起」这类回执，**不自动重跑**
   * （AC-IB-20-05 / 20-06）。
   */
  async chatResume(
    sessionId: string,
    decision: ConfirmationDecision,
    onEvent: (event: StreamEvent) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const session_id = (sessionId || '').trim();
    if (!session_id) {
      throw new ApiClientError({ status: 400, code: 'bad_request', message: '缺少会话标识 session_id' });
    }
    const response = await fetch(`${this.baseUrl}/api/chat/resume`, {
      method: 'POST',
      headers: this.headers({ Accept: 'text/event-stream', 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        session_id,
        decision: { gate_id: decision.gate_id, approved: decision.approved },
      }),
      signal,
    });
    if (!response.ok) {
      await this.decode(response);
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

  // ------------------------------------------------------------------ //
  // R13（IFC-IB-316 ~ 321）：账户 / 会话
  // ------------------------------------------------------------------ //
  //
  // 这一组方法**不需要** `Authorization` 头（`login` 尚无令牌），其余方法由 `headers()`
  // 统一注入 —— 页面上**不存在**第二处拼令牌的代码（IC-IB-01 的落点不变）。

  /**
   * 用户名 + 口令登录（IFC-IB-316）。
   *
   * 失败统一 `401`（后端**不区分**「不存在 / 口令错 / 停用」，防存在性探测预言机），
   * UI 据此只提示「用户名或口令不正确」。`429` 为条件性限速（OQ-IB-12）。
   * 成功即写入 `sessionStorage`（与 R1 的令牌位置一致，非 Cookie）。
   */
  async login(username: string, password: string): Promise<LoginResult> {
    const result = await this.request<LoginResult>(LOGIN_PATH, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    this.setToken(result.token);
    return result;
  }

  /** 注销当前会话（IFC-IB-317）→ `204`。无论成功与否都清除本地令牌。 */
  async logout(): Promise<void> {
    try {
      await this.request<null>('/api/auth/logout', { method: 'POST' });
    } finally {
      this.clearToken();
    }
  }

  /** 当前用户（IFC-IB-318）。用于刷新页面后恢复身份 / 判定改密态。 */
  me(): Promise<CurrentUser> {
    return this.request<CurrentUser>('/api/auth/me');
  }

  /**
   * 修改口令（IFC-IB-319）。成功后服务端会撤销**其他**会话并清除改密态。
   *
   * 首次登录强制改密走的**就是本方法** —— 服务端在改密态下只放行
   * `/api/auth/me`、`/api/auth/change-password`、`/api/auth/logout`（ADR-20），
   * 前端不承担「强制」职责（前端只是把限制可视化，绕过前端也无效）。
   */
  changePassword(oldPassword: string, newPassword: string): Promise<{ ok: boolean; must_change_password: boolean }> {
    return this.request('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
  }

  /** 续期当前会话（IFC-IB-320）→ 新的 `expires_at`。仅临近到期时服务端才真正延长。 */
  renewSession(): Promise<{ expires_at: string }> {
    return this.request('/api/auth/session/renew', { method: 'POST' });
  }

  /** 账户列表（IFC-IB-321，**仅 admin**；非 admin 后端 403）。 */
  listAccounts(projectId?: string): Promise<AccountListEnvelope> {
    const suffix = projectId ? `?project_id=${encodeURIComponent(projectId)}` : '';
    return this.request<AccountListEnvelope>(`/api/accounts${suffix}`);
  }

  /** 新建 ops 账户（IFC-IB-321，仅 admin；必须绑定 `project_id`）。 */
  createAccount(input: {
    username: string;
    password: string;
    project_id: string;
    role?: 'ops';
  }): Promise<AccountSummary> {
    return this.request<AccountSummary>('/api/accounts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'ops', ...input }),
    });
  }

  /** 停用账户（IFC-IB-321，仅 admin）；服务端同时撤销其全部会话。 */
  disableAccount(userId: string): Promise<AccountSummary> {
    return this.request<AccountSummary>(`/api/accounts/${encodeURIComponent(userId)}/disable`, {
      method: 'POST',
    });
  }

  /** 重置他人口令（IFC-IB-321，仅 admin，条件性 OQ-IB-14）；被重置者下次登录须改密。 */
  resetAccountPassword(userId: string, newPassword: string): Promise<{ user_id: string; must_change_password: boolean }> {
    return this.request(`/api/accounts/${encodeURIComponent(userId)}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: newPassword }),
    });
  }

  // ------------------------------------------------------------------ //
  // R14（IFC-IB-333）：项目枚举
  // ------------------------------------------------------------------ //

  /**
   * 列出**当前主体可见**的项目（IFC-IB-333）。
   *
   * 授权口径由服务端裁定：admin 见全部；ops 仅见自身（结果集长度恒为 1）。
   * 该端点**不是**项目级端点 —— 全局主体未选定项目时也返回 200。
   * 返回 `items`（`ProjectSummary[]`），由 `projectContext.load` 消费。
   */
  async listProjects(): Promise<ProjectSummary[]> {
    const envelope = await this.request<ProjectListEnvelope>('/api/projects');
    return envelope.items;
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
