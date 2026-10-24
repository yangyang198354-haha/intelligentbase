<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-10-24T23:25:21+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements_spec.md</file>
    <file>user_stories.md</file>
    <file>architecture_design.md</file>
    <file>module_design.md</file>
    <file>implementation_plan.md</file>
    <file>code_review_report.md</file>
    <file>phase_status.md</file>
    <file>implementation_plan.md（2.0.0）</file>
    <file>code_review_report.md（2.0.0）</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：资料管理——文件夹上传与云盘式目录管理（INCREMENTAL，intelligentbase-GROUP_D-001）

## 测试策略

- **被测改动**：MOD-001~015（目录树 / 批次上传 / 影子修订更新 / 检索存活过滤 / 分步删除 / 重建共存 / 007 迁移 / 新配置键 / HTTP 接口 / 前端目录式界面）。
- **范围（in）**：user_stories 4.0.0 全部 17 个故事 / 58 条 AC；GR-C-001 下发的三条 condition（同步 4 处过时断言；真实 Django 下覆盖 CR-001、CR-002；覆盖偏差 D-03、D-04、D-06）；Must Have 故事（US-001~011、015、017）每个至少 1 个真实执行的 E2E 用例。
- **范围（out）**：真实 Qdrant / DeepSeek / ib-embed / 外网（画像 P6 离线纪律）；浏览器内真实渲染与 `webkitdirectory` 选择交互（项目无浏览器 E2E 框架，仅做源码结构断言）；目标机 SQLite 版本、目标机磁盘与性能 P95（REQ-NFUNC-006 的目标机实测，属部署阶段 TBD）。
- **环境**：解释器 `/root/.venvs/intelligentbase/bin/python`（pytest 9.1.1 / pytest-cov / Django 6.0.9，未安装任何新包）；环境变量 `PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`；台账为内存替身，**需要真实 SQLite 的用例**使用 pytest `tmp_path` 下的临时库（`offline_mode=False` + 测试占位账户环境，用例内断言 `isinstance(ledger, SqliteLedgerRepository)`）；向量库 / 嵌入 / LLM 为内存 / fake 替身；前端 Node 内置 `node:test`。
- **分层**（画像 P3/P4，按目录）：unit = `tests/unit/`（单模块，外部依赖替身；含内存 / SQLite 参数化的存储端口一致性）；integration = `tests/integration/`（真实 Django 中间件 / 路由 / multipart 解析 / 真实认证头，或 lifecycle ↔ rebuild ↔ tree ↔ 向量库跨模块）；e2e = `tests/e2e/`（多步用户旅程，Django 测试客户端 + 真实上传 / worker 处理 / 检索管线）。新文件基名均带 `folder_` 前缀与 `_r25` 后缀（全局唯一，tests 目录无 `__init__.py`）。公共助手 `tests/folder_r25_support.py`（非用例文件）。
- **判定模式**：INCREMENTAL → `gate_mode=baseline`（零新增失败且新写用例全部通过才进入下一层）；critical path 通过率须 1.00。
- **基线来源**：PM 2026-10-24 在 HEAD 65490cf 独立 worktree 实测：`pytest tests` 436 passed；selfcheck 51/52（唯一失败 `core_framework_free`，sitecustomize，环境所致）；前端冒烟 40/40（画像记录）。改动后工作区 PM 复跑：3 failed / 433 passed；前端 39/40；selfcheck 53/54。
- **critical path 口径**：替代（无浏览器 E2E 框架；用 Django 测试客户端 + 真实认证头 + 真实 worker 处理 + 真实检索的多步 API 旅程）。
- **fail-open / 降级成对纪律**：检索存活过滤的"依赖齐备 → 不降级且有命中 / 全部不存活 → 不降级且 hits==[]"与"解析故障 → LEDGER_UNAVAILABLE"成对（TC-UNIT-R25-080/081/082）；worker 周期动作"永不抛"契约配有覆盖失败分支的用例并与正例成对（TC-UNIT-R25-110/111）；清理队列故障保留 + attempts+1 与恢复出队成对（TC-UNIT-R25-095）；更新失败保留旧版与重试成功成对（TC-UNIT-R25-071、TC-E2E-R25-009）；分步删除部分失败与恢复成对（TC-UNIT-R25-091、TC-E2E-R25-007）。
- **缺陷冻结纪律**：DEF-R25-001 在 0.1.0 以"当前错误行为 + 守卫串"冻结；修复后已于 0.2.0 翻转为正向断言（见下节"缺陷回流复测"）。

### GR-C-001 条件落实

| 条件 | 落实 | 证据位置 |
|---|---|---|
| 1. 同步 4 处过时断言 | 3 处 Python 键集 / 字典断言加 `doc_path`（并补成对值断言）；前端 REV-18 子用例改为断言目录式上传入口 | 见 unit / integration 报告"过时断言同步"表 |
| 2a. CR-001 | 真实 Django：批次 PUT 的 `MultiPartParser` 手动解析（内存分支 + >2.5MB 临时文件分支 + 非 multipart / 缺字段 / 幂等 / 魔数 / 503）；更新端点 `request.POST` 的 `on_conflict`（缺省 / fail / rename / 非法值） | TC-INT-R25-001~005 |
| 2b. CR-002 | `POST /api/files` 根目录同名（含大小写变体）→ 409；`create_document` 同名抛冲突；子目录同名不冲突（成对） | TC-INT-R25-010/011 |
| 3a. D-03 | `list_documents(include_revisions)` 三种口径 + 端口 / SQLite / 内存签名一致 | TC-UNIT-R25-031/032 |
| 3b. D-04 | 四个新配置键越界 / 非整数 → `ConfigError`（带键名、不回显值），边界值合法，`build_deps` 启动期 fail-fast | TC-UNIT-R25-101/102 |
| 3c. D-06 | 移动冲突选"覆盖"：文件替换（被覆盖文件移出台账、向量清理、检索 0 命中）、文件夹递归合并、跨类互相覆盖 → 400 | TC-UNIT-R25-024/025/026，TC-INT-R25-022 |

## 缺陷回流复测（0.2.0，defect_loops=1）

| 条件 | 落实 | 用例 |
|---|---|---|
| GR-D-001 feedback / GR-C-002：翻转 TC-INT-R25-055 | 去 GUARD；修订行写 v2、revision_of 指存活行、晋升推迟；激活后 new_hits 非空、old_hits==[]、searchable True、仅一条记录；内存 / SQLite 参数化 | TC-INT-R25-055 |
| 成对：窗口内普通新上传激活后可检索 | 命中 > 0（基线既有缺陷随修复消除） | TC-INT-R25-056 |
| GR-C-002-F01：succeeded 未激活 | 不同目标版本 → ConflictError/409；激活后启动成功；同目标版本幂等 | TC-INT-R25-057/058/059 |
| DEF-R25-002 文案 | 三条限额提示与 AC-015-01/02/04 字面一致 | TC-FE-46 |

回流后各层计数：unit 314、integration 225、e2e 45、agents 21、全量 605；前端 46；selfcheck 53/54（基线环境项）。AC 映射表中 AC-008-02 / AC-010-01 / AC-015-01/02/04 追加上述用例。

## AC 映射

级别：U=unit，I=integration，E=e2e，FE=前端冒烟（源码结构）。"现有/新写"：新写 = 本次新增；现有 = 本次沿用既有用例（无）。位置缩写：`U-tree`=tests/unit/test_folder_tree_store_unit_r25.py，`U-plan`=…_upload_plan_unit_r25.py，`U-life`=…_lifecycle_revision_unit_r25.py，`U-names`=…_names_unit_r25.py，`U-schema`=…_schema_migration_unit_r25.py，`U-cfg`=…_config_batch_worker_unit_r25.py，`I-http`=tests/integration/test_folder_http_api_int_r25.py，`I-reb`=…_rebuild_coexist_int_r25.py，`E-j`=tests/e2e/test_folder_e2e_journeys_r25.py，`FE`=src/frontend/tests/frontend.smoke.test.js。前置 / 动作 / 预期的完整 G/W/T 见各用例 docstring（逐条引用 AC 编号），下表给出摘要。

| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|
| AC-001-01 | TC-UNIT-R25-056；TC-E2E-R25-001 | U；E | 新写 | U-plan；E-j | 目标目录；A/x.txt、A/B/y.md | 计划 → 批次 → 逐文件上传 | A 下有 x.txt 与子文件夹 B，B 内 y.md；层级与本地一致 | 内联文本 |
| AC-001-02 | TC-UNIT-R25-054/055；TC-E2E-R25-001 | U；E | 新写 | U-plan；E-j | 含 bad.exe | 上传 | 合规入库，bad.exe 不入库并列入跳过，目录结构无 bad.exe | 内联 |
| AC-001-03 | TC-INT-R25-040 | I | 新写 | I-http | 非管理者（策略 can_manage=False） | 全部写端点 | 全部 403；无目录 / 文件产生；已有文件内容 / 状态 / 向量不变 | 内联 |
| AC-001-04 | TC-UNIT-R25-057；TC-E2E-R25-001 | U；E | 新写 | U-plan；E-j | A/x.txt、A/onlybad/z.exe、A/fake/q.pdf（魔数不符） | 上传 | 只创建 A（含 x.txt），A 下子文件夹 0；z.exe 列入跳过 | 内联 |
| AC-002-01 | TC-E2E-R25-002；TC-FE-42 | E；FE | 新写 | E-j；FE | 100 个文件 | 逐个 PUT 并查汇总 | 已处理数单调不减，结束 =100；进度条与"已处理 N / 总数"文案存在 | 内联 |
| AC-002-02 | TC-UNIT-R25-054/055；TC-E2E-R25-001/002 | U；E | 新写 | U-plan；E-j | 95 合规 + 3 不支持 + 1 空 + 1 超 50MB；魔数不符 | 计划 / 受理 | 成功 95 / 跳过 5 / 失败 0（和 100）；原因 UNSUPPORTED_TYPE / EMPTY_FILE / TOO_LARGE；魔数不符计跳过 MAGIC_MISMATCH | 内联 |
| AC-002-03 | TC-UNIT-R25-058；TC-INT-R25-004 | U；I | 新写 | U-plan；I-http | blob 不可用（注入） | 受理其中一项 | 该项 failed 并上抛 503，其余不受影响；同 idx 重试成功；汇总三数和 = 总数 | 注入故障 |
| AC-003-01 | TC-UNIT-R25-015；TC-INT-R25-020；TC-E2E-R25-003；TC-INT-R25-040 | U；I；E | 新写 | U-tree；I-http；E-j | A/B 两层 + 成员（不要求管理权限） | 逐级浏览 | 面包屑 [A]、[A,B]；点击面包屑回到 A；浏览在无管理权限下 200 且 can_manage=false | 内联 |
| AC-003-02 | TC-UNIT-R25-014；TC-E2E-R25-003 | U；E | 新写 | U-tree；E-j | 150 个条目 | 翻页 | 每页 ≤100，无重复无遗漏；文件夹在前再按名称升序；刷新一致 | 程序生成 |
| AC-003-03 | TC-UNIT-R25-016；TC-INT-R25-041；TC-E2E-R25-004 | U；I；E | 新写 | U-tree；I-http；E-j | P2 有目录 X；P1 成员（真实账户令牌） | 按目录 id 访问 / 声明他项目头 | 404 且与不存在的 id 响应逐字相同、不泄露名称；归属断言失败 403 project_mismatch；P2 数据完好 | 真实账户 |
| AC-004-01 | TC-UNIT-R25-010；TC-E2E-R25-005 | U；E | 新写 | U-tree；E-j | 目录 D | 新建 `设计` | 立即出现且为空，刷新仍在 | 内联 |
| AC-004-02 | TC-UNIT-R25-011；TC-INT-R25-021；TC-E2E-R25-005 | U；I；E | 新写 | U-tree；I-http；E-j | D 下已有 `设计` | 再建同名 | 409 name_conflict，仅一个 | 内联 |
| AC-004-03 | TC-UNIT-R25-012；TC-INT-R25-021 | U；I | 新写 | U-tree；I-http | 第 10 层目录 | 在其中新建 | 400 depth_exceeded | 程序生成 |
| AC-005-01 | TC-UNIT-R25-017；TC-E2E-R25-005 | U；E | 新写 | U-tree；E-j | 文件夹内 3 个已索引文件 | 重命名 | 3 个文件仍在、仍 indexed；引用路径 `新名/…`，不再有旧名 | 内联 |
| AC-005-02 | TC-UNIT-R25-011；TC-INT-R25-021；TC-E2E-R25-005 | U；I；E | 新写 | U-tree；I-http；E-j | 同级已有 `新名` | 重命名另一文件夹为同名 | 409，原名不变 | 内联 |
| AC-005-03 | TC-INT-R25-040 | I | 新写 | I-http | 非管理者 | PATCH 文件夹 | 403，名称不变 | 内联 |
| AC-006-01 | TC-UNIT-R25-030/090；TC-INT-R25-021；TC-E2E-R25-006 | U；I；E | 新写 | U-tree；U-life；I-http；E-j | A 含 2 子文件夹、10 文件 | 查详情 / 缺 confirm 的删除 | 详情"2 个子文件夹、10 个文件"；缺 confirm → 400 confirm_required；取消（不调用）后内容不变 | 程序生成 |
| AC-006-02 | TC-UNIT-R25-090；TC-E2E-R25-006 | U；E | 新写 | U-life；E-j | 同上 | 确认并分步删除 | 目录与文件消失，向量数 0，任一独有关键词命中该文件 0 条；其它文件不受影响 | 内联 |
| AC-006-03 | TC-UNIT-R25-091；TC-E2E-R25-007 | U；E | 新写 | U-life；E-j | 1 个文件向量清理失败（注入） | 删除 | failed 列出（稳定码、无异常文本）；该文件及目录链仍可见；恢复后 done=true、命中 0 | 注入故障 |
| AC-006-04 | TC-UNIT-R25-093；TC-E2E-R25-007 | U；E | 新写 | U-life；E-j | 文件处于 parsing | 删除后 worker 继续 | 删除成功；worker 收到受控"并发删除"信号，不写回向量 | 内联 |
| AC-007-01 | TC-UNIT-R25-067；TC-E2E-R25-008 | U；E | 新写 | U-plan；E-j | 目录 D | 选 3 个合规文件上传 | D 下出现 3 个，初始 pending → indexed；根目录无 | 内联 |
| AC-007-02 | TC-UNIT-R25-068；TC-E2E-R25-008；TC-FE-42 | U；E；FE | 新写 | U-plan；E-j；FE | 含 1 个不支持类型 | 上传 | 其余入库；不支持者 UNSUPPORTED_TYPE 不入库；未选文件不发起上传（`if (!picked.length) return`） | 内联 |
| AC-008-01 | TC-UNIT-R25-070；TC-E2E-R25-009 | U；E | 新写 | U-life；E-j | 已索引（K1），更新为 K2 | 更新并 worker 处理 | indexed；K2 命中、K1 命中 0；仅一条记录；目录 / 名称不变；最近更新时间非空（见观察项 OBS-1） | 内联 |
| AC-008-02 | TC-UNIT-R25-070；TC-E2E-R25-009；TC-INT-R25-050；TC-INT-R25-055 | U；E；I | 新写 | U-life；E-j；I-reb | 更新已提交、新版未索引 | 检索 K1 / K2 | K1 仍命中、K2 未命中；索引成功后 K1 为 0；重建在途同样成立 | 内联 |
| AC-008-03 | TC-UNIT-R25-071/072；TC-INT-R25-007；TC-E2E-R25-009 | U；I；E | 新写 | U-life；I-http；E-j | 新版索引失败（注入） | worker 处理 | update_failed + 原因码；旧版仍 indexed 且可检索；可重试，成功后切换（成对） | 注入故障 |
| AC-008-04 | TC-INT-R25-040 | I | 新写 | I-http | 非管理者 | POST revision | 403，文件内容 / 状态 / 向量不变，无修订行 | 内联 |
| AC-008-05 | TC-UNIT-R25-073 | U | 新写 | U-life | 规范.txt | 用 规范v2.md 更新 | 被接受；显示新名与新扩展名；目录与上传时间不变；K2 命中、K1 为 0 | 内联 |
| AC-008-06 | TC-UNIT-R25-074；TC-INT-R25-006 | U；I | 新写 | U-life；I-http | 已索引 | 用字节相同文件更新 | changed=false / 200 CONTENT_UNCHANGED；状态、indexed_at、content_updated_at、chunk_count 不变；差一字符则视为变化（成对） | 内联 |
| AC-008-07 | TC-UNIT-R25-075；TC-INT-R25-005；TC-E2E-R25-013 | U；I；E | 新写 | U-life；I-http；E-j | 规范.txt 与 规范v2.md | 用 规范V2.MD 更新规范.txt | 409 + 冲突条目；选前双方不变；覆盖=以冲突条目为更新目标，X 不变，条目数不变；两者保留=`规范V2 (2).MD`；跳过 / 关闭=不调用 | 内联 |
| AC-009-01 | TC-UNIT-R25-076；TC-E2E-R25-010 | U；E | 新写 | U-life；E-j | 受控时钟 | 上传 → 索引 | uploaded_at=T1，indexed_at=T2≥T1，content_updated_at=null；UTC 定长；本地时区显示为源码结构断言（FE-43） | 受控时钟 |
| AC-009-02 | TC-UNIT-R25-076；TC-E2E-R25-010 | U；E | 新写 | U-life；E-j | 同上 | 更新；重命名；移动 | 上传时间仍 T1；最近更新 / 索引成功更新；重命名 / 移动后三个时间不变 | 受控时钟 |
| AC-009-03 | TC-UNIT-R25-077；TC-E2E-R25-010 | U；E | 新写 | U-life；E-j | 失败 / pending / parsing 文件 | 查看列表 | status 与原因码正确，indexed_at=null；重试成功后才出现时间（成对） | 注入故障 |
| AC-009-04 | TC-UNIT-R25-078；TC-INT-R25-054；TC-E2E-R25-010 | U；I；E | 新写 | U-life；I-reb；E-j | 受控时钟，重建 | 重建重新索引 | indexed_at=T5≠T2；uploaded_at、content_updated_at 不变；状态 indexed；位置不变 | 受控时钟 |
| AC-010-01 | TC-E2E-R25-001/011；TC-INT-R25-056 | E | 新写 | E-j | 文件夹 / 目录内 / 旧入口 / 更新后的文件 | 检索独有内容 | 命中含该文件、chunk_count>0、引用路径正确 | 内联 |
| AC-010-02 | TC-E2E-R25-004 | E | 新写 | E-j | P1、P2 | P1 检索 P2 独有内容 | 无命中；P2 自身可命中（成对） | 内联 |
| AC-010-03 | TC-UNIT-R25-084；TC-E2E-R25-011 | U；E | 新写 | U-life；E-j | 索引失败的文件 | 检索 | 无命中；列表状态 failed；同批正常文件可检索（成对） | 注入故障 |
| AC-011-01 | TC-UNIT-R25-061；TC-INT-R25-030；TC-E2E-R25-012；TC-FE-41 | U；I；E；FE | 新写 | U-plan；I-http；E-j；FE | D 已有 a.txt | 再传 a.txt | 列出冲突，选择前原文件内容 / 状态 / 向量不变；未决提交 409；弹窗三选项源码断言 | 内联 |
| AC-011-02 | TC-UNIT-R25-062/063；TC-E2E-R25-012 | U；E | 新写 | U-plan；E-j | 同上 | 覆盖 / 跳过 / 两者保留 | 覆盖=update；跳过=USER_SKIPPED；保留=`a (2).txt`，顺延 `a (3).txt`；覆盖后旧向量移除、仅一个 a.txt | 内联 |
| AC-011-03 | TC-UNIT-R25-065/066；TC-E2E-R25-013 | U；E | 新写 | U-plan；E-j | 目标已有文件夹 A（x.txt、other.txt） | 上传文件夹 A，选覆盖 | 合并为一个 A；x.txt 单独确认并按更新；other.txt 不变；文件夹保留 / 跳过分支 | 内联 |
| AC-011-04 | TC-UNIT-R25-061；TC-E2E-R25-012；TC-FE-41 | U；E；FE | 新写 | U-plan；E-j；FE | 对话框已弹出 | 关闭（不提交） | 资料库无任何变化；弹窗三个出口只发 cancel | 内联 |
| AC-011-05 | TC-UNIT-R25-064；TC-E2E-R25-012 | U；E | 新写 | U-plan；E-j | D 已有 A2.txt / A.txt | 上传 a2.txt / a.txt | 同样触发冲突；保留=`a (2).txt` / `a2 (2).txt`，原文件不变；选前不出现 | 内联 |
| AC-012-01 | TC-UNIT-R25-018；TC-INT-R25-023 | U；I | 新写 | U-tree；I-http | 已索引 `旧.txt` | 重命名 | 状态与三时间不变；引用显示新名 | 内联 |
| AC-012-02 | TC-UNIT-R25-018；TC-INT-R25-023 | U；I | 新写 | U-tree；I-http | 同目录已有 `新.txt` | 重名 / 改扩展名 | 409；扩展名任何变化（含改为另一受支持类型）400 ext_change_not_allowed，名称不变 | 内联 |
| AC-013-01 | TC-UNIT-R25-020；TC-E2E-R25-014 | U；E | 新写 | U-tree；E-j | x.txt 在 A | 移到 B | A 无、B 有且 indexed；命中数不变；引用路径 `B/x.txt` | 内联 |
| AC-013-02 | TC-UNIT-R25-020；TC-E2E-R25-014 | U；E | 新写 | U-tree；E-j | 文件夹含 5 个文件 | 整体移到 C | 整体出现在 C 下、原位置无；检索不变 | 内联 |
| AC-013-03 | TC-UNIT-R25-022/023/024/025/026；TC-INT-R25-022 | U；I | 新写 | U-tree；I-http | 目标有同名 | 移动 | 未选 → 409 + conflicts，台账不变（全有全无）；skip / rename / overwrite（D-06）语义正确 | 内联 |
| AC-013-04 | TC-UNIT-R25-021/021b；TC-INT-R25-022；TC-E2E-R25-014 | U；I；E | 新写 | U-tree；I-http；E-j | 自身 / 子孙 / 超层级 / 他项目目标 | 移动 | move_into_self / depth_exceeded / 他项目目标 404；原结构不变（见观察项 OBS-2） | 程序生成 |
| AC-014-01 | TC-UNIT-R25-080；TC-E2E-R25-001；TC-INT-044（既有，已同步） | U；E | 新写 | U-life；E-j | `技术文档/设计/方案` | 检索引用 | 引用显示含目录路径与文件名 | 内联 |
| AC-014-02 | TC-UNIT-R25-006/080/017/020 | U | 新写 | U-names；U-life；U-tree | 根目录文件；移动 / 重命名后 | 引用 | 根目录文件仅显示文件名（无空前缀）；移动 / 重命名后显示新路径 | 内联 |
| AC-015-01 | TC-UNIT-R25-050；TC-INT-R25-030；TC-E2E-R25-015；TC-FE-42；TC-FE-46 | U；I；E；FE | 新写 | U-plan；I-http；E-j；FE | 1001 个文件 | 提交 | 400 limit_files {limit:1000, actual:1001}；无批次 / 目录 / 文件；恰 1000 个通过（见 DEF-R25-002 文案） | 程序生成 |
| AC-015-02 | TC-UNIT-R25-051；TC-INT-R25-030；TC-E2E-R25-015 | U；I；E | 新写 | U-plan；I-http；E-j | 目标第 8 层 + 3 层嵌套 | 提交 | 400 depth_exceeded（actual 11）；第 7 层通过；无半成品 | 程序生成 |
| AC-015-03 | TC-UNIT-R25-052；TC-UNIT-R25-100 | U | 新写 | U-plan；U-cfg | 配置 20 层 / 2000 个 | 1500 文件 / 15 层 | 通过校验；单文件 50MB 上限仍适用 | 配置注入 |
| AC-015-04 | TC-UNIT-R25-053；TC-E2E-R25-015 | U；E | 新写 | U-plan；E-j | L=1MB（配置） | 超 L / 恰为 L | 超：400 limit_total_bytes {limit, actual}，无任何产物；恰为 L 通过 | 配置注入 |
| AC-016-01 | TC-UNIT-R25-001/013；TC-INT-R25-021 | U；I | 新写 | U-names；U-tree；I-http | — | 空白 / `/` `\` / >255 | 拒绝并给出稳定码 name_empty / name_illegal_char / name_too_long，不创建 | 参数化 |
| AC-016-02 | TC-UNIT-R25-002/013 | U | 新写 | U-names；U-tree | — | 合法名 `2026 规范 v2`；非法名 | 合法成功；非法拒绝且原名保持 | 参数化 |
| AC-016-03 | TC-UNIT-R25-003/011；TC-INT-R25-021 | U；I | 新写 | U-names；U-tree；I-http | D 下已有 `Design` | 新建 `design` / 重命名为 `DESIGN` | 均 409，数量与原名不变；name_key NFC+casefold | 内联 |
| AC-017-01 | TC-UNIT-R25-042/043；TC-E2E-R25-016 | U；E | 新写 | U-schema；E-j | 001 形态老库（真实 SQLite）N=5/M=3，含大小写历史重名 | `ensure_schema` ×2 → 浏览 / 检索 | 根目录列全部 5 个，3 个 indexed，名称 / 大小 / 上传时间与升级前一致；独有内容仍可检索；重复升级结果不变 | 老库构造 |
| AC-017-02 | TC-E2E-R25-016 | E | 新写 | E-j | 升级后的既有文件 | 移动 / 改名 / 更新 / 删除 | 移动后仍命中；改名、更新、删除行为与新文件一致 | 老库构造 |

**非 AC 溯源的专项用例（对应设计偏差 / 门控条件 / NFUNC，写明溯源）**

| 关注点 | 用例 ID | 溯源 |
|---|---|---|
| 007 迁移单源 / 幂等 / 唯一索引 | TC-UNIT-R25-040/041/043/044/045 | 画像 P6；ADR-009；REQ-NFUNC-001 |
| 目录树内存 / SQLite 端口一致 | TC-UNIT-R25-010~032（参数化 `[memory]`/`[sqlite]`） | M-SA-001；MOD-002 |
| 检索存活过滤成对（正例 / 空结果 / 故障 / 无解析器基线） | TC-UNIT-R25-080~083 | ADR-005；MOD-005 |
| 清理队列故障 / 孤儿向量不可见 | TC-UNIT-R25-095；TC-INT-R25-050/051 | ADR-004/010；D-05 |
| worker 周期动作（正例 / 非致命失败 / 项目集合） | TC-UNIT-R25-110/111/112 | MOD-011；M-SA-018 |
| 批次存储（恒等 / 终态幂等 / 项目隔离 / TTL） | TC-UNIT-R25-105/106 | MOD-003 |
| 配置键 D-04、max_upload_mb 告警 | TC-UNIT-R25-100~104 | MOD-009；ADR-003 |
| 重建共存（推迟晋升 / 补晋升 / 失败修订不阻塞切换 / 删改并发） | TC-INT-R25-050~054 | ADR-007；REQ-NFUNC-004 |
| DEF-R25-001 回归（已翻转，两后端）及成对 / 行为变更用例 | TC-INT-R25-055~059 | REQ-NFUNC-004；AC-008-02；GR-C-002-F01/F02 |
| DEF-R25-002 文案断言 | TC-FE-46 | AC-015-01/02/04 |
| HTTP 契约 / 参数校验 / 状态码 / 鉴权 | TC-INT-R25-003/006/020~023/030/040~042 | IFC-001~013；REQ-NFUNC-005 |
| 前端结构契约（冲突弹窗 / 并发 2 / 三时间 / 删除对话框 / 客户端方法） | TC-FE-41~45；#32（已同步） | MOD-013/014；A-09 |

## 测试数据需求

- 全部为用例内联或程序生成的占位文本 / 字节（含中文文件名），**无外部数据文件**、无真实凭据。
- 会写入持久存储的数据：仅 SQLite 用例（`tmp_path` 临时库，用例结束随目录清理）；内存替身每用例 fresh 装配（`build_deps(force=True)`），共享状态（全局 deps、monkeypatch 的时钟 / 嵌入器 / 向量删除）在 teardown 由 monkeypatch / fixture 还原。
- 账户类用例使用测试占位口令（沿用 conftest 的 `R13_*` 占位常量及用例内占位串），**非任何生产凭据**。
- 受控时钟：替换各模块已导入的 `utc_now_iso`；批次 `expires_at` 由 `iso_plus_seconds` 用真实墙钟计算，TTL 类用例传显式时间或以真实当前时间为时钟起点。
- `[DATA_REQUIRED]`：无。

## 不可测项

| AC / 范围 | 原因 |
|---|---|
| AC-002-01 的页面实时渲染（N/100 进度条递增）、AC-011-01/04 的弹窗交互、AC-009-01 的"浏览器本地时区"实际换算、AC-007-02 的"按钮"交互、`webkitdirectory` 选择行为（A-09）、并发 2 的真实运行 | `[NOT_TESTABLE: 项目无浏览器端 E2E / 组件挂载框架]`：服务端语义已由 E2E 旅程真实执行，前端仅做源码结构断言（TC-FE-41~45，#32）；该部分不计入用例通过率分母（未计为用例） |
| REQ-NFUNC-006 的 P95（单目录 ≤1000 条目 2s / 建改名 1s）与 A-12 容量 | `[NOT_TESTABLE: 离线开发机数据不能代替目标机实测]`，列为部署阶段 TBD；本轮仅验证分页上限 100 与覆盖索引存在（TC-UNIT-R25-014/041） |
| 目标机 SQLite 版本（递归 CTE ≥3.8.3、部分索引 ≥3.8.0）与磁盘余量（A-01） | `[NOT_TESTABLE: 需目标机]`，交 GROUP_E1 部署计划核实 |
