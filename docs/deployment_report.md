<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-DR-001 |
| 标题 | intelligentbase 智能知识库基座 —— 生产部署报告（PHASE_11） |
| 产出代理 | 部署执行人（PHASE_11） |
| 项目 | intelligentbase |
| 阶段 | GROUP_E / **PHASE_11（生产部署）** |
| 版本 | 1.2.0（D-4/D-5 已部署复验通过；新增 D-6 修复 `be3f45a` 已部署复验） |
| status | **已验证**（D-4/D-5 目标机端到端复验通过；D-6 列表接口 500 修复并复验；遗留痕迹已清理） |
| 创建日期 | 2026-09-26 |
| 目标机 | `192.168.31.133`（Ubuntu 26.04 LTS / x86_64 / i7-3770S 4C8T / 11 GiB） |
| 上游输入 | `docs/deployment_plan.md`(1.1.0/R4)、`src/deploy/checklists.txt`(A1–A8 / B1–B14 / C)、`docs/phase_status.md` |
| 凭据纪律 | 本文件**不含任何真实凭据 / 口令 / 令牌**；服务令牌等一律写作「经 EnvironmentFile 注入」 |
| 执行门控 | 本报告记录 **PHASE_11 已实际执行的**部署步骤与真跑结果 |

---

## 1. 执行摘要

PHASE_11（生产部署）已完成 **B11（原文件留存与重建回滚）真跑**。真跑暴露并修复 **3 个生产阻断缺陷**（D-1/D-2/D-3，已部署复验），
另发现 **重建机制断裂 + 删除向量孤儿**（D-4/D-5，本轮代码修复并已部署复验），以及复验过程中新发现的 **列表接口 500 预存缺陷**（D-6，本轮修复并复验）。

**全部缺陷（D-1 至 D-6）现已部署到目标机 `192.168.31.133` 并端到端复验通过**；遗留测试痕迹已清理，`demo` 项目回到干净基线（active=v1、0 文档、0 任务、0 向量）。

| 结论 | 状态 |
|------|------|
| 文档上传 → 解析 → 切分 → 嵌入 → 写入 Qdrant 全链路 | ✅ **PASS**（修复 D-1/D-2/D-3 后，已部署复验） |
| 文档删除：blob + 台账行移除 | ✅ **PASS** |
| 文档删除：向量同步删除 | ✅ **PASS**（D-5，目标机复验 `vectors_deleted=1` 且 v1 点 1→0） |
| 重建：触发 → worker 推进 → 目标集合建库 | ✅ **PASS**（D-4a/b，目标机复验 `state=planned` → worker `indexed=1,pending=0`） |
| 重建：active 版本原子切换 / 回滚 | ✅ **PASS**（D-4c，目标机复验 activate v2 + rollback v1，active 原子切换） |
| 文件列表接口 query 参数解析 | ✅ **PASS**（D-6，目标机复验 `?page_size=100` 由 500 → 200） |

---

## 2. 已修复缺陷（6 个，均已部署复验）

**A 组（D-1/D-2/D-3）**：均为「**路由/依赖/写入层面**」的生产阻断，已提交、已部署、经真跑复验。
修复后一条 `.txt` 测试文档端到端索引成功（`status=indexed`、`chunk_count=1`、Qdrant `ib_demo_v1` `points_count=1`）。

| # | 缺陷 | 根因 | 修复 | commit |
|---|------|------|------|--------|
| **D-1** | 文档索引失败 `E_BLOB_UNAVAILABLE` | `FsBlobStore.put` 用 `tempfile.mkstemp`（固定 0600）落临时文件后 `os.replace`，最终 blob 文件对共享组不可读；`ib-web`（写）与 `ib-worker`（读）分属不同 systemd 用户，靠共同组 `ib` 共享访问 | 落盘前 `os.chmod(temp_path, 0o664)`，显式对齐台账侧 0664，不依赖部署机 umask | `93ef4e1` |
| **D-2** | `.docx` 上传全部 failed | `python-docx` 缺依赖（`SUPPORTED_EXTS` 含 docx，但 `DocxParser` 无运行时库） | `requirements.txt` 增 `python-docx>=1.1,<2.0` | `1fcaf12` |
| **D-3** | Qdrant 写入 `INVALID_ARGUMENT: Unable to parse UUID: <doc_id>#0` | 向量点 id 用 `f"{doc_id}#{index}"` 任意字符串，Qdrant 点 id 仅接受 UUID 或 uint64 | 改为 `uuid.uuid5(NAMESPACE_OID, f"{doc_id}#{index}")` 确定性哈希（`point_id_for`），`upsert` 与 `_process_one` 两处调用点统一 | `719bf5d` |

> 证据：修复后 `/api/files` 上传 → 轮询 `status: pending → parsing → indexed`；Qdrant `GET /collections/ib_demo_v1` → `points_count=1`。

**B 组（D-4/D-5）**：重建机制断裂 + 删除向量孤儿，**提交 `d99f36d`，本地回归 149 passed，已部署目标机并端到端复验通过**（根因明细见 §3，复验证据见 §7）。

| # | 缺陷 | 修复 | commit |
|---|------|------|--------|
| **D-4** | 重建机制整体断裂（4a 状态机失配 / 4b 无文档重置 / 4c 无激活回滚端点） | 状态机 `pending`→`planned`（两处 ledger 实现 + `IN_FLIGHT_REBUILD_STATES`）；`start_rebuild` 触发 `reset_documents_for_rebuild`（`indexed/failed → pending` 并写 `target_collection_version`）；`ibweb/urls.py` 新增 `POST /api/rebuild/activate` 与 `/rollback` 端点 | `d99f36d` |
| **D-5** | 删除路径向量孤儿（在飞重建期间删除只清目标集合，旧集合点成幽灵） | 新增 `delete_doc_everywhere(project_id, scope, doc_id)`（InMemory + Qdrant 双实现），删除跨**全部**版本集合清点；`lifecycle.delete_document` 改走它并移除 `_bind_write_collection` | `d99f36d` |

> 回归：`python -m pytest tests/` → **149 passed**（含新增 `test_TC_INT_072_delete_during_inflight_rebuild_clears_all_versions` 与扩展 `test_TC_E2E_011_rebuild_journey` 至 activate/rollback）。目标机端到端复验证据见 §7。

**C 组（D-6）**：文件列表接口 query 参数解析缺陷，**复验 D-4/D-5 时新发现，提交 `be3f45a`，已部署目标机并复验通过**。

| # | 缺陷 | 根因 | 修复 | commit |
|---|------|------|------|--------|
| **D-6** | `GET /api/files?page_size=N` 返回 500，列表接口任何 query 参数都触发 500 | `src/ibweb/views.py` 用 `dict(request.GET)` 解析 query，Django `QueryDict` 的 `dict()` 返回 **list 值**（`{'page_size': ['20']}`），DRF `IntegerField` 无法解析 list 值而校验失败 | 改为 `request.GET.dict()`，得到标量值（`{'page_size': '20'}`） | `be3f45a` |

> 影响面：D-6 是预存缺陷（与 D-4/D-5 无关），使复验脚本的 `doc_status` 探测（依赖 `GET /api/files?page_size=100`）拿到 500 → 返回 `None` → 两条「doc indexed in v1」断言误判为 FAIL。实际文档已正确索引（Qdrant `points_count=1`、worker `state=succeeded`），复验证据见 §7。

---

## 3. D-4/D-5 根因明细（已修复，保留作修复对照）

### D-4 重建机制整体断裂（三处独立缺陷叠加）

**D-4a 状态机失配：worker 永远不认领新任务**

- `create_rebuild_job`（`src/ib/ledger/sqlite_repo.py:702` 与内存实现 `src/ib/ledger/__init__.py:531`）写入初始状态 `"pending"`；
- worker `run_once`（`src/ibweb/worker.py:77`）只认领 `state in ("planned", "running")`；
- `RebuildState` 枚举（`src/ib/core/enums.py:96`）**根本无 `pending`**（有 `planned`）。
- **后果**：新任务永远停在被 `"pending"`，worker 从不推进。真跑实测：POST `/api/rebuild` 返回 `state=pending`，12s 后 GET 仍 `state=pending`。

**D-4b 无文档重置：`indexed` 文档永不被重新处理**

- `claim_pending`（`sqlite_repo.py:496`）只认领 `status='pending'`；
- 重建启动时**没有任何代码**把已 `indexed` 的文档重置回 `pending`（`indexed → pending` 仅被状态迁移表允许，但无触发点）；
- `target_collection_version` 字段（schema 里存在）**从未被写入非空值**——重建应标记「此文档须重索引到目标版本」的代码缺失。
- **后果**：即使 worker 推进了任务，`process_pending` 也找不到待处理文档；`step_rebuild` 的 `done = failed==0 and pending==0 and indexed>0` 因 v1 遗留的 `indexed` 计数直接误判为「完成」，目标集合空。

**D-4c 无激活/回滚 HTTP 端点**

- `RebuildService.activate_version` / `rollback` 已实现，但 `src/ibweb/urls.py` 仅暴露 `POST /api/rebuild`（plan+start）与 `GET /api/rebuild/<job_id>`（进度）；
- **后果**：即便重建跑通，也**没有任何入口**把 active 版本切到新集合或回滚。

**真跑证据（B11 重建部分）**：
```
POST /api/rebuild            → {"job_id":"6807ed0f...","state":"pending"}
GET  /api/rebuild/<job_id>   → {"state":"pending","indexed":1,"failed":0,"pending":0,"done":true}
Qdrant collections           → ['ib_demo_v1', 'ib_demo_v2']   # v2 被 start_rebuild 建出但从未写入
ib_demo_v1 points_count      → 1
ib_demo_v2 points_count      → 0
ledger rebuild_jobs.state    → 'pending'（从未 running/succeeded）
```
> 注意 `done=true` 是**假阳性**：`indexed=1` 来自 v1 遗留的 `indexed` 文档，`pending=0` 是因为没有文档被重置，两者叠加让 `done` 误判为真，而目标集合 `ib_demo_v2` 实际为空。

### D-5 删除路径向量孤儿（在飞重建期间）

- `delete_document`（`src/ib/lifecycle/__init__.py:701`）先 `_bind_write_collection` 再 `delete_by_doc`；
- `_bind_write_collection` 使用**写路径** `project_provider`（`RebuildAwareProjectProvider`），在存在 `pending`/`running` 重建任务时把 collection 重定向到**目标版本**；
- 文档向量实际在**旧集合**（v1），删除却打向**目标集合**（v2）→ `delete_by_doc` 删 0 个点。
- **后果**：blob 与台账行已删，但 v1 向量成「看不见但检索得到」的**幽灵向量**（代码注释明示这是「最危险的一类残留」）。

**真跑证据（B11 删除部分）**：
```
DELETE /api/files/<doc_id>  → {"vectors_deleted":0,"blob_deleted":true,"ledger_deleted":true}  (HTTP 200)
blob 目录                    → 已删除（dir gone）
ledger documents             → 空（行已删）
ib_demo_v1 points_count      → 1  ← 孤儿向量，未随删除清除
```
> 触发前提是存在在飞重建任务（`RebuildAwareProjectProvider.target_version()` 因 stuck 的 `pending` 任务返回 v2）。但即便重建健康运行中，此缺陷同样会在「重建期间删除文档」时复现——删除应清除**该文档在全部版本集合中的点**，而非仅当前写集合。

---

## 4. 遗留清理项（已执行）

真跑在目标机 `192.168.31.133` 上留下的**测试痕迹**已获用户授权清理，现已执行完毕，`demo` 项目回到干净基线：

| 痕迹 | 处置 | 结果 |
|------|------|------|
| 幽灵向量（D-5 复验上传的 d5.txt / d4.txt 向量） | 通过 `DELETE /api/files/<doc_id>` 走 `delete_doc_everywhere` 清点 | ✅ `vectors_deleted=1`，`ib_demo_v1` `points_count=0` |
| 卡死/在飞重建任务 | ledger `rebuild_jobs` 行清除 | ✅ `rebuild_jobs` 空 |
| 空集合 `ib_demo_v2` | Qdrant `DELETE /collections/ib_demo_v2` | ✅ 已删（404 gone） |
| 测试文档 d4.txt（`e18d268c…`） | `DELETE /api/files/<doc_id>` | ✅ `blob_deleted=true`、`ledger_deleted=true` |

> **清理后基线**：active_collection_version=`1`、documents=`0`、rebuild_jobs=`0`、`ib_demo_v1` `points_count=0`、无 `ib_demo_v2`。
> 本清理同时构成 D-5 的二次旁证：删除走新 `delete_doc_everywhere`，`vectors_deleted=1` 且集合点 1→0。

---

## 5. 未闭合项（与前几轮登记一致）

| 项 | 状态 | 说明 |
|----|------|------|
| **B7** DeepSeek 真跑 | ❌ 阻塞 | `IB_LLM_API_KEY` 未提供，LLM 侧 `AuthenticationError`；须用户提供真实 key 方可闭合（S-1/S-3） |
| **B13** SSE 长连接容量 | ⏸ 延后 | `[TBD-T15]` 复核前按保守 worker 数 + SSE 超时配置 |
| **B14** 日志纪律抽查 | ⏸ 待做 | no-body / no-credential 抽查 |

---

## 6. 结论与建议

1. **上传入库链路已可用**（D-1/D-2/D-3 修复后实测 PASS，已部署）。
2. **D-4（4a/4b/4c）与 D-5 已代码修复并部署复验通过**（commit `d99f36d`）：状态机 `planned` 对齐、`start_rebuild` 触发文档重置并写 `target_collection_version`、新增 activate/rollback 端点、删除跨全版本集合清点。本地回归 **149 passed**，目标机端到端复验 **18 项核心断言 16 PASS**（2 条「FAIL」为 D-6 引起的探测失效误报，非产品缺陷，见 §2 C 组与 §7）。
3. **D-6 已修复并部署复验**（commit `be3f45a`）：列表接口 query 解析改 `request.GET.dict()`，`?page_size=100` 由 500 → 200。
4. **遗留痕迹已清理**（见 §4），`demo` 项目回到干净基线。

---

## 7. 目标机端到端复验记录（D-4/D-5/D-6）

复验在目标机 `192.168.31.133` 上以服务账号 token + API + Qdrant/ledger 直查执行（token 一律服务端读取，不落盘、不打印）。

**复验结论**（`verify_d45.py`，18 项断言）：

```
D5 上传 201 + doc_id ✓            D5 rebuild 202 state=planned ✓
D5 删除 200 vectors_deleted=1 ✓   D5 v1 孤儿清除 points 1→0 ✓
D4 上传 201 ✓                     D4 rebuild 202 state=planned ✓
D4 启动重置 pending>=1 ✓          D4 worker 推进 indexed=1,pending=0 ✓
D4 activate 200 version=2 ✓       D4 rollback 200 version=1 ✓
D4 ledger active==1 after rollback ✓
total=18 passed=16 failed=2
  FAILED: D5 doc indexed in v1 | None
  FAILED: D4 doc indexed in v1 | None
```

> 两条「FAIL」为 D-6 所致：`doc_status` 探测走 `GET /api/files?page_size=100`，D-6 令其 500 → 探测返回 `None`。旁证确认文档实际已索引：Qdrant `ib_demo_v1` `points_count=1`、worker `state=succeeded`。D-6 修复后（`be3f45a`）列表接口复测 200、文档 `status=indexed` 正确返回，上述误报消除。

**部署动作**：目标机 `git pull origin main`（`81feff7..be3f45a` fast-forward）→ `systemctl restart ib-web`（D-6 仅改 web 视图，无需重启 worker/embed）→ 复验 → 清理。

> 至此部署报告中的「已修未验」项全部闭合；无未执行步骤。
