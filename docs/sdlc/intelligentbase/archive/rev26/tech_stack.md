<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-27T00:53:03+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements_spec.md</file>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（REV-26 增量）

**口径**：INCREMENTAL，沿用画像 P1 技术栈与既有模式；**本轮不新增任何第三方依赖（Python / npm / 系统组件）、不新增 systemd 单元、不引入容器 / Redis / Channels**。基线 `docs/tech_stack.md`（1.4.1，只读）继续有效，本文件只登记 REV-26 涉及或需要复核的条目与风险。版本一律来自仓库依赖清单 / 锁文件 / 本机实测命令输出，或标注 `[WEB: URL，日期]`；查不到的写"未知"。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增 / 沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | 开发机 3.12.3（`python3 --version` 实测 2026-10-27）；约束 `>=3.11,<3.14`，CI 3.12（`.github/workflows/ci.yml:55-58`） | 沿用 | 画像 P1；新代码全部 3.11 兼容的类型注解（`Literal` / `Final` / `Protocol` / `dataclass(slots=True)`） | 全部 | 低 |
| Web 框架 | Django + DRF（视图为函数式、手写序列化） | `Django>=5.0,<6.1`（`src/requirements.txt:14`）、`djangorestframework>=3.15,<4.0`（`:15`）；本机未安装，实际版本以目标机 venv 为准——**未知** | 沿用 | 新端点沿用现有 `views.py` 风格与手写 `to_representation`，不引入 ORM / `contrib.auth` | FUNC-010/014/016/017/023 | 低 |
| WSGI | Waitress（主）/ Gunicorn（备） | `waitress>=3.0,<4.0`（`:16`）、`gunicorn>=22.0,<24.0`（`:17`）；`ib-web.service` 用 `--threads=8`、`MemoryMax=1024M`（`src/deploy/systemd/ib-web.service`） | 沿用 | 热生效机制对进程数不敏感（ADR-53）；后台编译 / Builder 用进程内小线程池，不是新单元 | NFUNC-001/004 | 中：8 线程同时承载 SSE（问答 + 试运行）与 Builder 调用，容量须实测（TBD-T39） |
| 编排 | LangGraph | `langgraph>=0.2,<2.0`（`src/requirements.txt:23`）；PyPI 当前最新 1.2.17，MIT，`requires_python>=3.10` [WEB: https://pypi.org/pypi/langgraph/json，2026-10-27]；本机**未安装**，目标机实际版本——**未知** | 沿用 | DAG 以层归一化 + 中继节点编译，只用基础 API：`StateGraph` / `add_node` / `add_edge` / `add_conditional_edges` / `Send`（现有已用）与 `interrupt_before` + `MemorySaver`（仅 `confirm` 节点）；官方文档确认"节点收到任一入边消息即 active，同一超步并行运行，条件边可返回节点名列表" [WEB: https://docs.langchain.com/oss/python/langgraph/graph-api，2026-10-27] | FUNC-006/011；NFUNC-010 | **中**：`interrupt_before` / `MemorySaver` 与"超步合并运行一次"在 0.2~1.x 区间内的行为须由契约测试固化（A-R26-01 / TBD-T34）；版本区间宽（`<2.0`），升级到 1.x 与 `langchain-openai<0.3` 的共存性是既有风险，本轮不改约束 |
| LLM 接入 | `langchain-core` / `langchain-openai`（DeepSeek，OpenAI 兼容端点） | `langchain-core>=0.3,<2.0`（`:24`）、`langchain-openai>=0.2,<0.3`（`:25`，**P8：必须 <0.3**） | 沿用 | Builder 经 `OpenAiCompatibleProvider.complete`（实现侧新增方法，端口方法集不变）复用同一客户端 / 同一 Key（ADR-38 / 39）；**不依赖** `response_format` / 严格结构化输出（`<0.3` 与 DeepSeek 的行为未核实） | FUNC-018~022；NFUNC-014/015 | 中：JSON 输出靠提示词约束 + 容错解析，格式偶发失败需重试 / 报错（A-R26-03）；DeepSeek 无确定性保证，故评审 LLM 项采用持久化缓存（ADR-64） |
| 向量库 | Qdrant（裸装 .deb）+ `qdrant-client` | `qdrant-client>=1.7,<2.0`（`:43`） | 沿用 | 目录范围过滤使用既有 `PointFilter.doc_ids` → `MatchAny`（`src/ib/vectorstore/__init__.py:368-381`）；**不改 payload、不重建 collection** | FUNC-009 | 中：`doc_ids` 集合很大时过滤开销上升，超阈值走后过滤降级（ADR-62 / TBD-T35） |
| Embedding | bge-m3，独立 `ib-embed` | 见 `src/requirements-embed.txt`（基线登记；本轮不动） | 沿用 | 示例句向量化沿用冷路径（`embed_documents`），按文本哈希进程内缓存，换版只重算变更部分 | FUNC-006/014 | 低；注意 AVX2 / SIGILL 既有风险（基线 TBD-T18）本轮无新 wheel |
| 数据存储 | SQLite（WAL，台账） | 开发机 SQLite 3.45.1（`python3 -c "import sqlite3;print(sqlite3.sqlite_version)"` 实测）；**目标机 SQLite 版本——未知**（影响回滚时 `ALTER TABLE ... DROP COLUMN`，需 ≥3.35） | 沿用 | 新增 4 表 + 2 处扩列（迁移 008）；版本存储为"提交记录"，head 点查走主键；仍不用 Django ORM | FUNC-014/015/017；NFUNC-002/005/006 | 中：快照体积随版本增长（TBD-T33）；多线程写争用沿用既有 `busy_timeout` 纪律 |
| 文件存储 | 本地目录（定义文档 JSON + 提示词 markdown） | 现有 `IB_DEFINITION_DOC_PATH` / `IB_EXPERT_PROMPT_DIR` 布局不变 | 沿用 | 仍为两域真源（C-R26-04）；发布协议保证两域变更的一致终态（ADR-55） | FUNC-014 | 中：绕过系统直接改文件会被判漂移（有意取舍，ADR-55） |
| 前端框架 | Vue 3 + Vite + TypeScript | `vue 3.5.43`、`vite 5.4.21`、`typescript 5.9.3`、`vue-tsc 2.2.12`、`@vitejs/plugin-vue 5.2.4`（`src/frontend/package-lock.json`） | 沿用 | 组件拆分不引入新库（ADR-69） | 全部前端 | 低 |
| UI 组件 | Element Plus + vue-router（hash 模式） | `element-plus 2.14.5`、`vue-router 4.6.4`（`package-lock.json`；MIT，基线已登记） | 沿用 | 对话框 / 表单 / 抽屉 / 表格复用；悬停卡片用原生绝对定位 + Element Plus 弹层，无新依赖 | FUNC-001/002/004/016/017 | 低 |
| 图画布 | `@vue-flow/core` | `1.48.2`，MIT（`package-lock.json:1011-1015`；`node_modules/@vue-flow/core/package.json`）；已含 `nodeMouseEnter` / `edgeMouseEnter` / `connect` / `nodeDragStop` / `isValidConnection` / `nodesChange` / `edgesChange`（`node_modules/@vue-flow/core/dist` 类型声明实测） | 沿用 | 可交互画布所需事件均已具备；分层布局沿用现有 `layeredPositions`（迁入 `graphModel.ts`）；**不新增 dagre / elkjs 等布局库** | FUNC-001/003/011/012；NFUNC-009 | 中：30 节点 / 60 边的交互性能须在目标浏览器实测（TBD-T36）；传递依赖（d3 系 / `@vueuse/core`）许可沿用基线登记，本轮无变化 |
| 前端 HTTP | 原生 `fetch` 封装 `src/frontend/src/api/client.ts` | 无外部依赖 | 沿用 | P6/P8：无 axios、无 CDN；试运行 SSE 沿用 `chatResume` 的 `fetch + ReadableStream` | FUNC-023 | 低 |
| 前端测试 | Node 内置 `node:test` | 画像 P3：Node 20；开发机 `node --version` = v22.23.3（实测） | 沿用 | `graphModel` / 悬停卡片模型等纯函数冒烟，追加到 `src/frontend/tests/frontend.smoke.test.js` | 全部前端 | 低 |
| 后端测试 | pytest（离线替身） | 开发机**未安装**（画像 P4 已记录；子代理不得自行安装 → 测试标 BLOCKED） | 沿用 | 新测试清单见 `module_design.md` §测试文件规划 | NFUNC-013 | 中：契约测试 `test_langgraph_contract_r26.py` 需真实 `langgraph`（离线集 `requirements-offline.txt:20` 已含 `langgraph>=0.2,<2.0`） |
| 密码 / 凭据 | bcrypt（账号）；LLM Key 存 `llm_key` 表 | `bcrypt>=4,<5`（`src/requirements.txt:54`） | 沿用 | 本轮不新增凭据面；Builder 外发白名单禁凭据（ADR-65），审计 / 快照不含凭据 | NFUNC-011/014 | 低 |
| 进程管理 | systemd 四单元（ib-web / ib-worker / ib-embed / qdrant） | `src/deploy/systemd/*.service` | 沿用 | **无新增单元**（画像 P7）；后台编译 / Builder 线程池在 `ib-web` 进程内；维护步骤并入 `ib-worker` 既有循环 | C-R26-02 | 低 |
| 容器化 | 无 | — | 沿用（禁止） | 画像 P8 | — | — |
| CI/CD | GitHub Actions `ci.yml`（10 阶段） | `.github/workflows/ci.yml` | 沿用（迁移检查段增 008） | 新迁移须与 `schema.py` 生成器逐字一致（P6）；该文件仅在 `module_design.md` 明确要求时由 devops 修改 | NFUNC-012 | 低 |
| 部署方式 | 目标机 `git pull` + `sudo -n systemctl restart ib-web ib-worker` | 画像 P7 | 沿用 | 上线本身需重启一次；此后配置变更免重启 | C-R26-03 | 低 |
| 新增依赖 | **无** | — | — | 不新增 Python 包、npm 包、系统组件；因此无新许可 / 维护风险登记 | — | — |

## 许可与离线可用性核对（本轮复核，无新增）

| 项 | 许可 | 离线 / 本地打包 | 备注 |
|---|---|---|---|
| `@vue-flow/core` 1.48.2 | MIT（`package-lock.json` 的 `license` 字段） | 随 `npm run build` 本地打包，运行期无 CDN | 沿用基线登记 |
| `langgraph` | MIT [WEB: https://pypi.org/pypi/langgraph/json，2026-10-27] | pip 安装，无运行期联网 | 沿用 |
| 其余（Django / DRF / Waitress / Gunicorn / qdrant-client / bcrypt / Vue / Element Plus / vue-router / Vite） | 基线 `docs/tech_stack.md` 已登记 | 沿用 | 本轮无变化 |
| 云端 DeepSeek（LLM） | 外部服务（非软件依赖） | 需联网；Builder 失败时手工方式仍可用（REQ-NFUNC-015） | 外发边界见 ADR-65；`describe_egress` 声明补 Builder 类别 |

## 技术风险

### High

（无。）

### Medium

| 风险 | 说明 | 缓解措施 |
|---|---|---|
| R-01 LangGraph 超步 / 中断语义在版本区间内不一致 | 汇聚依赖"同一超步内被触发的上游合并运行一次"；`confirm` 节点依赖 `interrupt_before` + `MemorySaver`；本机未安装、官方文档页对"多入边 / `add_edge` 列表 / `defer`"未覆盖（A-R26-01） | 契约测试 `test_langgraph_contract_r26.py` 在真实依赖环境固化行为（TBD-T34）；不使用 `defer` 与 `add_edge([...])`；`IB_GRAPH_RUNTIME=legacy` 作回退；契约测试失败则 `confirm` 节点降级为不可用并回 GROUP_B |
| R-02 热生效时延 / 内存 | 编译在 `ib-web` 内（`MemoryMax=1024M`），含示例句向量与多份快照；INF-3 的 5 s 为占位 | 示例句向量按文本哈希缓存；快照最多保留当前 + 2 旧版 + 钉住版本；后台单飞编译；探针脚本与 TBD-T32 / T37 目标机实测 |
| R-03 评审"同输入同分"的残余 | DeepSeek 不保证确定性；LLM 判定项仅占 6 分且靠缓存复现，缓存失效后可能微差（ADR-64 / OQ-R26-A04） | 94 分规则化；LLM 项布尔化 + 证据 + 持久化缓存 + `coverage` 标记；交用户确认是否接受残余或改为仅规则项 |
| R-04 SSE / 线程预算 | 试运行与正式问答共用 8 个 Waitress 线程；Builder 调用另占进程内线程池 | 试运行并发上限（每项目 1 / 全局 2）、快速 429；Builder 池 2 且池满 429；沿用基线 TBD-T15 的容量纪律并新增 TBD-T39 |
| R-05 行为变更：按 agent 的工具参数首次真正生效 | 今天项目授权并集发给每个专家（F-4），升级后按专家的参数 / 授权生效，可能改变既有项目的检索条数 | 发布说明列出；金标 20 题对比；`IB_GRAPH_RUNTIME=legacy` 同时保留旧装配路径作回退基准 |
| R-06 画布交互性能 | 30 节点 / 60 边下悬停 ≤300 ms 为占位（INF-5） | 纯模型函数离线度量；目标浏览器实测（TBD-T36）；超标时再评估虚拟化 / 分组折叠（本轮不做） |

### Low

| 风险 | 说明 | 缓解措施 |
|---|---|---|
| R-07 提示词 20000 字符上限与模型上下文 | 上限是存储 / 交互边界，不保证模型装得下（A-R26-04） | TBD-T33 在所用模型上测 token 数后调整常量 `PROMPT_LAYER_MAX_CHARS` |
| R-08 回滚时 `DROP COLUMN` 对 SQLite 版本的要求 | 目标机 SQLite 版本未知（需 ≥3.35） | 部署前核对；回滚步骤标 `[MANUAL_ROLLBACK_REQUIRED]`，必要时重建表 |
| R-09 v1 → v2 文档下旧代码不可读 | 回退代码后 v2 文档会被旧 `SUPPORTED_SCHEMA_VERSION==1` 拒绝 | 回退前由用户按检查清单 B29 从基线版本快照还原 v1 文件；首存前的项目不受影响 |
| R-10 依赖版本区间宽 | `langgraph<2.0` 与 `langchain-openai<0.3` 的共存性由既有 CI 版本门保证，本轮不收紧 | 沿用 CI 版本门；契约测试覆盖本轮用到的 API |
