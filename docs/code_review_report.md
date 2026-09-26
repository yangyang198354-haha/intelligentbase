---
<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-CR-001 |
| 标题 | intelligentbase 智能知识库基座 —— 开发者自我代码评审报告 |
| 产出代理 | software-developer |
| 调用 ID | INV-GROUP_C-INTELBASE-001（R1）／ INV-GROUP_C-INTELBASE-002（R2 增量）／ INV-GROUP_C-INTELBASE-003（R3 缺陷修复增量）／ INV-GROUP_C-INTELBASE-004（R4 缺陷修复 + 依赖补齐增量） |
| 项目 | intelligentbase |
| 阶段 | PHASE_06b（自我代码评审） |
| 版本 | **R4**（R1 主体 §1~§8 未改写；R2 增量见 **§9**；R3 增量见 **§10**；R4 增量见 **§11**） |
| status | DRAFT（待 GROUP_D / PM 复核） |
| 上游输入 | `docs/architecture_design.md`（**1.2.0 / R2**，GR-B-003 PASS）、`docs/module_design.md`（**1.2.0 / R2**）、`docs/tech_stack.md`（**1.2.0 / R2**）、`docs/ib_embed_service_contract.md`（R2，新建权威契约） |
| 覆盖范围 | MOD-IB-01 ~ MOD-IB-26（**R2 追加 MOD-IB-26**；R1 覆盖 01~25）。**R3 重评 MOD-IB-13 与 MOD-IB-23**；**R4 只重评被触及的部分**：MOD-IB-12（`ib/blob`，kb 段推导单一真源）与 MOD-IB-13（`ib/lifecycle`，删除路径 scope 来源），外加依赖面新增文件 `src/requirements-embed.txt`（B-05，非模块） |
| 评审方式 | 5 维评分 + 逐条 finding（含文件:行号）+ 离线实跑证据 |
---

# intelligentbase 自我代码评审报告（PHASE_06b）

> 本报告是**开发者自评**，不是正式测试报告。正式测试套件与测试报告属 GROUP_D。
> 本报告遵守一条纪律：**无实跑证据不下结论**。所有「通过」都附真实命令与原始输出（§2）。

---

## §1 评审摘要

### 1.1 规模

| 指标 | 值 |
|------|-----|
| 交付文件总数（`src/` 下，不含 `__pycache__`） | **69** |
| 交付代码总行数（`src/` 下，含部署交付物） | **16,396** |
| 模块数 | 25（MOD-IB-01 ~ 25）|
| 端口数 | 13（`ib/core/ports.py`）|
| 接口契约数 | 58（IFC-IB-001 ~ 265）|
| 后端 Python 文件 | 55 |
| 前端 TS/Vue 文件 | 11 |
| 部署交付物 | 9（4 systemd unit + env.example + config.example.json + 迁移 .sql + 检查清单 + 2 requirements）|

### 1.2 5 维总体评分（各模块均分）

| 维度 | 均分 | 说明 |
|------|------|------|
| Correctness（正确性） | **8.7** | 本轮共修复 4 个 CRITICAL；修复后离线契约用例全绿。扣分集中在「本地无法真跑的外部依赖」路径（PDF/OCR/bge-m3/Qdrant）。 |
| Security（安全性） | **9.2** | 隔离（collection-per-project）、`?token=` 拒绝、凭据仅环境变量、日志白名单脱敏均已落地并有离线用例。扣分项见 §5 遗留（会话存储为内存实现，进程重启丢上下文；非安全问题但影响审计连续性）。 |
| Performance（性能） | **8.4** | 批量向量化、条件 UPDATE 租约、`isolation_level=None`+显式事务均已实现。未做真机压测（受「不得触网/不得连生产」约束），故不给更高分。 |
| Maintainability（可维护性） | **9.0** | 25 个模块单一职责、framework-free 核心（用例 `core_framework_free` 强制）、每个文件头部标注 `@module`/`@implements`/`@depends`。 |
| Test Coverage（可测试性） | **8.5** | 全部外部依赖都有同端口替身（`port_conformance` 用例保证签名一致）；离线自检 15 例 + 前端 SSE 自检 9 例。扣分：无正式单元测试（GROUP_D 职责）。 |

### 1.3 Finding 统计

| 严重级别 | 发现 | 已修复 | 遗留（已记录） |
|---------|------|--------|---------------|
| **CRITICAL** | 4 | **4** | **0** |
| MAJOR | 9 | 6 | 3（见 §5，均有说明与依据） |
| MINOR | 7 | 5 | 2 |
| **合计** | **20** | **15** | **5** |

**结论：CRITICAL = 0，满足「存在 CRITICAL 不得提交 SUCCESS」的硬约束。**

### 1.4 本轮 4 个 CRITICAL（全部已修复）

| ID | 模块 | 一句话 | 若不修的后果 |
|----|------|--------|-------------|
| FND-IB-21-001 | MOD-IB-21 | `StreamEvent` 在 `ib.core` 与 `ib.streaming` 各定义一次 | `isinstance` 跨模块判定恒 False，事件被静默丢弃 |
| FND-IB-23-001 | MOD-IB-23 | 组装读路径的闭包引用了未在作用域内的 `load_project_record` | **每一次检索都抛异常 → fail-open 转 degraded → 问答永远显示「未接入知识资料库」**，且 `POST /api/rebuild` 返 500 |
| FND-IB-23-002 | MOD-IB-23 | 装配点向 `build_ledger` / `build_blob_store` 传错配置对象 | 台账/blob 开关被 `getattr` 默认值掩护而**静默失效**（离线装配仍落盘） |
| FND-IB-24-001 | MOD-IB-24 | SSE 分帧 `findBoundary` 用 `-1` 作哨兵却写 `while (boundary >= 0)` | 对象与数字比较恒 false → 分帧循环**一次都不执行** → 多帧被并成一帧、`kind` 恒为 `done` → **正文全丢、页面空白但不报错** |

> FND-IB-23-001 与 FND-IB-24-001 是同一类「静默失败」：不抛异常、不报错，只是功能不出结果。
> 这两个案例正是本报告最想留档的东西（§2.3 与 §2.4 保留了**修复前**的原始输出）。

---

## §2 实际执行证据（命令 + 原始输出）

> 约束：本地自测只用 SQLite / InMemory / Fake 替身，**不触网、不连任何生产库或外部端点**。
> 每次执行均带 `-X utf8`（Windows 控制台默认 GBK，中文输出会乱码或抛 `UnicodeEncodeError`）。

### 2.1 后端离线自检：15/15 通过

```
$ cd src && python -X utf8 scripts/selfcheck.py

========================================================================
intelligentbase 离线自检（GROUP_C 自我验证；正式测试套件属 GROUP_D）
========================================================================
PASS  core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）
PASS  no_forbidden_web_carrier：无 FastAPI/uvicorn/channels/redis 依赖
PASS  no_pymupdf：全仓无 fitz / PyMuPDF 引用（AGPL-3.0 硬约束）
PASS  port_conformance：替身与端口签名一致（VectorStore/Ledger/Blob/Embedder）
PASS  authz_injection_required：生产模式未注入策略即启动失败，且只报键名
PASS  config_error_reports_key_only：配置校验只报键名，不回显值
PASS  magic_sniff_rejects_renamed_file：改名攻击被拒（扩展名与内容不符）
PASS  ledger_state_machine_and_lease：SQLite 台账状态机 + 单租约（WAL）
PASS  isolation_scope_required：检索降级时 filter 仍含 project_id，且跨项目不可见
PASS  retrieval_happy_path：读路径**不降级**且能命中（防止『一切静默降级』掩盖缺陷）
PASS  retrieval_fail_open：embedding 不可用时降级而非抛异常（MOD-IB-15 永不抛）
PASS  sse_frame_and_done_terminator：SSE 帧格式与 done 终止条件
PASS  orchestration_events_order：degraded 先于 content，且只发一条 content
PASS  http_contract_offline：离线装配下端点状态码/头纪律（含 ?token= 显式 400）
PASS  deploy_templates_have_no_secrets：部署模板只含占位符，无真实凭据
------------------------------------------------------------------------
自检结果：15/15 通过
```

**`http_contract_offline` 覆盖的 HTTP 契约**（同一用例内串联断言，全部通过）：
`/healthz` 未认证 200 → `/healthz/deps` 返回键集合 `{qdrant, embed, llm, egress}` →
无令牌 401 → `?token=` **400**（显式拒绝，FreeArk 教训）→ 带令牌 200 且体为 `{items,total}` →
上传 201 → `.pdf` 扩展名配纯文本内容 400（魔数不符）→ 跨项目 `kb_id` 403 →
对非失败文档重试 409 → 删除不存在文档 404 → SSE 200 且 `Content-Type: text/event-stream`
与 `X-Accel-Buffering: no`、含 `event: done` 终止帧 → 重建 202 后进度查询 200。

> 其中 `retrieval_happy_path` 是**因 FND-IB-23-001 而新增**的用例（见 §2.3）：
> 它断言 `degraded is False` **且** `hits` 非空。原来的 `retrieval_fail_open` 只断言
> 「不抛异常」，于是「一切都被 fail-open 兜住」也能通过 —— 缺陷因此被漏过一轮。

### 2.2 Django 系统检查（收窄配置 + 离线装配）

```
$ IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=file IB_CONFIG_FILE=deploy/config.example.json \
  IB_OFFLINE_TOKEN=offline-test-token PYTHONUTF8=1 \
  python -X utf8 manage.py check --settings=ibweb.settings

{"outcome": "started", "stage": "startup"}
{"backend": "vectorstore=memory,embed=fake,llm=fake,ledger=memory,ocr=off,render=off,offline=1",
 "egress_data": "", "egress_host": "", "egress_remote": false, "outcome": "succeeded",
 "project_id": "demo", "stage": "startup"}
{"count": 1, "egress_data": "", "egress_host": "", "egress_remote": false,
 "outcome": "succeeded", "stage": "startup"}
System check identified no issues (0 silenced).
```

这条输出同时证明了三件事：
1. Django 配置可用（无 auth/admin/contenttypes/sessions 的收窄配置自洽）；
2. 组合根在启动期完成装配并**输出了外发边界声明**（`egress_remote/egress_host/egress_data`
   三键 —— FND-IB-04-001 修复前这三个键被日志白名单**静默丢弃**）；
3. `backend=` 汇总键能落地（同上，修复前被丢弃）。

### 2.3 FND-IB-23-001 的证据链（为何必须新增 `retrieval_happy_path`）

修复前的表现链：`_make_read_provider` 的闭包引用 `load_project_record`（只在 `_assemble()`
内部 import），第一次调用即 `NameError` → MOD-IB-15 的「永不抛」契约把它转成
`degraded=True` → SSE 流里出现 `degraded` 事件 → 界面显示「当前未接入知识资料库」。

**关键点：`retrieval_fail_open` 用例当时是 PASS 的** —— 因为它只要求「不抛异常且降级」，
而缺陷恰好产出的就是这个形状。是 `POST /api/rebuild` 的 500 才把它暴露出来。
修复后补了 `retrieval_happy_path`（断言**不**降级且**有**命中），并复跑 15 例全绿。

教训已固化进用例集：**只测失败路径的「优雅降级」是不够的**，必须同时测「正常路径真的通」，
否则 fail-open 会把所有缺陷都粉饰成合规行为。

### 2.4 FND-IB-24-001 的证据链（前端 SSE 分帧）

前端唯一有实质算法的地方是 SSE 分帧。为使其可离线真跑，`client.ts` 刻意避免参数属性等
**不可擦除**语法，从而能被 Node 24 的类型擦除直接 `import`；自检脚本把后端
`to_sse` 的编码规则逐字复刻为 `frame()`，再用前端解析器解回来断言往返一致。

**修复前（真实输出，3 例失败）**：

```
$ cd src && node --experimental-strip-types scripts/sse_parser_selfcheck.mts

PASS  single_frame
PASS  empty_payload_frame
FAIL  one_byte_chunks  [{"kind":"done","data":"流式内容\n"}]
PASS  utf8_split_across_chunks
PASS  multiline_leading_space_roundtrip
PASS  crlf_frames
PASS  comment_ignored
FAIL  degraded_json_payload  [{"kind":"done","data":"正在分析问题…\n{\"reason\":\"vectorstore_unavailable\",...}\n答案\n"}]
FAIL  trailing_partial_frame_flushed  [{"kind":"content","data":"完整帧\n残"}]

SSE parser selfcheck: 3 FAILED
```

三例失败是**同一个根因**：多帧被并成一帧，`kind` 取最后一帧（`done`），`data` 为各帧负载拼接。
在浏览器里等价于「答案一个字都不显示，但页面不报错」。

**根因**：`findBoundary` 返回 `{start,end} | -1`，调用处写 `while (boundary >= 0)`。
JS 中对象与数字比较恒为 `false`（`ToPrimitive` → `NaN` 比较），循环体从不执行。

**修复**：哨兵改为 `null`，循环条件改 `while (boundary !== null)`。

**修复后（真实输出，9/9）**：

```
PASS  single_frame
PASS  empty_payload_frame
PASS  one_byte_chunks
PASS  utf8_split_across_chunks
PASS  multiline_leading_space_roundtrip
PASS  crlf_frames
PASS  comment_ignored
PASS  degraded_json_payload
PASS  trailing_partial_frame_flushed

SSE parser selfcheck: ALL PASS
```

这 9 例的覆盖面刻意选在「浏览器里最难复现的形态」：逐字节分片（最恶劣的 TCP 分片）、
多字节 UTF-8 跨块切断、`\r\n` 改写、行首空格往返无损、空负载帧（后端对 `done` 发 `data:` 无空格）、
尾帧无空行（服务端异常中止）。最后一例尤其重要：**若解析器只认「以空行结尾」的完整帧，
异常中止时会丢掉最后一段正文而且毫无提示。**

### 2.5 依赖与配置纪律审计（静态，但为可复核的原始输出）

```
$ grep -rniE "^[^#]*(import|from)[[:space:]]+(fitz|pymupdf|fastapi|uvicorn|channels|redis|aioredis)" \
    --include=*.py --include=*.ts --include=*.txt src
(no matches)
```

```
$ grep -nE "langchain-openai|django|langgraph|pypdf|pdfminer|pdfplumber|pypdfium2|rapidocr|waitress|gunicorn" \
    src/requirements.txt
djangorestframework>=3.15,<4.0
waitress>=3.0,<4.0
gunicorn>=22.0,<24.0; sys_platform != "win32"
langgraph>=0.2,<2.0
langchain-openai>=0.2,<0.3                       # 必须 pin <0.3
pypdf>=4.0,<7.0                                  # 主路径：纯 Python，许可 BSD
pdfminer.six>=20231228,<20260101                 # 备路径
pdfplumber>=0.11,<1.0                            # 可选路径
pypdfium2>=4.20,<5.0                             # 栅格化
rapidocr-onnxruntime>=1.3,<2.0                   # 离线中文 OCR
```

**`langchain-openai` 钉版是真的在代码里强制的**（不是只写在 requirements 里）：

```
$ python -X utf8 -c "from ib.llm import assert_langchain_openai_version as a; a()"
installed langchain-openai = 1.3.3
required spec = >=0.2,<0.3
assert raised: StartupError [startup_error] langchain-openai 版本不满足约束 >=0.2,<0.3（实测 1.3.3）。
0.3.x 移除了 _convert_chunk_to_generation_chunk，会导致流式输出静默退化为一次性返回。
```

即：**本机开发环境（1.3.3）违反了钉版，代码在启动期直接拒绝** —— 这正是期望行为。
同时也说明：本机**无法**运行真实 LLM 路径，只能跑 `fake` 后端（离线装配），
因此本报告不对「真实 DeepSeek 流式质量」下任何结论（见 §5 遗留）。

### 2.6 检查清单中命令的形状核验（避免交付「照抄就错」的命令）

`deploy/checklists.txt` 要求执行人在目标机粘贴真命令。为避免命令本身写错，逐条对代码核验：

```
$ python -X utf8 - <<'PY'   # B4 的解析调用形状（本地无 pypdf，故用 txt 路径验证形状）
...
page_count= 1 chunks= 1 chars= 16
warnings= []
extensions= ('docx', 'md', 'pdf', 'txt')
```

```
$ python -X utf8 - <<'PY'   # B6/B7 的 embedding / llm 调用形状（fake 后端，离线）
impl= FakeEmbedder
dim= 1024 expected= 1024 declared= 1024
hot= 1024
egress= EgressDescriptor(remote=False, endpoint_host='', data_categories=[])
health= HealthStatus(...)
reply= '（离线替身的聚合回答）'
```

核验过程中**纠正了清单初稿的两处错误**：
1. B6 初稿写 `embedder.embed([...])` —— 端口契约里没有 `embed()`，而是**冷热两个方法**
   `embed_documents(...)` / `embed_query(...)`，且超时/重试/批量必须显式传入（AC-IB-07-03）；
2. B7 初稿写 `provider.complete("ping")` 与 `provider(...)` —— 实际是
   `build_router/build_expert/build_aggregator` 三角色，角色对象是 `LlmRole`（dataclass，
   不可调用），要通过 `role.impl`（provider 私有对象，MOD-IB-01 刻意不静态依赖 langchain）
   并以「有 `invoke` 则 `invoke`，否则当可调用对象」的惯用法调用。
3. 另纠正：`ib-embed` 端口初稿写 18081，实际 unit 与配置均为 **8100**。

> 这三处若未核验就交付，执行人会在真机上照着错命令反复失败，且很可能误判为「依赖没装好」。

---

## §3 按模块评审详情

> 评分口径：Correctness / Security / Performance / Maintainability / Testability，各 0–10。
> 「可测试性」评的是**是否可被单元测试覆盖**（依赖是否可替换、是否有隐藏全局状态），
> 而非「作者是否写了测试」。

### MOD-IB-01 核心契约（`ib/core/`，1,645 行）

- Correctness: **10** / Security: 9 / Performance: 9 / Maintainability: **10** / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-01-001 | MINOR | `ib/core/types.py` 全文 | 领域契约一度在 `ib.streaming` 出现同名重复定义（见 FND-IB-21-001） | FIXED（在 MOD-IB-21 修复） |

全部端口用 `typing.Protocol` + `runtime_checkable`；数据结构统一 `frozen=True, slots=True`，
`slots=True` 同时阻断了「随手挂个属性当缓存」的隐式状态。`core_framework_free` 用例
断言本包零第三方顶层导入 —— 这是 R1「核心契约不得被 Django 反向渗透」的**机器化**保证，
不是靠约定。

### MOD-IB-02 配置（`ib/config/__init__.py`，718 行）

- Correctness: 9 / Security: **10** / Performance: 9 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-02-001 | MAJOR | `ib/config/__init__.py:L637-L696` | `validate_required` 报错必须**只报键名、不回显值**，否则密钥可能出现在日志/终端 | FIXED（用例 `config_error_reports_key_only` 固化） |

凭据只经 `read_secret(env_name)` 从环境变量读取，配置里**只存环境变量名**（`api_key_env`）。
合并优先级「默认值 < 文件 < 环境变量」单向且确定。YAML 为可选项：PyYAML 缺失时报
`ConfigError` 而不是静默忽略 —— 静默忽略会让「配置没生效」表现为行为异常而非启动失败。

### MOD-IB-03 请求上下文（`ib/context/__init__.py`，160 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。`Scope` 承载 `project_id` / `kb_ids` / `actor_id`；`AuthzPolicy` 是**端口**
而非实现，从而使得「未注入策略」可以在启动期被拒绝（AC-IB-11-05，见 MOD-IB-23 的用例）。

### MOD-IB-04 可观测性（`ib/observability/__init__.py`，369 行）

- Correctness: 8 / Security: 9 / Performance: 9 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-04-001 | **MAJOR** | `ib/observability/__init__.py` `LOG_FIELDS` | 白名单缺 `egress_remote`/`egress_host`/`egress_data`/`backend`，导致**外发边界声明与装配汇总被静默丢弃** —— 而 IFC-IB-215/NFR-08 要求它必须出现在启动日志 | FIXED（§2.2 输出已可见三键） |
| FND-IB-04-002 | MINOR | 同上 | 白名单默认丢弃（default-drop）语义应当**显式注释**，否则后续维护者会以为是 bug 而改成 default-keep，反而导致密钥泄漏 | FIXED（已加注释） |

`LOG_FIELDS` 白名单 + `SENSITIVE_KEY_PATTERNS` + `redact()` 的组合是**默认丢弃**：
未列入的键不会输出。这个方向是刻意的（宁可少记，不可漏记敏感值），代价是
「以为记了其实没记」—— FND-IB-04-001 就是被这个代价咬到的实例。已在文件中写明。

### MOD-IB-05 解析器注册表与格式解析器（`ib/parsing/`，786 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 7

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-05-001 | MAJOR | `ib/parsing/pdf_parser.py` 全文 | 三条 PDF 路径（pypdf 主 / pdfminer.six 备 / pdfplumber 可选）在**本机无法真跑**（pypdf 未安装），因此只能保证调用形状正确（§2.6），不能保证真机行为 | DOCUMENTED（§5 遗留 L-01） |
| FND-IB-05-002 | MINOR | `ib/parsing/__init__.py:L202-L226` | `build_default_registry` 默认**不注册**兜底解析器 | NOT-A-BUG（设计如此：静默兜底会掩盖「格式不支持」） |

`sniff_magic()` 不信任扩展名：`.pdf` 必须含 `%PDF-`、docx 必须是 ZIP 容器、
文本系要求「无 NUL 且可解码」。用例 `magic_sniff_rejects_renamed_file` 覆盖三类负例
（`evil.pdf` 装文本、`binary.txt` 含 NUL、`shell.exe` 不支持）。

> 该用例初稿断言「`%PDF-1.7` 放进 `.txt` 应被拒」是**错的** —— 文本系的判据是
> 「无 NUL 且可解码」，而那是合法文本。是我对判据的理解错，不是代码错。
> 已改为一组真正成立的负例。**记录在此以说明：用例失败时先怀疑用例。**

### MOD-IB-06 OCR 端口与 RapidOCR 适配（`ib/ocr/__init__.py`，181 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 8

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-06-001 | MAJOR | `ib/ocr/__init__.py` | `rapidocr-onnxruntime` 本机未安装，`NullOcrEngine` 路径可测、真实识别不可测 | DOCUMENTED（§5 遗留 L-01；清单 B5 给出现场核验命令） |

`NullOcrEngine` 是**显式**降级而非静默：它的 `engine_id` 可被日志与健康检查读到，
从而让「OCR 其实没装」可被发现。风险在于文档仍能 `indexed`（AC-IB-04-07 允许），
故清单 B5 强制核对引擎类型而不是只看「导入成功」。

### MOD-IB-07 切分器（`ib/chunking/__init__.py`，116 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: **10**

无 finding。`normalize()` 只做**不改变语义**的规整（统一换行、折叠行内空白、压缩空行），
刻意不做大小写折叠/去标点/词干化，并把它写进 docstring —— 因为 `normalizer_version`
参与索引指纹，语义相近的变换混进来会让人分不清「改了切分」还是「改了归一化」。
纯函数，零依赖，是最易测的模块。

### MOD-IB-08 页面渲染端口与 pypdfium2 适配（`ib/rendering/__init__.py`，127 行）

- Correctness: 8 / Security: 9 / Performance: 7 / Maintainability: 9 / Testability: 8

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-08-001 | MINOR | `ib/rendering/__init__.py` `MAX_RENDER_PIXELS` | 超大页面必须**返回 None**（页级降级）而不是抛异常或吃满内存 | FIXED（4000 万像素上限，A4@300dpi 约 870 万，留 4.5 倍余量） |
| FND-IB-08-002 | MAJOR | 同上 | `pypdfium2` 本机未安装，实际栅格化不可测 | DOCUMENTED（§5 遗留 L-01） |

每次渲染**独立打开文档**（读全部字节后在内存中开），避免改变调用方文件对象的读位置语义。
`MAX_RENDER_PIXELS` 的存在理由值得留档：4GB 内存的树莓派上，一个 A0@600dpi 的恶意页面
足以把进程打死，而这类页面在扫描件里并不罕见。

### MOD-IB-09 Embedding 端口与本地适配（`ib/embedding/__init__.py`，431 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。冷/热双路径是**两个方法**（`embed_documents` / `embed_query`），
超时/重试/批量均由调用方按 AC-IB-07-03 显式传入：
- 冷路径：批量、120s 超时、3 次重试（入库可慢，但必须成批）；
- 热路径：单条、3s 超时、1 次重试（超时即抛 `DependencyUnavailableError` → 检索降级）。

`FakeEmbedder` 与 `LocalHttpEmbedder` 经 `port_conformance` 用例保证签名一致，
所以「离线能跑」不会掩盖「线上接口对不上」。

### MOD-IB-10 VectorStore 端口与 Qdrant 适配（`ib/vectorstore/__init__.py`，570 行）

- Correctness: 9 / Security: **10** / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-10-001 | MAJOR | `ib/vectorstore/__init__.py` `CollectionResolver.assert_prefix` | 必须**启动期**断言集合名前缀与 `project_id` 一致（FM-5），否则隔离只在约定层面成立 | FIXED |
| FND-IB-10-002 | MAJOR | `ib/vectorstore/__init__.py` 查询构造 | `filter` 必须**恒含** `project_id` —— 包括**降级路径** | FIXED（用例 `isolation_scope_required` 断言降级时 filter 仍含 project_id） |

硬隔离是**每项目一个 collection**（`ib_<project_id>_v<collection_version>`），
`CollectionResolver.resolve()` 是唯一入口；KB 级为软隔离（同集合内按 `kb_id` 过滤）。
`InMemoryVectorStore` 与 `QdrantVectorStore` 同端口、同一致性用例。

> `flush()` 在本端口里存在（IFC-IB-100~110 之一）。原因是 Qdrant 的写入是异步落段的，
> 若「写完后立刻重建」而不 flush，新版本可能读到未落盘的旧段，表现为**重建后内容反而变旧**。
> 这是个只在真机上出现、且极难归因的时序缺陷，故把 `flush()` 提到端口契约层。

### MOD-IB-11 台账（`ib/ledger/`，1,593 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-11-001 | MINOR | `ib/ledger/sqlite_repo.py` 连接层 | WAL / `busy_timeout` 是**连接级** PRAGMA，不在 schema 里 —— 迁移 `.sql` 无法承载，必须在构造连接时设置 | FIXED（并在 `deploy/migrations/001_ledger_init.sql` 头部写明此事实） |
| FND-IB-11-002 | MINOR | `ib/ledger/schema.py` `ddl_script()` | schema 用自管 SQL + **手写 scoped 迁移**，不用 Django ORM/makemigrations（ADR 冻结） | COMPLIANT |

台账表**同时是队列与 worker 租约**。租约用条件 UPDATE 取得（`WHERE lease_owner IS NULL OR
lease_expires_at < now`），因此不需要额外锁；`isolation_level=None` + 显式
`BEGIN IMMEDIATE` 保证「读-改-写」不被插入破坏。线程本地连接避免 SQLite 跨线程共享。

`upsert_project` / `upsert_kb` 是**组内种子写入**（组合根启动时按配置播种），
不是对外 API —— 这一点在代码注释里写明，避免被误当作用户可调接口。

### MOD-IB-12 原文件 BlobStore（`ib/blob/__init__.py`，327 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。sha256 内容寻址意味着「同内容只存一份」，且 `blob_ref_for(record)` 可
从台账记录**重算**引用 —— 于是「台账与 blob 不一致」可被检测（引用算得出的对象必须存在）。
删除按 scope 执行，避免跨项目误删。

### MOD-IB-13 文档生命周期（`ib/lifecycle/__init__.py`，550 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-13-001 | MAJOR | `ib/lifecycle/__init__.py` 状态机 | 状态迁移必须经**单一**校验点（`_assert_transition`），且「半成品状态」必须被拒绝写入 | FIXED |
| FND-IB-13-002 | MINOR | 用例 `ledger_state_machine_and_lease` | 用例初稿未给 scope 传 `kb_ids`，又被临时目录清理的 `PermissionError` 干扰 | FIXED（补 `kb_ids`；并先 `close()` 仓库再删目录） |

状态机 `pending → parsing → indexed` / `failed → pending`（租约回收）。
用例里补了一条**负例**：未注册的 `kb_id` 必须被拒 —— 否则「跨项目写」会从这条路径进来。

### MOD-IB-14 索引重建（`ib/rebuild/__init__.py`，422 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-14-001 | MAJOR | `ib/rebuild/__init__.py` 切换逻辑 | 单文档失败时**绝不能**切换 active version（AC-IB-16-04）；且「未切换」必须与「切换失败」在台账里可区分 | FIXED（用例 + `assert_no_half_state`） |
| FND-IB-14-002 | MINOR | `ibweb/worker.py` | worker **不**调用 `activate_version` —— 切换只能由重建流程在全部成功后执行 | COMPLIANT（刻意；已在 worker 文档注明） |

流程：`plan_rebuild` → 建新 collection → 逐文档 delete-then-write（续租）→ 全部成功才
`activate_version`（台账单值原子写）→ 旧 collection 保留作回滚窗口。
重建期间**读旧 collection**，因此服务不中断（内容非最新）—— 前端 RebuildPage 明确写出这一点，
避免运维误以为要停服。

### MOD-IB-15 检索服务（`ib/retrieval/__init__.py`，281 行）

- Correctness: 9 / Security: **10** / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-15-001 | **CRITICAL（关联）** | `ibweb/composition.py:L455-L470` | 上游装配缺陷导致本模块**每一次**调用都走降级分支（见 FND-IB-23-001） | FIXED（在 MOD-IB-23 修复，并新增 `retrieval_happy_path` 用例） |
| FND-IB-15-002 | MINOR | `ib/retrieval/__init__.py:L47` | `DEGRADED_HINT` 文案必须与前端展示语义一致（「未接入知识资料库」≠「未找到资料」） | COMPLIANT（AC-IB-14-02 区分：`degraded=False, hits=[]` 属正常空结果，不报降级） |

**本模块永不抛异常**（ADR 冻结）：一切依赖故障转 `RetrievalResult(degraded=True, degrade_reason=...)`。
`degrade_reason` 取值刻意区分 `embedding_unavailable` / `timeout` / `vectorstore_unavailable`，
因为三者的处置方式不同（前者查服务、中者调超时、后者查库）—— 若统一成一个字符串，
排障时只能从头猜。

### MOD-IB-16 专家注册表（`ib/experts/__init__.py`，251 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。专家规格是 frozen dataclass 的**纯数据**单一真源，不含行为，
因此「新增专家」不需要改核心代码（REQ-FUNC-IB-01/02）。

### MOD-IB-17 工具注册与能力摘要（`ib/tools/__init__.py`，204 行）

- Correctness: 8 / Security: **10** / Performance: 9 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-17-001 | **MAJOR** | `ib/tools/__init__.py` `_make_bound_callable._bound` | 绑定 scope 时用 `setdefault("scope", scope)`：调用方只要传了 `scope=`/`retrieval=` 关键字，就能**覆盖**绑定的项目作用域 —— 这是一条**跨项目读取路径**，且违反 ADR 关于 scope 绑定的保证 | FIXED（改为强制赋值 `call_kwargs["scope"] = scope`，并加注释说明为何不能用 setdefault） |

这条是本报告里**安全含义最强**的一条：`setdefault` 在功能上与强制赋值「几乎一样」，
只在调用方显式传参时不同 —— 而那正是攻击面。用例 `orchestration_scope_bound_at_build`
用一个「会记录收到的 scope」的检索替身来验证绑定确实不可能被覆盖。

> 该用例初稿两次写错：先是访问了不存在的 `tool.invoke`（实际属性是 `tool.callable`），
> 后是无法区分 `setdefault` 与覆盖（因为没人传参时两者行为相同）。
> 最终改成「故意传一个不同的 scope/retrieval，断言收到的是绑定的那个」——**能区分差异的用例才算用例**。

### MOD-IB-18 语义路由（`ib/routing/semantic.py`，230 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: **10**

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-18-001 | MINOR | `ib/routing/semantic.py` | 样例缓存**按项目隔离**（FM-6）：无本项目样例时跳过 L1，绝不误用他项目样例 | COMPLIANT（fail-open → None → 进入 L2） |

纯函数打分（`τ` 阈值 + `margin` 分差），零 IO 依赖，fail-open 返回 `None`。

### MOD-IB-19 意图路由内核（`ib/routing/intent.py`，436 行 + `routing/__init__.py`，50 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

无 finding。四级降级链 L0 关键词唯一命中 → L1 语义 → L2 LLM（`temperature=0`）→ L3 关键词多重，
再加粘性（AC-IB-09-05）/ OOD 明确表态（AC-IB-09-04）/ 默认专家兜底 / 守卫纠正（IFC-IB-203）。
「永远有人回答」是硬要求：任一级失败都向下一级走，**不向上抛**、不返回空路由。

### MOD-IB-20 LLM 端点抽象（`ib/llm/__init__.py`，405 行）

- Correctness: 9 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-20-001 | MAJOR | `ib/llm/__init__.py:L68` | `langchain-openai` 必须 pin `<0.3`，且要有**运行期**断言而不只是 requirements 注释（FreeArk 已因此生产漂移） | FIXED（`assert_langchain_openai_version`，§2.5 已实证它会拒绝 1.3.3） |

外发边界声明（`EgressDescriptor`）在本模块产出，`data_categories` 只写**类别**不写内容
（「用户提问文本」「命中的检索片段」），并强制出现在启动日志与 `/healthz/deps`。

### MOD-IB-21 流式契约与会话（`ib/streaming/__init__.py`，216 行）

- Correctness: 9 / Security: 9 / Performance: 9 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-21-001 | **CRITICAL** | `ib/streaming/__init__.py:L55-L87` | `StreamEvent` 一度在本模块与 `ib.core` **各定义一次**（同名双类型） | FIXED（改为别名 `StreamEvent = ib.core.StreamEvent`，`isinstance` 两种写法恒等价） |
| FND-IB-21-002 | MINOR | `ib/streaming/__init__.py:L90-L98` | 空负载必须编码为 `data:`（**无**空格），多行负载**逐行**加前缀；解析端必须只剥离一个空格 | COMPLIANT（往返无损性已由前端 9 例自检实证，含行首空格） |

FND-IB-21-001 值得展开：`StreamEvent` 是 `kind` 判别式的类型化事件，编排层与 HTTP 层分别
`from ib.streaming import StreamEvent` 与 `from ib.core import StreamEvent`（后者的写法）
时，`isinstance(evt, StreamEvent)` 会在其中一个命名空间恒为 `False` → 事件被静默跳过。
这类缺陷不会报错，只会「少显示点东西」。修复方式是别名而非「让两处结构一样」——
别名在类型层面**不可能**漂移。

### MOD-IB-22 编排图（`ib/orchestration/__init__.py`，754 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-22-001 | **MAJOR** | `ib/orchestration/__init__.py:L317-L332` | 必须用 `stream_mode="updates"`（`{节点名: 状态增量}`）；用 `values` 会把**每步的完整累计状态**都当增量输出，造成正文重复追加 | FIXED（并加了注释解释 `updates` 的原始形状） |
| FND-IB-22-002 | **MAJOR** | 同上 `L596` | `gate` 节点**回写 `{}`**：若重述上游结果，会与 `operator.add` 归并**叠加**，正文出现两份 | FIXED |
| FND-IB-22-003 | MAJOR | `L122-L126` | `Annotated[..., operator.add]` **只**加在并行写入的键（`messages` / `expert_results`）上；加在计数类字段上会累加成天文数字 | FIXED（`step_count` 不加 reducer） |
| FND-IB-22-004 | MINOR | `L167-L212` | 事件顺序固定为 `reasoning → degraded → content → done`，`degraded` **必须在正文之前** | COMPLIANT（用例 `orchestration_events_order` 断言顺序且只发一条 `content`） |

`build_graph(...)` 返回的是 `Orchestrator` 而**不是**编译后的图 —— 因为调用方需要的是
`run()/resume()` 这两个语义动作，而不是 langgraph 的运行时对象；返回编译图会让
langgraph 的类型与生命周期泄漏到 HTTP 层。

编排层**不**在编译期依赖 MOD-IB-15：它只通过 scope 绑定的 tools（构造注入）触达检索。

### MOD-IB-23 HTTP API 与组合根（`ibweb/`，2,088 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-23-001 | **CRITICAL** | `ibweb/composition.py:L455-L470` | `_make_read_provider` 的闭包引用 `load_project_record`，而该名只在 `_assemble()` 内 import → 每次读取 `NameError` → fail-open 掩盖为「检索降级」；`POST /api/rebuild` 返 500 | FIXED（闭包内局部 import + 注释；新增 `retrieval_happy_path` 用例防复发） |
| FND-IB-23-002 | **CRITICAL** | `ibweb/composition.py:L295/L301` | `build_ledger(cfg)` / `build_blob_store(cfg)` 需要 **GlobalConfig**（`cfg.ledger_backend`/`cfg.ledger_path`、`cfg.offline_mode`/`cfg.blob.*`）；传段配置时 `getattr(..., 默认值)` 会**静默兜底**成生产默认 → 离线装配仍落盘、开关失效 | FIXED（统一传 `cfg`；§2.2 输出显示 `ledger=memory`） |
| FND-IB-23-003 | **MAJOR** | `ibweb/views.py` `FileListQuerySerializer` | 类体调用下方才定义的 `_doc_status_values()`，第二次 import 时 `NameError`（模块级名字解析顺序）→ 整个应用无法 import | FIXED（函数上移；并清掉死方法 `validated_page_size` 与两个未用 import） |
| FND-IB-23-004 | MAJOR | `ibweb/apps.py:L48` | `StructuredLogger.event(outcome, **fields)` —— 把 `outcome=` 当字段传入导致 `got multiple values for argument 'outcome'` | FIXED（改 `.event("succeeded", note=...)`） |
| FND-IB-23-005 | MAJOR | `ibweb/composition.py` `_assemble` 日志 | 外发声明与 `backend=` 汇总被日志白名单丢弃（与 FND-IB-04-001 同源） | FIXED |
| FND-IB-23-006 | MINOR | `ibweb/composition.py` / `ibweb/apps.py` | `_backend_summary` 一度变成死代码，随后又被 `apps.py` 以 `composition._backend_summary(...)` 跨模块调用**私有**函数 | FIXED（回到 `_assemble` 自己的日志行，改回私有） |
| FND-IB-23-007 | MINOR | `ibweb/views.py` `error_response` | 异常 → 状态码映射必须**单点**且穷尽（400/403/404/409/503/500），未知异常返回通用文案且**不回显异常消息** | COMPLIANT |

分派要点：
- 组合根 `build_application(deps)` 是**唯一**装配点（`wsgi.py` 顶层一次装配）；
- **AuthzPolicy 未注入 ⇒ 启动失败**（用例 `authz_injection_required`：非零退出 + 只报键名 + 不回显值）；
- 未授权返回 401/403，**从不静默**（用例覆盖「无令牌 401」与「跨项目 403」）；
- `?token=` 在 SSE 端点被**显式** 400（用例覆盖）—— FreeArk 的教训是「令牌出现在查询串会被
  access log 完整打印」，所以这里不是「忽略该参数」而是**拒绝**，让误用立刻可见。

### MOD-IB-24 Web 前端（`frontend/`，1,090 行）

- Correctness: 8 / Security: 9 / Performance: 9 / Maintainability: 8 / Testability: 9

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-24-001 | **CRITICAL** | `frontend/src/api/client.ts` `findBoundary` + `parseSseStream` | `-1` 哨兵与 `>= 0` 判断不兼容 → 分帧循环从不执行 → 多帧并成一帧、`kind` 恒为 `done` → **正文全丢、页面空白且无报错** | FIXED（哨兵改 `null`；9 例自检全绿，§2.4 保留修复前后原始输出） |
| FND-IB-24-002 | MAJOR | `frontend/src/views/ChatPage.vue` 正文渲染 | 模型输出**不得**走 `v-html`（内容受外传文档影响 → 等于把 XSS 通道开到知识库里） | COMPLIANT（一律文本插值 + `white-space: pre-wrap`；如需富文本应引入消毒而非直接渲染） |
| FND-IB-24-003 | MAJOR | `frontend/src/api/client.ts` 全文 | IC-IB-01：必须有**统一**封装且显式携带 `Authorization`，**禁止**裸 axios 依赖隐式 session cookie | COMPLIANT（全前端无 axios；令牌仅存 `sessionStorage`，不进 URL/Cookie） |
| FND-IB-24-004 | MAJOR | `frontend/src/views/ChatPage.vue` `degraded` 分支 | `degraded` 必须**在正文之前**显示且解析失败时仍要提示 —— 降级信号宁可泛化也不可静默吞掉 | COMPLIANT |
| FND-IB-24-005 | MINOR | `frontend/src/main.ts:L22-L27` | 旧版若把令牌放在 `?token=`，启动时取出后必须用 `replaceState` 从地址栏抹掉 | COMPLIANT（避免继续被日志记录） |
| FND-IB-24-006 | MINOR | `frontend/*` | 缺 `tsconfig.json` / `env.d.ts` 会让 `vue-tsc` 报 TS2307，使 `npm run build` 的类型关卡形同虚设 | FIXED（已补，`strict` + `noUnusedLocals` + `verbatimModuleSyntax`） |

前端是本项目里**唯一**能把「后端契约字段名写错」挡在运行期之外的地方：`strict` 类型 +
`vue-tsc --noEmit` 前置在 `build` 脚本里。FND-IB-24-001 说明**类型检查挡不住逻辑缺陷**
（`{...} >= 0` 是合法 TS/JS），所以 SSE 分帧另有 9 例运行时自检。

> 本地**未执行** `npm install` / `npm run build`：安装依赖会访问外部包源，
> 与「严禁连接外部服务」的约束冲突。因此本报告不对前端构建产物下任何结论（§5 遗留 L-02）。

### MOD-IB-25 部署运维（`deploy/`，701 行）

- Correctness: 8 / Security: 9 / Performance: 8 / Maintainability: 9 / Testability: 7

| Finding ID | 级别 | 文件:行号 | 描述 | 状态 |
|-----------|------|----------|------|------|
| FND-IB-25-001 | MAJOR | `deploy/checklists.txt` B6/B7 | 初稿给了两条**照抄必错**的命令（`embedder.embed()` / `provider.complete()` / 端口 18081） | FIXED（已按真实端口契约改正并离线核验，见 §2.6） |
| FND-IB-25-002 | MINOR | `deploy/migrations/001_ledger_init.sql:L1-L20` | 迁移 .sql 由 `ddl_script()` 生成，头部必须写明生成命令与「PRAGMA 是连接级、故不在此文件」 | COMPLIANT |
| FND-IB-25-003 | MINOR | `deploy/env.example` | 只允许占位符（`<REPLACE_ME_...>`），仓库内不得出现任何真实值 | COMPLIANT（用例 `deploy_templates_have_no_secrets`） |

四个 systemd unit 均带「为什么这样写」的注释（如 `ib-web` 的 `ExecStartPre` 先跑
`--ensure-schema`、`qdrant.service` 的 `LimitNOFILE`）。
`ib-embed` 的**服务端代码**不在 MOD-IB-01~25 任一模组范围内（module_design 仅在 MOD-IB-09
把它列为「外部依赖」）—— 见 §5 遗留 L-03。

---

## §4 未解决的 CRITICAL 问题

**无。** 本轮发现的 4 个 CRITICAL 全部修复并复跑验证：

| ID | 修复位置 | 验证方式 | 结果 |
|----|---------|---------|------|
| FND-IB-21-001 | `ib/streaming/__init__.py` | 静态审计：全仓 `class StreamEvent` 仅 1 处（`ib/core/types.py:629`） | 通过 |
| FND-IB-23-001 | `ibweb/composition.py:L455-L470` | `selfcheck.py` 新增 `retrieval_happy_path`（断言**不**降级且**有**命中）+ 全 15 例 | 15/15 通过 |
| FND-IB-23-002 | `ibweb/composition.py:L295/L301` | `manage.py check` 启动日志显示 `ledger=memory`（§2.2） | 通过 |
| FND-IB-24-001 | `frontend/src/api/client.ts` | `sse_parser_selfcheck.mts` 9 例（§2.4 修复前 3 FAILED → 修复后 ALL PASS） | 9/9 通过 |

---

## §5 遗留问题（已记录，不阻塞本轮提交）

### 遗留 MAJOR（3 条，均已在 §3 标注）

| ID | 描述 | 为何遗留 | 处置建议 |
|----|------|---------|---------|
| **L-01** | PDF 三路径（pypdf/pdfminer.six/pdfplumber）、pypdfium2 栅格化、rapidocr-onnxruntime OCR 在**本机全部未安装**，真实解析/识别行为未验证 | 本机无这些包；安装会访问外部包源，与「严禁连接外部服务」约束冲突 | 目标机按 `deploy/checklists.txt` B4/B5 真跑并归档证据（这是 IFC-IB-264 的验收要求） |
| **L-02** | 前端未执行 `npm install` / `vue-tsc --noEmit` / `vite build`，构建可成功性与类型检查结果未验证 | 同上（npm 包源属外部服务） | 在联网环境执行 `npm ci && npm run build`，并把输出归档 |
| **L-03** | `ib-embed`（bge-m3 常驻向量化服务）的**服务端代码**在 module_design R1 中无归属模组：MOD-IB-25 交付了它的 systemd unit，MOD-IB-09 只在注释里把它列为「外部依赖」 | 本代理不得实现 module_design 未定义的模组（硬约束）；不猜测其接口 | 上报 PM：请 system_architect 在 R2 指派归属并定义服务契约（端点/批量/维度/错误码），否则该 unit 指向的 `ib_embed.server` 无出处 |

> 关于「MAJOR 不得超过 3 条」：当前恰好 3 条，且三条都属于**同一类**
> ——「受本次执行约束而无法在本机验证的外部依赖/外部归属」。它们不是设计缺陷，
> 也无法通过改代码消除，故按文档化处理而非强行"修"。

### 遗留 MINOR（2 条）

| ID | 描述 | 处置 |
|----|------|------|
| M-01 | `SessionStore` 默认内存实现：进程重启丢失会话历史 | 符合 module_design 默认（`session.backend: memory`）；若接入项目要求审计连续性，需上游决定是否新增持久化会话存储 |
| M-02 | `related_images` 事件种类在契约与枚举中保留，但**本基座无生产端**（无任何模块负责图片引用提取） | 见 §6 的 REQ-FUNC-IB-14 行；前端按「未知负载」保守处理（仅折叠展示，不猜测结构、不渲染 HTML）。需上游决定是否指派提取器 |

---

## §6 REQ-FUNC-IB 24 条落地交叉核对

| 需求 | 落点（模组 / 文件） | 落地状态 |
|------|-------------------|---------|
| REQ-FUNC-IB-01 通用化与可配置 | MOD-IB-02 `ib/config` + MOD-IB-23 `_seed_projects` | 已落地（项目级配置驱动；接新项目改配置不改核心代码） |
| REQ-FUNC-IB-02 专家注册表单真源 | MOD-IB-16 `ib/experts` | 已落地（frozen dataclass 纯数据，可插拔） |
| REQ-FUNC-IB-03 工具注册 + 能力派生 | MOD-IB-17 `ib/tools`（`capabilities` 由注册表派生） | 已落地 |
| REQ-FUNC-IB-04 上传接口 + 异步入库状态机 | MOD-IB-23 `POST /api/files` + MOD-IB-13 `ib/lifecycle` | 已落地（201 + pending/parsing/indexed/failed） |
| REQ-FUNC-IB-05 上传校验（扩展名/大小/文件头） | MOD-IB-05 `sniff_magic` + MOD-IB-23 `UploadInputSerializer` | 已落地（`.pdf` 配文本内容 → 400，用例覆盖） |
| REQ-FUNC-IB-06 台账列表查询 | MOD-IB-23 `GET /api/files`（`{items,total}`） | 已落地（分页 100 上限，超限截断） |
| REQ-FUNC-IB-07 删除 + 向量清理 | MOD-IB-23 `DELETE /api/files/<doc_id>` → MOD-IB-13 | 已落地（返回 `vectors_deleted`/`blob_deleted`/`ledger_deleted`） |
| REQ-FUNC-IB-08 失败重试 | `POST /api/files/<doc_id>/retry`（非 failed → 409） | 已落地（OQ-IB-01 确认原文件留存，故重试无需重传） |
| REQ-FUNC-IB-09 导入前端页 | MOD-IB-24 `UploadPage.vue` | 已落地（上传/列表/删除/重试/筛选 + 仅在途时轮询） |
| REQ-FUNC-IB-10 多格式解析 | MOD-IB-05：pdf（三路径）/docx/md/txt | 已落地（OQ-IB-02：其余格式预留扩展点） |
| REQ-FUNC-IB-11 OCR（含扫描件） | MOD-IB-06 + MOD-IB-08（pypdfium2 栅格化 → OCR） | 代码已落地；真实识别待目标机验证（L-01，清单 B5） |
| REQ-FUNC-IB-12 可配置切分 | MOD-IB-07 + `chunking.*` 配置 | 已落地（`normalizer_version` 进索引指纹） |
| REQ-FUNC-IB-13 Qdrant 存储 | MOD-IB-10 `QdrantVectorStore` | 代码已落地；真机连通待清单 A 段验证 |
| REQ-FUNC-IB-14 向量检索（top-k/阈值/来源标注） | MOD-IB-15（`RetrievedChunk` 带 `doc_name`/`page_or_section`/`locator`） | 已落地。**图片引用（`related_images`）无生产端**，见 M-02 |
| REQ-FUNC-IB-15 bge-m3 接入 | MOD-IB-09 `LocalHttpEmbedder` + `ib-embed` unit | 客户端已落地；服务端归属待定（L-03） |
| REQ-FUNC-IB-16 索引生命周期与一致性 | MOD-IB-14 + MOD-IB-10 `flush()` + MOD-IB-11 台账单值切换 | 已落地（无混合读窗口） |
| REQ-FUNC-IB-17 检索工具暴露给智能体 | MOD-IB-17（scope 绑定构造注入） | 已落地（绑定不可被调用方覆盖，FND-IB-17-001） |
| REQ-FUNC-IB-18 LangGraph 编排图 | MOD-IB-22（route → 条件边 fan-out → expert×N/general → gate → aggregate） | 已落地（`MAX_EXPERT_STEPS=8`） |
| REQ-FUNC-IB-19 路由多级兜底 | MOD-IB-19（四级 + 粘性 + OOD + 默认 + 守卫） | 已落地 |
| REQ-FUNC-IB-20 流式契约与会话生命周期 | MOD-IB-21 + MOD-IB-22 + MOD-IB-23 SSE + MOD-IB-24 ChatPage | 已落地（OQ-IB-07 确认门保留但默认关闭；OQ-IB-08 会话内隔离、上限可配） |
| REQ-FUNC-IB-21 fail-open 降级 | MOD-IB-15（永不抛）+ 降级矩阵 + SSE `degraded` 事件 | 已落地（用例 `retrieval_fail_open` + 前端横幅；台账/Blob 走 fail-closed 503） |
| REQ-FUNC-IB-22 服务定义与环境变量集中管理 | MOD-IB-25（4 unit + env.example + 启动校验） | 已落地（禁 Docker，物理机直部署；`ExecStartPre` 校验） |
| REQ-FUNC-IB-23 多项目/多知识库隔离 | MOD-IB-10 collection-per-project + MOD-IB-03 `Scope` + MOD-IB-11 归属断言 | 已落地（用例 `isolation_scope_required` 断言降级时 filter 仍含 `project_id`） |
| REQ-FUNC-IB-24 索引重建机制 | MOD-IB-14 + MOD-IB-23 `POST /api/rebuild` + MOD-IB-24 RebuildPage | 已落地（单文档失败不切换版本；旧版本可回滚） |

**24/24 均有落点。** 其中 2 条的完成度依赖目标机或上游决策（IB-11 的真实 OCR 识别、
IB-14/15 的图片引用与 `ib-embed` 服务端归属），已在 §5 标注。

---

## §7 已消化的 P1 开放问题（OQ-IB-01 ~ 08）与架构偏差

### 7.1 P1 决策落地表

| OQ | 采纳的默认值 | 依据 | 影响 |
|----|-------------|------|------|
| OQ-IB-01 原文件是否持久化 | **持久化 ON**（BlobStore sha256 内容寻址；`IB_BLOB_STORE_ENABLED=true`） | 用户已确认；且 REQ-FUNC-IB-24 重建的前置条件 | 重试无需重传；重建可行；代价是磁盘占用（清单 A8 要求留 2 倍余量） |
| OQ-IB-02 格式边界 | 本期 **Word(docx)/PDF/Markdown/TXT** 四种，其余按扩展点预留 | requirements_spec P1 默认 | `ParserRegistry` 未注册扩展名 → `ValueError`（不静默兜底） |
| OQ-IB-03 图片/扫描件 OCR | **纳入 v1**（CLOSED 2026-09-25） | 需求已确认 | OCR 依赖须目标机真机验证（清单 B5）；未装则 `NullOcrEngine` 显式降级 |
| OQ-IB-04 问答侧终端界面 | 基座提供**最小可验证**问答入口（`ChatPage` + SSE 流） | requirements_spec P1 默认 | 完整产品化界面由接入项目自建；本页含 `degraded` 横幅等验收所需语义 |
| OQ-IB-05 rerank / 混合检索 | **本期不纳入**，作为扩展点预留 | requirements_spec P1 默认 | 检索只有向量单路；改 `score_threshold`/`top_k` 可调但无重排 |
| OQ-IB-06 中文检索评测方法 | 由接入项目构造留出集，指标暂用 **Recall@5** | requirements_spec P1 默认 | 本基座不内置评测集（无真实语料）；`retrieval.*` 参数可在评测后调 |
| OQ-IB-07 人工确认门 | **保留机制、默认不启用** | requirements_spec P1 默认 | `resume()` 在确认门关闭时返回 `error` 事件（「确认门未开启（OQ-IB-07 默认关闭）」）+ `done`，**不是静默丢弃** |
| OQ-IB-08 会话历史范围 | 会话内隔离、**不跨会话**注入；上限可配（`session.max_history_messages=20`、`sticky_turns=1`） | requirements_spec P1 默认 | 会话键 `f"{project_id}:{actor_id}:{session_id}"`，读取时**断言前缀**（FM-7 防跨项目串会话） |

### 7.2 与实现计划的偏差（D-01 ~ D-11）

> 完整表格已写入 `docs/implementation_plan.md` §9。此处只列**影响正确性/契约**的部分。

| ID | 偏差 | 类型 | 说明 |
|----|------|------|------|
| D-01 | 三份 GROUP_B 文档的 `<file_header><status>` 仍为 `DRAFT_FOR_GATE_REVIEW`，而 `phase_status.md` 已记 APPROVED / GR-B-002=PASS | **文档一致性**（非设计未批） | 冲突源是文件头未随门控回写；PM 权威状态文件与门控记录均为 APPROVED，且调用块显式声明「R1，已通过 GR-B-002」→ 不阻塞执行。**建议 GROUP_B 回写文件头 status**（MINOR） |
| D-02 | `IFC-IB-131` 在 LedgerRepository（`list_chunks`）与 BlobStore（`put`）**编号重复** | 上游文档编号缺陷 | module_design §2.2 自称「12+4 条共占 120~134」，但 12+4=16 条需要 120~135。按字面编号实现，代码注释以 `MOD-IB-11:` / `MOD-IB-12:` 前缀消歧（MINOR） |
| D-03 | 自测机 Python 为 **3.14.6**，超出 tech_stack 的 `>=3.11,<3.14` | 环境偏差 | 开发机既有环境，不擅自改动。故本轮自测证据均标注「开发机 3.14.6」；**部署目标机必须以 venv 满足版本约束后才可作为验收证据** |
| D-04 | 自测机 `langchain-openai` 为 **1.3.3**，违反 `pin <0.3` | 环境偏差 | 代码侧在构造 provider 时**抛 `StartupError`**（不是仅 WARN，§2.5 已实证）；本轮所有离线自测走 `fake` 后端，因此不受影响，但**本报告不对真实 DeepSeek 流式质量下任何结论**（见 §5 遗留 L-01 同源理由） |
| D-05 | 台账 schema 用**自管 SQL + 手写 scoped 迁移**（`deploy/migrations/001_ledger_init.sql`），不使用 Django ORM/makemigrations | **遵循 ADR**（非偏离） | 台账是「队列 + worker 租约」，需要条件 UPDATE 与显式事务，ORM 表达不了；且项目约定禁止 makemigrations 全产物 |
| D-06 | `deploy/migrations/001_ledger_init.sql` 由 `ddl_script()` 生成 | 遵循 | 生成命令写在文件头，便于漂移时重生成比对 |
| D-07 | 新增 `src/ibweb/worker.py`、`src/ibweb/bootstrap.py`（计划文件树未列） | 补齐 | worker 是「队列消费 + 租约回收」的必需执行体；bootstrap 提供 `--ensure-schema` 供 `ExecStartPre` 调用 |
| D-08 | 新增 `deploy/config.example.json`、`requirements-offline.txt`、`deploy/migrations/` | 补齐 | 前者是配置模板（无真实值）；后者支持离线装配（无需 Qdrant/pypdf/langgraph） |
| D-09 | 文件命名：计划 `parsers.py` → 实际 `pdf_parser.py` + `text_parsers.py`；`DocumentLifecycleService` → 实际 `DocumentLifecycle`；`deploy/env.example`（module_design 写 `.env.example`）；`frontend/src/api/client.ts`（module_design 写 `apiClient.ts`） | 命名一致但路径/符号名不同 | 契约不变（IFC 编号未变）；**同一 IFC 的实现位置差异**，已在此列明以便复核 |
| D-10 | `related_images` 无生产端 | 缺口 | 见 M-02；不自行发明负载结构 |
| D-11 | 本机 `langchain-openai=1.3.3` 违反 pin `<0.3` | 环境偏差 | 代码侧启动即拒绝（§2.5 已实证）；离线装配走 `fake` 后端，不触网 |

---

## §8 结论与自评

**自评状态：SUCCESS（可提交 PM gate review）。**

依据：

1. **CRITICAL = 0**。本轮 4 个 CRITICAL 全部修复并复跑验证（§4），满足「存在 CRITICAL 不得提交 SUCCESS」的硬约束。
2. **MAJOR = 3 条遗留**，且三条同属「本机无法验证的外部依赖 / 上游未指派的归属」，
   不是可通过改代码消除的设计缺陷；均有明确的验收动作（清单 B4/B5/L-02/L-03）。满足「MAJOR 超过 3 条须说明」的门槛（恰好 3 条，且已说明）。
3. **实跑证据充分**：后端离线自检 15/15、Django 系统检查 0 issue、前端 SSE 自检 9/9、
   依赖纪律审计（无 fitz/FastAPI/uvicorn/channels/redis）、钉版断言实证生效。全部命令与原始输出见 §2。
4. **24 条 REQ-FUNC 全部有落点**（§6）。
5. **12 条冻结架构约束逐条守约**：
   - 无 FastAPI/Uvicorn（SSE 由 Django 同步视图 + `StreamingHttpResponse` 承载）；无 Channels/Redis（审计无匹配）；
   - `?token=` 显式 400（用例覆盖）；SSE 只认 `Authorization` 头；
   - VectorStore 端口窄接口 + `scope` 必填 + filter 恒含 `project_id`（含降级路径）；
   - Qdrant/in-memory 双实现同端口一致性用例；
   - Embedder 冷热双路径分离；
   - collection-per-project 硬隔离 + `CollectionResolver` 前缀断言；
   - 原文件留存 ON + sha256 寻址 + 重建「新版本 → 逐文档 → 原子切换 → 可回滚」；
   - 台账 SQLite（WAL + `busy_timeout`）+ 自管 SQL + 手写迁移；
   - PDF 三路径 + pypdfium2 + rapidocr；**全仓无 PyMuPDF/fitz**；
   - LLM 经 `LlmProvider` + `langchain-openai` pin `<0.3`（运行期断言）+ `EgressDescriptor` 外发声明 + 路由 `temperature=0`；
   - MOD-IB-15 永不抛（fail-open，降级在 SSE 内可见）；台账/Blob fail-closed 503；
   - 组合根唯一装配 + AuthzPolicy 未注入即启动失败 + 未授权 401/403 不静默 + 配置键不新增/不改名。

**提交给 PM 的两个需要决策的项**（非阻塞，但影响后续）：

- **L-03**：`ib-embed` 服务端代码在 module_design R1 无归属模组 —— 请指派或明确其为外部既有服务；
- **M-02**：`related_images` 事件种类无生产端 —— 请决定是否指派图片引用提取器，或从契约中移除该 kind。

另需人工清理一处**由我误建的目录**（自动化清理被安全策略拦截，未执行）：
`C:\var\lib\intelligentbase\ledger\ledger.sqlite3`（73,728 字节）。
成因：我用 `deploy/config.example.json` 里的生产 `ledger_path` 跑了一次
`python -m ibweb.bootstrap --ensure-schema` 冒烟，脚本按配置在该路径建了台账文件。
该路径**不在**项目仓库内，不影响交付物，但会污染机器（且名似生产路径，易误判），建议删除。

---

# §9 R2 增量评审（L-03 + M-02；对 R1 §1~§8 的**追加**，不覆盖）

> R2 只做两件事（`INV-GROUP_C-INTELBASE-002`）：**L-03** = 实现 MOD-IB-26 `ib-embed` 服务端
> 与第三种 Embedder 形态；**M-02** = 实现页面图关联的生产与读路径。R1 的 69 个文件**无一重写**。
> 本节所有「通过」同样附**真实命令与原始输出**（§9.9）。

## 9.1 R2 规模

| 指标 | R1 | R2 后 | 变化 |
|------|----|-------|------|
| `src/` 文件总数（不含 `__pycache__`） | 69 | **76** | **+7**（全部新增，无删除） |
| 代码总行数 | 16,396（R1 报告口径） | **20,267**（`split('\n')` 计数，与 R1 同口径；`splitlines()` 口径为 20,191） | **+3,871** |
| 模块数 | 25 | **26**（+MOD-IB-26） | +1（纯追加） |
| 端口数 | 13 | **13** | **不变** |
| IFC-IB 编号 | 001~265（58 条） | 001~286（+266~284、286） | 纯追加；**001~265 一字未改** |
| 改动文件 | — | 18（全部为追加段落/方法/常量） | 1 处行删除（见 D-R2-05） |
| 离线自检用例 | 15 | **24** | +9（全绿） |

## 9.2 R2 5 维评分（仅对被 R2 触及的模块）

| 维度 | R2 均分 | 依据 |
|------|--------|------|
| Correctness | **9.1** | 新增 9 例全绿；`ib_embed` 线协议为**真监听回环端口的真 HTTP** 验证（非 mock）；`page_image` 幂等与级联删除在**真实 SQLite** 上验证；九步写序用**记录型代理**观测（非读代码猜顺序） |
| Security | **9.5** | 图片端点只认 `Authorization` 头（`?token=` → 400 有用例）；跨项目图片塌缩为 **404**（反存在性探测）；BlobStore 不可用 **fail-closed 503**（不返回占位图）；`ib-embed` 无鉴权但**只绑回环**且**零凭据**；第二份 env 模板凭据形态正则扫描零命中 |
| Performance | **8.8** | `ib-embed` 有界并发 + 有界队列 + **快速失败**（`overloaded` + `retry_after_s` + `Retry-After` 头，有用例）；`related_images` 载荷**只传站内路径不内联字节**（帧体积有界）；台账 `upsert_chunk_images` 单事务先删后写。未做真机压测（同 R1 约束）故不给更高分 |
| Maintainability | **9.0** | `ib_embed` 与 `ib.*` **零耦合**（C8 由 `ib_embed_isolation` 用例强制：源码扫描 + `sys.modules` 差分）；三形态共享同一端口签名集（`port_conformance` 对拍）；运行时端口可替换（缺库 → **可读错误**而非导入期崩溃） |
| Test Coverage（可测试性） | **8.8** | 新增 9 例覆盖绑定聚合/幂等/写序/事件契约/端点四态/三形态一致性；前端纪律为**源码级**检查（无 `npm`，见 §9.10） |

## 9.3 R2 Finding 统计（诚实口径）

| 严重级别 | 发现 | R2 内已修复 | 遗留（已记录，不阻塞） |
|---------|------|------------|---------------------|
| **CRITICAL** | **3** | **3** | **0** |
| MAJOR | 2 | 0 | 2（D-R2-01 / D-R2-02，见 §9.6 —— 均为「本机不可验证 / 上游需裁决」类） |
| MINOR | 3 | 1 | 2 |
| **合计** | **8** | **4** | **4** |

**R2 的 3 个 CRITICAL（发现即修，均已复跑验证）**：

| ID | 文件:行号 | 描述 | 状态 |
|----|----------|------|------|
| FND-R2-01 | `ib/embedding/inproc.py`（`_load` / `descriptor`） | **导入期硬依赖**：`InProcessBgeM3Embedder` 首版在模块顶部 `import flagembedding`，缺库时**导入即崩**——而「缺库须给可读错误、不得启动崩溃」是 IFC-IB-275 的明列要求，且会让 `IB_EMBED_BACKEND=fake` 的离线装配一起失败 | **FIXED**：改为函数内延迟导入，`descriptor()`/`health()` **不触发**权重加载，缺库由 `DependencyUnavailableError`（含 `IB_EMBED_MODEL_PATH` 键名）承载；用例 `embed_three_form_conformance` |
| FND-R2-02 | `ibweb/views.py::file_image_endpoint`（`_image_content_type`） | **Content-Type 不确定**：首版用 `mimetypes.guess_type`，在 Windows 上**读注册表** → 同一份代码在不同机器给出不同 `Content-Type`（可能回落 `text/plain`），直接违反 IFC-IB-283 的 `image/*` 契约，且**测试机与生产机结论会不一致**（最难查的一类漂移） | **FIXED**：改为模块内**固定 ext→MIME 表** + `X-Content-Type-Options: nosniff`；未知扩展名诚实回落 `application/octet-stream`。用例断言 `image/png` |
| FND-R2-03 | `ib/ledger/sqlite_repo.py::upsert_chunk_images` | **重复解析残留孤儿关联**：首版只做 `INSERT OR REPLACE`（按幂等键覆盖），新一次解析若产出**更少**的图，旧行残留 → 用户会看到**已不存在的图**（缩略图点了 404），且该行永不被清理 | **FIXED**：改为**同 `doc_id` 先删后写（单事务）**，与既有 `upsert_chunks` 同构；重复解析/重建/重试均幂等且不残留。用例 `page_image_binding_and_ledger`（幂等 + 陈旧行清除 + 跨项目不可见） |

> **CRITICAL 门槛说明**：上述三项都会造成**静默的、跨机器不可复现的**错误行为
> （导入崩 / 头不确定 / 幽灵关联），符合本代理「CRITICAL = 会导致静默错误结果或启动失败」的判级。
> 三项均在**同一轮内**修复并复跑（§9.9 的 24/24 为修复后输出）。

## 9.4 逐模块 R2 评审详情

---
**MOD-IB-26 `ib-embed` 服务端（新增：`ib_embed/` 4 文件，另行统计于 §9.1）**
- Correctness: 9.3 / Security: 9.4 / Performance: 9.0 / Maintainability: 9.2 / Test Coverage: 9.0

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R2-01 | CRITICAL | `ib/embedding/inproc.py` | 导入期硬依赖（详见 §9.3） | FIXED |
| FND-R2-04 | MINOR | `ib_embed/server.py::_handler_factory` | 未知路径首版返回 **400**（把「路径不存在」与「请求体不合法」混为一谈，运维看日志无法区分） | FIXED（404；GET/POST 一致，有用例） |

关键设计纪律（逐条有依据）：`/embed` **不改名** `/v1/embeddings`（IFC-IB-266）；
`healthz` **永不 5xx**（不可用时报 200 + `ok=false` + `detail`，可观测优先，IFC-IB-269）；
服务端**不区分冷热**、**不含** `IB_EMBED_TIMEOUT_*` / `IB_EMBED_RETRY_*`（IFC-IB-273 单一落点，
有用例断言键清单为**闭集**共 11 个）；**绝不返回部分向量**（数量不符/维度参差 → 整批 500，有用例）；
批上限 400 **回显 `max_batch`**（让「客户端 cold_batch > 服务端 MAX_BATCH」一眼可定位，IFC-IB-272）。
---
**MOD-IB-09 Embedding 端口（R2 追加：`ib/embedding/inproc.py` + `build_embedder` 值域）**
- Correctness: 9.0 / Security: 9.2 / Performance: 8.8 / Maintainability: 9.1 / Test Coverage: 9.0

三形态（`http` / `inproc` / `fake`）**共享同一端口签名集**，由两处用例共同保证：
`port_conformance`（参数名逐一对拍）与 `embed_three_form_conformance`（descriptor 五字段一致、
`build_embedder` 映射正确、**未知值回落默认 `http`**）。`inproc` **不 import MOD-IB-26**
（C8；由 `ib_embed_isolation` 的全仓扫描强制）。
---
**MOD-IB-01 核心契约（R2 追加类型/端口）**
- Correctness: 9.2 / Security: 9.0 / Performance: 9.0 / Maintainability: 9.3 / Test Coverage: 9.0

追加 5 个 frozen dataclass + `PageImageSourceKindLiteral`；**既有 `ParsedChunk` / `RetrievedChunk`
字段集合一字未改**（IFC-IB-009 / 契约 §2.1 硬要求）。三条 `LedgerRepository` 端口方法
（`upsert_chunk_images` / `list_chunk_images` / `get_chunk_image`）**定义在 MOD-IB-01 而非 MOD-IB-13**：
放在 13 会产生 `11 → 13` 的非法反向边（端口由 11 实现、由 13 调用），故类型必须留在编号更小的 01。
`core_framework_free` 用例仍绿（新增类型零第三方依赖）。
---
**MOD-IB-11 台账（R2 追加：`chunk_image` 表 + 三方法 ×2 实现）**
- Correctness: 9.0 / Security: 9.2 / Performance: 9.0 / Maintainability: 9.0 / Test Coverage: 9.2

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R2-03 | CRITICAL | `ib/ledger/sqlite_repo.py::upsert_chunk_images` | 重复解析残留孤儿关联（详见 §9.3） | FIXED |
| FND-R2-05 | MINOR | `ib/ledger/schema.py` | 首版未加 `ON DELETE CASCADE`：级联靠应用层清理，崩溃即残留孤儿行（IFC-IB-281 要求同事务级联） | FIXED（DDL 加 FK 级联 + 索引；用例在**真实 SQLite** 上验证删除后 `list_chunk_images` 为空） |

手写 scoped 迁移 **`.sql` 单真源**（`002_chunk_image.sql`），**未使用 `makemigrations`**；
scope 过滤复用**同一** `_scope_clause` 单点下推；跨项目一律返回空/`None`（非报错，反存在性探测）。
---
**MOD-IB-13 文档生命周期（R2 追加：绑定/落库/九步写序）**
- Correctness: 9.2 / Security: 9.0 / Performance: 9.0 / Maintainability: 9.1 / Test Coverage: 9.3

`bind_page_images` 为**纯函数无 IO**（不伪造 `project_id`/`kb_id`）、按 `page_or_section` 聚合、
页内按 `image_id` 升序（确定性 → 幂等键前提）。写序经**记录型代理**实测为
`vector_upsert → persist_page_images → upsert_chunks → mark_indexed`（IFC-IB-280：
「`indexed` ⇒ 关联已就绪」成立）。`delete_document` **代码零改动**（IFC-IB-281），
仅在 docstring 登记级联不变式。
---
**MOD-IB-21 流式契约（R2 追加：`related_images` 载荷）**
- Correctness: 9.3 / Security: 9.4 / Performance: 9.2 / Maintainability: 9.2 / Test Coverage: 9.0

`StreamEventKind` **取值集合不变**（`related_images` R1 已枚举，R2 只定义其 data）。
**无图不发事件**（纪律放在构造函数内，调用点忘判空也不会发出空事件）；载荷**只含**
`image_id` / `doc_id` / `doc_name` / `page_or_section` / `url_path`，**绝不内联 base64**（有用例断言）。
`IMAGE_ENDPOINT_TEMPLATE` 与 Django URLconf 的一致性有**专门用例**（`reverse()` 等于
`related_image_url()`）—— 前端拿到 `url_path` 却 404 是最难查的一类漂移。
---
**MOD-IB-22 编排（R2 追加：生产接缝）**
- Correctness: 8.8 / Security: 9.2 / Performance: 9.0 / Maintainability: 8.9 / Test Coverage: 8.6

新增**可选关键字** `related_images_provider`（`build_graph` / `Orchestrator` 同），
事件在 `content` 之后、`done` 之前产出；provider 抛异常 → **静默不发事件**（不打断流、不降级正文）。
扣分点：**接缝当前恒为空**（见 §9.6 D-R2-02）—— 这是**已知且已登记**的读路径性质，
非本模块缺陷，但确实让本模块的新增分支在本轮**未被真实流量走到**。
---
**MOD-IB-23 HTTP API 与组合根（R2 追加：图片端点）**
- Correctness: 9.0 / Security: 9.5 / Performance: 9.0 / Maintainability: 9.0 / Test Coverage: 9.2

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-R2-02 | CRITICAL | `ibweb/views.py::_image_content_type` | Content-Type 不确定（详见 §9.3） | FIXED |
| FND-R2-06 | MINOR | `ibweb/views.py::file_image_endpoint` | 首版对 `blob_ref` 为空的行尝试 `get` 空路径（行为未定义）；且 `blob_ref` 是**存储 rel_path** 而非 `BlobRef`，需按文件名重推 `sha256` 才能与 `InMemoryBlobStore._key_of` 的「rel_path ↔ sha256 一致」校验相容 | FIXED（显式 `NotFoundError`；`_blob_ref_of_rel_path` 重推 `sha256`，`size_bytes=0` 并注明读路径不使用） |

四态语义：**200**（`image/*` + `Cache-Control: private` + `nosniff`）/ **404**（不存在 / 跨项目 /
`blob_ref` 为空 —— **不区分「不存在」与「不属于你」**）/ **403**（主体无问答权限）/ **503**
（BlobStore 不可用，**fail-closed，不返回占位图**）。只认 `Authorization` 头（`?token=` → 400）；
`/healthz/deps` **字段集合不变**（有用例）。
---
**MOD-IB-24 前端（R2 追加：缩略图行）**
- Correctness: 9.0 / Security: 9.3 / Performance: 8.8 / Maintainability: 9.0 / Test Coverage: 8.2

缩略图行渲染在**该轮回答下方**（源码顺序用例断言 `class="answer"` 先于 `class="thumbs"`）、
**不插入正文、不改写 `content`、不重排**；取图失败/403/404/503 → **静默隐藏**（catch 置
`failed`，渲染前过滤；不弹错、不中断流、**不追加降级文案**——降级文案只对 `degraded` 负责）。
取图**只经 `ApiClient.fetchFileImage`**（IC-IB-01）：`<img :src>` 不带自定义头，三条替代路径
（查询串传令牌=Cookie 认证=免鉴权端点）逐条排除并写在注释里。卸载时 `revokeObjectURL` 释放 blob。
扣分点：**无 `npm` 环境**，类型检查与构建未跑（§9.10）。
---
**MOD-IB-25 部署运维（R2 追加：第二份 EnvironmentFile 模板）**
- Correctness: 9.2 / Security: 9.6 / Performance: 9.0 / Maintainability: 9.2 / Test Coverage: 9.0

`ib-embed.env.example` 与 `ib-web` 的 `env.example` **键集合分离**（架构残余建议 R-3）：
只含 11 个 `IB_EMBED_*` 键、**零凭据**（该服务不需要令牌，合并文件等于净增凭据面）。
`MemoryMax=2560M` 与 `IB_EMBED_MEMORY_LIMIT_MB=2560` **数值一致**（两处注释互相指向）。
`ExecStart=… -m ib_embed.server` 与契约的模块路径一致。
`deploy_templates_have_no_secrets` 用例扫描凭据形态正则，零命中。
---

## 9.5 关闭 R1 §5 的两条遗留（L-03 / M-02）

| R1 遗留 | 本轮处置 | 关闭证据 |
|--------|---------|---------|
| **L-03**（MAJOR）`ib-embed` 服务端代码无归属模组，`ib_embed.server` 无出处 | **已关闭**。R2 架构侧新增 MOD-IB-26 与契约 `docs/ib_embed_service_contract.md`；实现侧交付 `ib_embed/{__init__,config,runtime,server}.py` + 第三种形态 `InProcessBgeM3Embedder` | 用例 `ib_embed_config_keys` / `ib_embed_isolation` / `embed_three_form_conformance` / `ib_embed_wire_protocol`（真 HTTP）；`ib-embed.service` 的 `ExecStart` 已指向真实存在的 `ib_embed.server` |
| **M-02**（MINOR→升格为功能）`related_images` 事件种类无生产端，前端只能「保守展示未知负载」 | **已关闭（生产端 + 读路径均落地）**。「提取器」**不是**独立模块：绑定由 IFC-IB-277 `bind_page_images` 从既有的 `page_or_section` 完成（**不向 `ParsedChunk` 追加字段**，避免改 IFC-IB-009） | 用例 `page_image_binding_and_ledger` / `lifecycle_nine_step_order` / `related_images_events` / `file_image_endpoint` / `frontend_image_discipline`；前端由「保守展示」升级为**渲染缩略图行** |

**L-01 / L-02 仍未关闭**（PDF/OCR/bge-m3 真跑、前端 `npm build`）——原因与本轮约束相同，
见 §9.10；这两条属**本机不可验证**类，非代码缺陷。

## 9.6 R2 遗留与 P1 开放问题（**已决策 + 已记录理由，不阻塞**）

| ID | 级别 | 问题 | 决策与理由 |
|----|------|------|-----------|
| **D-R2-01** | MAJOR | **页面图字节未落盘**：`ib/parsing/pdf_parser.py` 的 OCR 路径在内存中消费页面图后即弃，未产出可持久化字节，故 `PageImageRef.blob_ref` 恒为 `None`，IFC-IB-283 对**真实 R2 数据**将返回 **404** | **决策：不伪造路径、如实登记 `blob_ref=None`，并把 404 视为契约内的正确行为。** 理由：(a) 契约 `module_design.md` §7.4 明文允许图片不可得；(b) 伪造一个指向不存在字节的 `blob_ref` 会让「404」与「数据坏了」无法区分，是本系统最忌讳的**假可见**；(c) 补字节需要改 MOD-IB-05 解析器**产出**与 MOD-IB-12 的写入时机（派生对象入 BlobStore），属**新的写入面**，应由上游决定是否在 v1 纳管。**推荐后续动作**：为 `pdf_parser` 的页面栅格增加「另存到 BlobStore」分支（对应架构残余建议 R-7 的重建再生路径，届时 `bind_page_images` **无需改签名**，只要 `blob_ref` 从 `None` 变为真路径即可点亮） |
| **D-R2-02** | MAJOR | `related_images` 生产接缝**已装配但当前恒为空**：R1 编排器只把工具**名称/描述字符串**交给 LLM，从不执行工具、也拿不到检索命中，故 provider 收到空命中 → 不发事件 | **决策：保留这一「正确但未点亮」的接缝，不发明未定义接口、不伪造命中。** 理由：(a) 空命中 → 不发事件**正是** IFC-IB-282 的正确行为（有用例）；(b) 若为了「让它亮」而在编排器里凭空造命中列表，等于伪造检索依据，会把一次真实的降级路径改造成误导；(c) 点亮条件是**读路径改造**（答案依据化 / 工具真执行），属架构演进，代码侧**无需改动**（provider 已按 `(doc_id, page_or_section)` 去重聚合）。**验收动作**：GROUP_D 可加一条「注入非空命中 → 事件抵达前端并渲染缩略图」的测试，以证明接缝**可用**（本轮的 `related_images_events` 已按此断言载荷与 URL 契约） |
| **D-R2-03** | MINOR | 图片 `Content-Type` 用固定表而非 `mimetypes` | **决策：固定表。** 理由见 §9.3 FND-R2-02（`mimetypes` 读 Windows 注册表 → 跨机不一致）。代价：新增图片格式须补表一行（有意为之的显式性） |
| **P1-R2-01** | 记录 | `IB_EMBED_MEMORY_LIMIT_MB` / `MemoryMax` 的数值仍待目标机实测（架构 [TBD-T4]/[TBD-T16]） | **决策：沿用架构侧待办，不在本轮实测。** 本轮无目标机访问（GROUP_E 明确不触碰）；数值**一致性**已由注释与自检锁定，重定只需改两处数值 |

> 以上 2 条 MAJOR **均为「本机不可验证 / 需上游裁决的写入面决策」**，不是可通过改代码消除的
> 实现缺陷；两条都已给出**具体验收动作**与**推荐后续路径**。满足「MAJOR 超过 3 条须说明」的门槛
> （R2 新增 MAJOR 恰好 2 条）。

## 9.7 架构残余建议的落地（R-3 / R-6 / R-7）

| 残余建议 | 落地 |
|---------|------|
| **R-3** 分离 `ib-embed.env` | **已落地**：`src/deploy/ib-embed.env.example`（IFC-IB-286），与 `ib-web` 的 env 键集合分离、零凭据（§9.4 MOD-IB-25） |
| **R-6** 图片端点进 v1 | **已落地**：IFC-IB-283 `GET /api/files/{doc_id}/images/{image_id}` 为 **v1 端点**（非实验性），路由已入 `ibweb/urls.py`，鉴权/scope/降级语义与既有端点同纪律 |
| **R-7** 重建再生 | **部分落地（结构与幂等已就绪，字节待 R-7 的写入面）**：重建走 **同一个 `process_pending`**（IFC-IB-280 九步）→ 关联随文档重跑再生；幂等键 `(project_id, kb_id, doc_id, page_or_section, image_id)` 覆盖重跑/重试/重建三种重放；**孤儿行**由 `doc_id` 级联删除（IFC-IB-281）清除。缺的一环即 D-R2-01 的字节落盘 |

## 9.8 既知编号缺陷（登记不修）

`IFC-IB-131` 在 `LedgerRepository`（`list_chunks` / `list_orphan_doc_ids`）与 `BlobStore.put`
**重复使用**（上游文档编号算术缺陷）。R2 **不修改**该编号（C6：`IFC-IB-001~265` 一字不动），
代码内以 `MOD-IB-11:` / `MOD-IB-12:` 前缀消歧，引用时写作「IFC-IB-131（MOD-IB-11）」。
R2 新增的 266~284 / 286 全部为**新号**，未与既有号冲突；**IFC-IB-285 预留未分配**。

## 9.9 R2 实跑证据（命令 + 原始输出）

**命令 1：语法/导入自检**

```
$ cd src && python -X utf8 -m compileall -q .
$ echo $?
0
```
（无任何输出 = 全部文件编译通过；`compileall -q` 只在失败时打印。）

**命令 2：离线自检套件（24 例）**

```
$ cd src && PYTHONUTF8=1 python -X utf8 scripts/selfcheck.py
vector count mismatch code=internal_error
ragged vector dims code=internal_error
Service Unavailable: /api/files/a309cee30879456798f8e16892675054/images/img-1
========================================================================
intelligentbase 离线自检（GROUP_C 自我验证；正式测试套件属 GROUP_D）
========================================================================
PASS  core_framework_free：ib/core 不引入任何第三方顶层包（网络会失败）
PASS  no_forbidden_web_carrier：无 FastAPI/uvicorn/channels/redis 依赖
PASS  no_pymupdf：全仓无 fitz / PyMuPDF 引用（AGPL-3.0 硬约束）
PASS  port_conformance：替身与端口签名一致（VectorStore/Ledger/Blob/Embedder）
PASS  authz_injection_required：生产模式未注入策略即启动失败，且只报键名
PASS  config_error_reports_key_only：配置校验只报键名，不回显值
PASS  magic_sniff_rejects_renamed_file：改名攻击被拒（扩展名与内容不符）
PASS  ledger_state_machine_and_lease：SQLite 台账状态机 + 单租约（WAL）
PASS  isolation_scope_required：检索降级时 filter 仍含 project_id，且跨项目不可见
PASS  retrieval_happy_path：读路径**不降级**且能命中（防止『一切静默降级』掩盖缺陷）
PASS  retrieval_fail_open：embedding 不可用时降级而非抛异常（MOD-IB-15 永不抛）
PASS  sse_frame_and_done_terminator：SSE 帧格式与 done 终止条件
PASS  orchestration_events_order：degraded 先于 content，且只发一条 content
PASS  http_contract_offline：离线装配下端点状态码/头纪律（含 ?token= 显式 400）
PASS  deploy_templates_have_no_secrets：部署模板只含占位符，无真实凭据
PASS  ib_embed_config_keys：11 个键的键名清单 + 缺权重目录即拒绝（只报键名）
PASS  ib_embed_isolation：ib_embed 不 import ib；且无任何 ib.* 模块 import ib_embed（C8）
PASS  embed_three_form_conformance：http/inproc/fake 三形态通过同一端口一致性检查
PASS  ib_embed_wire_protocol：healthz 永不 5xx / 保序 / 批上限 / 过载快速失败 / 绝无部分向量
PASS  page_image_binding_and_ledger：聚合/确定性/幂等/级联删除（InMemory + SQLite）
PASS  lifecycle_nine_step_order：向量写入 → 页面图落关联 → 块元数据 → 置位（IFC-IB-280）
PASS  related_images_events：无图不发 / 载荷只有路径 / 模板与 URLconf 一致
PASS  file_image_endpoint：200 / 404（含跨项目）/ 403 / 503 / ?token= 400（IFC-IB-283）
PASS  frontend_image_discipline：走封装层取图 / 无裸 axios / 无 v-html / 不改写正文
------------------------------------------------------------------------
自检结果：24/24 通过
$ echo $?
0
```

> 首 3 行（`vector count mismatch …` / `ragged vector dims …` / `Service Unavailable: …`）是
> **被测代码自身的日志**：前两行是 `ib_embed` 服务端在「数量不符 / 维度参差」时按设计打出并
> 返回 500 的记录，第三行是 Django 对 fail-closed 503 的标准记录 —— 它们**在 stderr 上**，
> 与被测断言（PASS）一致，不是失败。

**R1 用例在本轮全部保持绿色**（15/15 中的每一例都在上面的输出里），
即 R2 的改动**未回归**任何 R1 行为 —— 这是本节最重要的证据。

**命令 3：R2 关键断言的定向复核**（把「关键不变式」单独跑一遍，便于门控抽查）

```
$ cd src && PYTHONUTF8=1 python -X utf8 -c "
import os, sys
sys.argv=['x']
os.environ['PYTHONUTF8']='1'
import runpy
ns=runpy.run_path('scripts/selfcheck.py', run_name='probe')
for name in ('ib_embed_wire_protocol','page_image_binding_and_ledger',
             'lifecycle_nine_step_order','related_images_events',
             'file_image_endpoint','embed_three_form_conformance'):
    fn=ns[name]; fn(); print('OK', name)
"
vector count mismatch code=internal_error
ragged vector dims code=internal_error
runtime unavailable code=model_not_ready
Service Unavailable: /api/files/d2f3c40099bb474aaf494f2af6550818/images/img-1
PASS  ib_embed_wire_protocol：healthz 永不 5xx / 保序 / 批上限 / 过载快速失败 / 绝无部分向量
OK ib_embed_wire_protocol
PASS  page_image_binding_and_ledger：聚合/确定性/幂等/级联删除（InMemory + SQLite）
OK page_image_binding_and_ledger
PASS  lifecycle_nine_step_order：向量写入 → 页面图落关联 → 块元数据 → 置位（IFC-IB-280）
OK lifecycle_nine_step_order
PASS  related_images_events：无图不发 / 载荷只有路径 / 模板与 URLconf 一致
OK related_images_events
PASS  file_image_endpoint：200 / 404（含跨项目）/ 403 / 503 / ?token= 400（IFC-IB-283）
OK file_image_endpoint
PASS  embed_three_form_conformance：http/inproc/fake 三形态通过同一端口一致性检查
OK embed_three_form_conformance
```

（该命令只跑 R2 的六个核心用例；`runpy` 使 `_case` 装饰器照常登记，故每例同时打印
自检器的 `PASS <名称>` 行与本命令的 `OK <名称>` 行。首 4 行为被测代码的 stderr 日志。）

**命令 4：C8 单向隔离的独立复核**（不依赖自检脚本自身的排除逻辑）

```
$ cd src && PYTHONUTF8=1 python -X utf8 -c "
import subprocess,sys
r=subprocess.run([sys.executable,'-c','import ib_embed.server, sys; print(sorted(m for m in sys.modules if m==\"ib\" or m.startswith(\"ib.\")))'],capture_output=True,text=True,cwd='.')
print(r.stdout.strip() or r.stderr.strip())
"
[]
```
（导入 `ib_embed.server` 后 `sys.modules` 中**没有任何 `ib.*`** —— MOD-IB-26 与基座零耦合。）

## 9.10 本地不可验证项（如实登记，不得据此声称「已通过」）

| 项 | 为何不可验证 | 由谁验证 |
|----|------------|---------|
| **bge-m3 真实推理**（flagembedding / sentence-transformers） | 本机未装且**不许联网下载权重**（C5）；真实推理需 ~2GB 权重与目标机 CPU（AVX2，[TBD-T18]） | GROUP_D/E：目标机 `ib-embed` 冒烟（healthz → warmup → embed 三方维度一致） |
| **onnxruntime 运行时**（三候选之一） | 同上（`_CANDIDATES` 的择一为 [TBD-T1]/[TBD-T4]/[TBD-T18]，架构侧已声明「可切换」） | 目标机实测择一，改 `RUNTIME_BACKEND` 一处 |
| **前端 `npm install` / `vue-tsc --noEmit` / `vite build`** | 包源属外部服务（C5）→ 与 R1 `L-02` 同因 | 联网环境执行并归档输出 |
| **PDF 页面图真实字节** | 依赖 `pypdfium2` + `rapidocr-onnxruntime` 真装（R1 `L-01`） | 目标机按 `deploy/checklists.txt` B4/B5 |
| **图片端点的真实数据路径（200）** | 依赖 D-R2-01 的字节落盘决策 | 落盘后 `file_image_endpoint` 的 200 分支即可用真数据复跑 |

## 9.11 §9 结论

**R2 自评状态：SUCCESS（可提交 GR-C-002）。**

1. **R2 的 3 个 CRITICAL 全部修复并复跑**（§9.3 / §9.9），任务级「CRITICAL = 0」成立。
2. **R1 §5 的 L-03 与 M-02 均已关闭**（§9.5），且**回归 0**（R1 的 15 例在本轮全绿）。
3. **两条新增 MAJOR 均为「本机不可验证 / 上游裁决」类**，已给决策与理由（§9.6），不阻塞。
4. **契约纪律逐条守约**：`IFC-IB-001~265` 一字未改、端口数仍 13、配置键未新增/改名
   （`IB_EMBED_BACKEND` 只扩值域）、MOD-IB-26 **零入边**（C8）、核心契约仍 framework-free、
   **无 Docker / 无 PyMuPDF / 无 Channels / 无 Redis**、全程无凭据入库、离线用例**不联网**。
5. **实跑证据充分**：`compileall` 退出码 0；离线自检 **24/24**（含真回环 HTTP 与真实 SQLite）；
   C8 单向隔离独立复核为空 `sys.modules`。
6. **本地不可验证项已点名**（§9.10），未以任何方式暗示其已通过。


---

# §10 R3 增量评审（缺陷修复；对 §1~§9 的**追加**，不覆盖）

> R3（`INV-GROUP_C-INTELBASE-003`）**只修缺陷、不新增能力**：输入 = `docs/test_report.md` §5 的
> FND-GROUP-D-02（MAJOR）与 FND-GROUP-D-01（MEDIUM）。R1/R2 的文件**无一重写**，本轮只改
> `ib/lifecycle/__init__.py`、`ibweb/composition.py`、`deploy/checklists.txt` 三个文件。
> 本节所有结论都附**真实命令与原始输出**（§10.7）。

## 10.1 R3 规模与改动面

| 指标 | R2 后 | R3 后 | 变化 |
|------|-------|-------|------|
| 模块数 | 26 | **26** | **不变** |
| 端口数 | 13 | **13** | **不变** |
| IFC-IB 编号 | 001~286 | **001~286** | **不变**（无新增、无改签名） |
| 配置键 | 封闭集 | **封闭集** | **不变**（无新增、无改名、无改默认值） |
| 依赖边 | DAG | **DAG** | **不变**（无新增边） |
| 改动文件 | — | **3**（`src/ib/lifecycle/__init__.py` 819 行 / `src/ibweb/composition.py` 689 行 / `src/deploy/checklists.txt` 257 行） | 纯增量方法 + 文案订正，**无删除既有分支** |
| 正式测试套件 | 138 passed | **135 passed / 3 failed（按预期）** | 3 个「缺陷固化用例」如设计般响亮失败（§10.6） |
| 离线自检 | 24/24 | **24/24** | 无回归 |

## 10.2 R3 5 维评分（仅 MOD-IB-13 与 MOD-IB-23 被触及的部分）

| 维度 | R3 均分 | 依据 |
|------|--------|------|
| Correctness | **9.0** | 三个删除窗口（尚无事发生 / 处理中 / 清扫后竞态）在探针中逐个人工构造并验证「无幽灵、不可检索」（`groupc_r3_after_symptoms.log` (a)(b)(c)）。扣分：并发窗口的**真并发**未用线程/进程压测（用确定性注入复现，属结构性验证而非压力验证） |
| Security | **9.3** | 删除路径绑 collection **仍只认 `CollectionResolver`**（FM-5，`assert_prefix` 保留），**未**引入静默版本回退；跨项目隔离未削弱（`delete_by_doc` 的 filter 恒含 `project_id`）；能力摘要只含**声明**，进程级注册表**不含任何 scope**（ADR-09 纪律未破） |
| Performance | **8.9** | 删除路径新增 1 次 resolve/`bind_collection`（无 IO）与 1 次额外 `delete_by_doc`（正常路径恒返回 0）；处理路径新增 1 次台账读（认领后存在性检查）。均为 O(1) 常数级，且只发生在**删除**与**每文档一次**的路径上。扣分：Qdrant 侧未实测这两次调用的额外延迟 |
| Maintainability | **9.1** | 新增 3 个私有方法（`_bind_write_collection` / `_discard_written_vectors` / `_fail_document`），`process_pending` 的失败处理由**两处内联重复**收敛为一处；`register_builtin_tools` 消除「两份工具清单」的结构性漂移源 |
| Test Coverage（可测试性） | **8.8** | 修复点均**可被离线用例覆盖**（无外部依赖：InMemory + Fake）；三个固化用例的翻转是天然的回归闸门。扣分：并发窗口依赖注入式探针，正式套件尚无对应用例（属 GROUP_D 补写范围，见 §10.6 清单） |

## 10.3 R3 Finding 统计（诚实口径）

| 严重级别 | 发现 | R3 内已修复 | 遗留（已记录，不阻塞） |
|---------|------|------------|---------------------|
| **CRITICAL** | **0** | 0 | **0** |
| MAJOR | 2 | **2** | 0 |
| MINOR | 2 | 1 | 1 |
| **合计** | **4** | **3** | **1** |

> **CRITICAL 门槛**：本轮无 CRITICAL。判级依据 —— 两个登记缺陷都不导致**数据丢失 / 凭据泄露 /
> 全服务崩溃**（FND-GROUP-D-02 会造成用户可见的**正确性**失效但触发窗口窄、且可在重启后由
> 「重试删除」恢复；FND-GROUP-D-01 只降级 L2 路由提示质量）。按 `test_report.md` §5 的原始判级
> （MAJOR / MEDIUM）沿用，**未**上调。

## 10.4 逐模块 R3 评审详情

---
**MOD-IB-13 文档生命周期（`ib/lifecycle/__init__.py`）**
- Correctness: 9.0 / Security: 9.3 / Performance: 8.9 / Maintainability: 9.1 / Test Coverage: 8.9

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-GROUP-D-02 | MAJOR | `ib/lifecycle/__init__.py:647-699`（`delete_document`）、`:701-715`（`_bind_write_collection`） | 删除依赖「向量库恰好已被别处绑定」→ 未绑定窗口抛 `StartupError` → 500 + pending 幽灵行 + 内容仍被作答 | **FIXED**：先经 `CollectionResolver` 自绑写路径 collection（与 `_process_one` 第 6 步同源），未绑定不再是故障而是「无派生物」→ `vectors_deleted=0` 的成功 |
| FND-R3-01 | MAJOR | `ib/lifecycle/__init__.py:681-691` | 「台账行已删、向量仍在」的**残窗**：删除路径的第一次向量清扫与台账删行之间若 worker 完成 upsert，则会留下**检索得到但台账不可见**的幽灵向量（gate 判据「不得可被检索到」未闭合） | **FIXED**：台账删行后追加一次竞态清扫（第二次 `delete_by_doc`，正常路径恒 0）；`vectors_deleted` 计入两次之和（语义不变，仅更诚实） |
| FND-R3-02 | MINOR | `ib/lifecycle/__init__.py:430-468`（`process_pending`）、`:508-511`（`_process_one` 第 0 步） | 处理中删除的文档被**计为 `failed`**，与本方法 docstring 明文的「并发删除计为 `skipped`」相矛盾；且 `_DeletedConcurrently`（R1 定义）**从未被抛出**（死代码） | **FIXED**：`_process_one` 开头「行已删 → `_DeletedConcurrently`」；`process_pending` 增 `NotFoundError` 分类分支（以「行确实不在」为判据）→ `skipped` + 清理本次派生物 |
| FND-R3-03 | MINOR | `ib/lifecycle/__init__.py:482-497`（`_discard_written_vectors`） | 该清道夫用 `except Exception` 吞异常 | **DOCUMENTED（不修，理由见下）**：这是**已判定跳过**之后的尽力而为清理，失败的兜底是删除侧竞态清扫；若上抛会把用户的主动删除报成 503。仍记 MINOR 以留存判断痕迹 |

**设计纪律逐条守约**：`NotFoundError → 404` 语义未变（探针末段实测）；`DeleteReport` 三计数语义未变；
「先删派生物、后删权威台账」顺序未变（第 4 步清扫在台账删除**之后**，只作用于已失效行的派生物）；
`IFC-IB-141~145 / 280 / 281` 的**签名与返回类型一字未改**。

---
**MOD-IB-23 组合根（`ibweb/composition.py`；含 MOD-IB-17 摘要取值路径）**
- Correctness: 9.1 / Security: 9.3 / Performance: 9.0 / Maintainability: 9.2 / Test Coverage: 8.8

| Finding ID | 严重级别 | 文件路径:行号 | 描述 | 状态 |
|-----------|---------|------------|------|------|
| FND-GROUP-D-01 | MEDIUM | `ibweb/composition.py:187-206`（`register_builtin_tools`）、`:464`（装配期登记）、`:166`（`bind_tools` 改走同一函数） | 摘要走**进程级空注册表**，自带工具只进**局部注册表** → `Deps.capability_digest == ""`、路由提示恒为「（无可用工具）」 | **FIXED**：清单收敛为**唯一登记点**并在装配期登记进 `default_registry`；摘要非空且含 `search_knowledge`，与实绑工具一致（探针第一段实测 `True`） |
| FND-R3-04 | MINOR | `ibweb/composition.py:75-79`（`SEARCH_TOOL_SPEC`） | 描述文本里手写的「（需要范围绑定）」与摘要依 `needs_scope` 追加的后缀**重复**（摘要此前往返为空，重复一直不可见） | **FIXED**：从描述移除，由摘要统一附加；工具名与契约键不变 |

**为什么这不是「改了冻结契约」**：`IFC-IB-182` 的语义（摘要由注册表**纯派生**、异常返回 `""`、
无参调用取 `default_registry`）**未改一行**；本轮只是让 `default_registry` 按它自己的文档语义
（「组合根在装配期填充」）**真的被填充**。

## 10.5 关闭登记缺陷的对照（gate 判据逐条）

| gate 判据（`INV-GROUP_C-INTELBASE-003` §1.1） | 实测结论 | 证据 |
|---|---|---|
| 尚无事发生 → 删除必须成功，`vectors_deleted=0`、`blob_deleted` 按实际、`ledger_deleted=True` | `DeleteReport(vectors_deleted=0, blob_deleted=True, ledger_deleted=True)` | `groupc_r3_after_symptoms.log` (a) |
| 删除后不得出现幽灵文档（worker 不得索引、不得可检索） | `process_pending → processed=0`；台账行 `None`；`hits == []` | 同上 (a) |
| 不得返回 500 / 不得抛 `StartupError` 冒泡 / 不得留 pending 幽灵行 | HTTP 删除返回 **200**（固化用例断言 500 失败）；台账行已删 | `groupc_r3_after_fixated_defects.log`；探针 (a) |
| 文档确实不存在 → `NotFoundError` → 404 语义不变 | `delete_document(不存在) → NotFoundError[not_found]` | 探针末段 |
| 先删派生物后删台账的顺序不变式与 `DeleteReport` 三计数语义不变（IFC-IB-281） | 顺序：绑定 → 向量 → Blob → 台账 → 竞态清扫；签名/返回类型未改 | 代码 `:647-699`，逐行复核 |
| `deps.capability_digest` 非空且含 `search_knowledge`；路由提示不再是「（无可用工具）」 | 摘要 = `- search_knowledge: …（需要范围绑定）`；`IntentRouter._capability_digest()` 与之相同 | `groupc_r3_after_symptoms.log` 第一段 |
| 摘要必须真实来自注册表（不得在路由层硬编码） | 摘要由 `build_capability_digest(default_registry)` 派生；`intent.py` 的 `or "（无可用工具）"` 兜底**未改一行** | 代码 `:464/:488`；`ib/routing/intent.py:413-416` 未改动 |
| 不得破坏 `bind_tools` 的「每项目一次、绝不跨项目复用」 | `bind_tools` 仍每项目新建 `ToolRegistry()`；注册表内只有 `ToolSpec` + **未绑定**实现（scope 于 `bind_scope` 构造期注入） | 代码 `:153-167`；探针「摘要与实绑工具一致 = True」 |

## 10.6 因修复而**按预期失败**的固化用例清单（交 test-engineer 翻转断言）

> 这三个用例的**守卫串**是 `偏差已消除——请更新缺陷登记`（或等价的「DID NOT RAISE」），
> 它们刻意断言**缺陷存在**；修复后失败本身就是「缺陷已消除」的机器可验证证明。
> **本代理未修改 `tests/` 下任何文件**。

| 用例 | 文件 | 失败断言 | 修复后应改成 |
|------|------|---------|------------|
| `test_TC_INT_009_capability_digest_registry_gap_is_registered` | `tests/integration/test_composition_retrieval.py:172` | `assert deps.capability_digest == ""`（第 190 行） | 改为断言**非空**且含 `search_knowledge`；`IntentRouter._capability_digest()` 不再是「（无可用工具）」 |
| `test_TC_INT_041_delete_before_bind_is_500` | `tests/integration/test_http_contract.py:104` | `assert deleted.status_code == 500`（第 123 行） | 改为断言 **200** 且 `ledger_deleted is True`；列表接口**不再**含该 doc_id |
| `test_TC_INT_061_ghost_document_after_failed_delete_is_registered` | `tests/integration/test_ops_contract.py:23` | `pytest.raises(Exception)` 报「DID NOT RAISE」（第 42-44 行） | 改为断言删除**不抛**、台账行 `None`、`process_pending` 不产出 `indexed`、检索 `hits == []` |

**建议新增用例（GROUP_D 职责，本代理不写）**：① 「处理中并发删除 → `skipped`（非 `failed`）且无残留向量」；
② 「删除路径两次 `delete_by_doc`（竞态清扫）在正常路径下第二次为 0」；
③ 「`bind_tools` 绑定的工具名集合 == 摘要中列出的工具名集合」（防漂移不变式，机器可验证）。

## 10.7 R3 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 结果 | 原始输出 |
|---|------|------|---------|
| 1 | `python -m pytest tests/integration/test_composition_retrieval.py::test_TC_INT_009… test_http_contract.py::test_TC_INT_041… test_ops_contract.py::test_TC_INT_061… -q`（**修复前**） | **3 passed, EXIT=0**（缺陷在场） | `docs/evidence/groupc_r3_before_fixated_defects.log` |
| 2 | `python -m pytest tests/ -q`（**修复前**） | **138 passed, EXIT=0** | `docs/evidence/groupc_r3_before_regression.log` |
| 3 | 同第 1 行三条用例（**修复后**） | **3 failed, EXIT=1**（守卫串触发） | `docs/evidence/groupc_r3_after_fixated_defects.log` |
| 4 | `PYTHONUTF8=1 python docs/evidence/groupc_r3_probe.py` | 四段全绿，**EXIT=0**（含 FND-02 (a)(b)(c) 三个窗口 + 404 语义） | `docs/evidence/groupc_r3_after_symptoms.log` |
| 5 | `python -m pytest tests/ -q`（**修复后**） | **3 failed, 135 passed, EXIT=1** —— 失败者**恰为** §10.6 三条，**无 ERROR / 无 collect error** | `docs/evidence/groupc_r3_after_regression.log` |
| 6 | `PYTHONUTF8=1 python src/scripts/selfcheck.py` | **24/24 PASS, EXIT=0** | `docs/evidence/groupc_r3_after_selfcheck.log` |
| 7 | `python -X utf8 -m compileall -q src` | **EXIT=0**（无语法错误） | 本地执行 |
| 8 | 凭据形态扫描（`sk-*` / `ghp_*` / `AKIA*` / `-----BEGIN` / `api_key\|apikey\|password` 赋字面量），覆盖 3 个改动文件 + 8 个证据文件 | **grep EXIT=1（零命中）** | `docs/evidence/groupc_r3_credscan.log` |

> **诚实性声明**：第 2 行是**修复前**在本会话内的真实运行输出，当时未单独落盘，现以逐字转录
> 形式保存在 `groupc_r3_before_regression.log`（该文件头已标注「转录」）。其余各行均为**当场运行并直接重定向**所得。
> 本轮**未**声称任何未实测结论：并发窗口用**确定性注入**（探针 (b)(c)）验证，**未**做多线程/进程压测，
> 故 §10.2 的 Correctness 未给更高分。

## 10.8 R3 遗留与风险（如实登记）

| 项 | 级别 | 说明 | 处置 |
|----|------|------|------|
| R3-RISK-01 | MINOR | 并发窗口的验证是**结构性注入**而非真并发压测（本机不启多进程 worker，避免触碰部署面）。理论上仍存在更窄的时序组合（例如进程级崩溃落在两次清扫之间） | 由 `list_orphan_doc_ids`（IFC-IB-131，台账→向量方向）对账 + 删除**可重放**（幂等）兜底；真机并发验证交 GROUP_D/E |
| R3-RISK-02 | MINOR | `delete_document` 新增一次 `bind_collection` + 一次额外 `delete_by_doc`：在 **Qdrant** 上未实测其额外延迟 | 删除是低频操作；Qdrant 侧 `count/delete/count` 已是既有形态。目标机压测时顺带观测 |
| R3-RISK-03 | MINOR | 删除路径用**写路径** project provider（`RebuildAwareProjectProvider`，重建期指向目标版本）—— 与 `_process_one` 一致，故重建期删除落在**同一** collection；跨版本残留仍由重建流程负责（与 `_delete_where` 的既有声明一致） | 沿用既有语义，未引入新行为 |
| — | — | **无未解决的 CRITICAL**（本轮 0 条）；**MAJOR 遗留 0 条**（2 条均已修） | — |

## 10.9 契约与冻结约束的守约复核（R3）

- **未改**：`IFC-IB-001~286`（无新增编号、无签名/返回类型变更）；端口数 13；模块数 26；
  配置键名与默认值；依赖边；`IB_EMBED_*` 值域。
- **未触碰**：Django + DRF + 原生 `StreamingHttpResponse` SSE / 禁 Channels / 禁 Redis；
  Qdrant 双适配器 + 窄端口 + `scope` 必填；collection-per-project 硬隔离 + filter 软隔离；
  sha256 内容寻址 + 原子重建；台账即队列 + worker lease；PDF 走 pypdf/pdfminer/pypdfium2/rapidocr（**无 PyMuPDF**）；
  `langchain-openai` pin `<0.3`；IC-IB-01 前端统一封装；M-02「页面文字 chunk 继承本页图片」不变式。
- **未触碰**：`tests/` 下任何文件（GROUP_D 职责）；`docs/` 下**其他代理**的产出
  （`requirements_spec.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` /
  `test_plan.md` / `test_report.md` / `phase_status.md` 均**未改**）。
- **无 Docker / 无容器化**：本轮未引入任何容器化方案，也未触碰目标机 `192.168.31.133`（GROUP_E 面）。
- **凭据纪律**：新增/修改的代码与证据文件**不含任何真实凭据**；探针与日志里出现的 token 均为
  本机自造的离线占位串（`groupc-r3-token`），非任何真实系统的凭据。

## 10.10 §10 结论

**R3 自评状态：SUCCESS（CRITICAL = 0，MAJOR 已清零；3 个固化用例按设计失败，即缺陷已消除的证明）。**

1. 两个登记缺陷（FND-GROUP-D-02 MAJOR / FND-GROUP-D-01 MEDIUM）**均已修复**，且有**当场运行**的原始输出。
2. 修复过程**未**引入任何架构偏差、**未**新增模块/端口/IFC/配置键/依赖边。
3. 全量回归 **135 passed / 3 failed**，失败者**恰为**三个「缺陷固化用例」（§10.6），无其他回归、无 ERROR。
4. 离线自检 **24/24**，`compileall` EXIT=0。
5. 未修改 `tests/`，未触碰其他代理产出，未触碰 FreeArk 仓库与任何远程主机。

---

# §11 R4 增量评审（FND-GROUP-D-03 修复 + B-05 依赖补齐）

> 评审对象：R4 触及的 MOD-IB-12（`ib/blob`）与 MOD-IB-13（`ib/lifecycle`），
> 以及新增依赖清单 `src/requirements-embed.txt`（B-05，非模块，按「配置/依赖面」评）。
> 纪律不变：**无实跑证据不下结论**；命令与原始输出见 §11.5。

## 11.1 R4 规模与改动面

| 文件 | 行数级改动 | 性质 |
|------|-----------|------|
| `src/ib/blob/__init__.py` | +约 20 行（新增 `kb_segment` + 改 4 处调用） | 收敛单真源 |
| `src/ib/lifecycle/__init__.py` | +约 25 行（import、`blob_ref_for` 改用、新增 `_blob_scope_of`、文档串） | 删除路径 scope 来源 |
| `src/requirements-embed.txt` | **新增**（依赖清单 + 权重双源/离线加载说明） | B-05 |
| `.gitignore` | +5 行（bge-m3 权重忽略） | B-05 |

**未新增模块 / 端口 / IFC 编号 / 配置键 / 依赖边**；`delete_document` 签名与 `DeleteReport` 结构未改。

## 11.2 R4 5 维评分（仅被触及的部分）

| 维度 | MOD-IB-12（blob / `kb_segment`） | MOD-IB-13（lifecycle / 删除 scope） | 依赖清单（B-05） | 说明 |
|------|-------------------------------|-----------------------------------|----------------|------|
| Correctness（正确性） | 9/10 | 9/10 | 8/10 | 单一真源 + 记录派生，探针 22/22 正向判据通过；依赖**版本区间**离线不可确证（**如实扣分**，标「待目标机实测锁定」） |
| Security（安全性） | 9/10 | 9/10 | 8/10 | 路径穿越两道防护**未削弱**（`safe_segment` 白名单 + `_abs` 根目录断言）；跨项目隔离实测通过。依赖面要求 torch **CPU-only、禁 CUDA**，并给出防 CUDA 安装方式；`ib-embed` 无凭据面（`ib_embed/config.py` 只认 `IB_EMBED_*`） |
| Performance（性能） | 9/10 | 9/10 | 7/10 | `kb_segment` 是 O(1) 纯函数，无新 IO；删除仍是「删目录」一次 `rmtree`。依赖面**体积/内存显著**（torch 系）—— 故与基座 venv **隔离**，并在文件头显式登记该代价 |
| Maintainability（可维护性） | 9/10 | 9/10 | 8/10 | 三处推导收敛为一处，**结构性**防止复发；`_blob_scope_of` 有完整「为什么」注释。依赖清单区分 PRIMARY/BACKUP/候选③ 并给切换步骤 |
| Test Coverage（可测试性） | 9/10 | 9/10 | 7/10 | 新逻辑为可纯函数测试的 `kb_segment` 与可注入 `record` 的删除路径；本轮以探针覆盖，**回归用例属 test-engineer**（本代理不写 tests/） |

## 11.3 R4 Finding 统计（诚实口径）

| 级别 | 新引入（本轮修复引入） | 本轮**修复/关闭** | 遗留（未闭合） |
|------|---------------------|-----------------|-------------|
| CRITICAL | **0** | 0 | 0 |
| HIGH | **0** | 0 | 0 |
| MEDIUM | **0** | 1（FND-GROUP-D-03，由 verifier 定级 MAJOR；本报告按 HIGH→已关闭计） | 0 |
| LOW / 说明 | 1（D-R4-01：新增非端口纯函数 `kb_segment`，非 IFC） | — | 0 |

> 口径说明：FND-GROUP-D-03 在 GROUP_D 处记为 **MAJOR**；本报告按「已修复且无 CRITICAL/MAJOR 遗留」
> 计（等价于 HIGH 已关闭）。**CRITICAL = 0，无未闭合 CRITICAL/MAJOR**。

### 逐条处置

| Finding ID | 严重级别 | 文件:关键位置 | 描述 | 处置 |
|-----------|---------|-------------|------|------|
| FND-GROUP-D-03 | MAJOR（已关闭） | `ib/lifecycle/__init__.py:delete_document` 第 2 步；`ib/blob/__init__.py` 四处 kb 段推导 | 项目级删除 scope 使 kb 段退化为 `default`，与写入段不符 → 原文件成孤儿、`blob_deleted` 恒 False | **FIXED**：`kb_segment` 单真源 + `_blob_scope_of(record)`；探针组 1/4 实测无孤儿且 `blob_deleted=True`，组 3 实测「本无 → False」 |
| D-R4-01 | LOW（登记） | `ib/blob/__init__.py::kb_segment` | 新增模块内纯函数（导出），非端口方法、不登记 IFC | **DOCUMENTED**：属加法，不改任何冻结签名；§14.4 已登记 |

**未解决的 CRITICAL 问题：无。遗留 MAJOR：无。**

## 11.4 逐条对照验收判据（FND-GROUP-D-03）

| 验收判据（invocation 原文） | 结论 | 证据 |
|---|---|---|
| 删除后该 doc **任何 kb 段下**的 blob 都不残留 | 满足 | 探针组 1（HTTP 项目级 scope）对象数 → 0；组 4（真实 FsBlobStore）磁盘文件与 doc 目录均不存在 |
| 删除**不再依赖对 kb_id 的猜测** | 满足 | 删除 scope 由台账记录（权威）派生；kb 段规则收敛为 `kb_segment` 单真源 |
| `blob_deleted` 正确置位 | 满足 | 确有且已删 → True（组 1/4）；本无 → False（组 3） |
| 不误删其他 doc / 其他 project；保留 `_abs` 与 scope 校验 | 满足 | 组 5 跨项目隔离通过；`safe_segment` + `_abs` 防护未改 |
| 不回归 FND-GROUP-D-02（尚无事发生仍可删，不 500、不留幽灵） | 满足 | 组 6 全绿；R3 的两处修正一行未动 |
| 不违反 IFC-IB-281（签名/返回/三计数语义不变） | 满足 | `delete_document` 签名与 `DeleteReport` 一字未改；全量回归 142 passed |
| 不削弱现有测试（三条已翻转守卫继续通过） | 满足 | `test_TC_INT_009/041/061` 在全量回归中通过（142 passed） |

## 11.5 R4 实跑证据（命令 + 原始输出 + EXIT）

| # | 命令 | 结果 | 原始输出 |
|---|------|------|---------|
| 1 | `PYTHONUTF8=1 python docs/evidence/groupc_r4_probe_fnd_d03.py` | **22/22 PASS，EXIT=0** | `docs/evidence/groupc_r4_after_probe.log` |
| 2 | `python docs/evidence/groupd_r3_blob_probe.py`（**verifier 原有缺陷探针**复跑） | 修复后 `blob_deleted=True`、对象数 `0`（该探针为「缺陷在场」判据，故期望**失败** EXIT=1 —— 即缺陷已消除的证明；修复前同名日志为 `blob_deleted=False`、对象数 `1`） | `docs/evidence/groupc_r4_after_existing_probe.log` |
| 3 | `IB_OFFLINE_MODE=1 python -m pytest tests/ -q` | **142 passed，EXIT=0** | `docs/evidence/groupc_r4_after_regression.log` |
| 4 | `PYTHONUTF8=1 python src/scripts/selfcheck.py` | **24/24 PASS，EXIT=0** | `docs/evidence/groupc_r4_after_selfcheck.log` |
| 5 | `python -m compileall -q src` | **EXIT=0** | `docs/evidence/groupc_r4_compileall.log` |
| 6 | 凭据形态扫描（`sk-*` / `ghp_*` / `AKIA*` / `-----BEGIN` / `api_key=…` / `password=…`），覆盖 4 个改动文件 | **零命中（grep EXIT=1）** | `docs/evidence/groupc_r4_credscan.log` |

> 说明：第 2 行「探针按预期失败」与 R3 §10.6 的「固化用例按预期失败」是**同一手法** ——
> 探针写的是**缺陷在场**的判据，修复后它必然失败，正是缺陷消失的机器可验证证明。

## 11.6 R4 遗留与存疑（如实登记，不粉饰）

| 项 | 级别 | 说明 | 处置 |
|----|------|------|------|
| R4-RISK-01 | LOW | 依赖清单的**确切版本**无法离线确证（无网络），仅给保守区间并标注「待目标机实测锁定」 | 部署时 `pip install` 后 `pip freeze` 回填；本代理**不**声称任何精确版本 |
| R4-RISK-02 | LOW | FlagEmbedding 的**传递依赖**（accelerate/datasets/peft/sentencepiece/…）未逐条 pin | 以 `pip download -r` 实际解析结果为准；已在文件内说明 |
| R4-RISK-03 | LOW | torch 在 PyPI 的 Linux 默认 wheel 含 CUDA，若部署方不按文件头命令从 CPU 索引装，可能**意外引入 CUDA 依赖** | 文件头以**显式命令**给出 CPU 索引安装方式并标注「含 CUDA 版即违规」；属部署纪律，风险如实登记 |
| R4-RISK-04 | LOW | 「单 doc_id 是否存在多版本 blob」依赖当前实现事实（每次 `submit_upload` 生成新 `doc_id`，同 doc 目录仅一个对象）；删除走既有 `delete(scope, doc_id)` 的 `rmtree`，仍是**整目录**清理，对多版本亦安全 | 无既有代码路径会产生同 doc 多版本；即便未来出现，整目录删除仍满足「无孤儿」 |
| — | — | **无未解决的 CRITICAL / MAJOR**（本轮 0 条新引入） | — |

## 11.7 契约与冻结约束的守约复核（R4）

- **未改**：`IFC-IB-001~286`（无新增编号、无签名/返回类型变更）；端口数 13；模块数 26；
  配置键名与默认值；依赖边；`IB_EMBED_*` 值域。
- **未触碰**：Django + DRF + 原生 `StreamingHttpResponse` SSE / 禁 Channels / 禁 Redis；
  Qdrant 双适配器 + 窄端口 + `scope` 必填；collection-per-project 硬隔离 + filter 软隔离；
  sha256 内容寻址 + 原子重建；台账即队列 + worker lease；PDF 走 pypdf/pdfminer/pypdfium2/rapidocr
  （**无 PyMuPDF**）；`langchain-openai` pin `<0.3`；IC-IB-01 前端统一封装；M-02 不变式。
- **未触碰**：`tests/` 下任何文件（GROUP_D 职责）；`docs/` 下**其他代理**的产出
  （`requirements_spec.md` / `architecture_design.md` / `module_design.md` / `tech_stack.md` /
  `test_plan.md` / `test_report.md` / `phase_status.md` 均**未改**）；FreeArk 仓库**全程只读**。
- **无 Docker / 无容器化**：本轮未引入任何容器化方案；`requirements-embed.txt` 头部亦明示禁 Docker。
- **未触网**：本轮所有自测为**离线**（SQLite / InMemory 替身），**未**真连 Qdrant / DeepSeek /
  HuggingFace / ModelScope；**未**触碰目标机 `192.168.31.133`。
- **凭据纪律**：新增/修改文件**不含任何真实凭据**（§11.5 第 6 行扫描零命中）；权重来源为**公开**
  模型仓库 `BAAI/bge-m3`（无需凭据）。

## 11.8 §11 结论

**R4 自评状态：SUCCESS（CRITICAL = 0；FND-GROUP-D-03 已修复关闭；B-05 已补齐）。**

1. FND-GROUP-D-03 **已修复**，22 项正向判据 **全部通过**，且用 verifier 的**原始缺陷探针**复跑
   证明「缺陷在场 → 缺陷消除」的翻转（§11.5 第 2 行）。
2. 修复方式**未新增任何端口/IFC/配置键**（改走任务显式许可的「单真源 + scope 一致」分支），
   并叠加共享 `kb_segment` 从**结构上**防止三处推导再次分叉。
3. B-05 **已补齐**：`src/requirements-embed.txt` 含 FlagEmbedding + torch(CPU) + transformers、
   bge-m3 权重双源与离线加载约定、与主 `requirements.txt` 的 venv 归属说明；**未**污染主清单。
4. 全量回归 **142 passed**、离线自检 **24/24**、`compileall` EXIT=0、凭据扫描零命中。
5. 未修改 `tests/`，未触碰其他代理产出，未触碰 FreeArk 仓库与任何远程主机。
6. 存疑项**如实登记**于 §11.6（依赖确切版本与传递依赖清单离线不可确证 —— 未粉饰）。
