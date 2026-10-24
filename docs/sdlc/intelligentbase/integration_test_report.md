<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-24T23:25:21+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>user_stories.md</file>
    <file>implementation_plan.md</file>
    <file>code_review_report.md</file>
    <file>module_design.md</file>
    <file>test_plan.md</file>
    <file>phase_status.md</file>
    <file>implementation_plan.md（2.0.0）</file>
    <file>code_review_report.md（2.0.0）</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告：资料管理——文件夹上传与云盘式目录管理（INCREMENTAL，intelligentbase-GROUP_D-001）

## 摘要

- 执行时间：2026-10-24T23:22 起（缺陷回流复测，本层最后一次执行；0.1.0 初测为 22:41）；环境同单元报告。
- 命令：`python -m pytest tests/integration -q`
- 计数行（原文）：`225 passed in 92.00s (0:01:31)`
- **total = pass + fail + skip + blocked + not_testable = 225 = 225 + 0 + 0 + 0 + 0**
- 其中 既有 192（含已同步断言的 TC-INT-044）+ 新写 33 个收集项（TC-INT-R25-001~007、010~012、020~023、030、040~042、050~054 共 23 个编号无参数化 + 055~059 共 5 个编号各按 [memory]/[sqlite] 参数化 = 10 项；23 + 10 = 33；初测 24 项中的 055 由 1 项变为 2 项，另新增 056~059 共 8 项，24 - 1 + 10 = 33，总数 216 + 9 = 225）。
- 通过率 = 225/(225+0+0) = **1.00**；判定模式 baseline（相对基线零新增失败且新写用例全部通过）。
- **本层门控：PASSED**（既有失败 0；新增失败 0；新写 33/33 通过）。TC-INT-R25-055 已由"缺陷冻结（GUARD）"翻转为正向断言并通过（DEF-R25-001 状态：**FIXED-VERIFIED**，见下节）。

## 执行输出

```
$ python -m pytest tests/integration --collect-only -q | grep -cE '::'
225
$ python -m pytest tests/integration -q
........................................................................ [ 32%]
........................................................................ [ 64%]
........................................................................ [ 96%]
.........                                                                [100%]
225 passed in 92.00s (0:01:31)
```

## 缺陷回流复测（defect_loops=1，GR-D-001 feedback / GR-C-002 condition）

文件：`tests/integration/test_folder_rebuild_coexist_int_r25.py`（未新增文件；新增 fixture `xdeps` 参数化 `[memory]`/`[sqlite]`，SQLite 经 `sqlite_deps`，用例内断言台账为 `SqliteLedgerRepository`）。

### 1. TC-INT-R25-055 翻转（去掉 GUARD 冻结）

| | 翻转前（0.1.0，缺陷冻结） | 翻转后（0.2.0，正向断言） |
|---|---|---|
| 用例名 | `…055_DEF_R25_001_update_after_rebuild_succeeded_before_activation_loses_file_from_search` | `…055_DEF_R25_001_update_after_rebuild_succeeded_before_activation_keeps_file_searchable` |
| 后端 | 仅内存 | `[memory]` + `[sqlite]` 参数化（强度提升） |
| 修订行 | `promoted.revision_of is None and indexed_collection_version == "1"`（GUARD：写入 v1 并立即晋升）；`get_doc(live) is None` | `rev.indexed_collection_version == "2"`；`rev.status == "indexed" and rev.revision_of == live.doc_id`（晋升被推迟）；`get_doc(live) is not None`；激活前旧内容仍可检索 |
| 激活后检索 | `old_hits == [] and new_hits == []`（GUARD：新旧均丢失） | `new_hits` 非空；`old_hits == []` |
| 页面 | `view.searchable is False`（台账显示已索引但不可检索） | `len(files)==1 and total==1`；`view.record.doc_name=="窗口.txt"`、`doc_id == 修订行 id`、`revision_of is None`、`status=="indexed"`、`view.searchable is True`；存活旧行 `get_doc is None`；`delete_doc_everywhere(旧 doc_id) == 0`（两版本集合均无残留） |
| 守卫串 | `GUARD:DEF-R25-001` | 无 |

强度：覆盖 REQ-NFUNC-004 / REQ-NFUNC-001 与缺陷原描述的全部要点（写 v2、推迟晋升、激活后新命中/旧 0/searchable/单条记录），未低于原描述。

### 2. 新增成对与行为变更用例

| TC | 溯源 | 描述 | 结果（memory / sqlite） |
|---|---|---|---|
| TC-INT-R25-056 | REQ-NFUNC-004 / AC-010-01；GR-C-002-F02 | 与 055 成对：succeeded 未激活窗口内**普通新上传**文件，写入 v2（`indexed_collection_version=="2"`），激活后检索命中 > 0、`searchable is True`；窗口前文件同样可检索。**注：该窗口内普通新上传激活后丢失属基线（HEAD 65490cf）既有缺陷，随 DEF-R25-001 修复一并消除，并非本轮引入** | PASS / PASS |
| TC-INT-R25-057 | GR-C-002-F01 | succeeded 未激活任务存在时，启动**不同目标版本**（v3）新重建 → `ConflictError`，`error_response` 映射 HTTP 409；任务行仍只有原 v2 任务，v3 任务不存在 | PASS / PASS |
| TC-INT-R25-058 | GR-C-002-F01 | 成对：激活 v2 后 `plan_rebuild` 得 2→3，再启动成功，v3 任务行存在且为 planned/running | PASS / PASS |
| TC-INT-R25-059 | GR-C-002-F01 / IFC-IB-152 §6.2 | 同目标版本（v2）重复启动 → 幂等返回同一 job_id、状态 succeeded，任务行数仍为 1 | PASS / PASS |

说明：HTTP 端点 `POST /api/rebuild` 总是由 `plan_rebuild` 取 active+1，在 succeeded 窗口内只会得到同目标版本（幂等路径），无法经端点构造"不同目标版本"；故 057 在服务层以显式 `RebuildPlan(to_version="3")` 构造，并断言 409 映射（`ibweb.views.error_response`）。

### 3. 缺陷状态

- **DEF-R25-001：FIXED-VERIFIED**（055 正向断言 ×2 后端、056、057~059 全部通过；全量回归无新增失败）。
- 放弃 succeeded 未激活版本改走另一版本须先激活再回滚（GR-C-002-F01 行为变更），已由 057/058 固定。

## 过时断言同步（GR-C-001 条件 1，集成部分）

| 位置 | 改前断言 | 改后断言 |
|---|---|---|
| `tests/integration/test_orchestration_related_images.py:123`（TC-INT-044） | `set(json.loads(body)["images"][0]) == {"image_id","doc_id","doc_name","page_or_section","url_path"}`（精确键集 5 键） | `== {…同 5 键…, "doc_path"}`（精确键集 6 键）；新增：无台账回填的命中 → `doc_path == ""`；携带 `doc_path="技术文档/设计/atlas.txt"` 与 `doc_name` 的命中 → 载荷项与 `related_images_json` 输出均原样带出路径与名称（开发建议的"值取自当前路径"成对用例） |

## GR-C-001 条件 2 / 3 在真实 Django 下的覆盖结果

| 条件 | 用例 | 结果 |
|---|---|---|
| CR-001 批次 PUT 的 multipart 手动解析：小文件（内存上传）分支；> 2.5MB（Django 临时文件上传）分支，落盘字节数 = 上传字节数；声明大小小于实际 → `SIZE_MISMATCH`；重复 PUT 幂等；非 multipart → 400；multipart 缺 file → 400；GET/POST 该路由 → 405；无令牌 401；`?token=` 400；不存在批次 404；非法批次 id 400；越界 idx 404；魔数不符跳过；依赖故障 503 且同 idx 重试成功 | TC-INT-R25-001/002/003/004 | PASS（解析路径无缺陷） |
| CR-001 更新端点 `on_conflict` 取自 multipart 表单（`request.POST`）：缺省 / `fail` → 409 name_conflict + `conflicts`；`rename` → 202 + `final_name`=`规范V2 (2).MD`；非法取值 → 400；冲突时双方内容与名称不变 | TC-INT-R25-005 | PASS |
| CR-001 更新端点其它：内容相同 → 200 CONTENT_UNCHANGED；不支持类型 / 空文件 / 魔数不符 → 400（码 = `UploadRejection` 小写）；缺文件字段 400；404；非法 id 400；doc_busy 409；DELETE 丢弃 | TC-INT-R25-006 | PASS |
| CR-002 `POST /api/files` 根目录同名 → 409 name_conflict（含大小写变体 `LEGACY.TXT`）；被拒上传不留台账行；不同名 201（成对）；子目录同名不冲突 | TC-INT-R25-010 | PASS |
| CR-002 `submit_upload`/`create_document` 同名抛 `LibraryConflictError`，不留台账行 | TC-INT-R25-011 | PASS |
| CR-002 兼容端点 `GET /api/files` 不返回修订行（IFC-013） | TC-INT-R25-012 | PASS |

## 分项结果

按集成边界分组：

#### 边界 `ibweb.library_views` ↔ Django（URLconf / 中间件 / MultiPartParser / request.POST / 认证头）↔ `ib.library`（`test_folder_http_api_int_r25.py`，18 项）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-R25-001 | （专项/偏差） | CR-001：`PUT /api/uploads/{b}/items/{i}` 的 multipart 经 MultiPartParser 手动解析 —— 小文件内存分支：200  | PASS | — | — |
| TC-INT-R25-002 | （专项/偏差） | CR-001：> 2.5MB 的文件走 Django 临时文件上传分支 —— PUT 手动解析同样成功，落盘字节数与大小一致；声明大小 < 实际 → SIZE_MISMATCH 跳 | PASS | — | — |
| TC-INT-R25-003 | （专项/偏差） | CR-001：重复 PUT 返回既有终态且不重复入库；非 multipart 的 PUT → 400；multipart 缺 file 字段 → 400；GET/POST 该路由  | PASS | — | — |
| TC-INT-R25-004 | AC-002-02、AC-002-03 | CR-001 / AC-002-02 / AC-002-03：魔数不符 → 200 跳过 MAGIC_MISMATCH；依赖故障（blob 不可用）→ 503 且该项记 faile | PASS | — | — |
| TC-INT-R25-005 | （专项/偏差） | CR-001：`POST /api/files/{id}/revision` 的 `on_conflict` 取自 multipart 表单（request.POST）—— | PASS | — | — |
| TC-INT-R25-006 | AC-008-03、AC-008-06 | AC-008-06 / AC-008-03 / IFC-008~009：内容相同 → 200 CONTENT_UNCHANGED（不重新索引）；不支持类型 / 空文件 / 魔数不符 | PASS | — | — |
| TC-INT-R25-007 | （专项/偏差） | IFC-013：`POST /api/files/{id}/retry` —— 存活行 indexed 且其修订行 failed → 重试的是修订行（修订行回到 pending，存 | PASS | — | — |
| TC-INT-R25-010 | （专项/偏差） | CR-002：旧入口 `POST /api/files`（根目录）同名 → 409 name_conflict（含仅大小写不同的 `LEGACY.TXT`）；首个文件原样保留； | PASS | — | — |
| TC-INT-R25-011 | （专项/偏差） | CR-002（port 层）：`create_document` 对根目录同名抛 LibraryConflictError(name_conflict)，不留台账行；与上传管线的入 | PASS | — | — |
| TC-INT-R25-012 | （专项/偏差） | IFC-013：兼容端点 `GET /api/files` 不返回修订行（总数与条目均不含）。 | PASS | — | — |
| TC-INT-R25-020 | AC-003-01 | IFC-001 / AC-003-01/02：浏览返回 folder/breadcrumb/items/total/page/page_size/permissions；page_ | PASS | — | — |
| TC-INT-R25-021 | AC-004-01、AC-006-01、AC-016-01 | IFC-003~005 / AC-004-01/02/03 / AC-016-01~03 / AC-006-01：新建 201；非法名称 400 + 稳定码；同名（含大小写）409 | PASS | — | — |
| TC-INT-R25-022 | AC-013-01 | IFC-006 / AC-013-01/03/04 / D-06：移动 200；冲突无 resolution → 409 + conflicts[]（含发起方 entry），台账不 | PASS | — | — |
| TC-INT-R25-023 | AC-012-01 | IFC-007 / AC-012-01/02：`PATCH /api/files/{id}` 改名 200（状态与三时间不变）；同目录重名 409；改扩展名（含改为另一受支持类型） | PASS | — | — |
| TC-INT-R25-030 | AC-011-01、AC-015-01、AC-015-02 | IFC-010 / AC-015-01 / AC-015-02 / AC-011-01：超限 → 400 limit_files（error.details 含 limit/act | PASS | — | — |
| TC-INT-R25-040 | AC-001-03、AC-005-03、AC-008-04 | AC-001-03 / AC-005-03 / AC-008-04 / REQ-NFUNC-005：无管理权限的成员对全部写端点（建 / 改名 / 删 / 移动 / 上传计划 /  | PASS | — | — |
| TC-INT-R25-041 | AC-003-03 | AC-003-03 / REQ-NFUNC-005（真实账户体系令牌）：P1 成员以目录 id 访问 P2 的目录 → 404，响应体与访问一个不存在的 id 逐字相同，不泄露 P | PASS | — | — |
| TC-INT-R25-042 | （专项/偏差） | 成对正例：绑定本项目的运维账户（管理角色）可在本项目完成 建目录 → 批次上传 → 浏览，permissions.can_manage=true。 | PASS | — | — |

#### 边界 `ib.lifecycle` ↔ `ib.rebuild` ↔ `ib.ledger.tree` ↔ 向量库 ↔ 检索（`test_folder_rebuild_coexist_int_r25.py`，15 项 = 5 + 5×2）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-R25-050 | AC-008-02 | ADR-007 / REQ-NFUNC-004 / AC-008-02：重建在途时更新文件 —— | PASS | — | — |
| TC-INT-R25-051 | （专项/偏差） | MOD-011 / ADR-007：激活时补晋升失败（best-effort）不影响切换；worker 下一轮 `promote_ready_revisions` 完成晋升（成对： | PASS | — | — |
| TC-INT-R25-052 | （专项/偏差） | MOD-008：失败计数排除修订行 —— 更新失败不挡住版本切换；成对：普通文档失败仍拒绝切换（AC-IB-16-04 基线口径不变）。 | PASS | — | — |
| TC-INT-R25-053 | AC-006-02 | REQ-NFUNC-004 / AC-006-02：重建在途时删除文件 —— 跨版本清理向量，检索命中 0；重命名仅改台账，激活后引用名称为新名；重建不改变目录结构与上传时间。 | PASS | — | — |
| TC-INT-R25-054 | AC-009-04 | AC-009-04：重建重新索引完成于 T5 → 索引成功时间 = T5（不再是 T2），上传时间 T1 与最近更新时间（“—”）不变，状态 indexed，目录位置不变；激活后保 | PASS | — | — |
| TC-INT-R25-055[memory] / [sqlite] | AC-008-02 | 缺陷回归（已翻转）：succeeded 未激活窗口更新文件 → 修订行写 v2、revision_of 指向存活行；激活后 new_hits 非空、old_hits==[]、searchable True、仅一条记录（两后端） | PASS / PASS | — | — |
| TC-INT-R25-056[memory] / [sqlite] | AC-010-01 | 成对：窗口内普通新上传激活后可检索（命中>0） | PASS / PASS | — | — |
| TC-INT-R25-057[memory] / [sqlite] | （专项/GR-C-002-F01） | succeeded 未激活时启动不同目标版本 → ConflictError / 409 | PASS / PASS | — | — |
| TC-INT-R25-058[memory] / [sqlite] | （专项/GR-C-002-F01） | 激活后再启动下一版本 → 成功 | PASS / PASS | — | — |
| TC-INT-R25-059[memory] / [sqlite] | （专项/GR-C-002-F01） | 同目标版本重复启动 → 幂等返回同一任务 | PASS / PASS | — | — |


## 与基线对比（baseline 模式）

| 项 | 基线（HEAD 65490cf） | 本次 | 说明 |
|---|---|---|---|
| tests/integration 通过数 | 192 | 225 | = 192 + 33 新写收集项 |
| 失败 | 0 | 0 | PM 在改动后工作区复跑的 1 处集成失败（TC-INT-044）已按条件 1 同步并通过 |

既有失败：无。新增失败：0。

## 失败汇总（需路由给开发）

本层无失败用例，无待路由缺陷。DEF-R25-001（MAJOR）已 FIXED-VERIFIED；DEF-R25-002（MINOR，前端）见 E2E 报告，已 FIXED-VERIFIED。
