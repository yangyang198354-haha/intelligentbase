<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-27T00:48:17+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements_spec.md</file>
    <file>user_stories.md</file>
    <file>architecture_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计（REV-26 增量）— 可视化配置：热生效 / 自由 DAG / 版本化 / 三档权限 / Agent Builder

**范围**：只写 REV-26 增量；基线 `docs/module_design.md`（只读）继续有效。模块 = 本次**新建 / 修改**的代码单元，记为 `MOD-R26-NN`（编号即拓扑序，每条依赖边从高编号指向低编号，见 §依赖关系）；接口记为 `IFC-R26-NNN`。基线模块（`MOD-IB-xx`）只作"被修改的宿主"出现，并标注"修改现有"。
**书写约定**：签名为 Python ≥3.11 类型注解 / TypeScript 类型；Protocol 方法体的 `...` 仅表示"无实现"；不写函数体。所有错误响应沿用现有信封 `{"error": {"code": str, "message": str, "items"?: [...], "receipt"?: {...}}}`。所有 HTTP 端点：凭据只经 `Authorization: Bearer`（`?token=` 由既有中间件直接 400）；项目归属只认服务端结论 `ctx.authz.project_id`（admin 经 `X-IB-Project`），请求体中的项目标识一律忽略；"不存在"与"不属于本项目"返回同一状态码（404）。

---

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责（一句话） | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-R26-01 | 核心类型与端口（图 / 版本 / 范围 / 档位） | 新建 `src/ib/core/graph.py`；修改 `src/ib/core/types.py`、`src/ib/core/ports.py`、`src/ib/core/__init__.py`（宿主 MOD-IB-01） | 定义图规格、专家规格扩展、版本 / 差异 / 冲突值对象与新端口 Protocol | FUNC-005/008/009/011/012/015/017；NFUNC-004/012 | — |
| MOD-R26-02 | 图纯函数 | 新建 `src/ib/config/graph.py`（宿主 MOD-IB-02） | 图合法性校验、规范化默认图、层归一化、条件谓词求值（均为纯函数） | FUNC-006/011/013；NFUNC-010/012/013；US-006/011/013/021 | 01 |
| MOD-R26-03 | 配置访问档位纯函数 | 新建 `src/ib/config/access.py`（宿主 MOD-IB-02） | 由主体推导 view / edit / manage，端点所需档位表（纯函数） | FUNC-010；NFUNC-007/013；US-010 | 01 |
| MOD-R26-04 | 定义文档 v2 | 修改 `src/ib/config/definition.py`（宿主 MOD-IB-02） | schema v1/v2 载入 / 序列化 / 校验 / 白名单 / 语义哈希（省略默认值）/ 首存升级 | FUNC-005/006/008/009/011/012/013；NFUNC-012；US-005/008/011/012/013/020 | 01, 02 |
| MOD-R26-05 | 版本化纯函数 | 新建 `src/ib/config/versioning.py`（宿主 MOD-IB-02） | 快照构造 / 清单哈希 / 差异 / 三方冲突 / 提示词文本校验 | FUNC-016/017；NFUNC-005/013；US-016/017/018 | 01, 02, 04 |
| MOD-R26-06 | 台账扩展（版本 / 草稿 / 缓存 / 档位 / 审计 / 目录解析） | 新建 `src/ib/ledger/config_versions.py`；修改 `src/ib/ledger/schema.py`、`config_audit.py`、`accounts.py`、`tree.py`、`__init__.py`（宿主 MOD-IB-11） | 版本存储（pending / published / aborted）、草稿、评审缓存、账号档位、审计扩列与保留端口、目录子树文档解析 | FUNC-009/010/014/015/017；NFUNC-002/005/006；US-009/010/014/015/017/018/023 | 01 |
| MOD-R26-07 | 工具按 agent 绑定 | 修改 `src/ib/tools/__init__.py`（宿主 MOD-IB-17） | 按单个 agent 的授权 / 参数 / 目录范围构造工具列表 | FUNC-007/009；NFUNC-007/008；US-007/009 | 01 |
| MOD-R26-08 | LLM 客户端 | 修改 `src/ib/llm/__init__.py`（宿主 MOD-IB-20） | 有界 LRU 客户端缓存；工具循环上限与未授权回调；`complete()`（Builder 用） | FUNC-008/009/018；NFUNC-003/008/015；US-008/009/024 | 01 |
| MOD-R26-09 | 检索范围与路由候选集 | 修改 `src/ib/retrieval/__init__.py`（宿主 MOD-IB-15）、`src/ib/routing/intent.py`（宿主 MOD-IB-19） | 检索按资料目录范围过滤；路由器按候选集收窄 | FUNC-006/009；NFUNC-007；US-006/009 | 01 |
| MOD-R26-10 | DAG 编译与执行 | 新建 `src/ib/orchestration/dag.py`；修改 `src/ib/orchestration/__init__.py`（宿主 MOD-IB-22） | GraphSpec → LangGraph（层归一化 + 中继）；agent / route / condition / join / confirm 节点语义；安全网 | FUNC-006/011/014/015；NFUNC-002/003/010；US-011/014/015/021 | 01, 02 |
| MOD-R26-11 | Agent Builder | 新建 `src/ib/builder/`（`types.py`、`egress.py`、`adapt.py`、`rubric.py`、`service.py`、`assets/*.md`） | 生成 / 适配 / 自评 / 优化；单点外发 + 审计；评审缓存 | FUNC-004/018/019/020/021/022；NFUNC-006/008/014/015；US-004/024~028/030 | 01, 02, 04, 05 |
| MOD-R26-12 | 运行时快照与缓存 / 试运行 | 新建 `src/ib/runtime/`（`compile.py`、`cache.py`、`trial.py`） | 版本快照编译为不可变运行时配置；head 探测、单飞后台编译、原子换引用；试运行 | FUNC-014/015/023；NFUNC-001/002/003/004；US-014/015/029 | 01, 02, 04, 05, 07, 09, 10 |
| MOD-R26-13 | 配置发布服务 | 新建 `src/ib/confsvc/`（`publish.py`、`drafts.py`） | 预览 / 发布 / 回滚 / 采纳漂移 / 恢复；草稿副本 | FUNC-014/016/017；NFUNC-002/005/006；US-014/016/017/018/020 | 01, 02, 04, 05 |
| MOD-R26-14 | 组合根与账号 glue | 修改 `src/ibweb/composition.py`、`src/ibweb/accounts/__init__.py`、`src/ibweb/views.py`（聊天 / 旧配置端点 / 账号创建 / 审计端点）、`src/ibweb/serializers.py`（宿主 MOD-IB-23） | 装配新对象；聊天端点按快照取编排器并钉版本；旧 `PUT` 退化为发布包装；`cfg:<level>` 令牌 | 全部（装配）；FUNC-010/014/015；NFUNC-004/007 | 01, 06, 07, 08, 09, 10, 11, 12, 13 |
| MOD-R26-15 | 配置 HTTP 端点 | 新建 `src/ibweb/config_views.py`；修改 `src/ibweb/urls.py` | status / validate / preview / publish / versions / rollback / adopt-drift / drafts / access / trial | FUNC-001~003/010/012~017/023；NFUNC-005/007/011；US-001/010/013~018/029 | 03, 14 |
| MOD-R26-16 | Builder HTTP 端点 | 新建 `src/ibweb/builder_views.py`；修改 `src/ibweb/urls.py` | draft / evaluate / optimize / review-existing | FUNC-004/018~022；NFUNC-014/015；US-024~028/030 | 03, 11, 14 |
| MOD-R26-17 | worker 维护步骤 | 修改 `src/ibweb/worker.py`（宿主 MOD-IB-23） | 修剪版本 / 过期草稿 / 评审缓存；审计 1 年保留；陈旧 pending 回收 | NFUNC-006；FUNC-017；US-017/023 | 06, 14 |
| MOD-R26-18 | 前端 API 客户端与类型 | 修改 `src/frontend/src/api/client.ts`；新建 `src/frontend/src/stores/configDraft.ts`（宿主 MOD-IB-24） | HTTP 调用与 DTO 类型；草稿 / 脏标记 / 基线版本状态 | 全部前端需求 | HTTP 契约 |
| MOD-R26-19 | 前端画布组件 | 新建 `src/frontend/src/components/config/`：`FlowCanvas.vue`、`NodePalette.vue`、`NodeHoverCard.vue`、`EdgeHoverCard.vue`、`AgentDetailPanel.vue`、`graphModel.ts` | 画布编辑、悬停卡片、详情面板、图↔表单模型 | FUNC-001/002/003/005/006/007/008/009/011/012；NFUNC-008/009；US-001/002/003/005~009/011/012/022 | 18 |
| MOD-R26-20 | 前端发布 / 版本 / 试运行 / Builder 组件 | 新建 `PublishDialog.vue`、`ConflictDialog.vue`、`VersionHistory.vue`、`TrialPanel.vue`、`BuilderDrawer.vue`、`BuilderEvalView.vue` | 差异确认、冲突、历史与回滚、试运行、Builder 交互 | FUNC-004/016~022/023；NFUNC-005/014/015；US-004/014~018/024~030 | 18, 19 |
| MOD-R26-21 | 前端页面壳 | 修改 `src/frontend/src/views/ConfigPage.vue`（收敛为页面壳） | 组合各组件；去掉"重启后生效"提示；权限驱动的控件可用态 | FUNC-001~003/014；US-003/014 | 18, 19, 20 |
| MOD-R26-22 | 迁移 / 自检 / 部署资产 | 新建 `src/deploy/migrations/008_config_versions.sql`、`src/scripts/hot_effect_probe.py`；修改 `src/deploy/checklists.txt`、`src/deploy/env.example`、`src/scripts/selfcheck.py`、`.github/workflows/ci.yml` 迁移检查段 | 迁移快照、探针、静态规则、检查清单、CI 单源比对 | NFUNC-001/004/006/012/014 | — |

---

## 模块详情

### MOD-R26-01 核心类型与端口

**职责**：定义图 / 专家扩展 / 版本 / 差异 / 冲突 / 范围 / 档位等 frozen 值对象与新端口 Protocol（零依赖层）。
**外部依赖**：仅 stdlib。

**IFC-R26-001 图规格（新建 `src/ib/core/graph.py`）**

```python
NodeKind = Literal["start", "end", "route", "agent", "condition", "join", "confirm"]
InputMode = Literal["query_only", "with_upstream"]
ELSE_BRANCH: Final[str] = "__else__"
RELAY_PREFIX: Final[str] = "__relay__"
GRAPH_MAX_NODES: Final[int] = 60          # [ASSUMPTION A-R26-02]
GRAPH_MAX_EDGES: Final[int] = 200
NODE_ID_PATTERN: Final[str] = r"^[a-z0-9][a-z0-9_-]{0,47}$"   # 结构节点 id；agent 节点 id = 专家 name（沿用 ExpertSpec 命名规则）

@dataclass(frozen=True, slots=True)
class ConditionBranch:
    key: str                                   # 1..32 字符，不得为 ELSE_BRANCH
    keywords: tuple[str, ...] = ()             # kind="keyword" 时 ≥1 条，每条 1..32 字符，≤20 条

@dataclass(frozen=True, slots=True)
class ConditionPredicate:
    kind: Literal["keyword", "upstream_degraded"]     # OQ-R26-A03；无表达式 / 代码
    branches: tuple[ConditionBranch, ...] = ()        # keyword：≥1；upstream_degraded：固定分支键 "degraded"（不由用户配置，此处为空）

@dataclass(frozen=True, slots=True)
class GraphNode:
    id: str
    kind: NodeKind
    x: float = 0.0                              # 展示信息（INF-1）；有限数，|x| ≤ 100000
    y: float = 0.0
    expert: str | None = None                   # kind="agent" 必填且 == id
    input_mode: InputMode = "query_only"        # kind="agent"
    predicate: ConditionPredicate | None = None # kind="condition" 必填
    message: str = ""                           # kind="confirm" 必填，1..200 字符，由配置者提供

@dataclass(frozen=True, slots=True)
class GraphEdge:
    id: str                                     # NODE_ID_PATTERN
    source: str
    target: str
    branch_key: str | None = None               # None = 无条件边；route / condition 出边必须有值

@dataclass(frozen=True, slots=True)
class GraphSpec:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
```

**IFC-R26-002 专家规格与文档扩展（修改 `src/ib/core/types.py`，全部 append-only、带默认值）**

```python
KnowledgeMode = Literal["all", "folders"]
ExpertStatus = Literal["active", "disabled"]

@dataclass(frozen=True, slots=True)
class KnowledgeScope:
    mode: KnowledgeMode = "all"                 # "all" = 项目内全部资料（存量默认）
    folder_ids: tuple[str, ...] = ()            # mode="folders"：空 = 无知识范围（0 命中）；≤200 项

# ExpertSpecInput 末尾追加（既有 7 个字段、顺序、语义不变）：
#     status: ExpertStatus = "active"
#     max_steps: int | None = None              # 1..8；None = 默认 4（OQ-R26-A05）
#     knowledge_scope: KnowledgeScope = KnowledgeScope()
# DefinitionDocument 末尾追加：
#     graph: GraphSpec | None = None            # schema_version=2 时必填
# SessionState / CompletionPayload 末尾追加：
#     config_version: int = 0
# ConfigAuditEntry 末尾追加（见 IFC-R26-054）。
```

**IFC-R26-003 版本 / 差异 / 冲突值对象**

```python
@dataclass(frozen=True, slots=True)
class PromptLayers:
    main: str | None
    fallback: str | None

@dataclass(frozen=True, slots=True)
class ConfigSnapshot:
    definition: DefinitionDocument
    prompts: tuple[tuple[str, PromptLayers], ...]        # 按专家名升序；只含 definition.experts 中的专家

VersionKind = Literal["publish", "rollback", "baseline", "adopt"]
VersionStatus = Literal["pending", "published", "aborted"]

@dataclass(frozen=True, slots=True)
class VersionRecord:
    project_id: str
    version: int
    parent_version: int
    status: VersionStatus
    kind: VersionKind
    rolled_back_to: int | None
    actor: str
    created_at: str                                      # UTC ISO8601
    summary: str                                         # 系统生成，≤200 字符，不含提示词正文
    manifest_hash: str
    snapshot_bytes: int

@dataclass(frozen=True, slots=True)
class HeadState:
    project_id: str
    published_version: int                               # 0 = 虚拟版本（存量 v1 项目尚无版本行）
    pending_version: int | None
    updated_at: str

DiffKind = Literal[
    "agent_added", "agent_removed", "agent_disabled", "agent_enabled", "agent_field", "prompt",
    "tool_grant", "tool_param", "knowledge_scope", "route_param",
    "node_added", "node_removed", "node_changed", "edge_added", "edge_removed", "edge_changed", "layout",
]

@dataclass(frozen=True, slots=True)
class DiffItem:
    kind: DiffKind
    object_id: str                                       # agent 名 / 节点 id / 边 id / "route"
    field: str                                           # 如 "tool_names"、"main"、"branch_key"
    before: str | None                                   # 摘要 ≤120 字符；prompt 只给 长度 + 哈希前 8 位，不含正文
    after: str | None

@dataclass(frozen=True, slots=True)
class ConflictItem:
    kind: str                                            # "agent" / "node" / "edge" / "route" / "prompt"
    object_id: str
    fields: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ConflictReceipt:
    base_version: int
    head_version: int
    base_available: bool                                 # False = base 版本已被修剪，conflicts 退化为全部对象
    conflicts: tuple[ConflictItem, ...]

@dataclass(frozen=True, slots=True)
class ProjectRuntimeView:                                # 运行期只读视图（不含编译产物），供编排层消费
    version: int
    experts: tuple[ExpertSpec, ...]                      # 仅 status="active"
    default_expert: str
    prompts: Mapping[str, str]                           # 专家名 → 生效提示词（main > fallback）
    prompt_sources: Mapping[str, Literal["main_file", "fallback_file"]]
    cn_labels: Mapping[str, str]
    agents: Mapping[str, "AgentRuntime"]
    graph: GraphSpec
    max_expert_steps: int                                # 图级上限（route.max_expert_steps）

@dataclass(frozen=True, slots=True)
class AgentRuntime:
    name: str
    system_prompt: str
    tools: tuple[BoundTool, ...]                         # 仅本 agent 被授权的工具，参数 / 目录范围已闭包注入
    max_steps: int                                       # 1..8，传给 run_tool_loop(max_iterations)
    input_mode: InputMode
```

**IFC-R26-004 新端口（修改 `src/ib/core/ports.py`；既有端口的方法集不变）**

```python
BeginOutcome = Literal["ok", "stale_base", "busy"]

@dataclass(frozen=True, slots=True)
class NewVersion:
    kind: VersionKind
    actor: str
    summary: str
    rolled_back_to: int | None
    manifest_hash: str

@dataclass(frozen=True, slots=True)
class BeginResult:
    outcome: BeginOutcome
    version: int | None                                  # outcome="ok" 时为新（pending）版本号
    head_version: int                                    # stale_base / busy 时回执当前 head
    pending_version: int | None

class ConfigVersionStore(Protocol):
    def head(self, project_id: str) -> HeadState: ...
    def get_version(self, project_id: str, version: int) -> tuple[VersionRecord, ConfigSnapshot] | None: ...
    def list_versions(self, project_id: str, *, limit: int, before_version: int | None) -> tuple[VersionRecord, ...]: ...
    def begin_publish(self, project_id: str, *, base_version: int, new: NewVersion,
                      snapshot: ConfigSnapshot, extra_baseline: ConfigSnapshot | None,
                      now: str, stale_after_s: float) -> BeginResult: ...
    def commit_publish(self, project_id: str, version: int, *, now: str, keep: int) -> HeadState: ...
    def abort_publish(self, project_id: str, version: int, *, reason_code: str, now: str) -> bool: ...
    def claim_stale_pending(self, project_id: str, *, now: str, stale_after_s: float) -> int | None: ...
    def prune_all(self, *, keep: int) -> int: ...        # 维护步骤专用：保留 head + 每项目最近 keep 个已发布版本

@dataclass(frozen=True, slots=True)
class DraftRecord:
    draft_id: str
    project_id: str
    owner: str
    label: str                                           # 1..60 字符
    base_version: int
    created_at: str
    payload_bytes: int

class ConfigDraftStore(Protocol):
    def save(self, project_id: str, owner: str, *, label: str, base_version: int, payload_json: str, now: str,
             max_per_owner: int) -> DraftRecord: ...        # 超出配额 → ValidationError
    def list(self, project_id: str, owner: str) -> tuple[DraftRecord, ...]: ...
    def load(self, project_id: str, owner: str, draft_id: str) -> tuple[DraftRecord, str] | None: ...
    def delete(self, project_id: str, owner: str, draft_id: str) -> bool: ...
    def purge_older_than(self, cutoff_iso: str) -> int: ...

class ConfigAuditRetention(Protocol):                    # 仅注入 ib-worker；Web 层不持有
    def purge_before(self, cutoff_iso: str) -> int: ...

class DocScopeResolver(Protocol):
    def live_doc_ids(self, project_id: str, folder_ids: Sequence[str], *, limit: int) -> tuple[tuple[str, ...], bool]: ...
    # 返回 (子树内存活且已索引的 doc_id，是否因 limit 被截断)；folder_ids 里不存在 / 非本项目的 id 贡献空集

class BuilderEvalCache(Protocol):
    def get(self, cache_key: str) -> str | None: ...
    def put(self, cache_key: str, *, rubric_version: str, result_json: str, now: str) -> None: ...
    def purge(self, *, keep: int, older_than_iso: str) -> int: ...

class AccountConfigLevelStore(Protocol):                 # 与 AccountStore 并列的小端口（AccountStore 的 13 方法不变）
    def get_config_level(self, user_id: str) -> ConfigLevel | None: ...
    def set_config_level(self, user_id: str, level: ConfigLevel, *, now: str) -> bool: ...
    def list_project_levels(self, project_id: str) -> tuple[tuple[str, str, ConfigLevel, str], ...]: ...  # (user_id, username, level, status)
```

**IFC-R26-005 档位类型**：`ConfigLevel = Literal["view", "edit", "manage"]`；`LEVEL_RANK: Final[Mapping[ConfigLevel, int]] = {"view": 0, "edit": 1, "manage": 2}`。
**依赖模块**：无。

---

### MOD-R26-02 图纯函数（`src/ib/config/graph.py`，新建）

**职责**：图合法性校验、规范化默认图、层归一化、条件谓词求值；framework-free、无 I/O、可离线单测（REQ-NFUNC-013）。

**IFC-R26-010 `validate_graph`**

```python
def validate_graph(
    graph: GraphSpec,
    *,
    experts: tuple[ExpertSpecInput, ...],
    default_expert: str,
) -> tuple[ValidationErrorItem, ...]: ...
```

返回空元组 = 合法；每条错误 `path` 指向节点 / 边（如 `graph.nodes[kb-agent]`、`graph.edges[e3]`），`message` 不回显任何提示词或凭据。**错误码清单（固定集合）**：
`graph_too_large`、`graph_start_end_count`、`graph_node_id_invalid`、`graph_node_id_duplicate`、`graph_node_id_reserved`、`graph_node_kind_unknown`、`graph_position_invalid`、`graph_agent_expert_unknown`、`graph_agent_expert_disabled`、`graph_agent_id_mismatch`、`graph_agent_duplicate`、`graph_edge_id_invalid`、`graph_edge_id_duplicate`、`graph_edge_endpoint_missing`、`graph_edge_self_loop`、`graph_edge_duplicate`、`graph_start_has_incoming`、`graph_end_has_outgoing`、`graph_branch_source_invalid`（分支边源不是 route / condition）、`graph_always_edge_from_branching_node`、`graph_branch_key_duplicate`、`graph_branch_else_missing`、`graph_branch_else_multiple`、`graph_route_branch_target_invalid`（route 的分支键须是目标 agent 的专家名，或 `__else__`）、`graph_condition_predicate_missing`、`graph_condition_branch_invalid`、`graph_confirm_message_invalid`、`graph_join_inputs`（join 入边 <2）、`graph_cycle`（列出环上节点）、`graph_unreachable_from_start`、`graph_no_path_to_end`、`graph_default_expert_unreachable`、`graph_default_expert_missing`。
**输入校验 / 复杂度**：O(V+E)；节点 / 边数先于其余检查判 `graph_too_large`（≤60 / ≤200），非法输入不抛异常。

**IFC-R26-011 `canonical_graph_from_experts`**

```python
def canonical_graph_from_experts(
    experts: tuple[ExpertSpecInput, ...],       # 仅取 status="active"
    default_expert: str,
    *,
    positions: Mapping[str, tuple[float, float]] | None = None,
) -> GraphSpec: ...
```

产出：`START → route-1 → 每个启用专家(agent, query_only) → END`；route 的每专家分支键 = 专家名，`__else__` → 默认专家；agent → END 无条件边。供 v1 读时规范化与"新建项目种子"共用（ADR-58）。

**IFC-R26-012 `layerize_graph`**

```python
@dataclass(frozen=True, slots=True)
class RelayNode:
    id: str                                      # f"{RELAY_PREFIX}{edge_id}_{k}"
    edge_id: str                                 # 被拆分的原边
    level: int

@dataclass(frozen=True, slots=True)
class PlannedEdge:
    source: str
    target: str
    branch_key: str | None                       # 仅原边的第一跳携带分支键；中继后续跳为 None
    origin_edge_id: str

@dataclass(frozen=True, slots=True)
class LayerPlan:
    levels: Mapping[str, int]                    # 原节点 id → 最长路径层号（START = 0）
    relays: tuple[RelayNode, ...]
    edges: tuple[PlannedEdge, ...]               # 每条边恰好跨 1 层
    max_level: int

def layerize_graph(graph: GraphSpec) -> LayerPlan: ...
# 前置条件：validate_graph 返回空；违反前置条件抛 ValueError（编程错误，非用户输入路径）
```

**IFC-R26-013 `evaluate_condition`**

```python
def evaluate_condition(
    predicate: ConditionPredicate,
    *,
    query: str,                                   # 已剥离历史前缀的当前提问
    upstream_degraded: bool,
) -> str: ...                                     # 返回命中的分支键，否则 ELSE_BRANCH
```

`keyword`：对 `query` 与关键词均做 `strip().lower()` 归一化（与路由关键词同口径），按分支声明顺序首个命中；`upstream_degraded`：已激活上游结果任一 `degraded` → `"degraded"`，否则 `ELSE_BRANCH`。
**依赖模块**：01。

---

### MOD-R26-03 配置访问档位（`src/ib/config/access.py`，新建）

**IFC-R26-020**

```python
LEVEL_TOKEN_PREFIX: Final[str] = "cfg:"

ConfigAction = Literal[
    "read", "validate", "preview", "publish", "draft", "trial", "builder",
    "rollback", "adopt_drift", "grant_access", "read_audit",
]

REQUIRED_LEVEL: Final[Mapping[ConfigAction, ConfigLevel]] = {
    "read": "view", "validate": "edit", "preview": "edit", "publish": "edit", "draft": "edit",
    "trial": "edit", "builder": "edit", "rollback": "manage", "adopt_drift": "manage",
    "grant_access": "manage", "read_audit": "manage",
}

def config_level_of(authz: AuthzContext) -> ConfigLevel: ...
def allows(level: ConfigLevel, action: ConfigAction) -> bool: ...
def level_token(level: ConfigLevel) -> str: ...                       # "cfg:edit"
def roles_with_level(roles: tuple[str, ...], level: ConfigLevel) -> tuple[str, ...]: ...
def can_grant(grantor: AuthzContext, *, grantor_project_id: str, target_project_id: str) -> bool: ...
```

判定规则：`admin` 角色恒 `manage`；含 `cfg:<level>` 令牌者取该档；仅有 `manager` 且无令牌（离线策略 / 旧令牌）视为 `manage`（兼容）；无任何角色 → `view`（已通过项目授权的主体）。`can_grant`：要求 `manage` 且 `target_project_id == grantor_project_id`（admin 经 `X-IB-Project` 选定后同理）。纯函数，无 I/O。
**依赖模块**：01。

---

### MOD-R26-04 定义文档 v2（修改 `src/ib/config/definition.py`）

**IFC-R26-030 载入 / 序列化**

```python
SUPPORTED_SCHEMA_VERSIONS: Final[frozenset[int]] = frozenset({1, 2})          # 取代 SUPPORTED_SCHEMA_VERSION == 1 的单值判定
def document_from_json(project_id: str, text: str) -> DefinitionDocument: ...  # 签名不变；v2 解析 graph / 新字段；未知 schema_version → ConfigError
def document_to_json(doc: DefinitionDocument) -> str: ...                      # v1 文档仍按原键集输出；v2 输出 graph，不输出 orchestration
```

**IFC-R26-031 校验入口（append-only 关键字）**

```python
def validate(doc: DefinitionDocument, *, known_tools: frozenset[str] | set[str] | None = None) -> ValidationReport: ...
def validate_two_domains(
    doc: DefinitionDocument,
    *,
    known_tools: tuple[str, ...] | frozenset[str] | set[str] | None = None,
    tool_param_specs: tuple[ToolParamSpec, ...] = (),
    prompt_refs: tuple[ExpertPromptDocumentRef, ...] = (),
    known_folder_ids: frozenset[str] | None = None,          # 新增；None = 跳过目录存在性校验（离线）
) -> ValidationReport: ...
```

v2 分支（`doc.schema_version == 2`）：v1 的 `orchestration` 校验（nodes 非空 / 条件边 branch_map）**不适用**，改调 `validate_graph`；追加校验码：`expert_status_invalid`、`expert_default_disabled`（默认专家不得停用）、`expert_max_steps_range`（1..8）、`expert_keywords_limit`（≤20）、`expert_exemplars_limit`（≤10）、`knowledge_scope_invalid`（`mode="folders"` 外携带 folder_ids，或 >200 项）、`knowledge_folder_missing`（`known_folder_ids` 给定时）、`tool_grant_expert_disabled`；停用专家不参与"关键词撞车 / 标签唯一"之外的运行期校验但名称 / 标签仍须唯一（保留名称，历史可显示）。`ValidationReport` 仍无 force / ignore / warn_only。

**IFC-R26-032 白名单与不可编辑判定**

```python
def editable_field_whitelist() -> frozenset[str]: ...      # 在原 16 项上追加：
#   "experts[].status", "experts[].max_steps", "experts[].knowledge_scope",
#   "graph", "graph.nodes", "graph.edges"
def non_editable_changes(current: DefinitionDocument, submitted: DefinitionDocument) -> tuple[ValidationErrorItem, ...]: ...
# v2：只拒绝 project_id 变更与 schema_version 降级 / 非法跳变；允许 1→2（且 submitted.graph 非空）
# v1→v1 仍按原规则拒绝 orchestration 变更（旧客户端 / 旧测试路径）
NON_EDITABLE_FIELDS: Final[frozenset[str]]                  # 去掉 "orchestration*" 三项在 v2 的约束，保留常量供 v1 路径
```

**IFC-R26-033 语义哈希稳定规则**：`_semantic_payload` 对 `status == "active"`、`max_steps is None`、`knowledge_scope == KnowledgeScope()` 的专家**省略**新键；`graph is None` 时省略 `graph` 键 → 存量 v1 文档 `content_hash` 与升级前**逐位相同**；v2 文档含 `graph`（含 x / y 坐标），故"仅改位置"也改变哈希（版本 +1，行为不变）。
**IFC-R26-034 首存升级**

```python
def upgrade_to_v2(doc: DefinitionDocument, *, positions: Mapping[str, tuple[float, float]] | None = None) -> DefinitionDocument: ...
```

纯函数：v1 → v2（`graph = canonical_graph_from_experts(...)`，`schema_version=2`，`orchestration` 置空，重算哈希）；已是 v2 原样返回。
**依赖模块**：01, 02。

---

### MOD-R26-05 版本化纯函数（`src/ib/config/versioning.py`，新建）

**IFC-R26-040 ~ 045**（依次为：快照构造 `build_snapshot`；清单哈希与序列化 `manifest_hash` / `snapshot_to_json` / `snapshot_from_json`；差异 `diff_snapshots` / `summarize_diff` / `is_layout_only`；三方冲突 `detect_conflicts`；提示词文本校验 `validate_prompt_texts`；常量 `PROMPT_LAYER_MAX_CHARS`）。framework-free、无 I/O、可离线单测（REQ-NFUNC-013）。

```python
PROMPT_LAYER_MAX_CHARS: Final[int] = 20000                # INF-4 占位

def build_snapshot(doc: DefinitionDocument, prompts: Mapping[str, PromptLayers]) -> ConfigSnapshot: ...
def manifest_hash(snapshot: ConfigSnapshot) -> str: ...    # sha256(规范化 JSON{definition 语义哈希, 各专家各层 prompt_content_hash})
def snapshot_to_json(snapshot: ConfigSnapshot) -> str: ...
def snapshot_from_json(text: str) -> ConfigSnapshot: ...  # 非法输入 → ConfigError
def diff_snapshots(base: ConfigSnapshot, new: ConfigSnapshot) -> tuple[DiffItem, ...]: ...
def summarize_diff(items: Sequence[DiffItem]) -> str: ... # ≤200 字符，如"新增 agent billing-agent；修改 工具授权 kb-agent"
def is_layout_only(items: Sequence[DiffItem]) -> bool: ...
def detect_conflicts(base: ConfigSnapshot | None, head: ConfigSnapshot, submitted: ConfigSnapshot) -> ConflictReceipt: ...
# base is None（已被修剪）→ base_available=False，conflicts = 全部对象
def validate_prompt_texts(prompts: Mapping[str, PromptLayers], *, experts: tuple[ExpertSpecInput, ...]) -> tuple[ValidationErrorItem, ...]: ...
# prompt_too_long（>20000）、prompt_fallback_empty（fallback 给出但全空白）、prompt_missing（启用专家两层皆缺）、prompt_orphan_expert（给了不存在 / 已停用专家的层）
```

`diff_snapshots` 覆盖：agent 增删 / 停用启用 / 字段（标签、关键词、示例句、标记位、`max_steps`）、提示词层（只给长度与哈希前 8 位）、工具授权增减与参数、知识范围、路由参数、节点 / 边增删改、仅坐标变化（`layout`）；相同输入输出确定、不含提示词正文与凭据。
**依赖模块**：01, 02, 04。

---

### MOD-R26-06 台账扩展

**文件**：新建 `src/ib/ledger/config_versions.py`；修改 `src/ib/ledger/schema.py`（DDL 生成器与 `ensure_schema`）、`config_audit.py`、`accounts.py`、`tree.py`、`__init__.py`（工厂）。

**IFC-R26-050 版本存储**

```python
class SqliteConfigVersionStore:                          # 实现 ConfigVersionStore；线程局部连接 + WAL + busy_timeout（同 SqliteAccountStore 纪律）
    def __init__(self, ledger_path: str) -> None: ...
class MemoryConfigVersionStore: ...                      # 离线 / 内存态替身；同一套一致性测试
def build_config_version_store(cfg: Any, *, ledger_path: str, file_backed: bool) -> ConfigVersionStore: ...
# file_backed=False（定义 / 提示词存储为内存态）→ MemoryConfigVersionStore
```

语义要点：`begin_publish` 在 `BEGIN IMMEDIATE` 内完成"核对 head == base_version → 不等返回 `stale_base`；`pending_version` 非空且未陈旧返回 `busy`；`extra_baseline` 非空且 head 为虚拟 0 时先写 `version=1` 基线再写新版本；插入 pending 版本行并置 `config_head.pending_version`"；`commit_publish` 一个事务内置 published、更新 head、清 pending、按 `keep` 修剪（不删 head 与 pending）；`claim_stale_pending` 对 `pending_version` 做 CAS，仅一个调用方得到版本号。

**IFC-R26-051 草稿 / 评审缓存**：`SqliteConfigDraftStore` / `MemoryConfigDraftStore`（实现 `ConfigDraftStore`）；`SqliteBuilderEvalCache` / `MemoryBuilderEvalCache`（实现 `BuilderEvalCache`）。草稿 `payload_json` ≤1 MiB，每 owner 每项目 ≤10。
**IFC-R26-052 DDL 单源**（`schema.py`）：

```python
CONFIG_VERSION_DDL_STATEMENTS: tuple[str, ...]            # config_versions / config_head / config_drafts / builder_eval_cache + 索引
USERS_ADDED_COLUMNS: tuple[tuple[str, str], ...]          # ("config_level", "TEXT NOT NULL DEFAULT 'manage' CHECK (config_level IN ('view','edit','manage'))")
CONFIG_AUDIT_ADDED_COLUMNS: tuple[tuple[str, str], ...]   # version_before / version_after INTEGER；object_summary TEXT
def config_versions_ddl_script() -> str: ...              # = 迁移 008 快照的单源
def missing_config_version_columns(connection) -> dict[str, list[str]]: ...
# ensure_schema(connection) 追加：补列（PRAGMA table_info 探测，沿用 _ensure_project_registry_columns 做法）→ 建表 / 索引
```

**IFC-R26-053 账号档位**：`SqliteAccountStore` / `MemoryAccountStore` 追加实现 `AccountConfigLevelStore`（IFC-R26-004）；`UserRecord` 末尾追加 `config_level: ConfigLevel = "manage"`（带默认值，既有构造点不受影响）；`_U_COLUMNS` 追加 `config_level`。
**IFC-R26-054 审计扩展**

```python
# ConfigAuditEntry 末尾追加（默认值使既有构造点不变）：
#     version_before: int | None = None
#     version_after: int | None = None
#     object_summary: tuple[str, ...] = ()      # 对象 id / 类别清单，如 ("agent:billing-agent", "edge:e12")；≤50 项，不含正文与凭据
# ConfigAuditStore.record(entry: ConfigAuditEntry) -> None            # 签名不变
# ConfigAuditStore.list_by_project(project: str, *, limit: int, offset: int, action: str | None = None) -> tuple[ConfigAuditEntry, ...]   # action 为 append-only 可选关键字
# 新动作名（action 为自由文本，无 CHECK）：config.publish / config.rollback / config.adopt_drift / access.grant / builder.egress / config.trial
# result 仍取 saved | rejected（CHECK 不变）
class SqliteConfigAuditStore:                 # 另实现 ConfigAuditRetention.purge_before
```

**IFC-R26-055 目录子树文档解析**：`EntryTreeStore.live_doc_ids_in_subtrees(project_id: str, folder_ids: Sequence[str], *, limit: int) -> tuple[tuple[str, ...], bool]`（`_TreeLogic` 后端无关逻辑 + `SqliteEntryTree`（递归 CTE）+ `MemoryEntryTree`）；`EntryTreeStore` 实例即 `DocScopeResolver`（`live_doc_ids = live_doc_ids_in_subtrees` 的别名适配器 `TreeDocScopeResolver(tree)`）。过滤条件：`revision_of IS NULL`（排除修订行）、`status = 'indexed'`、`folder_id` 落在所给目录及其子孙内、同 `project_id`；`limit` 命中时返回 `truncated=True`。
**依赖模块**：01；宿主基线 MOD-IB-11。

---

### MOD-R26-07 工具按 agent 绑定（修改 `src/ib/tools/__init__.py`）

**IFC-R26-060**

```python
def build_agent_tools(
    grant: ToolGrantSpec | None,                         # None = 该 agent 无任何授权 → 空列表
    *,
    registry: ToolRegistry,
    specs: tuple[ToolParamSpec, ...],
    scope: Scope,
    retrieval: Any,
    knowledge: KnowledgeScope,
) -> list[BoundTool]: ...
```

只用**该 agent 自己的** `ToolGrantSpec`（沿用 `build_authorized_tools` 的校验与参数闭包，传入 `(grant,)`），再 `bind_scope`；对声明 `needs_scope` 的检索类工具另以 `functools.partial` 闭包注入关键字 `knowledge`（不出现在工具的 JSON Schema `parameters` 中，LLM 不可见、不可改）。`knowledge.mode == "folders"` 且 `folder_ids` 为空 → 工具调用恒返回既有 `EMPTY_HINT` 且不查询向量库。`build_authorized_tools` / `bind_scope` 既有签名不变。
**输入校验**：未知工具 / 参数越界 → `ToolParamValidationError`（编译期 fail-fast，保存期已拦）。
**依赖模块**：01。

---

### MOD-R26-08 LLM 客户端（修改 `src/ib/llm/__init__.py`）

**IFC-R26-070 工具循环**

```python
class _PromptedClient:
    def run_tool_loop(
        self,
        prompt: str,
        tools: list[Any],
        *,
        max_iterations: int = 4,                          # 既有形参；agent 的 max_steps 经此传入（1..8）
        on_unauthorized: Callable[[str], None] | None = None,   # 新增；模型给出未绑定工具名时回调（只传工具名）
    ) -> str: ...
```

**IFC-R26-071 缓存与 Builder 调用**

```python
class OpenAiCompatibleProvider:
    def __init__(self, ..., client_cache_max: int = 128) -> None: ...        # 既有形参不变；_clients 改为有界 LRU
    def complete(self, system: str, user: str, *, temperature: float = 0.0,
                 timeout_s: float | None = None) -> str: ...                  # 实现侧扩展，LlmProvider 端口方法集不变
class FakeLlmProvider:        def complete(self, system: str, user: str, *, temperature: float = 0.0, timeout_s: float | None = None) -> str: ...  # 可编程返回 / 可注入"永不返回"
class UnconfiguredLlmProvider: def complete(...) -> str: ...                    # 抛 DependencyUnavailableError（可读、不含 Key 信息）
```

LRU 键沿用 `(temperature, system_prompt)`；`system_prompt` 只允许是装配期常量（ADR-36 规则保留）；键名 `IB_LLM_CLIENT_CACHE_MAX`（仅键名）。
**依赖模块**：01。

---

### MOD-R26-09 检索范围与路由候选集

**IFC-R26-080 检索**

```python
class RetrievalService:
    def __init__(self, ..., doc_scope_resolver: DocScopeResolver | None = None, doc_scope_max_ids: int = 5000) -> None: ...   # 既有形参不变
    def search(self, query: str, *, scope: Scope, top_k: int | None = None, score_threshold: float | None = None,
               knowledge: KnowledgeScope | None = None) -> RetrievalResult: ...
    def search_as_tool(self, query: str, *, scope: Scope, top_k: int | None = None, score_threshold: float | None = None,
                       knowledge: KnowledgeScope | None = None) -> ToolResult: ...
```

`knowledge is None` 或 `mode="all"` → 行为与既有逐位一致；`mode="folders"`：`folder_ids` 空 → 返回 `hits=[]`、`degraded=False`（"空范围"≠"依赖故障"，ADR-13 不变量）且**不绑定 / 不查询向量库**；否则经 `doc_scope_resolver.live_doc_ids` 得 `doc_ids` → `PointFilter(project_id, kb_ids, doc_ids=...)`（`project_id` 恒在，FM-1）；解析结果为空 → 同上空结果；集合被截断（超过 `doc_scope_max_ids`）→ 改为"不加 doc_ids、候选倍数 ×2、按 `resolve_live` 的目录后过滤"并记 `doc_scope_overflow` 日志；解析器故障 → `DegradeReason.LEDGER_UNAVAILABLE`（既有枚举，不新增）。进程内 5 s 缓存 `(project_id, folder_ids)`。
**IFC-R26-081 路由**

```python
class IntentRouter:
    def classify_experts(self, query: str, *, history: Sequence[Message] = (), scope: Scope,
                         allow_ood: bool = False, restrict_to: Sequence[str] | None = None) -> RouteDecision: ...
```

`restrict_to` 非空：L0 关键词 / L1 语义 / L2 LLM 的候选与"默认专家回落"均限制在该集合内（不在集合内的专家被忽略）；`None` → 既有行为。
**依赖模块**：01。

---

### MOD-R26-10 DAG 编译与执行

**文件**：新建 `src/ib/orchestration/dag.py`；修改 `src/ib/orchestration/__init__.py`。

**IFC-R26-090 编译器**

```python
@dataclass(frozen=True, slots=True)
class TraceEntry:
    node_id: str
    kind: NodeKind
    status: Literal["ran", "skipped_inactive", "skipped_step_cap", "failed", "suspended"]
    elapsed_ms: int

@dataclass(frozen=True, slots=True)
class CompiledDag:
    graph: Any                                          # 编译后的 LangGraph
    plan: LayerPlan
    config_version: int
    has_confirm: bool

def compile_dag(
    graph: GraphSpec,
    *,
    view: ProjectRuntimeView,
    router: Any,                                         # IntentRouter 兼容（classify_experts 含 restrict_to）
    llm: Any,                                            # LlmProvider 兼容
    config: GraphConfig,
    scope: Scope,
    checkpointer: Any | None = None,                     # 含 confirm 节点时必填（MemorySaver）；否则 StartupError
) -> CompiledDag: ...
```

语义（ADR-57）：中继节点无操作；`route` 以其出边目标 agent 的专家名为候选调用 `router.classify_experts(..., restrict_to=候选)`，命中者的同名分支边激活，无命中走 `__else__`；`condition` 调 `evaluate_condition`；`agent` 以 `AgentRuntime.system_prompt` 作 system 位（空串传 `None` 守卫保留，ADR-36 决定 3）、`run_tool_loop(max_iterations=max_steps, on_unauthorized=记录)`，`with_upstream` 时把最近已激活上游 agent 输出作为"上游材料"并入 **human** 位；`join` 透传；`confirm` 用 `interrupt_before` 挂起并产出 `confirmation_required`（话术 = 节点 `message`）；每个 agent 失败降级为 `ExpertResult(degraded=True)`（沿用既有 reason 取值）；执行 agent 数超过 `view.max_expert_steps` → 后续 `skipped_step_cap`，单个 `route` 命中数超过上限 → 隐式 `general`（与旧 `_fan_out` 一致）；运行结束无任何可用输出 → 默认专家直接作答 → 仍失败则 `general` 文本（安全网）。每次回答产出 `TraceEntry[]`，以结构化日志 `chat.node` 逐条落（只含节点 id / kind / status / 耗时，不含正文），"未激活"= 图中 agent 减去 `ran`。

**IFC-R26-091 Orchestrator 追加形参（修改 `Orchestrator.__init__` / `build_graph`，append-only）**

```python
class Orchestrator:
    def __init__(self, *, ..., view: ProjectRuntimeView | None = None, dag: CompiledDag | None = None) -> None: ...
def build_graph(*, ..., view: ProjectRuntimeView | None = None, dag: CompiledDag | None = None) -> Orchestrator: ...
```

`view is None` → 既有进程级全局路径（离线 / 旧调用，逐位旧行为）；`view` 给定 → `_run_expert` / `_prompt_of` / `_expand_plan` / `_active_forbidden_labels` 全部读 `view`，不读 `ib.experts` 全局；`dag` 给定且 `IB_GRAPH_RUNTIME != "legacy"` → 用 DAG 编译图；`legacy` → 旧 `_compile_graph`（重命名为 `_compile_legacy_graph`，仅保留作回退与等价性基准）。`run()` 的事件顺序契约不变；`CompletionPayload.config_version` 填 `view.version`。`_persist_gate` 写入 `SessionState.config_version`；`resume` 由聊天端点按该版本取编排器（见 IFC-R26-111）。
**依赖模块**：01, 02。

---

### MOD-R26-11 Agent Builder（`src/ib/builder/`）

**IFC-R26-100 类型（`types.py`）**

```python
@dataclass(frozen=True, slots=True)
class AgentDraft:
    name: str                                    # 专家名模式同现有 ExpertSpec 命名规则；1..48
    cn_label: str                                # 1..32
    main_prompt: str                             # 1..20000
    fallback_prompt: str                         # 1..20000
    keywords: tuple[str, ...]                    # ≤20
    exemplars: tuple[str, ...]                   # ≤10
    is_data_expert: bool
    is_delegating: bool
    tool_names: tuple[str, ...]
    tool_params: tuple[tuple[str, str | int | float | bool], ...]     # (限定参数名, 值)
    knowledge_folder_ids: tuple[str, ...]
    max_steps: int
    source: Literal["generated", "optimized", "cloned", "blank"]

@dataclass(frozen=True, slots=True)
class AdaptationNote:
    code: Literal["tool_removed", "folder_removed", "param_adjusted", "steps_adjusted", "name_conflict",
                  "label_conflict", "clause_missing", "term_blocked", "requirement_not_adopted", "truncated"]
    field: str
    message: str                                 # 可读；不含凭据 / 提示词全文

@dataclass(frozen=True, slots=True)
class Deduction:
    dimension: Literal["completeness", "adaptation", "routing", "prompt", "safety"]
    check_id: str
    field: str
    points: int
    evidence: str                                # 指向字段 / 文本位置，≤200 字符；无 evidence 不产生扣分

@dataclass(frozen=True, slots=True)
class RubricResult:
    rubric_version: str                          # "r26.1"
    total: int                                   # 0..100
    grade: Literal["fail", "pass", "excellent"]  # <60 / 60–89 / ≥90
    dimension_scores: Mapping[str, int]          # 满分 20 / 25 / 15 / 25 / 15
    deductions: tuple[Deduction, ...]
    coverage: Literal["full", "rules_only"]
    cache_hit: bool

@dataclass(frozen=True, slots=True)
class FieldChange:
    field: str
    before: str | None                           # 摘要；prompt 给"段落级差异"由前端在持有两份文本时展示，此处只给长度 / 哈希前 8 位
    after: str | None
    note: str

@dataclass(frozen=True, slots=True)
class ProjectContext:                            # 由组合根构造（只含白名单类别）
    project_id: str
    agents: tuple[AgentDigest, ...]              # name / cn_label / keywords / exemplars
    tools: tuple[ToolDigest, ...]                # name / 参数声明（类型 / 范围 / 默认）
    folders: tuple[FolderDigest, ...]            # folder_id / 目录路径名；≤200
    constraints: ProjectConstraints              # 数值上限、保留名、grounding 三项

class BuilderUnavailable(Exception):
    reason: Literal["llm_unconfigured", "network", "timeout", "rejected", "parse_failed", "audit_failed"]
class BuilderBusy(Exception): ...
class EgressRejected(Exception):
    code: Literal["egress_secret_detected", "egress_payload_too_large", "requirement_empty", "requirement_too_long"]
```

**IFC-R26-101 外发（`egress.py`）**

```python
BUILDER_REQUIREMENT_MAX_CHARS: Final[int] = 2000
BUILDER_INSTRUCTION_MAX_CHARS: Final[int] = 1000
EGRESS_PAYLOAD_MAX_BYTES: Final[int] = 64 * 1024

EgressKind = Literal["generate", "judge", "optimize", "review_existing"]
FieldCategory = Literal["requirement_text", "instruction_text", "project_digest", "selected_agent", "rubric_items"]

@dataclass(frozen=True, slots=True)
class OutboundPayload:                           # 字段集 = 白名单；类型里没有会话 / 资料 / 账号 / 审计 / 其他项目字段
    kind: EgressKind
    requirement_text: str | None
    instruction_text: str | None
    project_digest: ProjectContext | None
    selected_agent: AgentDraft | None
    rubric_items: tuple[str, ...] = ()

class BuilderCompleter(Protocol):                # 由 provider.complete 适配
    def __call__(self, system: str, user: str, *, temperature: float, timeout_s: float) -> str: ...

class EgressGuard:
    def __init__(self, *, completer: BuilderCompleter, audit: ConfigAuditStore, clock: Callable[[], str],
                 timeout_s: float = 60.0, pool_size: int = 2) -> None: ...
    def send(self, payload: OutboundPayload, *, system: str, project_id: str, actor: str) -> str: ...
    # 顺序固定：规模 / 秘钥模式检查（EgressRejected）→ 写审计（失败 → BuilderUnavailable(audit_failed)，不发送）→ 线程池提交 → future.result(timeout) → 返回文本
    # 线程池满 → BuilderBusy；超时 → BuilderUnavailable(timeout)；NotConfigured → llm_unconfigured
def contains_secret_pattern(text: str) -> bool: ...    # sk-… / ghp_… / github_pat_… / AKIA… / -----BEGIN … PRIVATE KEY----- / password= 等；纯函数
```

审计记录：`action="builder.egress"`、`object_summary=(f"kind:{kind}", *[f"cat:{c}" for c in categories], f"bytes:{n}")`、`result="saved"`；不含需求原文与提示词全文。
**静态约束（`selfcheck.py` 新增规则）**：`ib.builder` 包不得 import `ib.retrieval` / `ib.vectorstore` / `ib.blob` / `ib.streaming`（会话类）/ `ib_embed`；`complete` 只在 `egress.py` 内被引用（`builder_no_data_imports` / `builder_single_egress`）。

**IFC-R26-102 适配器（`adapt.py`）**

```python
@dataclass(frozen=True, slots=True)
class RawDraft:                                  # 解析自 LLM 的未信任 JSON
    fields: Mapping[str, Any]

def parse_raw_draft(text: str) -> RawDraft: ...                    # 容错解析（代码围栏 / 前后缀文字）；失败 → BuilderUnavailable(parse_failed)
def adapt_draft(raw: RawDraft, ctx: ProjectContext, *, source: Literal["generated", "optimized"]) -> tuple[AgentDraft, tuple[AdaptationNote, ...]]: ...
```

纯函数，规则：不存在的工具 → 移除（`tool_removed`）；目录名 → 在 `ctx.folders` 内按 NFC + casefold 匹配到 `folder_id`，匹配不到 / 非本项目 → 移除（`folder_removed`）；工具参数未声明 / 越界 / 类型不符 → 调整为默认值（`param_adjusted`）；`max_steps` 越界 → 默认 4（`steps_adjusted`）；name / 中文标签与现有 agent 重复 → 保留值并标 `name_conflict` / `label_conflict`（**不覆盖**，加入画布前须改名，AC-024-03）；检索类 agent 缺 REQ-FUNC-IB-56 三项条款 → `clause_missing`；含业务专有词（FreeArk / 自由方舟 / 三恒）→ `term_blocked`；字段超长截断 → `truncated`。**任何来自 LLM 的字符串都当不可信文本**（REQ-NFUNC-008）：不执行、不解释为权限。

**IFC-R26-103 自评（`rubric.py`）**

```python
RUBRIC_VERSION: Final[str] = "r26.1"
def evaluate_draft(draft: AgentDraft, notes: Sequence[AdaptationNote], ctx: ProjectContext,
                   *, llm_checks: Mapping[str, tuple[bool, str]] | None) -> RubricResult: ...
# llm_checks：{check_id: (是否通过, 引用片段)}；None → coverage="rules_only"，LLM 项不计分且不扣分，总分按规则项满分（94）折算为 100 制并标注
LLM_CHECK_IDS: Final[tuple[str, ...]] = ("prompt_role_consistent", "prompt_no_contradiction", "prompt_no_guardrail_conflict")  # 各 2 分
def rubric_cache_key(draft: AgentDraft, notes: Sequence[AdaptationNote], ctx: ProjectContext, *, model_id: str) -> str: ...
```

评分表（`r26.1`）：D1 完整性与格式 20（规则）；D2 项目适配度 25（规则，证据 = 适配说明条目）；D3 路由质量 15（规则）；D4 提示词质量 25（规则 19 + LLM 布尔 6）；D5 安全与约束 15（规则）。`total = Σ dimension_scores`，同 `(draft, notes, ctx, model_id)` 输入规则项必然同分；每条扣分必须带 `evidence`。
**IFC-R26-104 服务（`service.py`）**

```python
class BuilderService:
    def __init__(self, *, guard: EgressGuard, cache: BuilderEvalCache, context_provider: Callable[[str, str], ProjectContext],
                 clock: Callable[[], str], model_id: str) -> None: ...
    def generate(self, project_id: str, actor: str, requirement: str) -> tuple[AgentDraft, tuple[AdaptationNote, ...], RubricResult]: ...
    def evaluate(self, project_id: str, actor: str, draft: AgentDraft, *, allow_llm: bool = True) -> RubricResult: ...
    def optimize(self, project_id: str, actor: str, draft: AgentDraft, instruction: str | None
                 ) -> tuple[AgentDraft, tuple[AdaptationNote, ...], RubricResult, RubricResult, tuple[FieldChange, ...]]: ...   # 单轮
    def review_existing(self, project_id: str, actor: str, expert: str, mode: Literal["evaluate", "optimize"],
                        instruction: str | None, *, published: ConfigSnapshot
                        ) -> tuple[RubricResult, AgentDraft | None, tuple[FieldChange, ...]]: ...
```

`BuilderService` **不依赖** `ConfigPublishService` / 任何写配置端口（类型层无法发布，REQ-FUNC-021）。
**依赖模块**：01, 02, 04, 05。

---

### MOD-R26-12 运行时快照与缓存 / 试运行（`src/ib/runtime/`）

**IFC-R26-110 编译（`compile.py`）**

```python
@dataclass(frozen=True, slots=True)
class RuntimeDeps:                               # 由组合根构造的只读依赖包
    llm: Any
    retrieval: Any
    embedder: Any
    sessions: Any
    tool_registry_factory: Callable[[], ToolRegistry]
    tool_param_specs: tuple[ToolParamSpec, ...]
    graph_config_factory: Callable[[RouteSpecInput], GraphConfig]
    related_images_provider_factory: Callable[[Scope], Any]
    exemplar_vector_cache: "ExemplarVectorCache"
    graph_runtime: Literal["dag", "legacy"]

@dataclass(frozen=True, slots=True)
class CompiledProjectConfig:
    project_id: str
    version: int                                  # 试运行 = -1
    view: ProjectRuntimeView
    dag: CompiledDag | None
    orchestrator: Orchestrator
    manifest_hash: str
    source: Literal["files", "snapshot"]          # snapshot = 漂移 / 钉旧版 / 回滚预览

def compile_project_config(project_id: str, version: int, snapshot: ConfigSnapshot, *, deps: RuntimeDeps,
                           source: Literal["files", "snapshot"], trial: bool = False) -> CompiledProjectConfig: ...
# 任一步失败抛 StartupError / ConfigError，不产生半成品；v1 文档先 canonical 规范化（不改文件）
```

**IFC-R26-111 缓存（`cache.py`）**

```python
RuntimeState = Literal["ok", "applying", "apply_failed"]

@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    applied_version: int
    head_version: int
    state: RuntimeState
    drift: bool
    last_error_code: str | None

@dataclass(frozen=True, slots=True)
class RuntimeLease:                               # 不可变引用；持有即"本次提问绑定该版本"
    compiled: CompiledProjectConfig

class ProjectRuntimeCache:
    def __init__(self, *, versions: ConfigVersionStore, loader: "ConfigSourceLoader", deps: RuntimeDeps,
                 check_interval_s: float = 1.0, keep_recent: int = 3, clock: Callable[[], float] = time.monotonic) -> None: ...
    def acquire(self, project_id: str) -> RuntimeLease: ...               # 热路径：节流内直接返回；越过节流读 head；不一致则触发后台单飞编译并继续返回旧版
    def acquire_version(self, project_id: str, version: int) -> RuntimeLease: ...   # 钉旧版（挂起会话恢复）；缓存未命中则按版本快照重编译；已被修剪 → ConfigVersionExpiredError
    def install(self, compiled: CompiledProjectConfig) -> None: ...      # 保存进程提交后立即换引用
    def refresh_async(self, project_id: str) -> None: ...
    def status(self, project_id: str) -> RuntimeStatus: ...
    def invalidate(self, project_id: str | None = None) -> None: ...     # reload_projects 调用
class ConfigVersionExpiredError(ConflictError): ...                       # → 409 config_version_expired

class ConfigSourceLoader(Protocol):              # 由组合根适配 definition_store / prompt_stores
    def load_files(self, project_id: str) -> ConfigSnapshot: ...         # v1 / v2 皆可；不修改任何文件
```

规则：冷启动（无快照）阻塞式编译，失败 `StartupError`（fail-closed）；之后编译失败 → 旧快照继续服务，退避 5 s 起 ×2，上限 60 s；`source="files"` 时比对 `manifest_hash` 与 head 版本行，不一致 → 改以 head 快照编译并 `drift=True`；head 为虚拟 0（无版本行）→ 仅 `files` 路径。
**IFC-R26-112 head 探测**：`ProjectRuntimeCache` 内部 `_HeadProbe.read(project_id) -> HeadState`，按项目节流（`check_interval_s`），键名 `IB_CONFIG_HEAD_CHECK_INTERVAL_S`。
**IFC-R26-113 试运行（`trial.py`）**

```python
@dataclass(frozen=True, slots=True)
class TrialLimits:
    per_project_concurrency: int = 1
    global_concurrency: int = 2
    per_actor_turns_per_10min: int = 20           # [ESTIMATE]
    draft_max_bytes: int = 1024 * 1024
    cache_size: int = 4
    cache_ttl_s: float = 600.0

class TrialBusyError(DependencyUnavailableError): ...                   # → 429 trial_busy

class TrialRunner:
    def __init__(self, *, deps: RuntimeDeps, validator: Callable[[ConfigSnapshot], tuple[ValidationErrorItem, ...]],
                 limits: TrialLimits = TrialLimits()) -> None: ...
    def validate(self, snapshot: ConfigSnapshot) -> tuple[ValidationErrorItem, ...]: ...
    def run(self, project_id: str, snapshot: ConfigSnapshot, query: str, *, ctx: RequestContext, session_id: str) -> Iterator[StreamEvent]: ...
    # 校验不过 → ValidationFailed（调用方在打开 SSE 之前转 400）；会话键 f"{project_id}:{actor}:trial-{session_id}"，独立 MemorySessionStore；运行记录 trial=true、config_version=-1
```

**依赖模块**：01, 02, 04, 05, 07, 09, 10（宿主基线 MOD-IB-16 `ExpertRegistryView` 与 MOD-IB-02 `merge_prompt_layers` 经注入使用）。

---

### MOD-R26-13 配置发布服务（`src/ib/confsvc/`）

**IFC-R26-120**（`ConfigPublishService`：`current` / `preview` / `publish` / `rollback` / `adopt_drift` / `recover`）与 **IFC-R26-121**（`ConfigDraftService`：草稿副本的保存 / 列表 / 载入 / 删除，owner 隔离、每人每项目 ≤10、单个 ≤1 MiB）。这是库内服务，不直接对外；HTTP 契约见 MOD-R26-15。

```python
@dataclass(frozen=True, slots=True)
class PublishRequest:
    project_id: str
    actor: str
    base_version: int
    document: DefinitionDocument
    prompts: Mapping[str, PromptLayers]          # 只含本次要写入 / 变更的专家（缺省 = 不变）；PromptLayers 内 None = 不变，"" 经 validate_prompt_texts 拒绝 / 视为删除该层仅限 main
    message: str | None                          # ≤200 字符

@dataclass(frozen=True, slots=True)
class PublishPreview:
    base_version: int
    head_version: int
    items: tuple[DiffItem, ...]
    layout_only: bool
    errors: tuple[ValidationErrorItem, ...]

@dataclass(frozen=True, slots=True)
class PublishResult:
    version: int
    previous_version: int
    content_hash: str

class PublishError(IbError):
    code: Literal["validation_error", "conflict", "config_busy", "no_changes", "apply_failed", "version_not_found", "drift_detected"]
    items: tuple[ValidationErrorItem, ...]
    receipt: ConflictReceipt | None

class ConfigPublishService:
    def __init__(self, *, versions: ConfigVersionStore, definition_store: Any, prompt_store_for: Callable[[str], Any],
                 loader: ConfigSourceLoader, precompile: Callable[[str, int, ConfigSnapshot], Any],
                 on_published: Callable[[str, int, Any], None], audit: ConfigAuditStore,
                 validator: Callable[[ConfigSnapshot], tuple[ValidationErrorItem, ...]],
                 clock: Callable[[], str], keep_versions: int = 50, pending_stale_s: float = 30.0) -> None: ...
    def current(self, project_id: str) -> ConfigSnapshot: ...                      # 文件态 → 快照（v1 规范化，不改文件）
    def preview(self, req: PublishRequest) -> PublishPreview: ...                  # 只读；base 不等 head → PublishError(conflict)
    def publish(self, req: PublishRequest) -> PublishResult: ...                   # ADR-55 协议 1~8
    def rollback(self, project_id: str, actor: str, *, target_version: int, base_version: int, message: str | None) -> PublishResult: ...
    def adopt_drift(self, project_id: str, actor: str, *, base_version: int) -> PublishResult: ...
    def recover(self, project_id: str) -> int | None: ...                          # 认领陈旧 pending → 依 head 快照还原文件 → abort；返回被中止的版本号
class ConfigDraftService: ...                                                      # save / list / load / delete，配额与大小限制，owner 隔离
```

要点：校验入口 = `validate_two_domains` ∪ `validate_prompt_texts`（保存路径与装配路径同一入口）；`precompile` 失败 → `PublishError(apply_failed)` 且**不落盘**；文件写入顺序 = 变更的提示词层 → 定义文档（最后）；任一步失败依 head 快照还原并 `abort_publish`；成功后 `on_published` 令本进程立即换引用；审计 `config.publish` / `config.rollback` / `config.adopt_drift` 的 `version_before` / `version_after` / `object_summary`（来自 `diff_snapshots`，只含对象 id）。无变更（`diff` 为空）→ `no_changes`，不产生版本。
**依赖模块**：01, 02, 04, 05（宿主基线 `ExpertPromptStore` 端口 MOD-IB-02 经注入）。

---

### MOD-R26-14 组合根与账号 glue

**修改点**：

- `Deps`（`composition.py`）追加字段：`version_store: ConfigVersionStore`、`draft_store: ConfigDraftStore`、`eval_cache: BuilderEvalCache`、`audit_retention: ConfigAuditRetention | None`、`runtime_cache: ProjectRuntimeCache`、`publish_service: ConfigPublishService`、`draft_service: ConfigDraftService`、`builder_service: BuilderService`、`trial_runner: TrialRunner`、`account_levels: AccountConfigLevelStore`。
- **IFC-R26-130** `Deps.runtime_for(project_id: str) -> RuntimeLease`；`Deps.orchestrator_for(project_id: str) -> Any` 保留为薄包装（= `runtime_for(project_id).compiled.orchestrator`），**不再**为每项目长期缓存 `Orchestrator`；`reload_projects()` 额外调用 `runtime_cache.invalidate()`。
- **IFC-R26-131** `chat_stream_endpoint` / `chat_resume_endpoint`（`views.py`）：流开始前取 `lease = deps.runtime_for(project_id)`，整个 `_events()` 生成器闭包持有 `lease`（即版本绑定）；日志 `chat.started` / `chat.completed` 增 `config_version`；`chat_resume_endpoint` 读 `state.config_version`，非 0 且 ≠ 当前版本 → `acquire_version(project_id, state.config_version)`，`ConfigVersionExpiredError` → 409 `config_version_expired`（fail-closed，不新建会话）。
- **IFC-R26-132** 旧端点退化为发布包装：`PUT /api/config/definition`、`PUT /api/config/prompts/{expert}/{layer}`（最低档 `edit`；响应形状保持并追加 `version`；乐观并发哈希冲突仍 409，回执追加 `receipt`）。`GET` 响应追加 `version` / `level` / `graph`；去掉前端"重启后生效"所需的 `config_key_names` 说明性字段不变。
- **IFC-R26-133** `effective_roles(user: UserRecord) -> tuple[str, ...]`（`ibweb/accounts/__init__.py`）：ops → `("manager", level_token(user.config_level))`，admin → `("admin",)`；`POST /api/accounts` 增必填 `config_level`（`view|edit|manage`，缺省 → 400），响应 `AccountSummary` 追加 `config_level`。
- **IFC-R26-134** 装配：`_assemble` 在 `build_config_audit_store` 之后构造版本 / 草稿 / 缓存存储（`file_backed = storage_state` 两域均为 `file`）、`RuntimeDeps`、`ProjectRuntimeCache`（并替换 `_inject_derived_experts` / `_inject_prompt_bundles` 在运行期路径上的作用：保留调用仅供离线 / `legacy` 回退，标注"REV-26 起不再作为运行期真源"）、`ConfigPublishService`、`BuilderService`（`context_provider` 只读 `definitions` / `tree.list_subtree_folders` / `known_tool_param_specs`，**不接触资料正文 / 会话**）、`TrialRunner`；装配期对每个项目执行 `publish_service.recover(project_id)`；外发声明 `llm.describe_egress()` 的数据类别追加 `builder` 类别。
- 示例句来源：`_load_exemplars` 降为"种子来源"，编译以 `ExpertSpecInput.exemplars` 为准（F-6）；`ExemplarVectorCache`（进程级，键 = 文本哈希）。

**依赖模块**：01, 06, 07, 08, 09, 10, 11, 12, 13（及基线 MOD-IB-02 / 11 / 15 / 16 / 17 / 19 / 20 / 21 / 22）。

---

### MOD-R26-15 配置 HTTP 端点（`src/ibweb/config_views.py`）

**通用校验**：请求体必须是 JSON 对象，原始字节 ≤ `CONFIG_BODY_MAX_BYTES = 8 MiB`（超出 → 400 `body_too_large`）；`base_version` 为整数 ≥0；`document` 经 `document_from_json`（失败 → 400 `validation_error`，信息只含字段路径）；`prompts` 形如 `{expert_name: {"main"?: str|null, "fallback"?: str|null}}`，层 ≤20000 字符、专家数 ≤200；`message` ≤200 字符；未登录 401；档位不足 403 `permission_denied`（`error.required_level` 给出所需档位名）；`IB_VISUAL_CONFIG_ENABLED` 关闭 → 404（沿用既有开关）。

| IFC | 方法 路径 | 最低档位 | 请求 | 响应 / 状态码 / 错误 |
|---|---|---|---|---|
| IFC-R26-140 | `GET /api/config/status` | view | — | 200 `{version:int, applied_version:int, apply_state:"ok"\|"applying"\|"apply_failed", drift:bool, pending:bool, schema_version:1\|2, legacy:bool, level:"view"\|"edit"\|"manage"}`；503 head 不可读（fail-closed，不返回空） |
| IFC-R26-141 | `GET /api/config/definition`（既有，扩展） | view | — | 200 `{document, derived, editable_fields, config_key_names, version:int, level:str, graph:Graph\|null}`；v2 的 `derived.agents[]` 含 `name, prompt_main_present:bool, prompt_main_head:str(≤120), prompt_fallback_present:bool, tool_count:int, nondefault_param_count:int`（不含凭据）；v1 沿用 ADR-52 投影；503 同既有 |
| IFC-R26-142 | `POST /api/config/validate` | edit | `{document, prompts?}` | 200 `{ok:bool, errors:[{path,code,message}]}`（校验结果本身不是错误，故恒 200；2 s 内返回，INF-5）；400 请求体非法 |
| IFC-R26-143 | `POST /api/config/publish/preview` | edit | `{base_version, document, prompts?}` | 200 `{base_version, head_version, items:[DiffItem], layout_only:bool, errors:[...]}`；409 `conflict` + `receipt` |
| IFC-R26-144 | `POST /api/config/publish` | edit | `{base_version, document, prompts?, message?}` | 200 `{version, previous_version, content_hash, applied:true}`；400 `validation_error`（逐条 items，**无"忽略并继续"**）；409 `conflict`（`receipt:{base_version, head_version, base_available, conflicts[]}`）；409 `config_busy`；422 `no_changes`；503 `apply_failed`（在用版本不变）；403 |
| IFC-R26-145 | `GET /api/config/versions?limit=&before=` | view | `limit` 1..50（默认 50，非法 → 400）、`before` 整数 | 200 `{head:int, items:[VersionRecordDto]}`（按 version 降序；`VersionRecordDto` 不含快照） |
| IFC-R26-146 | `GET /api/config/versions/{n}[?include=prompts]` | view | `n` 整数 | 200 `{record, document, prompts_summary:[{expert, main_len, fallback_len}]}`；`include=prompts` 追加全文（查看档可见，OQ-R26-07=A）；404 不存在 / 已修剪 / 非本项目（同码） |
| IFC-R26-147 | `GET /api/config/versions/{n}/diff?against=<m\|head>` | view | — | 200 `{from:int, to:int, items:[DiffItem], layout_only:bool}`；404 同上 |
| IFC-R26-148 | `POST /api/config/rollback` | manage | `{target_version, base_version, message?}` | 200 同 publish（产生新版本，`kind="rollback"`）；404 目标已修剪；409 `conflict` / `config_busy`；503 `apply_failed` |
| IFC-R26-149 | `POST /api/config/adopt-drift` | manage | `{base_version}` | 200 同 publish；409 `no_drift`（无漂移）；400 校验不过（逐条） |
| IFC-R26-150 | `GET /api/config/drafts` / `POST /api/config/drafts` / `GET /api/config/drafts/{id}` / `DELETE /api/config/drafts/{id}` | edit（仅本人草稿） | POST：`{label:1..60, base_version, document, prompts?}` | GET 200 `{items:[DraftRecordDto]}`；POST 201 `DraftRecordDto`（单个 ≤1 MiB，每人每项目 ≤10，超出 → 400 `draft_quota`）；GET one 200 `{record, document, prompts}`；DELETE 204；他人草稿 / 不存在 → 404 |
| IFC-R26-151 | `GET /api/config/access` / `PUT /api/config/access/{user_id}` | manage | PUT：`{config_level:"view"\|"edit"\|"manage"}` | GET 200 `{items:[{user_id, username, config_level, status}]}`（仅本项目账号）；PUT 200 同项；404 目标不在本项目；409 `last_manager`（不得降级项目内最后一个 manage 档，admin 除外）；400 档位非法；每次变更写审计 `access.grant`（`object_summary=("user:<id>", "from:<lv>", "to:<lv>")`） |
| IFC-R26-152 | `POST /api/config/trial`（SSE） | edit | `{document, prompts?, query:1..2000, session_id:1..64（不含 ":"）}` | 校验失败 → 400 `validation_error`（逐条，**不**打开 SSE、**不**调用 LLM）；通过 → 200 `text/event-stream`，事件与 `/api/chat/stream` 同形，首个 `reasoning` 事件标注"试运行"，`done` 携 `config_version:-1`；429 `trial_busy`；不进入正式会话列表 |
| IFC-R26-153 | `GET /api/config/audit?limit=&offset=&action=`（既有，扩展） | manage | `action` 可选，≤40 字符 | 200 `{items:[{timestamp, project, actor, action, changed_field_names, result, detail_code, version_before, version_after, object_summary}], total}`；修改 / 删除方法 → 405；403 |

**序列化纪律**：沿用现有手写 `to_representation`（不用 `asdict` 自动展开）；所有响应过凭据模式扫描（REQ-NFUNC-011）；提示词、关键词、节点 `message` 等不可信文本一律作为 JSON 字符串返回，渲染由前端纯文本完成。
**依赖模块**：03, 14。

---

### MOD-R26-16 Builder HTTP 端点（`src/ibweb/builder_views.py`）

**通用**：最低档 `edit`（否则 403，且**不向云端发任何请求**，AC-024-06）；`IB_VISUAL_CONFIG_ENABLED` 关闭 → 404；请求体 ≤1 MiB；错误码 `builder_unavailable`（503，`error.reason ∈ {llm_unconfigured, network, timeout, rejected, parse_failed, audit_failed}`，文案可读，`llm_unconfigured` 文案含"尚未配置 LLM Key"）、`builder_busy`（429）、`egress_rejected`（400，`error.code ∈ {egress_secret_detected, egress_payload_too_large, requirement_empty, requirement_too_long}`）、`builder_timeout`（504，60 s 内返回）。任一失败路径：不产生草案、不改任何配置、配置版本号不变。

| IFC | 方法 路径 | 请求（输入校验） | 成功响应 |
|---|---|---|---|
| IFC-R26-160 | `POST /api/builder/draft` | `{requirement: str}`：去首尾空白后 1..2000 字符，非空；含秘钥模式 → 400 | 200 `{draft:AgentDraftDto, notes:[AdaptationNote], evaluation:RubricResultDto}`（不写任何配置，AC-027-03） |
| IFC-R26-161 | `POST /api/builder/evaluate` | `{draft: AgentDraftDto}`：字段长度 / 条数上限同 `AgentDraft`；非法 → 400 | 200 `{evaluation}`（规则项必出；LLM 项命中缓存或调用，失败降级 `coverage="rules_only"`） |
| IFC-R26-162 | `POST /api/builder/optimize` | `{draft, instruction?: str ≤1000}` | 200 `{draft, notes, before, after, changes:[FieldChange]}`（单轮，不自动循环） |
| IFC-R26-163 | `POST /api/builder/review-existing` | `{expert: str(1..48), mode:"evaluate"\|"optimize", instruction?}`；专家不存在 / 已停用 → 404 | 200 `{evaluation, proposal: AgentDraftDto\|null, changes:[FieldChange]}`；仅被选 agent 的提示词与配置进入载荷（AC-028-03） |

空白表单与克隆**不经 Builder 服务端**：由前端组装草稿后走 `POST /api/config/validate`，LLM 不可用时不受影响（REQ-NFUNC-015）。
**依赖模块**：03, 11, 14。

---

### MOD-R26-17 worker 维护步骤（修改 `src/ibweb/worker.py`）

**IFC-R26-170**

```python
@dataclass(frozen=True, slots=True)
class MaintenanceSummary:
    versions_pruned: int
    drafts_purged: int
    audit_purged: int
    eval_cache_purged: int

def run_maintenance(*, deps: Any, now: str, audit_retention_days: int = 365, draft_ttl_days: int = 30,
                    eval_cache_keep: int = 2000, eval_cache_ttl_days: int = 90, keep_versions: int = 50) -> MaintenanceSummary: ...
```

在既有 `run_once` 循环内**每小时至多一次**（进程内时间戳守卫），不新增线程 / 单元；陈旧 `pending` 回收由 `ib-web` 在发布 / 启动路径处理，worker 只做删除类维护。删除审计仅通过 `ConfigAuditRetention.purge_before`（Web 层不持有该端口）。
**依赖模块**：06, 14。

---

### MOD-R26-18 前端 API 客户端与类型（`src/frontend/src/api/client.ts`、`src/frontend/src/stores/configDraft.ts`）

**IFC-R26-180 TS 类型（节选，与后端 DTO 一一对应）**

```ts
export type ConfigLevel = 'view' | 'edit' | 'manage';
export type NodeKind = 'start' | 'end' | 'route' | 'agent' | 'condition' | 'join' | 'confirm';
export interface GraphNodeDto { id: string; kind: NodeKind; x: number; y: number; expert?: string; input_mode?: 'query_only' | 'with_upstream'; predicate?: { kind: 'keyword' | 'upstream_degraded'; branches: { key: string; keywords: string[] }[] }; message?: string }
export interface GraphEdgeDto { id: string; source: string; target: string; branch_key?: string | null }
export interface GraphDto { nodes: GraphNodeDto[]; edges: GraphEdgeDto[] }
export interface ValidationItem { path: string; code: string; message: string }
export interface DiffItemDto { kind: string; object_id: string; field: string; before: string | null; after: string | null }
export interface ConflictReceiptDto { base_version: number; head_version: number; base_available: boolean; conflicts: { kind: string; object_id: string; fields: string[] }[] }
export interface PublishResultDto { version: number; previous_version: number; content_hash: string; applied: true }
export interface VersionRecordDto { version: number; parent_version: number; kind: 'publish' | 'rollback' | 'baseline' | 'adopt'; rolled_back_to: number | null; actor: string; created_at: string; summary: string }
export interface ConfigStatusDto { version: number; applied_version: number; apply_state: 'ok' | 'applying' | 'apply_failed'; drift: boolean; pending: boolean; schema_version: 1 | 2; legacy: boolean; level: ConfigLevel }
export interface AgentDraftDto { name: string; cn_label: string; main_prompt: string; fallback_prompt: string; keywords: string[]; exemplars: string[]; is_data_expert: boolean; is_delegating: boolean; tool_names: string[]; tool_params: [string, string | number | boolean][]; knowledge_folder_ids: string[]; max_steps: number; source: 'generated' | 'optimized' | 'cloned' | 'blank' }
export interface RubricResultDto { rubric_version: string; total: number; grade: 'fail' | 'pass' | 'excellent'; dimension_scores: Record<string, number>; deductions: { dimension: string; check_id: string; field: string; points: number; evidence: string }[]; coverage: 'full' | 'rules_only'; cache_hit: boolean }
export type PromptPatch = Record<string, { main?: string | null; fallback?: string | null }>;
```

**IFC-R26-181 `ApiClient` 新增方法**（全部经现有 `fetch` 封装与 `Authorization` 头；试运行沿用 `chatResume` 的 `fetch + ReadableStream` SSE 解析）：`configStatus()`、`definitionConfig()`（扩展返回 `version` / `level` / `graph`）、`validateDraft(doc, prompts?)`、`publishPreview(baseVersion, doc, prompts?)`、`publish(baseVersion, doc, prompts?, message?)`、`listVersions(limit?, before?)`、`getVersion(n, includePrompts?)`、`diffVersions(n, against)`、`rollback(target, baseVersion, message?)`、`adoptDrift(baseVersion)`、`listDrafts()` / `saveDraft(...)` / `loadDraft(id)` / `deleteDraft(id)`、`getAccess()` / `putAccess(userId, level)`、`trialStream(doc, prompts, query, sessionId, onEvent, signal)`、`builderDraft(requirement)`、`builderEvaluate(draft)`、`builderOptimize(draft, instruction?)`、`builderReviewExisting(expert, mode, instruction?)`。错误统一抛 `ApiClientError`（`status` / `code` / `items?` / `receipt?` / `requiredLevel?`）。
**IFC-R26-182 `configDraft` store**（手写 store，沿用 `stores/*.ts` 风格，无新库）：持有 `baseVersion`、`document`（草稿）、`promptPatch`、`dirty`、`positions`；操作 `load(env)`、`discard()`、`markSaved(version)`、`setNode(...)`、`connect(...)`、`toPublishPayload()`；**不使用** `localStorage` / `IndexedDB`（ADR-14 约束①②保留）。
**依赖模块**：无（仅 HTTP 契约）。

---

### MOD-R26-19 前端画布组件

| 组件 | Props / Emits（TS） | 要点 |
|---|---|---|
| `FlowCanvas.vue` | props：`graph: GraphDto`、`readonly: boolean`、`agents: AgentSummary[]`；emits：`update:graph`、`select-node(id)`、`select-edge(id)` | 基于 `@vue-flow/core`：`nodes-draggable` / `nodes-connectable` / `elements-selectable` 由 `readonly` 控制；`@connect` 先过 `isValidConnection`（预校验，仅体验）；`@node-drag-stop` 写回坐标；删除前确认（含"将同时删除 N 条边"）；节点 / 边悬停事件 `@node-mouse-enter` / `@edge-mouse-enter` 触发卡片 |
| `NodePalette.vue` | props：`readonly`；emits：`add-node(kind)` | 仅列开始/结束（固定）、路由、agent、条件分支、汇聚、人工确认；**无代码 / 表达式节点** |
| `NodeHoverCard.vue` / `EdgeHoverCard.vue` | props：`model: HoverCardModel` | 内容由纯函数 `buildHoverCardModel(node, derived)` 生成（可 `node:test`）；一律文本插值，不用 `v-html` |
| `AgentDetailPanel.vue` | props：`agent`、`prompts`、`tools`、`folders`、`readonly`；emits：`change(patch)` | 提示词全文（只读 / 可编辑取决于档位）、生效来源层、关键词 / 示例句、工具授权与参数、知识范围（目录多选）、最大步数、停用 / 删除（默认专家保护） |
| `graphModel.ts` | `graphToFlow(graph)`、`flowToGraph(...)`、`buildHoverCardModel(...)`、`precheckConnection(...)`、`layeredPositions(...)`（沿用并迁出现有函数） | 纯函数，离线单测 |

**依赖模块**：18。

### MOD-R26-20 前端发布 / 版本 / 试运行 / Builder 组件

| 组件 | Props / Emits | 要点 |
|---|---|---|
| `PublishDialog.vue` | props：`items: DiffItemDto[]`、`layoutOnly`、`errors`；emits：`confirm(message?)`、`cancel` | 差异清单分类展示；校验错误逐条指向节点 / 边 / 字段，**无忽略选项** |
| `ConflictDialog.vue` | props：`receipt: ConflictReceiptDto`；emits：`reload`、`save-draft` | "放弃并重新载入 / 另存为草稿副本"（OQ-R26-09） |
| `VersionHistory.vue` | props：`level`；emits：`rolled-back(version)` | 列表（版本号 / 保存人 / 时间 / 摘要）、与当前对比、回滚（仅 manage 可见 / 可用，二次确认） |
| `TrialPanel.vue` | props：`getDraftPayload: () => PublishPayload` | 试运行对话、标注"试运行"、校验错误原样展示 |
| `BuilderDrawer.vue` | emits：`add-to-canvas(draft)` | 四入口：空白表单 / 克隆 / 按需求生成 / 评审并优化已有 agent；草案可逐字段审阅修改；`name` / 标签重复须先改名才可"加入画布"；LLM 不可用时显示可读错误并保留手工入口 |
| `BuilderEvalView.vue` | props：`result: RubricResultDto` | 总分 / 等级 / 五维得分 / 扣分清单（字段 + 检查项 + 扣分 + 证据）、`coverage` 与 `cache_hit` 标记 |

**依赖模块**：18, 19。

### MOD-R26-21 前端页面壳（`ConfigPage.vue`）

收敛为：加载 `configStatus` + `definitionConfig` → 初始化 `configDraft` → 布局（左画布、右详情 / Builder / 版本历史 / 试运行页签）→ "保存并生效"按钮走 `publishPreview` → `PublishDialog` → `publish`；成功提示"已生效（版本 N）"，**不再出现"重启后生效"文案**；`apply_state="apply_failed"` / `drift=true` 的横幅；按 `level` 禁用控件（view：全部只读；edit：无回滚 / 授权）；`storage-state` 内存态提示保留。**依赖模块**：18, 19, 20。

### MOD-R26-22 迁移 / 自检 / 部署资产

`008_config_versions.sql`（= `config_versions_ddl_script()` 逐字摘录快照）；`selfcheck.py` 新增检查：`builder_no_data_imports`、`builder_single_egress`、`config_versions_schema_single_source`、`graph_validate_offline`；`ci.yml` 迁移检查段新增 008 单源比对与"老库形态 `ensure_schema` ×2 → 008 重放 ×2"断言（devops 在 E1 实施）；`checklists.txt` 新增 B29（008 迁移与热生效上线核对）；`env.example` 只登记键名：`IB_CONFIG_HEAD_CHECK_INTERVAL_S`、`IB_GRAPH_RUNTIME`、`IB_LLM_CLIENT_CACHE_MAX`、`IB_DOC_SCOPE_MAX_IDS`；`hot_effect_probe.py`：只读 CLI（见下）。

**IFC-R26-190 CLI `src/scripts/hot_effect_probe.py`**：`python src/scripts/hot_effect_probe.py --base-url URL --project ID --samples N`（`N` 1..500，非法 → 退出码 2；`--base-url` 必须 `http(s)://`）；**鉴权**：令牌只从环境变量 `IB_PROBE_TOKEN` 读取（不接受命令行传令牌，不回显）；只调用 `GET /api/config/status` 与 `GET /api/chat/stream`（只读提问），输出各样本所见 `version` 与收敛时间分布；`apply_state != ok` 或样本版本不一致 → 退出码 1。用于 TBD-T32 / AC-014-04 的目标机抽样（由用户在部署后执行，不属于 CI）。

---

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-001 悬停卡片 | US-001 | 15（IFC-R26-141 `derived.agents`）、19（`NodeHoverCard` / `graphModel.buildHoverCardModel`）、21 |
| REQ-FUNC-002 点击看提示词 | US-002 | 15（提示词层沿用 `GET /api/config/prompts` + IFC-R26-146）、19（`AgentDetailPanel`）、03（view 档只读） |
| REQ-FUNC-003 图随编辑联动 | US-003 | 18（`configDraft`）、19（`FlowCanvas`）、21 |
| REQ-FUNC-004 Agent Builder 入口（空白 / 克隆 / AI） | US-004、US-024 | 20（`BuilderDrawer`）、16、11、15（IFC-R26-142 校验草稿） |
| REQ-FUNC-005 停用 / 删除 | US-005 | 01、04（`status` / 默认专家保护）、19（删除确认）、05（差异）、12（停用不进快照） |
| REQ-FUNC-006 路由配置 | US-006 | 02（分支校验）、04、09（`restrict_to`）、10（route / condition）、19 |
| REQ-FUNC-007 工具授权与参数 | US-007、US-009 | 07、04（校验）、19、10 |
| REQ-FUNC-008 专家级参数（最大步数） | US-008 | 01、04、08（`max_iterations`）、10、19 |
| REQ-FUNC-009 运行时权限（工具 + 资料目录） | US-009 | 07、09（`knowledge`）、06（IFC-R26-055）、12（按 agent 编译）、08（`on_unauthorized`）、10 |
| REQ-FUNC-010 三档权限 | US-010 | 03、06（`config_level` 列）、14（令牌 / 账号接口）、15（IFC-R26-151）、17 |
| REQ-FUNC-011 自由画布 DAG | US-011 | 01、02、04、10、19、21 |
| REQ-FUNC-012 节点位置保存 | US-012 | 01（`x` / `y`）、04（v2 序列化）、05（`layout` 差异）、19 |
| REQ-FUNC-013 图合法性校验 | US-013 | 02（`validate_graph`）、04、15（IFC-R26-142 / 144）、20 |
| REQ-FUNC-014 保存并热生效 | US-014 | 06、12、13、14、15、18、20、21 |
| REQ-FUNC-015 进行中会话版本绑定 | US-015 | 12（`RuntimeLease` / `acquire_version`）、10（`config_version`）、14（IFC-R26-131）、01（`SessionState.config_version`） |
| REQ-FUNC-016 差异确认 | US-016 | 05（`diff_snapshots`）、13（`preview`）、15（IFC-R26-143）、20（`PublishDialog`） |
| REQ-FUNC-017 版本历史与回滚 | US-017 | 06、13（`rollback`）、15（IFC-R26-145~149）、17（修剪）、20（`VersionHistory`） |
| REQ-FUNC-018 AI 生成草案 | US-024 | 11、16（IFC-R26-160）、08（`complete`）、20 |
| REQ-FUNC-019 适配所在项目 | US-025 | 11（`adapt_draft`）、04 / 02（保存期仍全量校验）、15 |
| REQ-FUNC-020 自评与按意见优化 | US-026 | 11（`evaluate_draft` / `optimize`）、06（评审缓存）、16、20（`BuilderEvalView`） |
| REQ-FUNC-021 草案确认后才生效 | US-027 | 11（对发布服务无依赖）、16（无写路径）、20（"加入画布"）、13（保存走发布协议） |
| REQ-FUNC-022 对已有 agent 优化 | US-028 | 11（`review_existing`）、16（IFC-R26-163）、20 |
| REQ-FUNC-023 保存前试运行 | US-029 | 12（`TrialRunner`）、15（IFC-R26-152）、20（`TrialPanel`） |
| REQ-NFUNC-001 时限 | US-014 | 12（节流 + 单飞）、22（探针） |
| REQ-NFUNC-002 原子 / 失败安全 | US-014 | 13（预编译 + WAL）、06、12（保留旧快照） |
| REQ-NFUNC-003 进行中会话不受影响 | US-015 | 12、10、14 |
| REQ-NFUNC-004 多进程一致与可追溯 | US-014 | 06（head）、12、14（日志 `config_version`）、01（`CompletionPayload`） |
| REQ-NFUNC-005 并发冲突 | US-018 | 05（`detect_conflicts`）、06（CAS）、13、15、20（`ConflictDialog`） |
| REQ-NFUNC-006 审计 | US-017、US-023 | 06（IFC-R26-054）、13、17、11（外发审计） |
| REQ-NFUNC-007 越权防护 | US-009、US-010、US-019 | 03、07、09、14、15 |
| REQ-NFUNC-008 内容安全 | US-019、US-025、US-030 | 11（适配器 / 不信任）、19 / 20（纯文本渲染）、07 |
| REQ-NFUNC-009 画布性能 | US-022 | 19、02（纯函数耗时）、22（TBD-T36） |
| REQ-NFUNC-010 兜底不变式 | US-021 | 02（默认专家可达）、10（安全网 + 步数 / 迭代上限）、08 |
| REQ-NFUNC-011 凭据不外露 | US-019 | 15 / 16（序列化纪律）、11（外发白名单）、06（审计不含正文） |
| REQ-NFUNC-012 存量平滑升级 | US-020 | 04（读时规范化 / 哈希稳定 / `upgrade_to_v2`）、02（`canonical_graph_from_experts`）、13（基线版本）、10（`legacy` 回退） |
| REQ-NFUNC-013 可测试性 | US-013 | 02、03、05（纯函数） |
| REQ-NFUNC-014 外发边界 | US-030 | 11（`EgressGuard`）、22（静态规则） |
| REQ-NFUNC-015 降级与时限 | US-030 | 11、08、16、20 |

覆盖核对：REQ-FUNC-001~023 每行至少一个 MOD，无空行；REQ-NFUNC-001~015 同。

---

## 依赖关系

模块编号即拓扑序：每条边 `w(A) > w(B)`（A 依赖 B），故无环。

| 依赖边（经由接口） |
|---|
| 02 → 01（IFC-R26-001 / 002） |
| 03 → 01（IFC-R26-005） |
| 04 → 01, 02（IFC-R26-010 / 011） |
| 05 → 01, 02, 04（IFC-R26-003 / 010 / 033） |
| 06 → 01（IFC-R26-004，端口的适配器） |
| 07 → 01（IFC-R26-002 `KnowledgeScope`） |
| 08 → 01 |
| 09 → 01（IFC-R26-004 `DocScopeResolver`） |
| 10 → 01, 02（IFC-R26-001 / 003 / 012 / 013） |
| 11 → 01, 02, 04, 05（IFC-R26-003 / 031 / 040 系） |
| 12 → 01, 02, 04, 05, 07, 09, 10（IFC-R26-060 / 080 / 081 / 090 / 091） |
| 13 → 01, 02, 04, 05（IFC-R26-030~034 / 040 系） |
| 14 → 01, 06, 07, 08, 09, 10, 11, 12, 13（装配；IFC-R26-050 / 104 / 111 / 120 等） |
| 15 → 03, 14（IFC-R26-020 / 130） |
| 16 → 03, 11, 14 |
| 17 → 06, 14 |
| 18 → （HTTP 契约，无代码依赖） |
| 19 → 18；20 → 18, 19；21 → 18, 19, 20 |
| 22 → （无） |

**已检查：无循环依赖。** 说明：`ib.runtime`（12）依赖 `ib.orchestration`（10）而非反向——`Orchestrator` 只接收 `ProjectRuntimeView` / `CompiledDag` 这两个定义在 01 / 10 内的值对象；`ib.builder`（11）不依赖 `ConfigPublishService`（13）；发布服务通过注入的 `on_published` 回调通知运行时缓存（由 14 装配），故 13 与 12 之间无边；`ib.confsvc` 与 `ib.runtime` 都只依赖端口 / 纯函数。基线依赖图（`docs/module_design.md` §4.1）逐行不变，新增模块均为"被 14 / 15 / 16 / 17 依赖、无反向入边"的叶侧模块。

---

## 数据迁移

**迁移号**：`src/deploy/migrations/008_config_versions.sql`（手写，内容与 `src/ib/ledger/schema.py` 的 `config_versions_ddl_script()` 逐字一致；已存在的 001~007 不改）。随 `ib-web.service` 的 `ExecStartPre=python -m ibweb.bootstrap --ensure-schema` 自动应用；`ensure_schema` 先补列（`PRAGMA table_info` 探测）、再 `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`，**幂等**，可重放。

**新表**

| 表 | 列（类型 / 约束） | 索引 |
|---|---|---|
| `config_versions` | `project_id TEXT NOT NULL`、`version INTEGER NOT NULL`、`parent_version INTEGER NOT NULL`、`status TEXT NOT NULL CHECK (status IN ('pending','published','aborted'))`、`kind TEXT NOT NULL CHECK (kind IN ('publish','rollback','baseline','adopt'))`、`rolled_back_to INTEGER`、`actor TEXT NOT NULL`、`created_at TEXT NOT NULL`、`summary TEXT NOT NULL`、`manifest_hash TEXT NOT NULL`、`snapshot_json TEXT NOT NULL`、`snapshot_bytes INTEGER NOT NULL`、`PRIMARY KEY (project_id, version)` | `idx_config_versions_status (project_id, status, version)` |
| `config_head` | `project_id TEXT PRIMARY KEY`、`published_version INTEGER NOT NULL`、`pending_version INTEGER`、`updated_at TEXT NOT NULL` | 主键即点查索引 |
| `config_drafts` | `draft_id TEXT PRIMARY KEY`、`project_id TEXT NOT NULL`、`owner TEXT NOT NULL`、`label TEXT NOT NULL`、`base_version INTEGER NOT NULL`、`payload_json TEXT NOT NULL`、`payload_bytes INTEGER NOT NULL`、`created_at TEXT NOT NULL` | `idx_config_drafts_owner (project_id, owner, created_at)` |
| `builder_eval_cache` | `cache_key TEXT PRIMARY KEY`、`rubric_version TEXT NOT NULL`、`result_json TEXT NOT NULL`、`created_at TEXT NOT NULL` | `idx_builder_eval_created (created_at)` |

**新列（`ALTER TABLE ... ADD COLUMN`，幂等探测）**

| 表 | 列 | 说明 |
|---|---|---|
| `users` | `config_level TEXT NOT NULL DEFAULT 'manage' CHECK (config_level IN ('view','edit','manage'))` | 存量 ops 默认 `manage`（OQ-R26-A01 推荐）；admin 行忽略此列 |
| `config_audit` | `version_before INTEGER`、`version_after INTEGER`、`object_summary TEXT`（JSON 数组） | 既有行为 NULL；`result` 的 CHECK 不变 |

**迁移方式**：画像 P6（手写 scoped SQL + 与 `schema.py` 单源 + `IF NOT EXISTS` + 回滚说明；不用 Django ORM）。**文件态数据不迁移**：既有定义文档 / 提示词目录一字不改（REQ-NFUNC-012）；v1 文档仍为 v1，首次保存才升级为 v2。
**是否可逆 / 回滚说明（写入 008 文件头）**：
- 代码回退（`git revert` → 目标机 pull + 重启）：旧代码对 `users` / `config_audit` 一律按**命名列清单**查询（`accounts.py` 的 `_U_COLUMNS`、`config_audit.py` 的 `_A_COLUMNS`，已核实无 `SELECT *`），忽略新列，可运行；新表被忽略。回退前须确认没有 `pending` 版本（`SELECT 1 FROM config_head WHERE pending_version IS NOT NULL`）；v2 文档在旧代码下**不可读**（旧 `SUPPORTED_SCHEMA_VERSION == 1`）——回退前须经"回滚到基线版本 + 对 v2 文档执行 `downgrade` 说明"或从版本快照 1 还原为 v1 文件（`MANUAL_ROLLBACK_REQUIRED`，步骤写入 `checklists.txt` B29）。
- 撤销新结构（仅在确需时，先备份台账文件，**由用户执行**）：`DROP TABLE builder_eval_cache; DROP TABLE config_drafts; DROP TABLE config_head; DROP TABLE config_versions; ALTER TABLE users DROP COLUMN config_level; ALTER TABLE config_audit DROP COLUMN version_before; ... version_after; ... object_summary;`（`DROP COLUMN` 需 SQLite ≥3.35，开发机为 3.45.1，目标机版本**未知**，须部署前核对；低版本需重建表）。标 `[MANUAL_ROLLBACK_REQUIRED]`；回滚丢失版本历史与评审缓存。
**数据风险**：① `config_versions.snapshot_json` 存提示词全文，随版本数增长（保留 50 个；最坏约 2–6 MB / 版，TBD-T33）；② 迁移期间 `ib-web` 重启窗口内无热生效（上线本身需重启）；③ 台账文件属主 / 权限须保持 `660 ib-web:ib` 且覆盖 `-wal` / `-shm`（检查清单 B22 既有口径，新表无额外要求）。

---

## 受影响的运行单元 / 构建

| 运行单元 / 构建 | 动作 | 原因 |
|---|---|---|
| `ib-web` | **重启一次**（`sudo -n systemctl restart ib-web`；迁移 008 随 `ExecStartPre` 自动应用） | 全部后端代码 / 迁移 / 装配变更；此后配置变更不再需要重启 |
| `ib-worker` | **重启一次** | 共享 `ib.ledger.schema` / `ib.core` 变更；新增维护步骤 |
| `ib-embed` | 不动 | 无契约变更（示例句向量化沿用既有冷路径） |
| `qdrant` | 不动 | 仅使用既有 `doc_ids` 过滤条件；无 collection / payload 变更 |
| nginx | 不动（无需 reload） | `/api/` 已满足 SSE 与体积（F-14） |
| systemd unit / env 文件 | 无变更必需；`env.example` 仅**新增可选键名**，`/etc/intelligentbase/*.env` 由用户按需自行添加（本设计的缺省值即可运行） | 画像 P7：env 修改由用户执行 |
| 前端构建 | 目标机 `npm ci && npm run build` 后发布到 web root（无新依赖，`package-lock.json` 不变） | `ConfigPage.vue` 与新组件、`client.ts` |
| CI | `ci.yml` 迁移检查段新增 008 单源比对；`pytest` 目录不变；前端 `npm run build && npm test` | MOD-R26-22 |
| 定时任务 | 无新增（维护步骤在 `ib-worker` 既有循环内） | 画像 P7：不新增运行单元 |
| 部署后验证 | `systemctl is-active ib-web ib-worker ib-embed`；`GET /api/config/status`；`hot_effect_probe.py`（用户执行）；`journalctl -u ib-web --since <启动时刻>` 无 `runtime_compile_failed` / `config_drift` | 画像 P7 验证口径 + TBD-T32 |

---

## 测试文件规划（画像 P3：目录与命名；基名全局唯一，带 `_r26` 后缀）

| 层 | 文件（新建） | 覆盖 |
|---|---|---|
| 单元 | `tests/unit/test_graph_validate_r26.py`、`test_graph_layerize_r26.py`、`test_condition_eval_r26.py` | MOD-02：全部错误码、环节点列表、汇聚语义（含"只激活一路"）、层归一化每边跨 1 层 |
| 单元 | `tests/unit/test_config_access_r26.py`、`test_definition_v2_r26.py`、`test_config_diff_conflict_r26.py` | MOD-03 / 04 / 05：档位表、v1/v2 往返、哈希稳定（存量哈希不变）、差异与三方冲突 |
| 单元 | `tests/unit/test_config_version_store_r26.py`、`test_publish_protocol_r26.py`、`test_runtime_cache_r26.py` | MOD-06 / 12 / 13：`begin / commit / abort / claim_stale`、崩溃恢复各步注入、单飞编译、失败保留旧版、挂起版本钉住 |
| 单元 | `tests/unit/test_agent_tools_enforce_r26.py`、`test_doc_scope_filter_r26.py`、`test_llm_client_lru_r26.py` | MOD-07 / 08 / 09：按 agent 绑定、未授权回调、空范围 0 命中且不查向量库、`doc_ids` 条件 |
| 单元 | `tests/unit/test_builder_adapt_rubric_r26.py`、`test_builder_egress_r26.py` | MOD-11：适配规则、评分可复现（10 次同分）、白名单载荷 / canary 命中 0 / 秘钥拦截 / 审计先行 |
| 集成 | `tests/integration/test_config_publish_api_r26.py`、`test_hot_effect_r26.py`、`test_config_access_api_r26.py`、`test_builder_api_r26.py`、`test_trial_api_r26.py`、`test_config_schema_migration_r26.py`、`test_legacy_equivalence_r26.py` | MOD-14 / 15 / 16：发布 / 冲突 / 回滚 / 草稿；两线程模拟多进程收敛；三档 403；Builder 降级与时限；迁移幂等与老库形态；v1 项目 `legacy` ↔ `dag` 金标 20 题一致 |
| E2E | `tests/e2e/test_config_journeys_r26.py` | US-014 / 015 / 017 / 018 / 020 / 029 旅程（Django 测试客户端，离线替身） |
| 前端 | `src/frontend/tests/frontend.smoke.test.js`（追加断言） | `graphModel` 纯函数、hover 卡片模型、`client.ts` 方法存在、无 `v-html` / `localStorage` / axios / CDN、锁文件与 `package.json` 同步 |
| 契约（需真实 langgraph） | `tests/integration/test_langgraph_contract_r26.py` | ADR-57 假设 A-R26-01（缺依赖时标 BLOCKED，不安装） |

既有需随取代而重新基线的测试见 `architecture_design.md` §6.3。

---

## 自检

- 每条 REQ-FUNC（001~023）与 REQ-NFUNC（001~015）至少被一个 MOD 覆盖（覆盖表无空行）。
- 所有对外接口（HTTP 12 组 / SSE 1 条 / CLI 1 条）均写明鉴权方式（沿用 Bearer + 配置三档）与输入校验（类型 / 长度上限 / 非法输入错误码）；无需鉴权的端点：无新增（`/healthz` 既有不变）。
- 引用的现有文件 / 类 / 函数均经 `git grep` 或读码核实：`composition.py:266 orchestrator_for / :205 reload_projects / :340`、`views.py:609 / :650`、`orchestration/__init__.py:1003 _compile_graph / :1105 _run_expert`、`llm/__init__.py:162 / :241 / :477`、`tools/__init__.py:364 build_authorized_tools / :150 bind_scope`、`retrieval/__init__.py:97 search / :245 search_as_tool`、`ledger/tree.py:110 EntryTreeStore`、`ledger/schema.py:206 / :293 / :801`、`config/definition.py:99 / :165 / :206 / :555`、`ibweb/accounts/__init__.py:156 effective_roles`、`ibweb/accounts/policy.py`、`core/ports.py:605 / :881`。
- 接口均带类型；无函数体与示例实现；JSON / 表格仅为数据格式。
- 无画像 P8 禁用技术；无新增 systemd 单元；无新增第三方依赖（见 `tech_stack.md`）。
