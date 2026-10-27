<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-24T18:05:41+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>docs/sdlc/intelligentbase/requirements_spec.md</file>
    <file>docs/sdlc/intelligentbase/architecture_design.md</file>
    <file>docs/sdlc/intelligentbase/module_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 资料管理：文件夹上传与云盘式目录管理 — 技术选型（INCREMENTAL）

> 结论：**本增量不新增任何第三方依赖、不升级任何版本、不新增运行单元、不改 nginx/systemd。** 因此未联网查询（协议 §L-7：INCREMENTAL 且不引入新依赖通常不需要联网）；所有版本均来自仓库依赖清单（`文件:行`），不以网页覆盖。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | `>=3.11,<3.14`，CI 用 3.12（画像 P1：`ci.yml:57,150-152`） | 沿用 | 既有栈；新代码用标准库 `unicodedata`（`name_key`）、`sqlite3` | REQ-FUNC-011/016 | 低 |
| Web 框架 | Django + DRF，Waitress（8 线程） | `Django>=5.0,<6.1`（`src/requirements.txt:14`）；`djangorestframework>=3.15,<4.0`（`:15`）；`waitress>=3.0,<4.0`（`:16`）；`--threads=8`（`src/deploy/systemd/ib-web.service:52`） | 沿用 | 新端点沿用函数式视图 + 自有 authz（`_require_manage`/`_ctx_of`），不引入 ORM/contrib.auth（画像 P6） | REQ-NFUNC-005 | 中：批量上传并发 2 与 SSE 共享 8 线程（见技术风险 R-2） |
| 数据存储 | SQLite（WAL，`BEGIN IMMEDIATE` 写事务） | 随系统/Python 标准库；开发机实测 `sqlite3.sqlite_version`=3.45.1（`python3 -c "import sqlite3;print(sqlite3.sqlite_version)"`，2026-10-24）；**目标机版本未知** | 沿用 | 目录树/批次/清理队列与 `documents` 同库同事务；写锁全局串行化是同名唯一性与单事务晋升的基石（ADR-002/004） | REQ-NFUNC-001/002/007 | 低：所需特性（部分索引≥3.8.0、递归 CTE≥3.8.3）门槛远低于开发机版本；部署前核实目标机版本 |
| 迁移机制 | 手写幂等 SQL 迁移 `007_folder_tree.sql` + `ensure_schema` 补列/回填 | 沿用 `001~006`（`src/deploy/migrations/`，已核实存在）；补列模式参照 REV-18（`src/ib/ledger/schema.py:340-352,531-551`） | 沿用（新增号 007） | 画像 P6 硬约定：与 `schema.py` 生成器逐字一致、已有迁移不改、随 `ib-web` 重启自动应用 | REQ-FUNC-017 | 中：含一步 Python 回填（`name_key` 的 casefold 无法用 SQL 表达），见风险 R-4 |
| 向量库 | Qdrant（裸装）+ `qdrant-client` | `qdrant-client>=1.7,<2.0`（`src/requirements.txt:43`） | 沿用，**端口零新增方法** | 存活过滤与影子修订均不要求向量库新能力（ADR-004/005），遵守"端口方法集不随需求改" | REQ-NFUNC-001/002/004 | 低 |
| Embedding | `ib-embed` 独立服务（bge-m3，CPU-only） | 见 `src/requirements-embed.txt`（不入基座清单） | 沿用，不变更 | 修订行走既有入库流水线 | REQ-FUNC-010 | 低（单 worker 排队，批量上传后索引耗时线性增长，C-05） |
| 编排/LLM | LangGraph + `langchain-openai` | `langchain-openai>=0.2,<0.3`（`src/requirements.txt:25`；画像 P8 禁 ≥0.3） | 沿用，不变更 | 与本增量无关；仅检索工具文本行改用 `doc_path` | REQ-FUNC-014 | 低 |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + vue-router（hash） | `vue ^3.4.0`、`element-plus ^2.8.0`、`vue-router ^4.4.0`、`vite ^5.2.0`、`typescript ^5.4.0`（`src/frontend/package.json:18-26`） | 沿用 | 文件夹选择用原生 `<input webkitdirectory>`；HTTP 只经 `client.ts`；无 axios/CDN（画像 P6/P8） | REQ-FUNC-001~003 | 中：`webkitdirectory` 浏览器支持差异（A-09） |
| 进程管理 | systemd：`ib-web` / `ib-worker` / `ib-embed` / `qdrant`（固定四个） | `src/deploy/systemd/*.service`（ADR-03） | 沿用，**不新增单元、不多实例 worker** | 晋升与清理挂在 `ib-worker` 既有轮询周期（ADR-010） | REQ-NFUNC-002/004 | 低 |
| 反向代理 | nginx（非 systemd 自有单元） | `client_max_body_size 64m`（`src/deploy/nginx/intelligentbase.conf.example:96`） | 沿用，**不变更** | 批次逐文件上传（≤50MB）天然低于 64MB；用户无需 reload nginx（ADR-003） | REQ-FUNC-015 / C-02 | 低：`IB_MAX_UPLOAD_MB` 若被调到 >60 会触发 413（配置加载时 WARNING 提示） |
| 测试 | pytest（后端）、Node 20 `node:test`（前端冒烟） | 画像 P3/P4；`tests/unit|integration|e2e`；`src/frontend/tests/frontend.smoke.test.js` | 沿用 | 同一套端口一致性测试跑 Sqlite 与 Memory 两实现（M-SA-001）；新测试基名全局唯一（画像 P3） | 全部 | 低：开发机当前无 pytest（画像 P4），执行类验证可能 BLOCKED |
| CI/CD | GitHub Actions `.github/workflows/ci.yml`（10 阶段） | 画像 P7 | 沿用 | 迁移单源检查如需覆盖 007，由 devops 阶段决定（CI 配置属 devops 写权限） | REQ-FUNC-017 | 低 |
| 部署方式 | 目标机 `git pull` + `sudo -n systemctl restart ib-web/ib-worker`；前端目标机本地 build；禁 scp/rsync | 画像 P7；SKILL.md §5-6 | 沿用 | 新环境键与 nginx 无变更；迁移随 `ib-web` 重启 | — | 低 |
| 新增依赖 | **无** | — | — | 名称规范化用标准库 `unicodedata.normalize` + `str.casefold`；上传分类复用既有 `ib.parsing`；无需新包 | — | 无 |
| 新增配置键 | `IB_UPLOAD_BATCH_MAX_FILES`(1000)、`IB_UPLOAD_BATCH_MAX_TOTAL_MB`(1024 `[ESTIMATE]`)、`IB_LIBRARY_MAX_DEPTH`(10)、`IB_UPLOAD_BATCH_TTL_HOURS`(24) | 默认值见 ADR-003；只在 `ib-web.env` 可选覆盖（`/etc/intelligentbase/ib-web.env`，用户执行，不得回显值） | 新增（非依赖） | 满足 AC-015-03 可配置；`ib-worker` 不需要 | REQ-FUNC-015 | 低 |

## 技术风险

### High
无。

### Medium
- **R-1 重建期间更新/新增的"已索引但暂不可检索"窗口**（ADR-007）：重建在途时写目标集合、读旧 active 集合，新增/更新文件在激活前不可检索；回滚到旧版本后重建期内新增/更新的内容同样不可检索（基线既有限制，A-08）。缓解：API 暴露 `searchable`，UI 明确提示；更新的旧版在激活前保持存活可检索（NFUNC-002 不被破坏）；运维文档注明"回滚后需重新触发重建"；集成测试成对覆盖（激活前/后）。
- **R-2 Waitress 8 线程容量被批量上传与 SSE 共享**（沿用 M-SA-006 的容量约束）：每次上传请求在内存中读完整文件（≤50MB，沿用 `submit_upload` 的 `data.read()`，`src/ib/lifecycle/__init__.py:335-336`），并发 2 → 峰值 ~100MB + 2 个线程。缓解：前端并发固定 2；单文件上限不变；容量上限/问答延迟在目标机实测前标 `[TBD]`（沿用基线 TBD 机制，不以开发机数据代替目标机）。
- **R-3 更新后 `doc_id` 改变**（ADR-004，A-06）：外部持有旧 `doc_id` 的链接/旧图片 URL 失效。缓解：前端更新后整表刷新；旧引用图片 404 属预期（内容已替换）；如后续需要稳定 id，另立需求引入 entry_id 层。
- **R-4 迁移含 Python 回填步骤**（ADR-009）：`name_key` 的 `casefold` 无法用纯 SQL 回填，007 快照不能单独完整应用；且 `ib-web` 与 `ib-worker` 均会调 `ensure_schema`。缓解：补列包 `BEGIN IMMEDIATE` 并容忍 `duplicate column name`；回填只处理 `name_key=''` 行（幂等）；唯一索引放在回填之后；007 头注释写明部署路径是 `ensure_schema`；对旧库副本做"重放两次 + 并发启动"测试（`test_library_schema_migration_007.py`）。
- **R-5 总大小上限默认值依据不足**（A-01）：`1024MB` 为 `[ESTIMATE]`，目标机磁盘余量未知；blob 永久持久化。缓解：可配置；部署阶段按磁盘余量确认；用户编辑 env 后重启 `ib-web`。

### Low
- **R-6 `webkitdirectory` 浏览器差异**（A-09）：缓解：特性检测，不支持则隐藏文件夹入口，保留多文件上传。
- **R-7 清理延迟**（ADR-010）：晋升/覆盖后旧向量与旧 blob 物理清理延迟至多一个 worker 周期（默认 5s）；期间孤儿向量被存活过滤遮蔽，不可检索。缓解：清理队列持久化、可重试、`attempts` 可观测。
- **R-8 台账故障时检索 fail-closed**（ADR-005）：`resolve_live` 故障使问答降级为 `LEDGER_UNAVAILABLE` 空结果。缓解：与基线台账不可用的降级口径一致（该枚举值已存在），不新增降级值；成对正例判据见 module_design。
- **R-9 旧入口兼容**：`POST /api/files` 同名改为 409（此前允许重名）。缓解：这是 REQ-FUNC-011 的直接后果；前端新界面不再使用该入口；契约测试覆盖。
- **R-10 向量库存储开销**：更新期间同一文件新旧两份向量共存至晋升为止（至多 ×2，短时）。缓解：晋升后清理队列回收；失败修订可被丢弃/重试。
