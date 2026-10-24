<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-24T17:56:54+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/user_stories.md</file>
    <file>docs/sdlc/intelligentbase/phase_status.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 资料管理：文件夹上传与云盘式目录管理 — 架构设计（INCREMENTAL）

> 基线：`docs/architecture_design.md`（legacy_baseline，只读，不修改）。本文只描述增量。
> 编号：本文 ADR 用新序列三位数 `ADR-001…`；基线 ADR 为两位数（`ADR-03`、`ADR-41` 等），引用时一律写"基线 ADR-NN"，二者不冲突。
> 引用的现有代码均已用 `git grep -n` / `sed -n` 核实存在（见各处 `文件:行`）。

## 架构概览

### 本次改动在现有系统中的位置

现有系统（基线）：Vue 3 前端（`src/frontend`）→ nginx → `ib-web`（Django + DRF，Waitress 8 线程，`src/deploy/systemd/ib-web.service:49-54`）→ 框架无关核心 `src/ib/*`；SQLite 台账（WAL）+ sha256 blob store + Qdrant（collection-per-project）；`ib-worker` 单实例做入库与重建；`ib-embed` 做向量化。资料以**平铺**方式存在 `documents` 表（`src/ib/ledger/schema.py:82-101`），无目录、无同名约束、无独立"索引成功时间"。

本增量在同一套栈上叠加四类能力，**不新增运行单元、不新增依赖、不改 nginx**：

1. **目录树**：台账新增 `folders` 表（邻接表）；`documents` 增加 `folder_id`、`name_key` 等列。目录与同名规则只在台账层存在，向量库不感知目录。
2. **批次上传会话**：一次文件夹上传 = 一个"批次"（计划 + 逐文件上传），解决"1000 个文件"与"单请求体 64MB"的量级冲突（C-02）。
3. **文件更新（影子修订）**：更新 = 建一个隐藏的"修订行"走既有入库流水线，索引成功后在**一个台账事务**内替换旧行；检索对命中做"台账存活过滤"，使新旧切换一次性生效（REQ-NFUNC-002）。
4. **检索命中以台账为权威**：检索后按 `doc_id` 向台账解析"是否存活 + 当前名称 + 目录路径"，使重命名/移动/文件夹重命名无需改写向量 payload 即可保持引用一致（REQ-NFUNC-001、REQ-FUNC-014）。

### 与基线 ADR 的关系

| 基线 ADR | 关系 | 说明 |
|---|---|---|
| 基线 ADR-03（v1 固定四个 systemd 单元） | 遵守 | 不新增单元；清理/晋升挂在既有 `ib-worker` 轮询周期内（ADR-010） |
| 基线 ADR-05（原始文件持久化 + 索引重建、新集合 + 原子切换） | 沿用并扩展 | 更新替换已持久化原始文件；与重建共存见 ADR-007 |
| 基线 ADR-07（先向量后台账、台账为可见性权威） | 沿用并强化 | 本增量把"台账可见性权威"从删除路径扩展到检索路径（ADR-005） |
| 基线 ADR-10（SQLite 队列 + 租约认领） | 沿用 | 修订行是普通 `documents` 行，走同一 `claim_pending`；无新队列载体 |
| 基线 ADR-41（`kb_id ≡ project_id`） | 沿用 | 目录树、批次、清理队列均按 `project_id` 作用域；`kb_id` 仍由服务端从已认证主体推导，请求体不接收 |
| 基线 OOS-07（同名覆盖等不纳入） | 被需求 C-06 取代其"同名覆盖"一项 | 本文 ADR-004 实现；多版本共存/回滚仍不做 |

### 关键质量属性（引用 REQ-NFUNC）

| 质量属性 | 需求 | 架构手段 |
|---|---|---|
| 一致性（无幽灵向量、无"可见不可检索"） | REQ-NFUNC-001 | 台账为存活权威 + 检索期存活过滤（ADR-005）；物理清理沿用"先向量→blob→台账 + 竞态清扫" |
| 更新期间可用性 | REQ-NFUNC-002 | 影子修订行 + 台账事务晋升（ADR-004） |
| 失败可见 | REQ-NFUNC-003 | 修订失败不影响旧版；`update_state` 字段对外暴露失败原因码 |
| 与重建共存 | REQ-NFUNC-004 | 晋升推迟到"修订的索引版本 = 项目当前 active 版本"（ADR-007） |
| 权限与隔离 | REQ-NFUNC-005 | 所有新端点沿用 `_require_manage` / `_ctx_of` + `composition.resolve_scope`；项目取自鉴权结论（ADR-012） |
| 性能 | REQ-NFUNC-006 | 目录浏览走覆盖索引 + 分页上限 100；批次上传前端并发 2，不阻塞页面（ADR-003、ADR-011） |
| 部分失败隔离 | REQ-NFUNC-007 | 逐文件独立请求/事务；递归删除分步可恢复（ADR-008）；移动为单事务全有全无 |

### 数据流（增量）

```
浏览器 ──POST /api/uploads(计划/提交)──▶ UploadBatchService ──▶ EntryTreeStore(台账事务)
   │  ──PUT /api/uploads/{b}/items/{i}(每文件≤50MB, 并发2)──▶ lifecycle.submit_library_document
   │                                        └─ 台账事务: 建缺失目录链 + 建 pending 行 ─▶ 落盘 blob
ib-worker ──claim_pending──▶ _process_one ──(普通行) mark_indexed
                                           └(修订行) promote_revision: 台账事务内 删旧行/晋升新行 + 入清理队列
                                              └ 晋升后 drain_purge_queue: 删旧向量(全版本)/旧 blob
检索: Qdrant 命中 ─▶ entry_resolver.resolve_live(台账) ─▶ 丢弃非存活命中 + 填当前名称/目录路径
```

## 部署视图

仅使用画像 P7 存在的环境与运行单元；无 staging。

| 组件 | 运行单元 | 环境 | 变更 |
|---|---|---|---|
| 目录/批次/修订 HTTP 端点、台账迁移 | `ib-web`（`ExecStartPre … --ensure-schema` 自动应用迁移） | dev/local、CI、production | 修改；重启 `ib-web` |
| 修订晋升、清理队列排空、入库流水线分支 | `ib-worker`（`ibweb/worker.py` 轮询周期内调用） | 同上 | 修改；重启 `ib-worker` |
| 检索命中解析（存活过滤 + 路径） | `ib-web`（问答链路在 ib-web 进程内） | 同上 | 修改；随 `ib-web` 重启 |
| 前端资料管理页 | 前端静态产物（目标机 `npm run build` 后拷贝 web root，不重启） | 同上 | 修改；无需重启 |
| nginx | 外部反代（非 systemd 自有单元） | production | **不变**（`client_max_body_size 64m` 保持，见 ADR-003） |
| ib-embed、qdrant | — | — | 不变 |

## ADR

### ADR-001: 目录树存储模型（邻接表 `folders` 表 + `documents.folder_id`）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-001/003/004/005/006/013/015/017 需要目录层级、面包屑、重命名、移动、10 层深度限制；REQ-FUNC-001 与 AC-004-01 要求能表达**空文件夹**（用户手动新建）；REQ-NFUNC-006 要求单目录 ≤1000 条目浏览 P95 ≤2s；REQ-NFUNC-001 要求重命名/移动不触碰向量。现状 `documents` 平铺，台账是 SQLite（基线 ADR-07）。
- Options:
  - A. **邻接表**：新表 `folders(folder_id, project_id, parent_id, name, name_key, depth, …)`；`documents.folder_id` 指向所属目录（`''` = 根）。优：能表达空文件夹；重命名文件夹只改一行；移动文件夹只改一行 `parent_id` 并重算子树 `depth`；目录路径由父链（≤10 跳）推导，不存冗余路径；浏览 = 按 `(project_id, parent_id)` 索引取子项。缺：取路径/子树需沿父链或递归 CTE（SQLite 支持 `WITH RECURSIVE`）；`depth` 是冗余列，移动时需在同一事务内重算。
  - B. **物化路径**：每个目录/文件存完整路径字符串（`A/B/C`）。优：取路径免递归。缺：文件夹重命名/移动要改写全部后代的路径（O(子树) 行写，且极易与引用/清理漂移）；空文件夹仍需独立记录；路径含大小写与分隔符的转义问题；与"重命名不得影响检索"的零向量改动相容但写放大大。
  - C. **仅在 `documents` 加 `path` 列、不建目录表**。优：改动最小。缺：无法表达空文件夹（直接违反 AC-004-01）；目录重命名等同 B 的写放大；无处承载目录级唯一约束。
- Decision: 选 A，因为只有 A 同时满足"空文件夹可表达（REQ-FUNC-004）"与"重命名/移动 O(1) 写、无向量改动（REQ-NFUNC-001）"，且浏览走索引满足 REQ-NFUNC-006。`depth` 作为冗余列保留，用于 10 层校验的 O(1) 判定；移动时在同一写事务内用递归 CTE 重算子树 `depth`。
- Consequences: 正向——重命名/移动文件夹是单事务小写入；目录路径永不陈旧（无存储副本）。负向——① 引用完整性无法用外键表达（`documents.folder_id` 由 `ALTER TABLE ADD COLUMN` 补列，SQLite 的 ADD COLUMN 不允许带非空默认的外键），改由服务层事务内校验 + 自检对账（MOD-015）；② `depth` 冗余需随移动维护；③ 路径推导 O(层数)，为此检索期批量解析按 `doc_id` 集合一次完成（ADR-005）。

### ADR-002: 同名唯一性（不区分大小写、并发安全）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-011/016：同目录同名判定**不区分大小写**；REQ-NFUNC-005/007：并发上传下仍成立（用户要求的核心保证之一）。现状 `documents` 无任何同名约束（`schema.py:82-101`，B-04）。台账有两类并发写者：`ib-web`（Waitress 8 线程）与 `ib-worker`，写事务一律 `BEGIN IMMEDIATE`（`src/ib/ledger/sqlite_repo.py:239-253`），即**所有写事务被 SQLite 写锁全局串行化**。
- Options:
  - A. **应用侧计算 `name_key = NFC(name.strip()).casefold()` 存列 + 部分唯一索引 + 写事务内先检查后写入**：`UNIQUE(project_id, folder_id, name_key) WHERE name_key<>'' AND revision_of IS NULL`（文件），`UNIQUE(project_id, parent_id, name_key)`（文件夹）。文件与文件夹之间（跨表）的同名由写事务内显式检查（`BEGIN IMMEDIATE` 已串行化，检查与写入之间无窗口）。唯一索引是第二道保险：并发冲突或漏检时抛 `IntegrityError`，映射为 409 `name_conflict`。优：完整 Unicode casefold 语义；并发保证由"全局写锁 + 数据库唯一约束"双重承担；与 Python/前端展示规则同源。缺：历史行需回填 `name_key`（ADR-009）。
  - B. **SQLite `COLLATE NOCASE` 唯一索引**。优：声明式、无需回填列。缺：`NOCASE` 仅折叠 ASCII，对 `É/é`、`ß` 等不成立，与"不区分大小写"需求在非 ASCII 名称上不符；也无法实现文件/文件夹跨表同名检查。
  - C. **只在应用层检查，无唯一索引**。优：改动小。缺：任一代码路径漏检（如批次上传 + 重命名并发）即产生重复，且无法在测试中用数据库约束兜底；违反"并发上传下成立"的可验证性。
- Decision: 选 A（REQ-FUNC-011、REQ-FUNC-016、REQ-NFUNC-007）。名称规则（非空、无 `/` `\`、≤255）、`name_key` 计算与"下一个可用改名 `名称 (n).ext`"集中在 `ib/core/library.py` 的纯函数（MOD-001），写入路径只此一份实现。
- Consequences: 正向——并发上传同名文件，必有且仅有一个成功，其余得 409/批次内 `NAME_CONFLICT` 跳过；`casefold` 保证 `A.pdf`/`a.pdf` 同名。负向——① 修订行（隐藏）`name_key=''`，不占名；晋升事务内若发现名称已被占用，则自动按 `(n)` 顺延改名而非失败（避免"索引成功后因命名失败丢更新"）；② 同一目录下文件与文件夹同名（如文件夹 `x.pdf`）也算冲突，范围略大于需求字面（`[ASSUMPTION A-05]`）。

### ADR-003: 大批量上传的传输方案（批次会话 + 逐文件请求）与"单次上传总大小"默认值
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-015 / C-02 / OQ-05：单次最多 1000 个文件、每文件 ≤50MB，与"单请求体 64MB"（`src/deploy/nginx/intelligentbase.conf.example:96` 的 `client_max_body_size 64m`；`src/ibweb/settings.py:118` 的 `DATA_UPLOAD_MAX_MEMORY_SIZE`）量级不相容；总大小上限默认值需本阶段给出。REQ-NFUNC-007：单文件失败不影响其他；"超限在上传开始前整体拒绝，不产生半成品"；画像 P7：nginx reload 必须由用户执行。
- Options:
  - A. **单请求 multipart 一次传整个文件夹**，并上调 nginx 与 Django 限制。优：协议最简。缺：必须改 nginx 并由用户 reload；单请求占用一个 Waitress 线程（共 8 线程，SSE 问答也占线程，见 M-SA-006 容量约束）达数分钟；中途失败整体重来，违反 REQ-NFUNC-007；服务端需缓冲 GB 级请求体（4GB 内存目标机）。
  - B. **批次会话 + 逐文件请求（选）**：① `POST /api/uploads` 提交**清单**（相对路径 + 大小，纯 JSON，1000 项约数百 KB）→ 服务端一次性完成全部上限校验、分类（跳过原因）、同名冲突检测并落批次记录；② 客户端以**并发 2** 逐个 `PUT /api/uploads/{batch}/items/{idx}` 上传文件体（每个 ≤50MB，天然 <64MB）；③ `GET /api/uploads/{batch}` 取汇总。优：**无需改 nginx/Django 限制**（用户无需 reload nginx）；单文件失败天然隔离；进度 = 已处理数/总数；失败可对单文件重试（同一 `idx` 幂等）。缺：多一类批次状态（两张小表）；需要批次过期清理。
  - C. **分块断点续传（chunked/resumable）**。优：可传超大文件、断点续传。缺：单文件上限本就 50MB，收益有限；引入分块协议与合并步骤，复杂度远超需求。
- Decision: 选 B（REQ-FUNC-015、C-02、REQ-NFUNC-007）。**配置项与默认值**：
  - `IB_UPLOAD_BATCH_MAX_FILES`，默认 `1000`；
  - `IB_UPLOAD_BATCH_MAX_TOTAL_MB`，默认 `1024`（1 GiB）`[ESTIMATE]`；
  - `IB_LIBRARY_MAX_DEPTH`，默认 `10`；
  - `IB_UPLOAD_BATCH_TTL_HOURS`，默认 `24`（批次记录过期清理）；
  - 单文件上限沿用 `IB_MAX_UPLOAD_MB`（默认 50，`src/ib/config/__init__.py:368`）。
  总大小默认 1 GiB 的依据：典型资料（PDF/DOCX/MD/TXT）单个远小于 50MB，1000 个文件 × 平均 1MB ≈ 1GB 量级可覆盖"整份项目文档夹"；同时它给磁盘占用（blob 永久持久化，基线 ADR-05）和单 worker 的索引排队（C-05）设上界。目标机磁盘剩余空间未知 `[ASSUMPTION A-01]`，数值须由部署阶段按磁盘余量确认，可经 env 调整。
  - **传输约束**：`IB_MAX_UPLOAD_MB` 加 multipart 开销必须 <64MB（nginx 与 Django 限制保持不变）；配置装载时若 `IB_MAX_UPLOAD_MB > 60` 记录 WARNING（不改变基线行为）。
  - **服务端权威**：客户端清单不被信任——每个文件到达时服务端按批次记录核对序号、声明大小、实际大小，并以累计已接受字节数强制总上限。
  - **用户侧步骤**：本方案**不要求用户修改或 reload nginx**；新增的 env 键（可选）写入 `/etc/intelligentbase/ib-web.env` 须重启 `ib-web`，由用户执行（画像 P7）。
- Consequences: 正向——零 nginx 变更、零新依赖；失败隔离与进度展示自然成立。负向——① 并发 2 的上传会占用 2 个 Waitress 线程，与 SSE 问答共享 8 线程容量（M-SA-006）；故前端并发固定为 2，且上传请求体上限独立于问答；② 批次状态引入两张表与过期清理；③ 批次中途关闭页面会留下"未上传"项，汇总里显示为 `pending`，过期后清除（已入库的文件不回滚——"全有全无"只在**上传开始前的校验**阶段成立，与 REQ-FUNC-015/REQ-NFUNC-007 一致）。

### ADR-004: 文件更新的"旧版继续可检索、新版成功后一次性切换"（影子修订行 + 台账事务晋升）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-008、REQ-NFUNC-002（AC-008-02/03）、REQ-NFUNC-001：更新期间旧版继续可检索；新版索引成功后一次性切换，检索不再命中旧内容；新版失败保留旧版并显示"更新失败"；不保留历史版本（C-04）。现状：向量点 id = `point_id_for(doc_id, chunk_index)`（`src/ib/vectorstore/__init__.py:50`），入库步骤 6 是 `delete_by_doc` 再 `upsert`（`src/ib/lifecycle/__init__.py:573-585`）——对**同一 doc_id** 重跑会让旧向量先消失；删除路径是"先向量、再 blob、最后台账行，并做竞态清扫"（`lifecycle/__init__.py:696-717`）；认领是 `claim_pending` 条件 UPDATE（`sqlite_repo.py:484-521`），崩溃由 `reap_expired_leases` 回收（`sqlite_repo.py:532-551`）。
- Options:
  - A. **同 `doc_id` 原地重新入库**（把旧行置 `pending` 换新 blob 再跑流水线）。优：改动最小。缺：步骤 6 `delete_by_doc` 使旧内容立刻消失，新版索引完成前检索不到该文件，且新版失败时旧版已丢——直接违反 AC-008-02/03。
  - B. **影子修订行 + 台账事务晋升（选）**：更新 = 新建一行 `documents`（"修订行"，`revision_of=旧 doc_id`，新 `doc_id`，`name_key=''`，不出现在目录列表，状态 `pending`），原样走既有 `claim_pending → _process_one`；向量以**新 doc_id** 写入（与旧向量共存于同一 collection，互不覆盖）。索引成功后，worker 在**一个台账写事务**内：校验旧行仍存在 → 删除旧行（级联 chunks/chunk_image）→ 把修订行晋升为正式行（继承旧行的 `folder_id`、`uploaded_at`、`created_at`，写 `content_updated_at=now`、`indexed_at=now`、置 `indexed`）→ 把旧 `doc_id` 写入清理队列表。**检索对命中做"台账存活过滤"**（ADR-005）：事务提交前，修订行不存活→其向量命中被丢弃（旧版独占）；提交后，旧行不存在→旧向量命中被丢弃（新版独占）。物理删除旧向量/旧 blob 由清理队列在提交后进行。优：切换点是**单个 SQLite 事务**（真正的原子）；失败路径天然保留旧版；复用全部既有流水线、租约与重试；不需要向量库新能力。缺：`doc_id` 在更新后改变（外部持有旧 `doc_id` 的链接失效，如旧引用图片 URL）；多一张清理队列表；检索多一次台账批量查询。
  - C. **新向量写入"暂存可见性"标记，晋升时 `set_payload` 翻转**。优：可见性在向量库内表达。缺：翻转与删旧是两步向量库操作，**不是原子**，必现"新旧同时可见"或"两者都不可见"的窗口；向量库端口需新增 `set_payload` 能力（违反"端口方法集不随需求改"，M-SA-001）；fail-open 与 fail-closed 难以界定。
- Decision: 选 B（REQ-FUNC-008、REQ-NFUNC-002、REQ-NFUNC-001）。**与现有 lifecycle/租约的配合**：
  1. **认领与租约**：修订行是普通 `pending` 行，`claim_pending` / `renew_lease` / `reap_expired_leases` 一字不改；崩溃回收后重跑是幂等的（`delete_by_doc(新 doc_id)` 再写）。
  2. **晋升事务的守卫**：晋升复用 `_assert_transition(parsing→indexed)`（与 `mark_indexed` 同源，`sqlite_repo.py:449-469`）——若修订行已被回收重认领或已删除，转移非法/行不存在，晋升失败，不产生半状态；旧行不存在（用户在索引期间删除了文件）则晋升被拒绝，worker 走既有 `NotFoundError` 分支清扫新向量（`lifecycle/__init__.py:445-464`）。
  3. **删除**：`delete_document(旧 doc_id)` 先递归删除其修订行（同样的"向量→blob→台账"顺序），再删旧行；删除与晋升的竞态由"台账行存在性"裁决（先提交者胜），败者的向量由既有竞态清扫/`_discard_written_vectors` 处理。
  4. **崩溃安全**：晋升事务提交后、物理清理前崩溃——旧向量/旧 blob 成为"台账无记录"的孤儿，**对读路径不可见**（ADR-005 存活过滤），并由清理队列（`doc_purge_queue`）在下一个 worker 周期重试，直到成功才出队。
  5. **每个旧行至多一个修订行**（`UNIQUE(revision_of)` 部分唯一索引）；新更新到来时，若已有修订行处于 `pending`/`failed` 则丢弃重建；处于 `parsing` 则 409 `update_in_progress`。
  6. **内容未变化**：`sha256` 与旧行相同且旧行 `indexed` 时，直接返回 `changed=false`，不建修订行（AC-008-06）。
  7. **格式变化**：修订行有自己的 `ext`/blob 路径（`blob_ref_for` 由 `(project, kb, doc_id, sha256, ext)` 纯推导，`lifecycle/__init__.py:109-138`），故 pdf→docx 无障碍（AC-008-05）。
- Consequences: 正向——AC-008-01/02/03 全部由"单事务切换 + 存活过滤"成立；无向量库 API 变更。负向——① `doc_id` 随更新改变（`[ASSUMPTION A-06]`：前端更新后整表刷新；旧 `doc_id` 的图片 URL 在更新后 404，属预期，因内容已被替换）；② 更新期间同一 collection 内临时存在两份该文件的向量（存储开销 ×2，至多持续到晋升）；③ 晋升时若新名称被占用，自动 `(n)` 改名（ADR-002）。

### ADR-005: 检索命中以台账为"存活 + 当前名称/路径"的权威
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-001（检索引用的名称/路径与台账当前值一致，已删/被替换内容命中数为 0）、REQ-FUNC-014（引用显示目录路径）、REQ-FUNC-005/012/013（重命名/移动后引用路径同步）。现状：检索命中的 `doc_name` 取自向量 payload（`src/ib/retrieval/__init__.py:178-186`），`RetrievalService` 刻意不依赖台账（类文档 `retrieval/__init__.py:58-66`）；引用项 `CitationItem`（`src/ib/core/types.py:752`）与引用编码（`src/ib/streaming/__init__.py:482-490`）、关联图 `chunk_image.doc_name`（`schema.py:155`）也携带名称快照。
- Options:
  - A. **改写向量 payload**：重命名/移动/文件夹重命名时对受影响文档批量 `set_payload`。优：检索链路不变。缺：需新增向量库端口方法（M-SA-001）；文件夹重命名是 O(文件数) 次跨服务写，**非原子**，失败即出现"名称/路径陈旧但文件可见"；与重建（多 collection 版本）叠加时要对所有版本集合重复；无法解决"被替换的旧向量仍命中"（ADR-004）。
  - B. **检索期台账解析（选）**：`RetrievalService` 新增可选注入的窄端口 `EntryResolver.resolve_live(project_id, doc_ids)`（返回台账中**存活**文档的当前名称与目录路径）；命中按 `doc_id` 去重后**一次**批量查询；不存活的命中被丢弃；名称/路径以台账为准填入 `RetrievedChunk`/`CitationItem`。payload 中的 `doc_name` 降级为"入库时快照，仅供诊断"。重命名/移动因此只改台账，**零向量操作**。优：REQ-NFUNC-001 的"命中数为 0"由台账事务边界保证（含 ADR-004 的原子切换、删除窗口、孤儿向量）；文件夹重命名/移动 O(1)；与重建版本无关。缺：每次检索多一次台账读（`IN (…)` ≤ `top_k×候选倍数` 个 id，主键查询）；台账故障时无法证明存活。
- Decision: 选 B（REQ-NFUNC-001、REQ-FUNC-014）。**降级语义（遵守 M-SA-005）**：解析端口抛异常 → 返回 `degraded=True, degrade_reason=LEDGER_UNAVAILABLE`、命中为空（fail-closed：宁可无引用也不返回未验证存活的内容）；**不新增 `degrade_reason` 枚举值**。**正例判据**（供测试成对验证）：台账可用且命中均存活时 `degraded=False`，每个 `RetrievedChunk.doc_name`/`doc_path` 等于台账当前值；全部命中被过滤时 `degraded=False` 且 `hits==[]`（"空结果"与"依赖故障"取值不同）。`chunk_image.doc_name` 在文件重命名的同一事务内同步更新（台账内部，不涉及向量库）。
- Consequences: 正向——重命名/移动一致性无需跨服务补偿；孤儿向量对读路径不可见。负向——检索多一次台账读 `[ESTIMATE：主键 IN 查询 <5ms]`；`RetrievalService` 构造参数增加一个可选端口（默认 `None` 时行为同基线，利于渐进测试）；payload 快照名称不再被展示，需在文档中说明避免误用。

### ADR-006: 三个时间（上传 / 最近更新 / 索引成功）的语义与数据来源
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-009、REQ-NFUNC-003、REQ-NFUNC-004、AC-009-01~04。现有 `updated_at` 在每次状态流转时被改写（`set_status`/`mark_indexed`/`claim_pending`/`renew_lease` 均 `updated_at=now`，`sqlite_repo.py:427-469,484-531`），不能当"最近更新时间"；`created_at` 同时是认领排序键（`claim_pending` 的 `ORDER BY created_at`，`sqlite_repo.py:497-505`）。
- Options:
  - A. **新增三列**：`uploaded_at`（首次上传登记时间，建行时写入，之后不变）、`content_updated_at`（NULL = 从未更新；晋升修订时写入）、`indexed_at`（NULL = 尚无；每次索引真正成功时写入，含重建重新索引）。优：语义独立、查询简单、重命名/移动不影响；旧数据可确定性回填。缺：3 列迁移。
  - B. **复用 `created_at`/`updated_at`**。缺：`updated_at` 语义不符（见上），违反 AC-009-02（重命名/移动后三时间不变）。
  - C. **事件表**（按事件类型记时间）。优：可追溯历史。缺：为 3 个标量引入一张表与 JOIN，超出需求（C-04 不保留历史）。
- Decision: 选 A（REQ-FUNC-009）。数据来源与规则：
  - `uploaded_at`：`create_document` 写入；修订晋升时**继承旧行**的值；回填 `= created_at`。
  - `content_updated_at`：仅晋升事务写入；普通行为 NULL；"内容未变化"不改。
  - `indexed_at`：在 `mark_indexed` 与 `promote_revision` 的同一 UPDATE 中写入（失败/重试/处理中不写）。**对外只在 `status='indexed'` 时返回**，其余状态返回 `null`（满足 AC-009-03：失败/处理中显示"—"，旧版时间不当作新版时间）。重建重新索引经 `mark_indexed` 自动刷新（AC-009-04、REQ-NFUNC-004），`uploaded_at`/`content_updated_at` 不被 `reset_documents_for_rebuild` 触及（`sqlite_repo.py:787-808` 不涉及这两列）。
  - 回填（既有数据）：`indexed_at = updated_at WHERE status='indexed'`（既有 `indexed` 行的 `updated_at` 即 `mark_indexed` 时刻，之后不再变化；此为最佳近似 `[ASSUMPTION A-07]`）。
  - 时间格式沿用台账 `YYYY-MM-DDTHH:MM:SSZ` UTC 定长（`schema.py:22`）；前端按浏览器本地时区格式化到秒（沿用 `UploadPage.vue:170-177` 的 `fmtDate` 口径）。
- Consequences: 正向——三个时间互不污染；回填无需访问外部系统。负向——`indexed_at` 回填为近似值；`DocumentRecord`（`src/ib/core/types.py:409-428`）新增字段须全部带默认值（尾部追加），避免破坏按位置构造的既有测试。

### ADR-007: 与索引重建（多 collection 版本、activate/rollback）共存
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-004、REQ-NFUNC-001：重建期间或之后，删除/更新/移动/重命名/新增均须保持一致，且更新/新增的文件在激活后不丢失；重建后 `indexed_at` 刷新。现状：重建期间写路径被 `RebuildAwareProjectProvider` 重定向到**目标版本**（`src/ib/rebuild/__init__.py:132-161`），读路径仍读旧 active 版本；`reset_documents_for_rebuild` 把 `indexed`/`failed` 行置回 `pending`（`sqlite_repo.py:787-808`）；`activate_version` 要求无 `failed`、无 `pending/parsing`（`rebuild/__init__.py:356-391`）；删除已跨全部版本集合清理（`delete_doc_everywhere`，`lifecycle/__init__.py:700-701`）。**关键事实**：重建往往因 embedding 模型/维度变更而发起，旧 active 版本的向量只能由旧模型产生，因此**无法双写**（新进程只有新 embedder）。
- Options:
  - A. **重建期间双写 v1+v2**。缺：技术上不可行（见上）。
  - B. **晋升推迟（选）**：修订行索引成功后，仅当其 `indexed_collection_version == 项目当前 active 版本` 时才立即晋升；否则（重建在途，修订行只写进了目标集合）保持"就绪待晋升"（`indexed` 且 `revision_of` 仍非空，旧行继续是存活行，继续被旧 active 版本检索）。**激活成功后**由 `RebuildService.activate_version` 钩子与 worker 每轮扫描共同触发晋升。重建在途时新增/更新的文件，其 API 字段 `searchable=false`（`status='indexed'` 但 `indexed_collection_version != active`），前端显示"已索引，重建切换后可检索"。
  - C. **重建期间禁止更新/新增**。优：最简单。缺：违反"重建期间可用"的需求意图（REQ-NFUNC-004 明确要求共存），且阻塞用户。
- Decision: 选 B（REQ-NFUNC-004）。逐项落实：
  1. 删除：沿用跨版本清理 + 存活过滤（ADR-005），重建期间删除不留可检索残余。
  2. 重命名/移动/文件夹操作：仅改台账，不依赖 collection 版本，天然一致；重建重新索引时 payload 快照由当前台账记录重建（`_payload_for` 取 `record.doc_name`，`lifecycle/__init__.py:819-844`），不影响展示（展示以台账解析为准）。
  3. 新增/更新：写目标集合；激活后可检索；更新的晋升按 B 推迟，保证旧版在 v1 期间持续可检索（NFUNC-002）。
  4. 激活守卫：`failed` 计数**排除**修订行（更新失败不应阻塞重建切换）；`pending/parsing` 计数**包含**修订行（保守，避免切换时遗漏在途修订）。
  5. 重建后 `indexed_at` 刷新、`uploaded_at`/`content_updated_at`/目录结构不变（ADR-006）。
  6. 回滚到旧版本：沿用基线语义——重建后新增/更新的内容不在旧集合中，回滚后不可检索；这是基线既有限制，本增量不改变（`[ASSUMPTION A-08]`，写入风险）。
- Consequences: 正向——无向量库新能力、无双写；一致性规则全部可由台账裁决。负向——重建期间新增文件的"已索引但暂不可检索"状态需要在 API 与 UI 中表达（`searchable` 字段）；晋升逻辑多一个"激活后补晋升"路径，须有测试覆盖（激活→晋升→旧向量清理）。

### ADR-008: 递归删除文件夹（分步、可恢复、逐文件失败隔离）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-006、REQ-NFUNC-001、REQ-NFUNC-007、AC-006-01~04。一个文件夹可含最多数千文件；单文件删除要做 2 次跨版本向量清理 + blob 删除 + 台账删除（`lifecycle/__init__.py:696-717`），向量库不可用时单文件会失败；Waitress 仅 8 线程、`--channel-timeout=120`（`ib-web.service:49-54`）。
- Options:
  - A. **单请求同步删完整棵子树**。优：协议最简。缺：大目录可能超过 120s 通道超时并长期占用线程；中途超时后状态不明。
  - B. **分步删除（选）**：`DELETE /api/library/folders/{id}` 每次处理至多 `N` 个文件（默认 100）且有时间预算（默认 20s），返回 `{done, deleted_files, failed:[…], remaining_files}`；客户端循环调用至 `done=true`。每个文件调用既有 `delete_document`（先修订行后正式行；顺序"向量→blob→台账"不变）；某文件失败则**保留该文件及其所在目录链**，继续处理其他文件；所有文件处理完后，仅删除"已不含文档且已无子目录"的目录（自底向上）。优：无新运行单元；无状态——中断后重发即可续；失败隔离天然；不引入"删除中"状态（失败文件仍可见且可再次删除，AC-006-03）。缺：需要客户端循环；多管理员并发删除同一目录时第二个请求会看到较小的 `remaining`。
  - C. **后台任务（worker 执行）**。优：不占 web 线程。缺：要新增任务载体/状态机，且"幽灵可见"窗口需额外处理；v1 不新增运行单元，复用 worker 轮询要新增任务表，超出本增量。
- Decision: 选 B（REQ-FUNC-006、REQ-NFUNC-007）。文件被并发上传进正在删除的目录时：该目录因含文档而保留，结果报告 `remaining_files>0`（可见、可再次删除，不产生"看不见但可检索"）。`parsing` 中的文件沿用既有"删除后 worker 安全退出"路径（AC-006-04，`lifecycle/__init__.py:445-464`）。
- Consequences: 正向——失败逐项列出，不出现无主文件；中断可恢复。负向——UI 需展示逐步进度；大目录删除耗时随文件数线性。

### ADR-009: 既有平铺数据迁移与老库补列（REQ-FUNC-017）
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-017：上线后既有全部文件显示在根目录，索引状态/检索不变。
- 约束来源与被排除方案：画像 P6——**手写幂等 SQL 新号迁移 `src/deploy/migrations/007_*.sql`，内容与 `src/ib/ledger/schema.py` 生成器逐字一致，已有迁移不改，由 `ib-web` 的 `ExecStartPre … --ensure-schema` 自动应用，写回滚说明**；老库补列沿用 REV-18 先例（`schema.py:340-352,531-551`：`PRAGMA table_info` 探测 + 逐列 `ALTER TABLE ADD COLUMN`，因 SQLite 无 `ADD COLUMN IF NOT EXISTS`）。被排除：① 修改 `001_ledger_init.sql`/`DDL_STATEMENTS`（违反"已有迁移不改"）；② Django ORM/`makemigrations`（画像 P6 禁用）；③ 一次性离线迁移脚本（违反"随 ib-web 重启自动幂等应用"）。
- Decision（REQ-FUNC-017）：新增 `007_folder_tree.sql` ← `schema.py::folder_tree_ddl_script()`；`ensure_schema()` 新增 `_ensure_document_tree_columns`（探测补列，且并发安全：ib-web 与 ib-worker 都会跑 `ensure_schema`，补列包在 `BEGIN IMMEDIATE` 内并容忍 "duplicate column name"）。既有行 `folder_id=''`（根）、`uploaded_at=created_at`、`indexed_at=updated_at（仅 indexed 行）` 由幂等 SQL 回填。`name_key` 的 `casefold` 无法用 SQLite 表达，由 `ensure_schema()` 内的 Python 步骤 `backfill_name_keys` 回填：**先于唯一索引创建**；历史上已存在的同目录（根）重名行，后到者的 `name_key` 追加 `\x1f<doc_id>` 去重——显示名**不变**（满足 AC-017-01"名称与上线前一致"），仅不再参与新冲突判定；用户重命名/移动该行时按正常规则重新校验。
- Consequences: 正向——零停机、零数据重写（仅补列与回填标量）；`ib-web` 重启即完成。负向——① 迁移快照 007 须经 `ensure_schema` 应用才完整（手工 `sqlite3 < 007` 不含 Python 回填，007 头注释写明）；② 回滚（DROP 表/列）需人工（`MANUAL_ROLLBACK_REQUIRED`）；③ 回退代码后，旧代码会把子目录里的文件在平铺列表中全部展示（旧代码忽略新列），且修订行（隐藏行）会作为普通文档出现——回退前须先丢弃进行中的修订行（运维步骤，见 module_design）。

### ADR-010: 不新增运行单元；晋升与清理挂在 `ib-worker` 既有轮询周期
- Status: Proposed
- Type: constraint-driven
- Context: REQ-NFUNC-002/004 需要"晋升已就绪修订"与"排空清理队列"两个周期性动作；C-05 要求单个后台 worker 顺序处理。
- 约束来源与被排除方案：画像 P7（v1 固定四个 systemd 单元，新增单元须回架构评审）、画像 P8（禁多实例 `ib-worker`，双 OOM）、基线 ADR-03。被排除：① 新增专职清理/晋升 systemd 单元；② 多实例 worker 并行；③ 用 Celery/Redis 任务队列（基线 ADR-10 已否决，P8 禁 Redis 用于实时推送且无该基础设施）。
- Decision: 在 `ibweb/worker.py::run_once` 的既有序列（回收租约 → `process_pending` → 重建推进，`worker.py:53-102`）末尾追加两步：`promote_ready_revisions` 与 `drain_purge_queue`，均小批量（默认各 ≤50）、异常不外抛（与 `reap` 同口径）。
- Consequences: 正向——部署形态零变化。负向——清理延迟 ≤ 一个 worker 轮询间隔（默认 5s，`ib-worker.service:46`），期间孤儿向量由 ADR-005 的存活过滤遮蔽。

### ADR-011: 前端落点与交互约束
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-001/002/003/011 的页面交互；用户确认的项目约定：前端功能必须有导航入口（"资料管理"页，路由 `files`，`src/frontend/src/router/index.ts:73-79`）；前端 HTTP 只经 `src/frontend/src/api/client.ts`；禁 axios、CDN（画像 P6/P8）；路由 hash 模式。
- 约束来源与被排除方案：被排除：axios、运行期 CDN/外链字体、新增独立路由入口（保持唯一入口 `UploadPage.vue`）。
- Decision: 在 `UploadPage.vue`（沿用既有导航入口与 `props: { client }` 契约）内重构为"云盘式"视图并拆出子组件（`src/frontend/src/views/library/`）；文件夹选择用原生 `<input type="file" webkitdirectory multiple>` 与 `File.webkitRelativePath`；UI 组件沿用已有 Element Plus；批次上传并发固定 2；浏览分页 `page_size ≤ 100`。同名冲突弹窗、进度条、汇总面板为独立组件。
- Consequences: 正向——无新依赖、无新路由；可复用前端冒烟测试体系（`src/frontend/tests/frontend.smoke.test.js`）。负向——`webkitdirectory` 在非 Chromium/Firefox 之外的浏览器支持有差异 `[ASSUMPTION A-09]`（目标用户浏览器未知；不可用时降级为仅多文件上传）。

### ADR-012: 权限、项目隔离与输入校验沿用现有机制
- Status: Proposed
- Type: constraint-driven
- Context: REQ-NFUNC-005、C-03、基线 REQ-FUNC-IB-48/32。
- 约束来源与被排除方案：基线 `docs/architecture_design.md:120`（范围不可由客户端自证）与 `src/ibweb/views.py:285-290`（`_require_manage`）、`views.py:344-362`（列表仅需已认证主体）、画像 P6（自建 authz、`Authorization: Bearer`、`X-IB-Project`）。被排除：请求体携带 `project_id`/`kb_id`；浏览接口要求管理权限（用户确认 CL-008：浏览不要求）。
- Decision: 所有写端点（建/改名/删/移动目录、上传、更新、文件改名、丢弃修订）= `_require_manage`；浏览端点 = `_ctx_of`（已认证项目成员）；作用域 = `composition.resolve_scope(ctx)`（`composition.py:1868-1874`）。运行期新建项目不在 `cfg.projects`（项目取自注册表，经验 M-SA-018）：本增量**不读取** `cfg.projects`，所有项目维度依据台账 `project_id` 与注册表。"不存在"与"不属于你"（跨项目的目录/文件/批次）统一返回 404（M-SA-007）；无管理权限 403。`kb_id` 恒由 `scope.project_id` 推导。
- Consequences: 正向——不引入新的鉴权面。负向——"跨项目目录 id 访问返回 404 而非 403"与 US-003 AC-003-03 字面"返回 403"不同：AC-003-03 针对"请求属于 P2 的目录"，本设计在**项目由头部/令牌给定**时，对非本项目的 `folder_id` 返回 404（不泄露存在性）；而**归属断言失败**（令牌项目与 `X-IB-Project` 不一致）仍由既有中间件返回 403。该口径差异登记为 `[ASSUMPTION A-10]`，交测试阶段按此口径验证（若 PM/用户要求字面 403，仅需改映射一处）。

## 开放问题 / ASSUMPTION

> 需求侧无开放问题；以下均为设计层假设，不阻塞下游，需 PM 在门控/部署前知悉。

| ID | 假设 / 问题 | 影响 | 建议 |
|---|---|---|---|
| A-01 | `IB_UPLOAD_BATCH_MAX_TOTAL_MB=1024` 为 `[ESTIMATE]`；目标机磁盘余量未知 | 总大小默认值；blob 永久持久化占盘 | 部署阶段按磁盘余量确认并写入 `ib-web.env`（用户执行，需重启 `ib-web`） |
| A-02 | AC-008-07"覆盖"语义：更新文件 X 时新文件名与同目录另一条目 Y 同名，用户选"覆盖"——按 REQ-FUNC-011"同名文件覆盖=按更新处理"，设计为**以该文件更新 Y**（X 不变）；"两者都保留并自动改名"= X 更新且显示名自动改为 `名称 (2).ext`；"跳过/关闭"= 取消 | 前端弹窗文案与调用目标；服务端仅返回冲突信息与支持 `on_conflict=rename` | 需求措辞未明，若用户期望"X 更新且 Y 被删除"，仅改前端调用目标/增加删除步骤 |
| A-03 | 移动时同名冲突：`overwrite` 对文件 = 目标文件被替换删除；对文件夹 = 合并，**嵌套同名文件沿用同一动作**（overwrite→后者覆盖前者）；`skip`/`rename` 同上传语义 | 数据覆盖风险 | 前端弹窗对"文件夹合并并覆盖同名文件"给出二次警示文案 |
| A-04 | 文件重命名**不允许改变扩展名**（返回 400 `ext_change_not_allowed`），因 `blob_ref_for` 由 `ext` 推导落盘路径（`lifecycle/__init__.py:109-138`）；AC-012-02 仅要求"改为不支持类型则拒绝"，本设计更严（改为另一支持类型也拒绝） | REQ-FUNC-012 边界 | 如需允许支持类型间改扩展名，需另立需求（涉及 blob 重命名与重新解析） |
| A-05 | 同目录下文件与文件夹同名（含大小写）也视为冲突 | 范围略大于字面 | 保持，简化心智模型 |
| A-06 | 更新后 `doc_id` 改变；前端更新后整表刷新 | 外部书签、旧图片 URL 失效 | 可接受；若需稳定 id，需引入独立的 entry_id 层（不在本增量） |
| A-07 | 既有 `indexed` 行的 `indexed_at` 回填为 `updated_at`（近似） | 上线首日历史时间可能略偏 | 可接受，在发布说明里注明 |
| A-08 | 重建回滚到旧版本后，重建期间/之后新增或更新的文件在旧集合中不存在（基线限制，本增量不改变） | 回滚场景 | 运维文档提示"回滚后需重新触发重建" |
| A-09 | 目标用户浏览器对 `webkitdirectory` 的支持未知 | 文件夹上传入口可用性 | 不支持时 UI 隐藏文件夹入口，保留多文件上传 |
| A-10 | 跨项目 `folder_id`/`doc_id`/`batch_id` 访问返回 404（不泄露存在性），与 AC-003-03 字面 403 的差异 | 测试口径 | 见 ADR-012；PM 如坚持字面 403，仅改映射 |
| A-11 | 批次文件级校验：深度检查仅统计"至少含一个未被类型/大小/空文件规则跳过的文件"的目录（与"不创建空/全跳过子文件夹"一致） | AC-015-02 边界 | 魔数校验失败发生在上传时，可使实际深度更小，不会更大，故保守 |
| A-12 | 每个 Waitress 线程同时处理上传/问答；批量上传并发 2 与 SSE 共享 8 线程 | 问答在批量上传期间的容量 | 前端并发固定 2；容量实测列入 TBD（沿用基线 §9 的 TBD 机制），不用开发机数据代替目标机 |
