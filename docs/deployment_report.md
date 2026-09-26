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
| 版本 | 1.0.0（初稿） |
| status | **DRAFT**（未门控；B11 重建回滚部分 FAIL，待 PM 裁决） |
| 创建日期 | 2026-09-26 |
| 目标机 | `192.168.31.133`（Ubuntu 26.04 LTS / x86_64 / i7-3770S 4C8T / 11 GiB） |
| 上游输入 | `docs/deployment_plan.md`(1.1.0/R4)、`src/deploy/checklists.txt`(A1–A8 / B1–B14 / C)、`docs/phase_status.md` |
| 凭据纪律 | 本文件**不含任何真实凭据 / 口令 / 令牌**；服务令牌等一律写作「经 EnvironmentFile 注入」 |
| 执行门控 | 本报告记录 **PHASE_11 已实际执行的**部署步骤与真跑结果 |

---

## 1. 执行摘要

PHASE_11（生产部署）已进入 **B11（原文件留存与重建回滚）真跑**。真跑暴露并修复 **3 个生产阻断缺陷**（均提交并部署），
另发现 **4 个未修复缺陷**，其中**重建机制整体断裂**（B11 重建回滚部分 FAIL），
以及一个**删除路径向量孤儿**缺陷。

| 结论 | 状态 |
|------|------|
| 文档上传 → 解析 → 切分 → 嵌入 → 写入 Qdrant 全链路 | ✅ **PASS**（修复 D-1/D-2/D-3 后） |
| 文档删除：blob + 台账行移除 | ✅ **PASS** |
| 文档删除：向量同步删除 | ❌ **FAIL**（D-5：`vectors_deleted=0`，向量孤儿） |
| 重建：触发 → worker 推进 → 目标集合建库 | ❌ **FAIL**（D-4：任务卡死 `pending`，目标集合空） |
| 重建：active 版本原子切换 / 回滚 | ❌ **FAIL**（D-4：无 HTTP 端点，且前提不成立） |

---

## 2. 已修复缺陷（3 个，已提交、已部署、经真跑复验）

三个缺陷均为「**路由/依赖/写入层面**」的生产阻断，修复后一条 `.txt` 测试文档端到端索引成功
（`status=indexed`、`chunk_count=1`、Qdrant `ib_demo_v1` `points_count=1`）。

| # | 缺陷 | 根因 | 修复 | commit |
|---|------|------|------|--------|
| **D-1** | 文档索引失败 `E_BLOB_UNAVAILABLE` | `FsBlobStore.put` 用 `tempfile.mkstemp`（固定 0600）落临时文件后 `os.replace`，最终 blob 文件对共享组不可读；`ib-web`（写）与 `ib-worker`（读）分属不同 systemd 用户，靠共同组 `ib` 共享访问 | 落盘前 `os.chmod(temp_path, 0o664)`，显式对齐台账侧 0664，不依赖部署机 umask | `93ef4e1` |
| **D-2** | `.docx` 上传全部 failed | `python-docx` 缺依赖（`SUPPORTED_EXTS` 含 docx，但 `DocxParser` 无运行时库） | `requirements.txt` 增 `python-docx>=1.1,<2.0` | `1fcaf12` |
| **D-3** | Qdrant 写入 `INVALID_ARGUMENT: Unable to parse UUID: <doc_id>#0` | 向量点 id 用 `f"{doc_id}#{index}"` 任意字符串，Qdrant 点 id 仅接受 UUID 或 uint64 | 改为 `uuid.uuid5(NAMESPACE_OID, f"{doc_id}#{index}")` 确定性哈希（`point_id_for`），`upsert` 与 `_process_one` 两处调用点统一 | `719bf5d` |

> 证据：修复后 `/api/files` 上传 → 轮询 `status: pending → parsing → indexed`；Qdrant `GET /collections/ib_demo_v1` → `points_count=1`。

---

## 3. 未修复缺陷（4 个，B11 重建回滚部分 FAIL 的直接原因）

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

## 4. 遗留清理项（需 PM/用户明确授权后方可执行）

真跑在目标机 `192.168.31.133` 上留下了以下**测试痕迹**（`demo` 项目内），当前**保留未删**（删除状态数据未经用户点名授权）：

| 痕迹 | 位置 | 影响 |
|------|------|------|
| 幽灵向量 1 个 | Qdrant `ib_demo_v1`（点 id = UUID5(`6685ca7069dd42d881e895c362051f96#0`)） | 检索可见但台账无行 |
| 卡死重建任务 | ledger `rebuild_jobs` 行 `6807ed0f6d594e4ebd00634d93c7c2fa`（state=`pending`） | 使 `demo` 项目**持续处于写路径重定向状态**，后续所有删除都会孤儿化向量（D-5 持续触发） |
| 空集合 | Qdrant `ib_demo_v2` | 占位，无害 |

> **卡死任务必须清理**：它不删除，D-5 会在 `demo` 项目持续发生。清理命令（需授权）：
> `DELETE FROM rebuild_jobs WHERE job_id='6807ed0f6d594e4ebd00634d93c7c2fa'`、
> Qdrant `DELETE /collections/ib_demo_v2`、`POST /collections/ib_demo_v1/points/delete`（按上述 UUID5 点 id）。

---

## 5. 未闭合项（与前几轮登记一致）

| 项 | 状态 | 说明 |
|----|------|------|
| **B7** DeepSeek 真跑 | ❌ 阻塞 | `IB_LLM_API_KEY` 未提供，LLM 侧 `AuthenticationError`；须用户提供真实 key 方可闭合（S-1/S-3） |
| **B13** SSE 长连接容量 | ⏸ 延后 | `[TBD-T15]` 复核前按保守 worker 数 + SSE 超时配置 |
| **B14** 日志纪律抽查 | ⏸ 待做 | no-body / no-credential 抽查 |

---

## 6. 结论与建议

1. **上传入库链路已可用**（D-1/D-2/D-3 修复后实测 PASS）。
2. **B11 重建回滚部分 FAIL**：D-4（4a/4b/4c）为设计层缺口而非单点笔误——重建的「文档重置」与「激活/回滚端点」在实现期未交付，`target_collection_version` 字段成死列。建议路由 `software_developer` 以 GROUP_C 增量修复，并经 `test_engineer` 回归 + 独立 verifier 复核（与既有 R3/R4 流程一致）。
3. **D-5 删除向量孤儿** 是数据完整性缺陷，与 D-4 耦合（修复 D-4 后需单独覆盖「重建期间删除文档」场景）。
4. **遗留痕迹清理** 需用户明确授权（见 §4）。

> 本报告未修改任何生产数据（清理动作已被权限系统拦截，留待授权）。
