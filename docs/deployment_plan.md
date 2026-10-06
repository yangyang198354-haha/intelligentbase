<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-DP-001 |
| 标题 | intelligentbase 智能知识库基座 —— 生产部署计划 |
| 产出代理 | devops-engineer (author_agent) |
| 调用 ID | INV-GROUP_E-INTELBASE-005（**REV-14 增量**；前序 -004 / -002 / -003） |
| 项目 | intelligentbase |
| 阶段 | GROUP_E / **PHASE_10（部署计划，仅计划）**；PHASE_11（实际部署）**PENDING，禁止执行** |
| revision | **REV-14**（R13 回归缺陷修复：全局管理员「当前项目」选择与 `X-IB-Project` 传播；前端产物替换 + 后端新端点，**无迁移**） |
| 版本 | **1.3.0**（REV-14 增量；在 1.2.0/REV-13 之上追加 R14 部署面，见 §14） |
| status | **APPROVED**（1.3.0/REV-14 经 **GR-E-005 = PASS_WITH_CONDITIONS** 门控通过，仅计划层；GR-E-001 对 R4 前版本有效、GR-E-002 对 1.1.0 有效、GR-E-003 对 1.1.1/R10 有效、GR-E-004 对 1.2.0/REV-13 有效）。**PHASE_11 实际部署仍 PENDING/冻结**，须用户明确 `PRODUCTION_DEPLOY_CONFIRM=true` |
| 创建日期 | 2026-09-26 |
| 更新日期 | 2026-10-06（REV-14 增量） |
| 目标机 | `192.168.31.133`（Ubuntu 26.04 LTS / x86_64 / i7-3770S 4C8T / 11 GiB / 78 GiB 可用 / GTX 960 弃用） |
| 上游输入 | `docs/architecture_design.md`(**1.6.0/REV-14**，ADR-28 + §2.0.5)、`docs/module_design.md`(**1.6.0/REV-14**，IFC-IB-333~336)、`docs/tech_stack.md`(**1.4.0/REV-13**，**NO_CHANGE**)、`docs/ib_embed_service_contract.md`(1.0.0/R2)、`docs/implementation_plan.md`(**2.9.0/R14**)、`docs/test_plan.md`(**1.9.0/R14**)、`docs/test_report.md`(**1.10.0/R14**，§19)、`docs/code_review_report.md`、`docs/phase_status.md`（GR-B-007 / GR-C-010 / GR-D-011）、`docs/rev14_project_context_apply_package.md`、`src/deploy/**`（含 **`migrations/003_accounts.sql`**、**`nginx/intelligentbase.conf.example`**）、`src/requirements*.txt`（含 **`bcrypt>=4,<5`**）、`src/ibweb/{views,urls}.py`、`src/frontend/**`（均**只读**） |
| 凭据纪律 | 本文件**不含任何真实凭据 / 口令 / 令牌**；凡涉及凭据一律写「经环境变量 / EnvironmentFile 注入」；目标机 SSH 口令**不记录** |
| 执行门控 | 任何目标机写操作（SSH 写 / rsync / scp / apt / pip / systemctl / 服务启动）**在收到 PM 的 `PRODUCTION_DEPLOY_CONFIRM=true` 之前一律禁止**；本轮为纯文档产出，**未连接、未触碰目标机** |

> **冻结决策遵循声明**：本计划的每一条都以下列已冻结决策为准，不拟改。① 后端 Django 5.x + DRF + Waitress/Gunicorn，流式用 Django 原生 `StreamingHttpResponse` 原生 SSE，**不引 Channels / 不引 Redis**；② Qdrant collection-per-project 硬隔离 + payload filter 软隔离，向量端口 11 方法、`scope` 必填；③ bge-m3 `dim=1024`，独立常驻服务 `ib-embed`（形态可逆），**CPU-only**；④ PDF 走 pypdf + pdfminer.six + pypdfium2 + rapidocr-onnxruntime，**严禁 PyMuPDF/fitz**；⑤ `langchain-openai>=0.2,<0.3` 且**装配期 fail-fast 断言**；⑥ 云端 LLM = DeepSeek，凭据只走环境变量；⑦ **禁 Docker**，物理机裸装 + systemd 直管；⑧ 代码交付 `git pull`，**禁 pscp 逐文件上传**。
>
> **本轮纪律**：本计划**不执行任何步骤**。所有命令均为**待 PM 确认后**由执行人（或 PHASE_11 的部署代理）在目标机上执行的**计划内容**，不是已执行记录。

> **REV-13 增量声明（前轮，INV-GROUP_E-INTELBASE-004）**：本文件为 **PHASE_10 计划层增量**——**仅更新计划**。**未连接、未触碰目标机 `192.168.31.133`**；**未执行任何 SSH / 写操作 / `git clone` / `apt` / `pip` / `systemctl` / `nginx` 写 / 文件上传**；**未 commit / push**；**未改 `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md`**；**未触发 PHASE_11**（本代理**未**、也**不得**自赋 `PRODUCTION_DEPLOY_CONFIRM`）。R13 增量内容见 **§13**，**所有命令须 PM CONFIRM 后执行**。

> **REV-14 增量声明（本轮，INV-GROUP_E-INTELBASE-005）**：本文件为 **PHASE_10 计划层增量**——**仅更新计划，未执行任何部署**。**未连接、未触碰目标机 `192.168.31.133`**；**未执行任何 SSH / 写操作 / 连接 / 安装 / 服务启停 / `nginx` 写 / 文件上传**；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改 `src/**` 实现代码 / `tests/**` / 设计真源四文档（`architecture_design.md` / `module_design.md` / `tech_stack.md` / `requirements_spec.md`）/ `user_stories.md` / `docs/phase_status.md` / `docs/test_*.md`**；**未触发 PHASE_11**；**未收到、也未自赋 `PRODUCTION_DEPLOY_CONFIRM`**（本轮 `special_instructions` 明确「无 PRODUCTION_DEPLOY_CONFIRM；PHASE_11 保持冻结」）。R14 增量内容见 **§14**，**所有命令须 PM CONFIRM 后执行**。
>
> **R14 变更面（一句话）**：后端**新增 `GET /api/projects`**（`views.py` + `urls.py`，**无 schema 变更 / 无 DB 迁移**）+ 前端 `projectContext` store 与 `client.ts` 单点注入 `X-IB-Project`（**需前端重建 + 发布新 `dist/`**）——**无新第三方依赖（`tech_stack.md` NO_CHANGE）、无新 env 键、无 unit / nginx 站点改动**。故 R14 部署面 = **`git pull` → `npm ci && npm run build` → 发布新 `dist/` → 重启 `ib-web`**（见 §14.3），**风险面最小、回滚无数据迁移**（见 §14.4）。
>
> **R14 门控前置备注（如实登记，待 PM 归口）**：本轮读取时，`docs/phase_status.md`（权威控制文档）记载 **GROUP_B = APPROVED（GR-B-007 PASS_WITH_CONDITIONS）**、**GROUP_C = APPROVED（GR-C-010）**、**GROUP_D = APPROVED（GR-D-011）**，三者对 REV-14 增量均为 PASS_WITH_CONDITIONS；设计真源 `architecture_design.md` / `module_design.md` 已落盘 **1.6.0/REV-14**（`tech_stack.md` NO_CHANGE 保持 1.4.0/REV-13）。**测试基线以此为准 = Python 245/245（unit 95 / integration 129 / e2e 21）+ 前端冒烟 21/21 + `selfcheck.py` 47/47**（`test_report.md` 1.10.0 §19；其 `file_header.status` 对 §19 的逐节 APPROVED 标注略滞后于 phase_status 的 GR-D-011，登记为**同源不同步**的 P1 待澄清项，**不阻塞计划层**——`tests/**` 属 test-engineer 制品，本代理不改）。**CRED-01**（未提交工作包不得原样提交）自 GR-B-007 起连续结转，见 §14.6。
>
> **门控前置备注（如实登记，待 PM 归口）**：本轮读取时，设计真源文件头 `status` 实测为 **`DRAFT_FOR_GATE_REVIEW`**（`architecture_design.md` 1.5.0/REV-13、`tech_stack.md` 1.4.0/REV-13）；而 `docs/phase_status.md`（权威控制文档）记载 **GROUP_B = APPROVED（GR-B-006）**、**GROUP_C = APPROVED（GR-C-009）**、**GROUP_D = APPROVED（GR-D-010，condition_1「DEFECT-R13-01 已修复并独立复跑闭合」）**。本代理据 phase_status 的**组级 APPROVED** 推进**计划层**；**文件头 status 一致性**登记为本轮 **P1 待澄清项**（不阻塞计划层，但 PHASE_11 执行前须由 PM 归口）。另：`test_report.md` §18 文件副本仍记 **238 pass / 1 fail**（DEFECT-R13-01），与 phase_status 的「已闭合」为**同源不同步**（tests/** 属 test-engineer 制品，本代理不改）——**测试基线以 phase_status 的闭合结论为准 = 239/239**。

---

## 1. 前置条件（Blockers / 待用户或 PM 补齐）

> **未满足下列任一「阻塞级」前置，则本计划无法执行**。这些是**外部前置**，不是本代理能在本轮自行闭合的。

### 1.1 阻塞级（P0 — 未闭合则不得进入 PHASE_11）

| # | 前置 | 当前实际状态（已核验） | 影响 | 闭合责任方 |
|---|------|------------------------|------|-----------|
| **B-01** | **intelligentbase 须存在 git 仓库与 remote** | **未建立**。实测 `git remote -v` → `fatal: not a git repository (or any of the parent directories): .git`；项目根目录**无 `.git`**。代码当前仅存在于工作目录（`docs/`、`src/`、`tests/`） | 冻结决策 ⑧ 要求目标机以 **`git pull`** 交付代码。无仓库 / 无 remote 则**第 8 节整套交付流程不可执行**；若绕道用 rsync/scp 即为**违反冻结决策** | 用户 / PM：`git init` + 建远端（内网 Git 或 VPS 裸仓库）+ 首次 push |
| **B-02** | **目标机 SSH 凭据注入方式须确定** | SSH 用户 `yangyang198354` 已实测回填；**口令值未提供、且不得写入任何入库文件** | 无凭据 → 任何远程操作（含只读）都无法执行 | 用户：日后经**环境变量**注入（如 `FREEARK_/IB_SSH_PASS` 类）；**不得**回填到本文件或任何被 git 跟踪的文件 |
| **B-03** | **目标机 apt / pip 外网或内网源可达性须确认** | 未实测。Ubuntu 26.04 为较新发行版 | 不可达则 `apt install`（python3.12、build-essential、libgl1 等）与 `pip install -r requirements.txt` 全部失败 | 用户 / PM：确认 apt 源与 PyPI 镜像可达；若隔离网需预置离线 wheel 缓存 |
| **B-04** | **`FND-GROUP-D-03`（MAJOR）处置裁决** | **未闭合**。`docs/phase_status.md` 与 `docs/test_report.md` §10.6 记载：生产 HTTP 删除路径下 `DeleteReport.blob_deleted` **恒 False** → 原文件字节成孤儿（隐私 / 磁盘泄漏，不影响检索正确性）。verifier 已独立复现。**phase_status 明确「建议阻塞 PHASE_11」** | 属生产写路径缺陷，部署前应修或由 PM 显式接受风险 | PM：路由 developer 修复，或书面接受 |
| **B-05** | **`ib-embed` 推理运行时三选一未定**（**部分闭合**：清单与来源已定；运行时三选一仍须目标机实测锁定，属 PHASE_11 前置） | `IB_EMBED_BACKEND` 运行时选型（FlagEmbedding / sentence-transformers / onnxruntime 直载）**须目标机实测 [TBD-T1/T3/T4/T18] 后定**（**本轮未锁定**）。依赖清单**已补**：`src/requirements-embed.txt`（R4）给出 FlagEmbedding（首选）+ `torch`(CPU) + `transformers` 的**保守区间**、bge-m3 双源（HuggingFace / ModelScope）与「权重不进 git」约定；基座 `src/requirements.txt` 仍**刻意不含** torch/FlagEmbedding（进程隔离 C8）。**区间不是锁定值** | 第 4 节安装清单的**来源**已唯一确定（`src/requirements-embed.txt`）；但**精确版本**仍须目标机 `pip install` 后以 `pip freeze` 回填（**区间不得当锁定值上线**）；若选 onnxruntime 直载，还须自备 bge-m3 的 ONNX 导出与 tokenizer | PM：授权在目标机做选型实测并在部署时锁定；锁定后**以 `pip freeze` 回填锁文件**（属 PHASE_11 前置） |
| **B-06** | **bge-m3 模型权重获取方式与来源须定** | 权重约 2.3 GB，**不得进 git**。契约 §9 要求 `IB_EMBED_MODEL_PATH` 指向**本地权重目录**、**离线加载**（不联网下载） | 无权重 → Embedder 冷启动失败 → 检索**静默降级**为「无知识库」而问答照常出答案（最危险的静默事故） | 用户 / PM：确定 offline 拷入路径（U 盘 / 内网制品库）；本计划只登记「权重不进 git」 |

### 1.2 待确认级（P1 — 不阻塞规划，但执行前须澄清）

| # | 待确认项 | 依据 |
|---|----------|------|
| C-01 | **DNS / 防火墙**：目标机 18080（nginx）是否需对内网/外网开放？Qdrant 6333 / ib-embed 8100 **必须仅回环**（`checklists.txt` A3 强制），是否已有冲突进程占用？ | ADR-03；checklists A3 |
| C-02 | ✅ **已闭合（R4）**：nginx **已明确为第 5 个交付组件**（**系统 nginx 站点**，非自研 unit）——见 **§7.5**（站点落点 / 静态 `dist/` 托管 / `/api`+`/healthz` 反代 `127.0.0.1:18080` / **SSE `proxy_buffering off`** / `proxy_read_timeout`）与 **§10.1 DEPLOY-009**。依据事实：`settings.py` 未配 `STATIC_ROOT`/staticfiles（已核验）；`vite.config.ts` 注释「生产由 nginx 反代 `/api` 与 `/healthz` 到 `127.0.0.1:18080`」 | ADR-11-R1；`vite.config.ts`；`settings.py`；`ib-web.service` |
| C-03 | ✅ **已闭合（R4）**：新增 `src/deploy/ib-worker.env.example`（**纯占位符，键集与 `src/deploy/env.example` 逐键一致**，**未新增/改名任何键**）；见 **§7.4 / §7.6** | `src/deploy/systemd/ib-worker.service:42`；§5 键名契约 |
| C-04 | ✅ **已闭合（R4）**：以官方 `.deb` 实际落点 **`/usr/bin/qdrant`** 为唯一规范，已修正 `src/deploy/systemd/qdrant.service` 的 `ExecStart` **一行**；安装后以 `which qdrant` + `systemctl cat qdrant \| diff - <repo>/src/deploy/systemd/qdrant.service`（须为空）为核验门，见 **§3.5 / §7.1** | ADR-03 / tech_stack §4.1 vs unit 文件 |
| C-05 | ✅ **已闭合（R4）**：单一确定方案 = 软链 `ln -s /opt/intelligentbase/src/ib_embed /opt/ib-embed/ib_embed`（**禁止复制第二份源码**）；创建 / 验证 / 回滚见 **§8.1** | `ib-embed.service`（`WorkingDirectory=/opt/ib-embed` + `-m ib_embed.server`）vs 仓库布局 |
| C-06 | ✅ **方案已定（R4）**：§6.1 已细化为**有序决策树 + 目标机最小探针优先**，**OCR 与 embedding 两条链路合并评估**；wheel 具体选型仍须目标机实测锁定 | 契约 §10；tech_stack §5.2；`src/requirements-embed.txt` |

### 1.3 REV-13 增量：部署前实测 / 确认项（不阻塞规划，执行前须确认）

| # | 项 | 依据 / 实测要求 |
|---|----|----------------|
| **R13-D1** | **`bcrypt` 版本落地**：目标机须落 `bcrypt>=4,<5`（CI/开发机曾装到 **5.0.0**，与 pin 不符） | `phase_status` **MINOR-R13-03**：部署前须把目标机落到 **4.x**，或由 PM 裁决放宽 pin。**不得**以「API 兼容子集 `hashpw/gensalt/checkpw` 可用」代替版本门（checklists B21 / §13.2） |
| **R13-D2** | **HTTPS 证书策略**：内网自签 / 内网 CA 二选一；证书与私钥**不进仓库**（私钥 **0600**）；**HSTS 仅在受信证书下启用** | `src/deploy/nginx/intelligentbase.conf.example` §证书策略；checklists **B15** |
| **R13-D3** | **对外 80/443 端口与防火墙放行**（承 C-01）；Qdrant `6333` / ib-embed `8100` **仍仅回环** | ADR-25 / §7.5；checklists A3 / B15 |
| **R13-D4** | **账户/会话后端确认为 `sqlite`**（非 `memory`）；`IB_AUTHZ_POLICY_MODULE` **显式**指向 `ibweb.accounts.policy`（内置）或接入方模块 | IFC-IB-312 / ADR-22；checklists B9 / B19 |
| **R13-D5** | **默认管理员初始口令**：由用户生成，**仅**经 **0600 EnvironmentFile** 注入；仓库 / 文档 / 日志 / 测试**零命中** | C-IB-09 / REQ-NFR-IB-15；checklists B18 / B19 |

---

## 2. 目标机环境准备

> 目标机：`192.168.31.133`，Ubuntu **26.04 LTS**（较新发行版），x86_64，i7-3770S（**Ivy Bridge，有 AVX、无 AVX2**），11 GiB，78 GiB 可用。
> **【版本可用性待实测确认】**：Ubuntu 26.04 属新发行版，下列包名 / 版本**均为计划，须在目标机实测确认**（不得以开发机（Windows / Python 3.14.6）结果替代 —— test_report DEV-01 已明令）。**凡下文命令中的包名与路径，执行前须以 `apt-cache policy <pkg>` / `which <bin>` 复核。**

### 2.1 apt 依赖（计划，待实测）

```bash
# 计划命令（须 PM CONFIRM 后执行；下列包名以 Ubuntu 26.04 实测为准）
sudo apt-get update
sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    build-essential pkg-config \
    git curl ca-certificates \
    libgl1 libglib2.0-0 libgomp1 \
    nginx
```

要点与理由：

- **`python3.12`**：`tech_stack` 约束 `>=3.11,<3.14`，`requirements.txt` / `deploy/*` 均按 **3.12** 写（venv 路径 `/opt/intelligentbase/venv`）。Ubuntu 26.04 base 的默认 Python 版本**须实测确认**；若非 3.12，须加 deadsnakes 或从 apt 装 3.12 包。**须以 `python3.12 -V` 留证**（checklists B1）。
- **`libgl1` / `libglib2.0-0`**：`pypdfium2`、`rapidocr-onnxruntime`（底层 OpenCV）在无头服务器上常见缺 `libGL.so.1` 导致 import 崩溃。
- **`libgomp1`**：`onnxruntime` / torch 的 OpenMP 运行时；缺失时报「libgomp.so.1: cannot open shared object file」。
- **`build-essential` / `pkg-config`**：仅当某依赖无 x86_64 wheel 需源码编译时用；**不是**默认必需，但 [TBD-T18] 若判定须自源码编译并关 AVX2（见 §6），则必需。
- **`nginx`**：见 C-02，承担静态前端 + 反代 + **SSE 不缓冲**（`proxy_buffering off`）。

### 2.2 Python venv（**每进程一个 venv** 的落地）

冻结决策与 ADR-03 要求「每进程一个 venv」。本计划按**两个 venv**规划：

| venv | 路径 | 用途 | 依赖来源 |
|------|------|------|----------|
| 基座 venv | `/opt/intelligentbase/venv` | `ib-web`、`ib-worker`（Django/DRF/Waitress/qdrant-client/pypdf/rapidocr…） | `src/requirements.txt` |
| ib-embed venv | `/opt/ib-embed/venv` | `ib-embed` 进程（**推理运行时**：FlagEmbedding 或 sentence-transformers 或 onnxruntime+transformers） | **`src/requirements-embed.txt`（R4 新增；保守区间，非锁定值）**；精确版本须目标机 `pip freeze` 回填（见 §4.2 / §1.1 B-05） |

> **为何分开**：embedding 运行时（尤其若选 FlagEmbedding）带入 `torch` + `transformers`（体积/内存面最大，tech_stack §1「Embedding 推理运行时」行 + §2），与 Web 进程依赖面不同；分开可使 `ib-embed` 崩溃/升级不牵连 `ib-web`，也避免把 `torch` 装进 Web venv 白占内存。

```bash
# 计划命令（示例；venv 以 root 建、chown 给运行用户，保证 systemd User= 可执行）
sudo python3.12 -m venv /opt/intelligentbase/venv
sudo /opt/intelligentbase/venv/bin/pip install --upgrade pip
sudo PYTHONUTF8=1 /opt/intelligentbase/venv/bin/pip install -r /opt/intelligentbase/src/requirements.txt
```

- **`PYTHONUTF8=1`**：tech_stack §3 强制（中文路径 / 编码）。**须同时写入两个 unit 的 `EnvironmentFile`** 或 systemd 单元环境。
- **pip 源配置**：若目标机走内网镜像，建议写入 `/etc/pip.conf`（**不含凭据**；若私服需凭据，凭据只走环境变量，不入 `/etc/pip.conf` 的明文 URL）。

### 2.3 CPU-only 约束（**禁 CUDA**）

- 目标机 GTX 960 为 Maxwell（太老），现代 PyTorch / onnxruntime **不支持** → **一律 CPU-only**。
- **硬禁令**：不得安装任何 `+cuXXX` 变体的 torch / onnxruntime（`onnxruntime-gpu`）；不得依赖 CUDA/cuDNN。
- 计划核验（PHASE_11）：`python -c "import onnxruntime; print(onnxruntime.get_available_providers())"` 输出**不含** `CUDAExecutionProvider`。

---

## 3. Qdrant 安装（官方 `.deb` 裸装）

依据：ADR-03 Q1（选中）+ `src/deploy/systemd/qdrant.service` + `src/deploy/checklists.txt` §A。

### 3.1 版本选择

- 取**最新稳定版**的官方 `.deb`（x86_64），**部署时锁定版本号并记入部署记录**（tech_stack「向量数据库」行）。
- **[TBD-T14] 状态**：x86_64 架构可用性已由 phase_status 回填 **CLOSED=x86_64**；但**具体 release 对 Ubuntu 26.04 codename 的适配须实测**（较新发行版，`.deb` 依赖 codename 时可能不匹配 → 回退 Q2 tarball / Q3 源码，见 ADR-03）。
- **客户端匹配**：`qdrant-client`（requirements 已 pin `>=1.7,<2.0`）与服务端**大版本须匹配**（tech_stack §4.1 第 7 项）。

### 3.2 安装步骤（计划）

```bash
# 计划命令（须 PM CONFIRM 后执行）
# 1) 专用非特权系统用户（C-IB-08；checklists A1）
sudo useradd --system --no-create-home --shell /usr/sbin/nologin qdrant

# 2) 数据目录：storage 与 snapshots 必须分开且都要 qdrant 可写
#    （官方 .deb 不建 snapshots 目录，缺失会 panic —— ADR-03 强制补齐项）
sudo install -d -o qdrant -g qdrant /var/lib/qdrant/storage
sudo install -d -o qdrant -g qdrant /var/lib/qdrant/snapshots

# 3) 安装 .deb（版本由实测锁定）
sudo apt-get install -y ./qdrant_<version>_amd64.deb      # 或 apt install ./qdrant_*.deb

# 4) 配置：只监听回环（无内建鉴权，绝不放 0.0.0.0）
#    /etc/qdrant/config.yaml 由 .deb 提供示例，须核对：
#      service.host = 127.0.0.1
#      storage.storage_path = /var/lib/qdrant/storage
#      storage.snapshots_path = /var/lib/qdrant/snapshots
#    路径一律绝对路径（ADR-03）

# 5) 安装 systemd 单元（来自仓库交付物；C-04 已闭合：ExecStart 统一为 /usr/bin/qdrant）
sudo install -m 0644 <repo>/src/deploy/systemd/qdrant.service /etc/systemd/system/qdrant.service
sudo systemctl daemon-reload
sudo systemctl enable --now qdrant
```

### 3.3 磁盘 / 内存预算

- **磁盘**：向量按 `dim=1024`、千级文档量级估算，本体不大；**关键是重建窗口**——重建期间新旧 collection **并存**，故 checklists A8 要求「可用空间 ≥ 现有数据量 2 倍」。
- **内存**：`on_disk_vectors: true`（`config.example.json`）可把向量落盘、降低常驻内存；HNSW 图仍在内存。11 GiB 下 Qdrant 量级温和（架构 §4：千级文档风险主要在 embedding 侧，不在存储侧）。
- **`LimitNOFILE=65536`（unit 强制）**：段文件随 collection 数线性增长，默认 1024 会在负载上来时随机 500（checklists A5）。

### 3.4 备份与恢复

- **备份**：`POST /collections/{name}/snapshots` → 快照落 `/var/lib/qdrant/snapshots`（须确认与 storage **不同子目录**，否则恢复时会把快照当段文件加载，checklists A2）。
- **恢复**：`PUT /collections/{name}/snapshots/recover`。
- **一致性**：向量库快照**必须**与台账（SQLite 文件）+ Blob 目录**同批备份**，恢复后须跑「删除重放对账」验证（ADR-07 反向不一致路径）。

### 3.5 单元与自启

- 由 `systemctl enable --now qdrant` 保证开机自启（checklists A4）。
- **C-04 已闭合（R4）**：统一为官方 `.deb` 实际落点 **`/usr/bin/qdrant`**（ADR-03 / tech_stack §4.1 即此值）；`src/deploy/systemd/qdrant.service` 的 `ExecStart` 已由 `/usr/local/bin/qdrant` 修正为 `/usr/bin/qdrant`（**只改这一行**）。安装后核验门：`which qdrant` 指向 `/usr/bin/qdrant`，且 `systemctl cat qdrant | diff - <repo>/src/deploy/systemd/qdrant.service` **须为空**（checklists A4）。若实测 `.deb` 落点并非 `/usr/bin/qdrant`，则**反过来**以实测落点为准并回改 unit —— 关键是**消除二义**，不迁就任一方。

---

## 4. bge-m3 常驻服务 `ib-embed`

依据：`docs/ib_embed_service_contract.md`（**权威契约，IFC-IB-266~274**）、ADR-02、`src/deploy/systemd/ib-embed.service`、`src/deploy/ib-embed.env.example`、checklists B6。

### 4.1 实现事实（已核验，用于排障对齐）

- `src/ib_embed/server.py` **仅用标准库 `http.server`**（零三方依赖），提供 `/embed`、`/healthz`、`/warmup`、`/descriptor`，监听 `127.0.0.1:8100`，**无鉴权**（回环专用）。
- `src/ib_embed/runtime.py` 的推理后端**惰性 import**、**候选顺序** `("flagembedding", "sentence_transformers", "onnxruntime")`；缺库 → 进程进入 `unavailable` 态、`/healthz` 给可读原因而**不崩溃**。

> **由此定义「ib-embed 部署」的两段**：(a) 服务端进程与端口（纯 stdlib，必成）；(b) **推理运行时与权重**（须 B-05/B-06 锁定，是真正的风险点）。**(b) 未成就表现为 `/healthz` 可 200 但 `model_loaded=false`** —— 即「服务起来了」不等于「能向量化」。

### 4.2 推理运行时（CPU-only）与依赖

- 三候选**择一、不得并行安装**（tech_stack §1「Embedding 推理运行时」行）：① `FlagEmbedding`（MIT，带 torch+transformers）② `sentence-transformers`（Apache-2.0，带 torch+transformers）③ `onnxruntime` 直载 bge-m3 的 ONNX 导出（MIT，**无 torch**，但 tokenizer 与池化须自备）。
- **CPU-only 硬约束**：三者均可纯 CPU；选 ③ 时**只装 CPU 版 wheel**、不得装 `onnxruntime-gpu`。
- **依赖清单（B-05，R4 部分闭合）**：`src/requirements-embed.txt` 已补（R4 新增）——给出 FlagEmbedding（首选）+ `torch`(CPU) + `transformers` 的**保守区间**、bge-m3 双源（HuggingFace / ModelScope）与「权重不进 git」约定；**区间不是锁定值**。基座 `src/requirements.txt` 仍**刻意不含**这三者（进程隔离 C8）。运行时三选一（见 §6.1 决策树）仍须目标机实测锁定后，以 `pip freeze` 回填精确版本。许可复核：`torch`（BSD-3）/`transformers`（Apache-2.0）按 tech_stack §2「条件性采纳」登记 + 按发行包 `LICENSE` 复核。

```bash
# 计划命令（来源 src/requirements-embed.txt；**区间非锁定值**，见 §1.1 B-05）
sudo python3.12 -m venv /opt/ib-embed/venv
sudo /opt/ib-embed/venv/bin/pip install --upgrade pip

# ① torch **必须经 PyTorch 官方 CPU 索引**显式安装
#    （PyPI 上的 Linux 默认 wheel 是 CUDA 版，会拖入 nvidia-* 包 —— 违反 CPU-only 硬约束）
sudo /opt/ib-embed/venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.2,<2.6"

# ② 再装 ib-embed 其余依赖（FlagEmbedding + transformers）；**不得**对全文件加 --index-url
sudo PYTHONUTF8=1 /opt/ib-embed/venv/bin/pip install -r /opt/intelligentbase/src/requirements-embed.txt

# ③ 部署前硬门（CI/CD D-1）：以 pip freeze 回填**精确版本**（区间不得当锁定值上线）
sudo /opt/ib-embed/venv/bin/pip freeze > /opt/intelligentbase/requirements-embed.lock.txt
```

### 4.3 模型权重获取（**权重不进 git**）

- `IB_EMBED_MODEL_PATH`（**必填、无默认**，契约 §9）指向本地权重目录；**离线加载，不联网下载**。
- 获取方式**由用户/PM 定**（§1.1 B-06）：内网制品库 / U 盘离线拷入。**严禁**把权重提交进仓库（体积 + 许可再分发合规面）。
- 落点建议 `/opt/ib-embed/models/bge-m3`（与 unit 的 `ReadOnlyPaths=/opt/ib-embed/models` 一致 —— 权重只读挂载，运行期不得改写）。

### 4.4 内存预算（对照 `MemoryMax=2560M` 与 `IB_EMBED_MEMORY_LIMIT_MB=2560`）

- **二者必须数值一致**（契约 §13 第 4 项 + unit 注释）——同一约束的两个落点（内核 cgroup 上限 vs 服务自述）。**改一处必须改另一处。**
- **当前 2560M 是「按物理 4 GB」写就的历史值**，而目标机实为 **11 GiB**；unit 注释与 `ib-embed.env.example` 均已标「须在 [TBD-T4]/[TBD-T16] 实测后重定（仅参数与注释）」。**本计划不擅改该值**，PHASE_11 实测后再定。
- **11 GiB 同机预算（须实测校准）**：Qdrant（约 1–3 G）+ `ib-embed`（cap 2.5 G）+ `ib-web`（cap 1 G）+ `ib-worker`（cap 2 G，OCR 峰值超 Web）+ OS ≈ 8–10 G 量级。**理论可行但余量不大**；OCR 与 embedding 的**叠加峰值 [TBD-T4']** 是同机最大内存风险点（tech_stack §5.2）。

### 4.5 冷 / 热启动与超时纪律（对齐 ADR-02 / IFC-IB-273）

- **服务端不区分冷热**（无状态 HTTP）：冷路径「愿意等」= **客户端**长超时+多重试；服务端只提供**有界并发 + 有界队列**。
- 契约值（**客户端**侧，`config.example.json`）：冷 `cold_timeout_s=120 / cold_max_retries=3 / cold_batch_size=16`；热 `hot_timeout_s=3 / hot_max_retries=1`。
- **服务端不许无界排队**：超 `IB_EMBED_QUEUE_DEPTH`（默认 8）即 `503 overloaded` + 回显 `retry_after_s`。
- **批上限硬约束**：`IB_EMBED_MAX_BATCH`（64）**必须 ≥ 客户端 `cold_batch_size`（16）**；若运维调大客户端批量而服务端未同步 → 冷路径必然 `400 batch_too_large` 且**不重试** → 整批入库失败（契约 §4.2）。
- **冷启动**：首次加载权重耗时须记录（[TBD-T3]）；`/warmup` **幂等**，客户端调用超时 `max(cold_timeout, 300s)`。

### 4.6 健康检查 `/healthz`

- `GET http://127.0.0.1:8100/healthz` → **200 且永不 5xx**；字段 `{ok, detail, model_id, dim, model_loaded, warm, queue_depth, inflight}`。
- **验收判据**：`ok=true` **且 `model_loaded=true` 且 `dim=1024`**。仅看进程 active **不足**（会掩盖「权重没加载」的静默降级）。

---

## 5. Django 栈（`ib-web` / `ib-worker`）

依据：`src/ibweb/**`、`src/deploy/systemd/ib-web.service`、`src/deploy/env.example`、`src/deploy/config.example.json`、checklists B1/B2/B3/B8/B9/B12/B13。

### 5.1 安装与版本钉

```bash
# 计划命令（基座 venv）
sudo PYTHONUTF8=1 /opt/intelligentbase/venv/bin/pip install -r /opt/intelligentbase/src/requirements.txt
```

- **必须核验 `langchain-openai < 0.3`**（checklists B2）：`0.3.x` 移除 `_convert_chunk_to_generation_chunk` 致**流式路径**AttributeError（FreeArk 生产漂移史）。冻结决策 ⑤ 要求**装配期 fail-fast 断言**——`ibweb/composition.py` 侧已于构造期断言（test_report DEV-02 实测：装配 `openai_compatible` 时抛 `StartupError: langchain-openai 版本不满足约束 >=0.2,<0.3（实测 1.3.3）`）。
- **【硬约束】确认无 PyMuPDF/fitz**（checklists B3）：
  `python -c "import importlib.util as u; print(u.find_spec('fitz'), u.find_spec('pymupdf'))"` → **两个均须 None**。
- 前端（Vue 3 + Vite）在**构建机**产 `dist/`；目标机只需托管产物（见 §7/C-02）。

### 5.2 台账（SQLite）与生产库选择

- **台账 = 自管 SQL 的 SQLite**（**不经 Django ORM**，ADR-07-R1）：路径 `IB_LEDGER_PATH=/var/lib/intelligentbase/ledger/ledger.sqlite3`。
- **WAL + `busy_timeout` 必开**（连接级 PRAGMA，**不在** schema 里）：运行期核验 `PRAGMA journal_mode` = `wal`、`PRAGMA busy_timeout` = `5000`（checklists B8）。
- **`DATABASES = {}`**（settings.py 已核验）：Django **不接任何生产库**；`ib-web` 的 `ExecStartPre` 跑 `python -m ibweb.bootstrap --ensure-schema` 幂等建表（退出码 0/2/3/4）。
- **本基座无外部 DB（无 MySQL/PG）**——与 FreeArk 不同，勿套用 FreeArk 的 MySQL 生产库。

### 5.3 静态文件

- `settings.py` **未启用 staticfiles / 无 `STATIC_ROOT`**（已核验）→ 前端 `dist/` **不由 Django 托管**，由 **nginx** 提供（见 §7 与 **C-02**）。
- 构建：`cd src/frontend && npm ci && npm run build`（`build` = `vue-tsc --noEmit && vite build`），产物 `src/frontend/dist/`（`sourcemap: false`）。**须计入 NV-07**。

### 5.4 启动参数按 4C / 8T / 11 G 调参（[TBD-T15]）

- 载体 `Waitress`（主；`requirements.txt` 同时含 Gunicorn 为备，**二者不得同时起**，否则 18080 争抢）。
- `ib-web.service` 现为 `--host=127.0.0.1 --port=18080 --threads=8 --channel-timeout=120`。
- **`--threads` 是 SSE 并发容量的硬旋钮**（ADR-11-R1：一个 SSE 长连接独占一个线程至流结束）。**8 是「4 GB」时代的保守值**，注释已标「真机压测后调整」。i7-3770S 4C/8T 下**须以 [TBD-T15] 实测**：并发发起 N≥threads 个 SSE，确认**超出部分明确 503（fail-closed）而非排队**（checklists B13）。
- `--channel-timeout=120` **须 > SSE 最长静默期**：调小会让长问答中途断开，且**日志无错误**（是正常超时）。

### 5.5 `--settings` 约定

- 生产：`DJANGO_SETTINGS_MODULE=ibweb.settings`（`wsgi.py`/`manage.py` 均已 `setdefault`）。
- 测试（**非部署**，仅供 CI 参照）：`--settings=ibweb.settings` + `IB_OFFLINE_MODE=1`（离线替身，不触网、不连生产库）。

---

## 6. rapidocr / onnxruntime（CPU）——含无 AVX2 处理

依据：ADR-12、tech_stack §4.3 / §5.2、契约 §10、[TBD-T18]、checklists B4/B5。

### 6.1 「无 AVX2」的实质与可行路径

- 目标机 i7-3770S（Ivy Bridge）**有 AVX、无 AVX2**。部分**官方预编译 x86_64 wheel** 以 AVX2 为基线 → 在该 CPU 上触发 **SIGILL（非法指令，进程级崩溃，不可捕获）**。
- **风险同源，须一次性合并评估**：**OCR 链路**（`rapidocr-onnxruntime` → `onnxruntime`）与 **embedding 链路**（`torch` / `FlagEmbedding`，或候选③的 `onnxruntime` 直载）**受同一 CPU 指令集基线约束**（tech_stack §5.2 + 契约 [TBD-T18]）。**分链路各修会重复踩坑、且排障时会错误归因**（一条链路 SIGILL 可能被误判为「配置错」）。
- **链路不可用会表现为什么（把「静默降级」显式化）**：

  | 链路 | 挂掉时的可观测症状 |
  |------|--------------------|
  | **embedding** | `ib-embed` `/healthz` 仍可能 **200**，但 `model_loaded=false`（或进程反复重启）→ 检索**静默降级**为「无知识库」，问答照常出答案（**最危险的静默事故**，见 §4.6 / R-06） |
  | **OCR** | 扫描页解析失败 / 识别 0 字；若被 `NullOcrEngine` **静默接管**，则扫描件「成功入库 0 字」而状态仍 `indexed`（见 §11 导语） |

- **本计划不拍板 wheel 选型**（冻结决策要求以目标机实测为准）。PHASE_11 按**有序决策树**执行，**目标机最小探针优先**（**导入 + 一次真实推理**，非 `pip list`；开发机（新 CPU）结果**不得**替代 —— test_report DEV-01）：

  - **(0) 目标机最小探针第一**（在锁定任何版本前先跑；两条链路**各自独立进程**运行，一条崩不掩盖另一条；进程崩 = SIGILL）：
    ```bash
    # OCR 链路：import + 一次极小 onnxruntime session
    python -c "import onnxruntime as ort; print('ort ok', ort.__version__, ort.get_available_providers())"
    # Embedding 链路（若选 FlagEmbedding/torch）：import torch + 一次极小张量运算
    python -c "import torch; x=torch.randn(2,2); print('torch ok', torch.__version__, (x@x).sum().item())"
    ```
    （ONNX session 需一个极小 `.onnx` 探针模型；`torch` 侧极小张量乘法即可触发指令集路径。）
  - **(1) 换用不要求 AVX2 的 CPU wheel**（首选规避）：下调候选版本区间（如 `onnxruntime` / `torch` 取较早 CPU 版）。**判定方法**：`pip debug --verbose`（看平台 tag 与 wheel 兼容性）、`python -c "import onnxruntime; print(onnxruntime.get_available_providers())"`、**以及以探针 (0) 实际跑通为准**。
  - **(2) 自源码编译并关 AVX2**：`-mno-avx2` 类编译开关；**此时才需要 `build-essential` / `pkg-config`**（见 §2.1；二者**不是**默认必需）。
  - **(3) 降级纯 Python 后备路径**：embedding 侧切到**候选③ onnxruntime 直载 bge-m3**（**不引 torch**，见 §4.2 / `src/requirements-embed.txt` 的「候选③」段 —— 该路径是规避 SIGILL 的**最省风险路径**）；OCR 侧降级为「无 OCR」（须**显式**降级、不得静默）。
  - **若两条链路均 SIGILL 且无可用构建 → 回 PM 裁决**（是否放宽 OCR 能力），**不得**以引入 PyMuPDF 或 Docker 规避（硬禁令）。

- **与 `src/requirements-embed.txt` 的交叉引用**：若 (3) 选 **候选③（onnxruntime 直载，不引 torch）**，则 **embedding 链路与 OCR 链路共用同一个 `onnxruntime`**（已在基座 `src/requirements.txt`）——**AVX2 风险收敛为「单一 `onnxruntime` wheel 是否满足此 CPU」一个问题**，且候选③额外只需 `transformers`（tokenizer）。本决策树与 `src/requirements-embed.txt`「运行时选型」「候选③」两段**互相引用、结论一致**：三选一仍须目标机实测锁定。

### 6.2 onnxruntime 线程数调优（避免与 Qdrant / ib-web / ib-embed 抢核）

- 目标机 8 线程（4 物理核）。CPU 竞争者共四：Qdrant、`ib-embed`、`ib-web`(Waitress threads)、`ib-worker`(OCR)。
- 建议（**待 [TBD-T16]/[TBD-T7] 实测校准，本计划不擅改默认**）：
  - OCR 侧限制 intra-op 线程，避免「OCR 吃满 8 核 → SSE 请求排队」；`ib-worker.service` 已设 `CPUQuota=200%`（限 2 核）。
  - `ib-embed` 侧 `IB_EMBED_THREADS=2`（契约默认）。
- **总原则**：向量化已用满核时**超订会整体劣化**（架构 §4 第 4 条），故宁少不多。

---

## 7. 交付组件（四个 systemd 单元 + 系统 nginx 站点）

四个 unit 为**仓库交付物**（`src/deploy/systemd/*.service`）+ **EnvironmentFile 模板**（`src/deploy/*.env.example`），**本代理不安装到目标机**；**nginx 由系统包提供**（非自研 unit），是**事实上的第 5 个必需组件**（见 §7.5 / C-02）。安装均在 PHASE_11（须 CONFIRM）。

### 7.1 `qdrant`（向量库）

| 项 | 值 |
|---|---|
| 职责 | 向量存储与相似度检索；独立失败域 |
| `User/Group` | `qdrant`（**非特权**，`nologin`） |
| `WorkingDirectory` | `/var/lib/qdrant` |
| `ExecStart` | `/usr/bin/qdrant --config-path /etc/qdrant/config.yaml`（**C-04 已闭合（R4）**：unit 与 ADR-03 / tech_stack §4.1 统一为 `/usr/bin/qdrant`；见 §3.5） |
| `EnvironmentFile` | **无**（Qdrant 无凭据需求；本部署**未启用 api-key**，故**仅回环**） |
| `Restart=` | `on-failure` / `RestartSec=5s` |
| 限制 | `LimitNOFILE=65536`；`ProtectSystem=strict` + `ReadWritePaths=/var/lib/qdrant/{storage,snapshots}` |
| 自启 | `WantedBy=multi-user.target` → `enable` |

### 7.2 `ib-embed`（bge-m3 常驻推理）

| 项 | 值 |
|---|---|
| 职责 | `/embed` `/healthz` `/warmup` `/descriptor`（MOD-IB-26；契约唯一落点 `docs/ib_embed_service_contract.md`） |
| `User/Group` | `ib-embed` |
| `WorkingDirectory` | `/opt/ib-embed`（**C-05 已闭合（R4）**：包经软链 `→ /opt/intelligentbase/src/ib_embed` 落位，见 §8.1） |
| `ExecStart` | `/opt/ib-embed/venv/bin/python -m ib_embed.server --host 127.0.0.1 --port 8100` |
| `EnvironmentFile` | **`/etc/intelligentbase/ib-embed.env`**（**11 个 `IB_EMBED_*` 键，零凭据**；缺失即启动失败，unit **不加** `-` 前缀） |
| `Restart=` | `always` / `RestartSec=10s` |
| 限制 | `MemoryMax=2560M`（**须与 `IB_EMBED_MEMORY_LIMIT_MB` 同值**，见 §4.4）；`ReadOnlyPaths=/opt/ib-embed/models`；`ProtectSystem=strict` 等 |
| 自启 | `enable` |

### 7.3 `ib-web`（Django + Waitress，HTTP API + SSE + 静态前端）

| 项 | 值 |
|---|---|
| 职责 | HTTP API + SSE 流式问答；`After=qdrant.service ib-embed.service`（**`Wants` 非 `Requires`**：依赖挂了 Web 仍可服务，检索降级而非全站不可用） |
| `User/Group` | `ib-web` |
| `WorkingDirectory` | `/opt/intelligentbase` |
| `ExecStartPre` | `/opt/intelligentbase/venv/bin/python -m ibweb.bootstrap --ensure-schema`（**失败即中止启动，不得加 `-`**） |
| `ExecStart` | `/opt/intelligentbase/venv/bin/waitress-serve --host=127.0.0.1 --port=18080 --threads=8 --channel-timeout=120 ibweb.wsgi:application` |
| `EnvironmentFile` | **`/etc/intelligentbase/ib-web.env`**（**凭据唯一来源**，权限 **0600**、属主 `ib-web`） |
| `Restart=` | `on-failure` / `RestartSec=3s`；`KillSignal=SIGTERM` / `TimeoutStopSec=30`（留给 SSE 写回会话） |
| 限制 | `MemoryMax=1024M`；`ReadWritePaths=/var/lib/intelligentbase` |
| 自启 | `enable` |

### 7.4 `ib-worker`（入库队列 + 重建推进）

| 项 | 值 |
|---|---|
| 职责 | 异步入库 / 删除重放 / 索引重建（ADR-10，台账表即队列）；`After=ib-web.service qdrant.service ib-embed.service` |
| `User/Group` | `ib-worker` |
| `WorkingDirectory` | `/opt/intelligentbase` |
| `ExecStart` | `/opt/intelligentbase/venv/bin/python -m ibweb.worker --interval 5 --limit 8` |
| `EnvironmentFile` | **`/etc/intelligentbase/ib-worker.env`**（**C-03 已闭合（R4）**：模板 `src/deploy/ib-worker.env.example` 已补，**键集与 `ib-web.env` 逐键一致**，未新增/改名任何键 —— 见 §7.6） |
| `Restart=` | **`always`**（常驻轮询，正常路径**永不自行退出**，任何退出都是异常）；`KillSignal=SIGTERM` / `TimeoutStopSec=300` |
| 限制 | `MemoryMax=2048M`；`CPUQuota=200%`（OCR 限 2 核）；`ReadWritePaths=/var/lib/intelligentbase` |
| 自启 | `enable`；**单实例**（**不加** `@` 模板后缀） |

### 7.5 `nginx`（反向代理 + 静态前端；**系统服务，非自研 unit**）—— C-02 闭合

> **为何是必需的「第 5 个交付组件」而非可选项**：`src/ibweb/settings.py` **未配置 `STATIC_ROOT`/staticfiles**（已核验）→ 前端 `dist/` **不由 Django 托管**；`src/frontend/vite.config.ts` 生产注释明确「由 nginx 把 `/api` 与 `/healthz` 反代到 `127.0.0.1:18080`」。故**没有 nginx 就没有前端与流式入口**。它由 `apt install nginx`（§2.1）安装，**不计入四个自研 unit**，但**必须列入部署步骤与回滚表**（§10.1 DEPLOY-009）。

| 项 | 值 |
|---|---|
| 职责 | 对外 HTTP 入口；**托管前端 `dist/` 静态产物**；把 `/api` 与 `/healthz` 反代到 `ib-web`；**SSE 不缓冲** |
| 归属 | **系统 `nginx` 包**提供的 `nginx.service`（`apt` 提供，非本仓库交付） |
| 站点文件 | `/etc/nginx/sites-available/intelligentbase`，软链到 `sites-enabled/` |
| 静态根 | `dist/` 落 `/var/www/intelligentbase/`（构建产物，不入 git，见 §5.3 / §8） |
| 反代目标 | `proxy_pass http://127.0.0.1:18080;` —— **以 `ib-web.service` 的 Waitress `--port=18080` 为准**（已核验 `src/deploy/systemd/ib-web.service:51`；`vite.config.ts` 同值） |
| **对外监听端口** | **由 C-01（DNS/防火墙）定**；**⚠ 不得与 Waitress 的 `127.0.0.1:18080` 冲突**——同机同端口不可复用（`0.0.0.0:18080` 与 `127.0.0.1:18080` 会 EADDRINUSE）。故 nginx 对外**必须另用一个端口**（如 80/443）；若 PM 坚持对外 18080，则须**同步改 `ib-web.service` 的 Waitress 端口**（属 src 改动，**超本轮授权范围**，须单独立项） |
| **SSE 必需** | `proxy_buffering off;`（必要时叠加 `proxy_set_header X-Accel-Buffering no;`）——**否则流式问答被缓冲、首字节永不外发，前端「功能静默失效」**（`ib/streaming/__init__.py`、`ibweb/sse.py`、`scripts/selfcheck.py` 均以此为硬断言） |
| 超时 | `proxy_read_timeout` **必须 > SSE 最长静默期**（对齐 `ib-web --channel-timeout=120`，建议 ≥ 300s；调小会让长问答中途断开，**且日志无错误**） |
| 回环纪律 | `127.0.0.1:6333`（Qdrant）与 `127.0.0.1:8100`（ib-embed）**不经 nginx 暴露**；nginx **只**对外服务前端 + `/api` + `/healthz` |

站点骨架（**计划，须 PM CONFIRM 后落盘**；`<host>` 须与 `ib-web.env` 的 `IB_ALLOWED_HOSTS` 一致，否则 `DEBUG=False` 下所有请求 400）：

```nginx
server {
    listen 80 default_server;        # 对外端口由 C-01 定；**不得**用 18080（与 Waitress 冲突）
    server_name <host>;
    root /var/www/intelligentbase;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }   # SPA 回退

    location /api/ {
        proxy_pass http://127.0.0.1:18080;             # 以 ib-web.service 实际端口为准
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;                           # SSE 必需（功能正确性硬条件）
        proxy_set_header X-Accel-Buffering no;
        proxy_read_timeout 300s;                       # > SSE 最长静默期
    }

    location = /healthz { proxy_pass http://127.0.0.1:18080; }
}
```

> **落盘纪律（PHASE_11）**：改站点文件后 **必须先 `nginx -t`（CI/CD 硬门 D-2）通过**，**再** `systemctl reload nginx`；语法错的重载会让对外服务直接不可用。回滚同样须 `nginx -t` 通过后方可 `reload`（见 §10.1 ROLLBACK-009）。

#### 7.5.1 REV-13 增量：HTTPS/TLS 终止站点（**以仓库模板为准**）

> **R13 变更**：用户已把 **HTTPS** 列为部署项（ADR-25 / DR-15）。仓库新增 **`src/deploy/nginx/intelligentbase.conf.example`（IFC-IB-331）** 作为**权威站点模板**，其上为 `80 → 301 https` + `443 ssl`（TLSv1.2/1.3）的 **TLS 终止**形态；上面 §7.5 的 HTTP 骨架降级为**最小示例**（若 PM 决定暂不启用 TLS，则以 §7.5 骨架为准，并**显式记录该决策**）。R13 模板相对 §7.5 骨架的**新增硬条件**：

| # | R13 模板新增项 | 为何是硬条件 |
|---|----------------|---------------|
| 1 | `listen 443 ssl;` + `ssl_certificate` / `ssl_certificate_key`（**占位符**） | TLS 终止落点；**证书与私钥不进仓库**（私钥 0600，见 §13.4） |
| 2 | `80 → return 301 https://$host$request_uri`（ACME 挑战路径先放行） | 明文只存在于回环；浏览器一律走 HTTPS |
| 3 | `proxy_set_header Authorization $http_authorization;` | 认证**走 Authorization 头、非 Cookie**（DR-10）；缺此则后端一律 401（表现为「本地 OK、线上登录后仍 401」） |
| 4 | `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;` | 供**登录限速**按客户端 IP 计数（IFC-IB-326） |
| 5 | `proxy_buffering off;`（**保留**，IFC-IB-331） | SSE 不缓冲——**功能正确性硬条件**，流式问答的唯一正确性依赖 |
| 6 | 前端 **hash 路由**（`createWebHashHistory`）→ 服务端只需 `/` | 少一处「本地能跑、线上刷新 404」的配置依赖；`try_files` 回退仅为保险 |
| 7 | 安全响应头（`X-Content-Type-Options` / `X-Frame-Options: DENY` / `Referrer-Policy`）；`client_max_body_size 64m` | 基线加固；上传体上限与后端一致 |
| 8 | `location = /index.html { Cache-Control: no-store }`；`/assets/` 长缓存 | 防发版后加载旧 `index.html` 指向已删除哈希资源 → 白屏 |

> **HSTS 纪律**：`Strict-Transport-Security` **仅在**内网 CA / 受信证书下启用；**自签证书下不得启用**——否则证书链出问题时浏览器在 `max-age` 内拒绝一切降级访问，用户无法通过「继续访问」恢复，**排障路径被自己封死**（B15 验收点）。

### 7.6 EnvironmentFile 注入方式（**凭据不落 git**）

```bash
# 计划命令（须 root；示例路径以仓库交付物为准）
sudo install -m 0600 -o ib-web    -g ib-web    <repo>/src/deploy/env.example           /etc/intelligentbase/ib-web.env
sudo install -m 0600 -o ib-worker -g ib-worker <repo>/src/deploy/ib-worker.env.example /etc/intelligentbase/ib-worker.env   # C-03 已补模板（键集与 ib-web.env 逐键一致）
sudo install -m 0600 -o ib-embed  -g ib-embed  <repo>/src/deploy/ib-embed.env.example  /etc/intelligentbase/ib-embed.env
sudo install -m 0640 -o ib-web    -g ib-web    <repo>/src/deploy/config.example.json   /etc/intelligentbase/config.json
```

- **`0600` + 属主为运行用户**：`ib-web.env` **是**凭据真源（值经环境变量注入进程）；`0644` 会让同机任何用户读到 LLM API Key / 服务账号令牌。
- **`ib-worker.env` 与 `ib-web.env` 键集逐键一致**（C-03）：worker 是**同一代码基座**的另一入口，读同一份 `config.json` / 台账 / 向量库 / LLM / 鉴权键。R4 只**补齐缺失的模板**（`src/deploy/ib-worker.env.example`），**未新增、未改名任何键**——键名契约以 module_design §5 为准，新增键须先回设计文档评审。
- **填值只在部署机的 0600 文件里做**；模板被 git 跟踪，写真实值会**永久留在 `git log -p`**。
- **`ib-embed.env` 零凭据**（本服务不需令牌；加令牌 = 净增凭据面）。
- **启动期必填校验**：缺失必填项 → **非零码退出 + 只报键名、不回显值**（AC-IB-12-03；checklists B9）。

---

## 8. 代码交付流程（`git pull`，**禁 pscp 逐文件上传**）

> **前置：B-01（git 仓库 + remote）必须先闭合**，否则本节不可执行。

```bash
# 计划步骤（须 PM CONFIRM 后执行；凭据只走环境变量，不入命令历史/文档）
# 0) 首次核对主机指纹（防中间人；指纹非 secret，已实测回填）
#    ssh-ed25519 SHA256:BwIe6k9QhLUWCPPyrOykjSDtrWn+EgtesTllQjUd2eY
#    用 ssh-keyscan 得到的 host key 与此指纹比对，不一致即中止

# 1) 首次：在目标机克隆到约定路径
sudo git clone <remote-url> /opt/intelligentbase        # remote-url 不含凭据（走 SSH key/agent）
# 或：先 git init + remote add + fetch，再 checkout main

# 2) 后续每次部署：拉取（**直接 main，不开分支+PR** —— 沿用 FreeArk）
cd /opt/intelligentbase && sudo git fetch --prune origin && sudo git checkout main && sudo git pull --ff-only
```

- **不得**用 `pscp`/`scp`/`rsync` 逐文件上传（冻结决策 ⑧）：逐文件上传会导致**生产与仓库版本不一致、不可复现**。
- 代码落 `/opt/intelligentbase`；`ib_embed` 包须在 `/opt/ib-embed` 可导入（**C-05 已闭合，方案见 §8.1**）：用 `install -d` + **符号链接**，**不复制第二份源码**（否则漂移）。
- 前端 `dist/` 属**构建产物**，建议构建机产出后按 `git pull` 之外受控方式同步（或目标机构建），**不入 git**（`.gitignore` 已含 `dist/`）。
- 部署后**必须**核对：`git -C /opt/intelligentbase rev-parse HEAD` 与预期 commit 一致（可追溯）。

### 8.1 `ib_embed` 包落点（**C-05 闭合**：单一软链方案）

`ib-embed.service` 要求 `WorkingDirectory=/opt/ib-embed` 且 `ExecStart=/opt/ib-embed/venv/bin/python -m ib_embed.server`，即包须在 `/opt/ib-embed/ib_embed` 可导入；而源码在 `/opt/intelligentbase/src/ib_embed`。**唯一确定方案 = 软链**（`python -m` 会把 cwd 加入 `sys.path`，cwd=`/opt/ib-embed` 时即可解析到软链）：**禁止复制第二份源码**（否则两份漂移，且 `git pull` 只更新源目录一份）。

```bash
# 计划命令（须 PM CONFIRM 后执行）
sudo install -d -o ib-embed -g ib-embed /opt/ib-embed
sudo ln -sfn /opt/intelligentbase/src/ib_embed /opt/ib-embed/ib_embed

# 验证：导入路径须指向软链目标（而非副本）
/opt/ib-embed/venv/bin/python -c "import ib_embed; print(ib_embed.__file__)"
#   期望输出：/opt/intelligentbase/src/ib_embed/__init__.py
```

- **回滚**：`sudo rm /opt/ib-embed/ib_embed`（**只删软链**，`/opt/intelligentbase/src/ib_embed` 源不动）；必要时回退上一版 `ib_embed` 代码（`git checkout <上一版 commit>`）。
- **为何不用复制 / `git archive` 导出**：副本会使「已在跑的服务」与「`git pull` 后的仓库」成为两个版本源，排障时 `import ib_embed` 的实际落点不可知 —— 软链把「唯一真源」保持在 `src/`。
- **只读纪律**：`ib-embed.service` 未把 `/opt/ib-embed` 列入 `ReadWritePaths`（`ProtectSystem=strict` 下只读），故软链只需**可读**；创建软链的 `install`/`ln` 在 PHASE_11 由 root 执行，不在服务运行期改动。

---

## 9. DeepSeek 真跑 smoke 验证（闭合 DEV-02 + NV-06 骨架）

> **为什么必须真跑**：`docs/test_report.md` §5.4 **DEV-02** 记载——本机 `langchain-openai=1.3.3` 违反 pin，**远程 LLM 全链路从未真跑**，`describe_egress` 仅以类级验证。故 **PHASE_11 必须以真实 DeepSeek 调用闭合 DEV-02**（checklists B7）。

### 9.1 端到端 smoke 步骤（计划，可粘贴）

```bash
# 前置：ib-web.env 已按 0600 注入 IB_LLM_BASE_URL / IB_LLM_MODEL / IB_LLM_API_KEY
#       （凭据不回显、不入日志、不入文档）

# (1) LLM 连通性 + 外发边界声明（checklists B7）
/opt/intelligentbase/venv/bin/python - <<'PY'
from ib.config import ConfigurationResolver, FileConfigurationSource
from ib.llm import build_llm_provider
cfg = ConfigurationResolver(FileConfigurationSource("/etc/intelligentbase/config.json")).global_config()
provider = build_llm_provider(cfg)                 # 版本不符应在此构造期即抛（pin 断言）
print("egress=", provider.describe_egress())       # 期望含 endpoint_host + data_categories
print("health=", provider.health())
impl = provider.build_aggregator().impl
reply = impl.invoke("ping") if hasattr(impl, "invoke") else impl("ping")
print("reply=", repr(str(getattr(reply, "content", reply))[:60]))
PY

# (2) 上传 → 解析 → 向量化 → 检索（用文本层 PDF 与扫描件 PDF 各一份，见 checklists B4）
#     经 HTTP 上传（Authorization 头，**禁 ?token=**）：
curl -sS -X POST -H "Authorization: Bearer <令牌>" -F "file=@样本.pdf" \
     -F "project_id=<已认证主体解析，请求体该字段被忽略>" http://127.0.0.1:18080/api/files
#     轮询状态至 indexed：
curl -sS -H "Authorization: Bearer <令牌>" "http://127.0.0.1:18080/api/files?..."   # 观察 status

# (3) SSE 问答（真实流式；**逐条**收事件，非一次性）
curl -sS -N -H "Authorization: Bearer <令牌>" \
     "http://127.0.0.1:18080/api/chat/stream?q=<提问>" | head -20
```

### 9.2 预期观测点与判据

| # | 观测点 | 判据 |
|---|--------|------|
| S-1 | `build_llm_provider` 构造期 | **不抛**（版本 pin 满足，闭合 DEV-02 的前提） |
| S-2 | `describe_egress()` | 含 `endpoint_host` 与 `data_categories`（**数据外发声明**，AC-IB-12-05） |
| S-3 | `ping` 回复 | 一次成功极小调用有非空回复（**真实调用 DeepSeek 至少一次**） |
| S-4 | 上传返回 | 2xx；`status` 由 `pending → parsing → indexed`；`chunk_count > 0` |
| S-5 | 检索 | `/api/chat/stream` 的回答**基于上传语料**（非空知识库时 `degraded=false`；空库时 `degraded=false, hits=[]`，**二者须可区分**，AC-IB-14-02） |
| S-6 | SSE | 响应 `Content-Type: text/event-stream`，可见 `event:` 帧**逐条**到达；响应头含 `X-Accel-Buffering: no` / `Cache-Control: no-cache` |
| S-7 | 流内降级 | 若 embedding/向量库不可达，须发 `degraded` 事件；**答复不得静默降级**（这是 fail-open 的可见性要求） |
| S-8 | 日志 | 无 `Bearer ` / `token=` / 凭据 / 问句正文 / 检索片段原文（checklists B14） |
| S-9 | 断网对照 | 离线时该检查失败，且系统**降级到关键词档位**（不崩、不空转） |

> **纪律**：DeepSeek 调用是**已知且已声明的数据外发**（问句 + 命中片段外发云端），不是泄漏；但**凭据本身不得出现在任何输出/日志**。

---

## 10. 回滚方案

> 原则：**每个正向步骤都有对应的严格逆操作**；回滚按**逆序**执行。无法自动回滚者显式标注 `[MANUAL_ROLLBACK_REQUIRED]`。
> 本表为**计划**（PHASE_10）；PHASE_11 执行时须逐步记录结果并写入 `deployment_report`。

### 10.1 正向步骤与逆操作（DEPLOY-NNN ↔ ROLLBACK-NNN）

| 正向 | 正向操作 | 对应回滚 | 回滚操作 |
|------|----------|----------|----------|
| **DEPLOY-001** | 目标机环境准备（apt 包 / `python3.12` venv） | **ROLLBACK-001** | 卸载新增 apt 包（`apt-get remove --purge`）；删除 venv 目录。**低风险、可重做** |
| **DEPLOY-002** | Qdrant `.deb` 安装 + 用户/目录/unit | **ROLLBACK-002** | `systemctl disable --now qdrant`；`apt-get remove qdrant`；**保留** `/var/lib/qdrant/storage`（**不得**在未备份前删数据） |
| **DEPLOY-003** | Qdrant 启动 + 建 collection 冒烟 | **ROLLBACK-003** | `systemctl stop qdrant`；删除冒烟 collection（`DELETE /collections/ib_smoke_*`） |
| **DEPLOY-004** | `ib-embed` 运行时/权重就位 + 启动 | **ROLLBACK-004** | `systemctl disable --now ib-embed`；保留 `/opt/ib-embed/models`（权重可复用） |
| **DEPLOY-005** | 基座 venv + `requirements.txt` 安装 | **ROLLBACK-005** | `pip install -r` 前先 `pip freeze > requirements.lock.bak`；回滚 = 按备份重建 venv |
| **DEPLOY-006** | 四份 `EnvironmentFile` + `config.json` 就位 | **ROLLBACK-006** | 恢复上一版 `0600` 文件的离线备份（**凭据文件必须在版本控制之外另存**） |
| **DEPLOY-007** | `ib-web` 安装 unit、启动 | **ROLLBACK-007** | `systemctl disable --now ib-web`；`git checkout <上一版 commit>` 后重启 |
| **DEPLOY-008** | `ib-worker` 安装 unit、启动 | **ROLLBACK-008** | `systemctl disable --now ib-worker` |
| **DEPLOY-009** | nginx 站点（`/etc/nginx/sites-available/intelligentbase`：静态 `dist/` 托管 + `/api`、`/healthz` 反代 `127.0.0.1:18080` + **SSE `proxy_buffering off`**，见 §7.5）+ 静态产物 `dist/` 就位 | **ROLLBACK-009** | 回滚 = 恢复**上一版**站点文件（离线备份）→ **`nginx -t` 必须通过** → `systemctl reload nginx`；恢复上一版 `dist/`。**回滚同样须 `nginx -t` 通过后方可 `reload`**（不得带语法错误重载，否则对外服务直接不可用） |
| **DEPLOY-010** | 部署后验证（§11） + DeepSeek smoke（§9） | **ROLLBACK-010** | 若冒烟失败 → 按 §10.2 决策树整体回滚 |
| **DEPLOY-011 ~ 016** | **REV-13 增量步骤**（bcrypt 依赖 / 003 迁移 / R13 环境变量 / 默认管理员播种 / nginx HTTPS / 令牌纪律校验）—— 正向定义见 **§13.6** | **ROLLBACK-011 ~ 016** | **R13 逆操作**（详见 **§13.7**；逆序执行，含 `[MANUAL_ROLLBACK_REQUIRED]` 项） |
| **DEPLOY-017 ~ 021** | **REV-14 增量步骤**（`git pull` / 前端重建 `npm ci && npm run build` / 发布新 `dist/` / 重启 `ib-web` / 部署后验证）—— 正向定义见 **§14.3**。**无 DB 迁移、无新依赖、无新 env 键、无 unit 或站点改动** | **ROLLBACK-017 ~ 021** | **R14 逆操作**（详见 **§14.4**；逆序执行，**不涉数据迁移**，无 `[MANUAL_ROLLBACK_REQUIRED]` 项） |

> **逆序纪律**：一旦某步失败，**立即停止后续步骤**，从该步向 DEPLOY-001 **逆序**回滚，并记录每一步结果。**R13 步骤（DEPLOY-011~016）同样适用**：失败即从该步逆序回滚（先 ROLLBACK-016 → … → ROLLBACK-011），**不跳步**。**R14 步骤（DEPLOY-017~021）同样适用**：失败即从该步逆序回滚（先 ROLLBACK-021 → … → ROLLBACK-017），**不跳步**；因 R14 **零迁移**，其回滚**不涉数据迁移**（见 §14.4）。

### 10.2 按变更类型的回滚动作

| 变更类型 | 回滚动作 | 备注 |
|----------|----------|------|
| **Qdrant 升级** | 停服 → 换回旧 `.deb` / 旧二进制 → 恢复**升级前快照**（`/var/lib/qdrant/snapshots`）→ 起服 → 校验 collection 可查 | **必须**升级前先做快照；快照与 storage **不同目录** |
| **代码版本** | `git checkout <上一版已部署 commit>` → 重启 `ib-web`/`ib-worker` | 已核验 commit 可追溯（§8） |
| **unit 变更** | 恢复上一版 unit → `systemctl daemon-reload` → 重启受影响单元 | 保留旧 unit 副本 |
| **配置 / 模型 / 权重变更** | 恢复上一版 `config.json` / `EnvironmentFile`（离线备份）→ 重启；权重目录整体保留旧版本 | 模型/配置变更后**须重跑冒烟** |
| **索引重建（collection 版本切换）** | **切换前**旧 collection 保留回滚窗口（ADR-05）；回滚 = 把台账 `active_collection_version` **写回旧值** | 重建**中途失败**：不切换 active 版本（旧集合仍可查，服务不中断） |
| **`langchain-openai` 漂移** | 强制 reinstall 到 `<0.3`：`pip install "langchain-openai>=0.2,<0.3"` → 重启 | 装配期 fail-fast 会先拦住；此为兜底 |
| **DNS / 防火墙变更** | 恢复上一版 nginx 站点与防火墙规则（`ufw`/`iptables` 备份） | — |
| **nginx 站点 / 静态产物变更**（C-02） | 恢复上一版 `sites-available/intelligentbase`（离线备份）→ `nginx -t` → `reload`；恢复上一版 `dist/` | **`nginx -t` 是 `reload` 的硬前置**；SSE 段回滚后须**复验 `proxy_buffering off` 仍在**（缺此项 = 流式静默失效） |

> `[MANUAL_ROLLBACK_REQUIRED]`：**Qdrant 数据目录恢复**与**台账 SQLite 恢复**属破坏性操作，须**人工确认 + 先备份当前状态**，不纳入自动回滚。

---

## 11. 验证清单（对齐 `src/deploy/checklists.txt`，并归档 NV-01~08 证据）

> `checklists.txt` 是**核对清单**（不是脚本），每条须在目标机**真跑**并留**可复查证据**（命令 + 原始输出 + 时间戳）。
> 其核心价值：把两类**静默降级**由「没人发现」变成「显式」——① 权重未就绪 → 检索降级为「无知识库」而问答照常；② OCR 引擎未装 → `NullOcrEngine` 静默接管 → 扫描件「成功入库 0 字」而状态仍是 `indexed`。

### 11.1 与 8 项 NV（本机不可验证项）的对应归档

| NV | 不可验证项（test_report §6） | 对齐 checklists 条目 | 部署后须归档的证据 |
|----|------------------------------|----------------------|--------------------|
| **NV-01** | 真实 bge-m3 推理（维度 / 语义质量） | **B6** | `impl=LocalHttpEmbedder`（**非** FakeEmbedder）；`dim=1024`；冷/热**两路径都返回向量**；自相似度余弦 ≈ 1；首次冷启动耗时（[TBD-T3]） |
| **NV-02** | `onnxruntime` 真实运行 | **B5 + B2** | `RapidOcrEngine().available() is True`；`recognize()` 有预期文字；**进程未 SIGILL**（[TBD-T18]）；`onnxruntime` 版本与 providers 列表（**不含 CUDA**） |
| **NV-03** | PDF **文本层**解析 | **B4（文本层 PDF）** | `page_count` / `chunks` / `chars > 0`；`warnings` 为空；耗时毫秒级（未触发栅格化） |
| **NV-04** | 扫描页 / 内嵌图 OCR | **B4（扫描件 PDF） + B5** | 触发 `pypdfium2` 栅格化 + OCR，`chars > 0`；整篇非零；页级空识别**有 WARNING**（否则为**静默失败缺陷**） |
| **NV-05** | 真实 Qdrant 写入 / 重启持久化 | **A6 / A7 / A8 / B12** | `/readyz`=200；集合名全为 `ib_<pid>_v<ver>`；**重启后数据仍在**；`LimitNOFILE=65536`；磁盘 ≥ 2× |
| **NV-06** | 目标机 embedding 延迟 / 千级 P95 | **B6 + tech_stack §4.2 第 6 项** | 单条 P50/P95（[TBD-T1]）；批量吞吐与最优批量（[TBD-T2]）；端到端检索 P95（[TBD-T6]）；**不得用开发机数据替代** |
| **NV-07** | 前端 `npm install` / `vue-tsc` / `vite build`、页面刷新 | **B12（前端产物） + §5.3** | `npm run build` 成功；`dist/` 由 nginx 托管；一次端到端问答页面可用；`vue-tsc --noEmit` 零错 |
| **NV-08** | 部署：systemd 常驻 / 开机自启 / 原生依赖真装 | **B12 + B1/B2/B3 + A4** | 四自研单元 `is-enabled=enabled` / `is-active=active`；**`nginx.service` enabled/active + `nginx -t` exit 0 + 站点含 `proxy_buffering off`**；`/healthz`=200；`python -V`=3.12.x；无 PyMuPDF；`langchain-openai<0.3` |

### 11.2 其余强制条目（摘要）

- **A1–A8**（Qdrant）：专用用户 / 目录属主 / **仅回环 6333** / unit 一致 / `LimitNOFILE` / `/readyz` / 集合前缀 / 磁盘 2×。
- **B1–B3**：Python 3.12.x；`pip install -r` 无待装项 + `langchain-openai<0.3`；**无 `fitz`/`pymupdf`**。
- **B4/B5**：PDF 三路径真跑（文本层 + 扫描件）与 OCR 真加载真识别。
- **B6**：`ib-embed` 直连验证（**用基座自己的 Embedder 调**，同时验证「服务起来了」与「客户端契约对得上」）。
- **B7**：DeepSeek 连通性 + **外发边界声明**（见 §9）。
- **B8**：SQLite `journal_mode=wal` / `busy_timeout=5000`。
- **B9**：缺 `IB_AUTHZ_POLICY*` → **退出码非零**且**不回显值**（**绝不退化为匿名放行**）。
- **B10**：SSE **`?token=` 必须 4xx**（非 200）；`Authorization` 头 SSE 返回 `text/event-stream`；**真实令牌不得出现在 nginx/waitress 访问日志**。
- **B11**：原文件留存（sha256 对象在 BlobStore）+ 删除联动；重建中途失败**不切换** active 版本。
- **B12**：四自研单元 active + **nginx `nginx -t` 通过且站点含 `proxy_buffering off`（C-02）** + `/healthz`=200 + 前端产物就位。
- **B13**：SSE 并发容量（[TBD-T15]）：**超出明确 503，不排队**。
- **B14**：日志纪律抽查——**零命中** `Bearer /token= /password /api-key`；**无问句正文、无片段原文、无完整向量**。
- **B15~B20（R13 增量；IFC-IB-332）**：**B15** HTTPS 生效（`http→301` / `https→200`；HSTS 与证书策略一致；证书/私钥 0600 且不在仓库）；**B16** 零 `Set-Cookie`（DR-10）；**B17** `?token=` / `?access_token=` 全端点（含 R13 新增）**4xx**；**B18** 默认管理员首登强制改密（服务端受限会话；绕过前端同被 403；改密撤销其它会话）；**B19** `EnvironmentFile` **0600** + `IB_DEFAULT_ADMIN_PASSWORD` **唯一落点**（仓库/日志零命中）；**B20** 迁移可前向可幂等（`--ensure-schema` 连跑无副作用）。—— 详细验收见 **§13.8（V13-1~V13-12）**。

### 11.3 签署

- [ ] 全部 A / B 条目勾选，证据（命令原文 + 时间戳）归档到 `docs/evidence/`
- [ ] 本计划相关文件自检：**无真实凭据**（`grep -nE 'sk-|ghp_|BEGIN .*PRIVATE KEY'` 零命中）
- [ ] 执行人 / 复核人 / 日期：____ / ____ / ____

---

## 12. 风险与开放项

### 12.1 风险

| # | 风险 | 影响 | 缓解 |
|---|------|------|------|
| R-01 | **Ubuntu 26.04 兼容性**（新发行版） | apt 包名/版本、Qdrant `.deb` codename、Python 3.12 可得性可能与预期不符 | §2 已标「**待实测确认**」；ADR-03 备 Q1→Q2→Q3 三级回退 |
| R-02 | **无 AVX2 → SIGILL** | 进程级崩溃（**不可捕获、非降级**）；OCR 与 embedding **两条链路各可能独立命中**且**表现不同**（embedding 挂 → 检索静默降级为「无知识库」；OCR 挂 → 扫描页解析失败 / 静默接管为 `NullOcrEngine`，见 §6.1 表）；开发机（新 CPU）可用会**掩盖**问题 | §6.1 **有序决策树 + 目标机最小探针优先**（探针**各自独立进程**）；两条链路**合并评估**；缓解 (0) 探针先行 / (1) 换无 AVX2 的 CPU wheel / (2) 自编译关 AVX2 / (3) 纯 Python 后备（embedding 走候选③、OCR 显式降级） |
| R-03 | **11 GiB 是否够同机跑 Qdrant + bge-m3 + Django** | OOM 会杀 `ib-worker`（OCR 峰值）或 `ib-embed`（模型常驻） | 各单元 `MemoryMax` 已设；**OCR + embedding 叠加峰值 [TBD-T4'] 须实测**；必要时收紧 `CPUQuota`/并发、或把 OCR 与 embedding 分时（后续可切换形态） |
| R-04 | **磁盘 78 GiB 预算** | 模型（~2.3 G）+ venv（选 ① / ② 时 `torch` 数 G）+ Qdrant（重建期 **2×**）+ Blob（内容寻址，随语料增长）叠加 | [TBD-T5] 记录实际占用；重建前核 `df -h`（≥ 2×）；选运行时 ③（无 torch）可显著省盘 |
| R-05 | **单点故障** | 目标机单机承载全部四组件；无 HA | 备份策略（Qdrant 快照 + SQLite + Blob 同批）；`Restart` 策略保证进程级自愈；跨机容灾**非本期范围** |
| R-06 | **静默降级被发现得太晚** | 权重/OCR 未就绪时系统「看起来正常」 | 靠 §11 的**显式直连验证**（不看「问答能出字」，看 `/healthz.model_loaded`、`RapidOcrEngine.available()`） |
| R-07 | **`FND-GROUP-D-03`（MAJOR，未闭合）** | 删除路径下原文件字节成孤儿 | PM 裁决：修复或书面接受（**phase_status 建议阻塞 PHASE_11**） |

### 12.2 开放项（须 PM / 用户裁决或 PHASE_11 实测闭合）

| ID | 开放项 | 类型 |
|----|--------|------|
| O-01 | **git 仓库与 remote 未建立**（B-01） | **阻塞** |
| O-02 | 目标机 SSH 凭据注入方式（B-02） | **阻塞** |
| O-03 | apt/pip 源可达性（B-03） | **阻塞** |
| O-04 | `FND-GROUP-D-03` 处置（B-04） | **阻塞** |
| O-05 | `ib-embed` 运行时三选一 + 补 requirements（B-05） | **部分闭合（R4）**：清单/来源已定（`src/requirements-embed.txt`）；**运行时三选一仍须目标机实测锁定** |
| O-06 | bge-m3 权重离线获取方式（B-06，**权重不进 git**） | **阻塞** |
| O-07 | DNS/防火墙对外端口（**C-01，仍待 PM 定**）；**C-02~C-06 已于 R4 处置**（nginx 归属 / `ib-worker.env` 模板 / Qdrant 二进制路径 / `ib_embed` 包落点 / 无 AVX2 决策树） | C-01 待澄清；C-02~C-06 已闭合 |
| O-08 | [TBD-T1/T2/T3/T4/T4'/T5/T6/T7/T15/T16/T18] 目标机实测 | PHASE_11 实测 |
| O-09 | `MemoryMax` / `IB_EMBED_MEMORY_LIMIT_MB` 数值重定（仅参数与注释，不改契约） | PHASE_11 实测 |

---

## 13. REV-13 增量：账户 / 认证 / HTTPS / 前端商用界面 部署面

> **本节为 REV-13 增量（INV-GROUP_E-INTELBASE-004），仅计划** —— **未连接、未触碰目标机**，**所有命令须 PM CONFIRM 后执行**。
> 依据：`architecture_design.md` 1.5.0（**ADR-18~27**：账户/会话落点、不透明服务端会话令牌（无 Cookie）、bcrypt 口令存储与首登强制改密、账户↔项目 1:1 绑定、与 AuthzPolicy 端口协作、前端重构与路由、粘贴令牌入口废除、HTTPS 落点、迁移/种子/回滚、登录失败限速与审计）/ `module_design.md` 1.5.0（**IFC-IB-309~332**、AccountStore 第 15 端口 IFC-IB-310）/ `tech_stack.md` 1.4.0（§1.4 客户端键、§2.2 前端依赖许可、§4.5 第 13~18 项）/ `test_report.md` 1.9.0（§18）/ `src/deploy/**`。

### 13.1 R13 交付物清单

| 交付物 | 路径 | 性质 / 交付方式 |
|--------|------|-----------------|
| 账户与会话模块 | `src/ib/core/accounts.py`、`src/ib/ledger/accounts.py`、`src/ibweb/accounts/{policy,throttle}.py`、`src/ibweb/{authz,views,urls,composition}.py` | 代码（**`git pull`** 交付） |
| 账户/会话 DDL 迁移 | `src/deploy/migrations/003_accounts.sql`（**IFC-IB-330**） | 迁移脚本（纯追加） |
| nginx TLS 终止模板 | `src/deploy/nginx/intelligentbase.conf.example`（**IFC-IB-331**） | 配置模板（占位符） |
| EnvironmentFile 模板（含 R13 键） | `src/deploy/env.example`、`src/deploy/ib-worker.env.example`（**键集逐键一致**） | 模板（纯占位符） |
| 验收清单 R13 段 | `src/deploy/checklists.txt` **`[B15]`~`[B20]`** | 核对清单 |
| 前端（Element Plus 本地打包 + vue-router + Claude 主题 + 中文） | `src/frontend/**` → `dist/` | **构建产物**（`dist/` 不入 git） |

### 13.2 依赖与迁移（bcrypt / 003_accounts.sql）

- **新依赖 `bcrypt>=4,<5`**（`src/requirements.txt` 已 pin，`src/requirements-offline.txt` 同 pin）。**只使用** `hashpw` / `gensalt` / `checkpw` 三个函数；**不用** Django `contrib.auth` / ORM。
- **迁移 = 纯追加**：`003_accounts.sql` 只 `CREATE TABLE IF NOT EXISTS users / sessions` + 索引，**不动任何既有表 / 列**；`users.password_hash` 只承载 **bcrypt 摘要**、`sessions.token_digest` 只承载 **sha256 摘要** —— **绝不落口令 / 令牌原文**（C-IB-09 / ADR-19）。
- **应用方式（正常部署无需手工执行）**：`ib-web.service` 的 `ExecStartPre`（`python -m ibweb.bootstrap --ensure-schema`）**幂等建表**（对既有 R1/R2 库同样生效）。手工核对（可选）：`sqlite3 /var/lib/intelligentbase/ledger/ledger.sqlite3 < 003_accounts.sql`。
- **幂等（B20）**：全部 `CREATE ... IF NOT EXISTS`，**重复重放无副作用**（CI 亦以此作迁移门，见 `cicd_pipeline.md` §3.2）。
- **部署前硬门 D-1（CI/CD）**：迁移脚本须与 `ib/ledger/schema.py::account_ddl_script()` **单源一致**（本文件为「可人工审阅的增量快照」）。

### 13.3 新增环境变量（R13，共 9 键；**逐键登记，全部占位符**）

> 键名权威：`module_design.md` **IFC-IB-312**（R13 增记）。**本表只登记键名与语义，不含任何值**。

| # | 键名 | 语义 | 值 / 注入方式 |
|---|------|------|---------------|
| 1 | `IB_ACCOUNT_BACKEND` | 账户存储后端 | `sqlite`（**生产**）/ `memory`（仅离线替身；生产误设表现为「每次重启都要重建账户」而非报错） |
| 2 | `IB_SESSION_TTL_SECONDS` | 会话有效期（秒） | 默认 `43200`（12h；[TBD-T22] 定稿前取保守值） |
| 3 | `IB_SESSION_RENEW_WINDOW_SECONDS` | 续期窗口（秒） | 默认 `3600`（仅剩余有效期低于窗口时才真正延长，避免无限续期） |
| 4 | `IB_PASSWORD_MIN_LENGTH` | 口令最小长度 | 默认 `8`（复杂度另要求大小写 / 数字 / 符号命中 ≥2 类，服务端裁决） |
| 5 | `IB_DEFAULT_ADMIN_USERNAME` | 默认管理员**用户名** | 默认 `admin`（**用户名非机密**） |
| 6 | `IB_DEFAULT_ADMIN_PASSWORD` | 默认管理员**初始口令** | **`<REPLACE_ME_generated_random_password>`** —— **仅**经 **0600 EnvironmentFile** 注入（见下） |
| 7 | `IB_LOGIN_MAX_FAILURES` | 登录失败阈值 | **条件性**（ADR-27 / OQ-IB-12/13 未裁决前**不设置**，保持注释） |
| 8 | `IB_LOGIN_LOCK_SECONDS` | 登录锁定窗口（秒） | **条件性**：#7 / #8 **必须成对**出现，否则组合根按未启用处理 |
| 9 | `IB_AUTHZ_POLICY_MODULE`（**R13 语义变更**） | 鉴权策略模块 | 内置账户体系 → `ibweb.accounts.policy`；**必须显式指向**（内置模块**不会**自动启用），否则组合根启动期 `StartupError`（fail-closed） |

**注入纪律（硬约束，对齐 C-IB-09 / REQ-NFR-IB-15 / checklists B19）**：

- 全部经 **0600 `EnvironmentFile`** 注入（`install -m 0600 -o ib-web -g ib-web <repo>/src/deploy/env.example /etc/intelligentbase/ib-web.env`）；`ib-worker.env` 与 `ib-web.env` **键集逐键一致**（同一代码基座另一入口，读同一份配置 / 台账 / 向量库 / LLM / 鉴权键）。
- **不落盘 / 不回显 / 不进 git**：模板被 git 跟踪，真实值**只在部署机的 0600 文件里**填入；`IB_DEFAULT_ADMIN_PASSWORD` 在仓库 / 文档 / 日志 / 测试（含示例与注释）中**零命中** —— 出现即视为**泄露事故**。
- **启动期必填校验**：生产库中无管理员且本键为空 → 组合根**启动失败**（fail-closed，不允许「无管理员可登录」的僵死实例）；任一必填项缺失 → **非零码退出 + 只报键名、不回显值**。
- **口令生成**：`python -c "import secrets;print(secrets.token_urlsafe(18))"`（在部署机执行，生成值不回显到日志 / 终端历史之外）。

### 13.4 nginx HTTPS/TLS 接入（R13）

- **以 `src/deploy/nginx/intelligentbase.conf.example` 为准**（IFC-IB-331，详见 **§7.5.1**）：`80 → 301 https` + `443 ssl`（TLSv1.2/1.3）；静态 `dist/` 于 `/var/www/intelligentbase`；`/api/`、`/healthz` 反代 `127.0.0.1:18080`（`upstream ib_web` + `keepalive 16`）。
- **三条硬条件**（缺任一即功能静默失效或全站 401）：① **`proxy_buffering off`**（SSE 不缓冲）；② **`proxy_set_header Authorization $http_authorization`**（认证走头、非 Cookie）；③ **`X-Forwarded-For`**（登录限速按客户端 IP 计数）。
- **证书策略**：内网自签 / 内网 CA；证书与私钥**不进仓库**，私钥 **0600**（建议 root 或专用证书用户）。**HSTS 仅在受信证书下启用**（自签下不启用）。
- **前端 hash 路由**（`createWebHashHistory`）→ 服务端永远只看到 `/`；`try_files $uri $uri/ /index.html` 仅为保险。
- **落盘纪律**：`install -m 0644 ... /etc/nginx/sites-available/intelligentbase` → `ln -sfn ... sites-enabled/` → **`nginx -t`（D-2 硬门）通过后**方可 `systemctl reload nginx`；回滚同样须 `nginx -t` 通过后方可 `reload`。

### 13.5 令牌纪律的部署约束（DR-10 / ADR-19）

- 会话令牌**仅经 `Authorization: Bearer <token>` 头**传递；**禁 Cookie / 禁服务端 session**（全站**零 `Set-Cookie`**）。
- **`?token=` / `?access_token=` 一律 4xx**（含 R13 新增端点 `/api/auth/me`、`/api/auth/logout`、`/api/auth/session/renew`、`/api/accounts`）。理由：查询串会被 nginx / Waitress 访问日志**完整记录**（FreeArk 已因 WS 令牌进查询串**实际泄露过一次**）。
- 前端令牌**只存 sessionStorage**（非 localStorage、非 Cookie）；登录页**已移除**粘贴访问令牌入口。
- **日志纪律**：`Bearer `/`token=`/`password`/`api-key` **零命中**；**无问句正文、无片段原文、无完整向量**（checklists B14）。

### 13.6 R13 正向部署步骤（DEPLOY-011 ~ DEPLOY-016）

> 前置：DEPLOY-001~010 已按 §10.1 完成且全绿。**每步失败即从该步逆序回滚**（§13.7）。

---
**DEPLOY-011: 基座 venv 依赖增量（bcrypt）**
- **组件**：`ib-web` / `ib-worker`（`src/requirements.txt`）
- **操作**：`sudo PYTHONUTF8=1 /opt/intelligentbase/venv/bin/pip install -r /opt/intelligentbase/src/requirements.txt`；安装后核验 `pip show bcrypt` 版本**落在 `[4,5)`**。
- **预期结果**：`bcrypt` 版本 ∈ `[4,5)`；`import bcrypt` 成功；**无** `+cuXXX` 变体被拖入（CPU-only）。
- **对应回滚**：ROLLBACK-011
- **备注**：**若目标机落不到 4.x → 暂停并上报 PM**（见 §1.3 R13-D1；不得以「API 子集可用」代替版本门）。

---
**DEPLOY-012: 账户 / 会话迁移应用（003_accounts.sql，幂等）**
- **组件**：SQLite 台账（`IB_LEDGER_PATH`）
- **操作**：`/opt/intelligentbase/venv/bin/python -m ibweb.bootstrap --ensure-schema`（**幂等**建表）；**连跑两次**确认重放无副作用。
- **预期结果**：`users` / `sessions` 两表存在（`sqlite3 ... ".tables"` 命中）；两次执行均退出码 0；既有表 / 列未变。
- **对应回滚**：ROLLBACK-012
- **备注**：**纯追加**，正常路径**无需**破坏性 DDL。

---
**DEPLOY-013: R13 环境变量经 0600 EnvironmentFile 注入**
- **组件**：`ib-web` / `ib-worker`（`/etc/intelligentbase/{ib-web,ib-worker}.env`）
- **操作**：`install -m 0600 -o <run-user> -g <group> <repo>/src/deploy/env.example /etc/intelligentbase/ib-web.env`（并对 `ib-worker.env` 同法）；按 §13.3 填 9 个 R13 键（**占位符 → 真实值只在此处**）。
- **预期结果**：`stat -c '%a %U:%G'` = `600 <run-user>:<group>`；`IB_ACCOUNT_BACKEND=sqlite`；`IB_AUTHZ_POLICY_MODULE` 已显式设置；`IB_DEFAULT_ADMIN_PASSWORD` **仅**在此文件出现。
- **对应回滚**：ROLLBACK-013
- **备注**：**含凭据**——文件须在版本控制之外**另存离线备份**。

---
**DEPLOY-014: 默认管理员播种 + 首登强制改密（校验）**
- **组件**：组合根装配（IFC-IB-314 幂等种子）
- **操作**：启动 `ib-web`（装配期执行幂等种子）；以默认管理员登录一次，确认返回**受限会话**且 `must_change_password=true`；**不在任何输出中记录初始口令**。
- **预期结果**：模拟登录 → 200 + 令牌；受限会话调其它端点 → **403**；改密后受限解除；**种子幂等**（重启不覆盖既有口令）；库中无管理员且键为空 → **启动失败**（fail-closed）。
- **对应回滚**：ROLLBACK-014
- **备注**：口令值**绝不**出现在日志 / 文档 / 响应。

---
**DEPLOY-015: nginx HTTPS/TLS 站点接入 + 静态前端产物就位**
- **组件**：系统 `nginx`（非自研 unit）
- **操作**：`install -m 0644 <repo>/src/deploy/nginx/intelligentbase.conf.example /etc/nginx/sites-available/intelligentbase` → `ln -sfn ... sites-enabled/` → 部署证书（私钥 0600）→ **`nginx -t`（D-2）** → `systemctl reload nginx`；同步 `dist/` 至 `/var/www/intelligentbase/`。
- **预期结果**：`nginx -t` **exit 0**；`http → 301 https`；`https://<host>/healthz` = **200**；站点含 **`proxy_buffering off`** 与 **`Authorization` 透传**；`index.html` 不缓存、`/assets/` 长缓存。
- **对应回滚**：ROLLBACK-015
- **备注**：**`nginx -t` 是 `reload` 的硬前置**——带语法错误重载会让对外服务**立即不可用**。

---
**DEPLOY-016: 令牌纪律与前端自包含校验**
- **组件**：传输层 + 前端产物
- **操作**：按 checklists **B16/B17** 全端点扫描：`Set-Cookie` 零命中；`?token=` / `?access_token=` **全 4xx（非 200）**；`Authorization` 头 SSE 返回 `text/event-stream`；前端产物**零运行时 CDN**（Element Plus 本地打包）。
- **预期结果**：**零** `Set-Cookie`；`?token=` 全端点 4xx；SSE 经头认证可用；`dist/` 自包含、无外网引用。
- **对应回滚**：ROLLBACK-016
- **备注**：见 §13.5。

---

### 13.7 R13 回滚步骤（ROLLBACK-011 ~ ROLLBACK-016；**逆序执行**）

> 逆操作是正向步骤的**严格逆操作**；**逆序**：最后一个部署的组件最先回滚（016 → 015 → … → 011）。

---
**ROLLBACK-011: 回退 bcrypt 依赖（逆 DEPLOY-011）**
- **回滚操作**：按 `pip freeze` 备份重建 venv，或 `pip install "bcrypt<4"` / 移除增量；**依赖备份**：DEPLOY-011 前已 `pip freeze > requirements.lock.bak`。
- **预期结果**：依赖恢复至 DEPLOY-011 前状态；`ib-web` 可起。

---
**ROLLBACK-012: 回退账户 / 会话迁移（逆 DEPLOY-012）**
- **回滚操作**：**首选 = 代码回滚**（回退 `git checkout <上一版 commit>`；**旧代码不引用新表，可直接启动**，无需破坏性 DDL）。**仅在未投产且确需清空时**：`DROP TABLE users; DROP TABLE sessions;`。
- **预期结果**：旧代码正常启动；新表不被引用。
- **备注**：`[MANUAL_ROLLBACK_REQUIRED: DROP TABLE 属破坏性操作，丢数据，须人工确认 + 先备份当前台账]`。

---
**ROLLBACK-013: 恢复上一版 EnvironmentFile（逆 DEPLOY-013）**
- **回滚操作**：恢复上一版 **0600** `ib-web.env` / `ib-worker.env` 的**离线备份**（必须在版本控制之外另存）。
- **预期结果**：环境变量恢复至注入前状态；权限仍为 0600。
- **备注**：**凭据文件不得进版本控制**。

---
**ROLLBACK-014: 回退默认管理员播种（逆 DEPLOY-014）**
- **回滚操作**：恢复播种前台账**离线快照**；或将该账户 `status` 置 `disabled`（**保留审计**，不物理删除）。
- **预期结果**：默认管理员回到播种前状态 / 被停用；不影响其它数据。
- **备注**：种子为幂等 `INSERT ... DO NOTHING`，**无部分写入**；`[MANUAL_ROLLBACK_REQUIRED: 台账快照恢复属破坏性操作，须人工确认]`。

---
**ROLLBACK-015: 恢复上一版 nginx 站点与静态产物（逆 DEPLOY-015）**
- **回滚操作**：恢复上一版 `/etc/nginx/sites-available/intelligentbase`（离线备份）→ **`nginx -t` 通过** → `systemctl reload nginx`；恢复上一版 `dist/`。
- **预期结果**：站点恢复；对外服务可用；**SSE 段 `proxy_buffering off` 复验仍在**（缺此项 = 流式静默失效）。
- **备注**：**`nginx -t` 是 `reload` 的硬前置**。

---
**ROLLBACK-016: 回退令牌纪律校验（逆 DEPLOY-016）**
- **回滚操作**：**无独立副作用**——随 ROLLBACK-015（nginx 站点）或代码回滚（`git checkout`）一并回退；若为前端产物问题，恢复上一版 `dist/`。
- **预期结果**：传输层与前端恢复至上一版行为。
- **备注**：令牌纪律**不得**作为「对调参数」被放松（DR-10 为冻结决策）。

---

### 13.8 R13 部署后验证项（Post-deployment Verification，R13 增量）

| # | 检查项 | 检查方法（命令 / URL / 工具） | 成功标准 | 对齐 |
|---|--------|------------------------------|----------|------|
| V13-1 | **HTTPS 生效** | `curl -o /dev/null -w '%{http_code}' http(s)://<host>/healthz` | http = **301**（或 444）、https = **200** | B15 |
| V13-2 | **零 Cookie** | `curl -D - -o /dev/null -k https://<host>/api/auth/login`（及 /healthz、/api/files）| **零 `Set-Cookie`** | B16 / DR-10 |
| V13-3 | **`?token=` 全 4xx** | 对 `/api/files`、`/api/chat/stream`、`/api/auth/me`、`/api/auth/logout`、`/api/auth/session/renew`、`/api/accounts` 附 `?token=x` | **全部 4xx（非 200）** | B17 |
| V13-4 | **Authorization 头可用** | `curl -H "Authorization: Bearer <令牌>" https://<host>/api/auth/me` | 200；SSE 端点返回 `text/event-stream` | B17 / B10 |
| V13-5 | **默认管理员首登强制改密** | 登录 → 受限会话调其它端点 | 受限态 **403**；**绕过前端直接调接口同样 403**（服务端为强制者） | B18 / ADR-20 |
| V13-6 | **改密后撤销其它会话** | 改密成功后，旧令牌再请求 | 旧令牌 → **401** | B18 |
| V13-7 | **运维账户项目隔离** | ops 账户访问非本 `project_id` 资源 | **403 / 404**（跨项目不可见） | checklist / REQ-FUNC-IB-32 |
| V13-8 | **令牌过期与续期** | TTL 过期后请求；窗口内调 `/api/auth/session/renew` | 过期 → **401**；窗口内 → 续期成功；窗口外 → 不延长 | IFC-IB-312 / [TBD-T22] |
| V13-9 | **迁移幂等** | `python -m ibweb.bootstrap --ensure-schema` 连跑两次 | 两次均 exit 0；`users`/`sessions` 存在且无重复 | B20 |
| V13-10 | **前端商用界面可用** | 浏览器访问 `https://<host>/`：登录 → 运维台（左导航 + 右内容 + 暗/亮主题 + 中文） | 登录后进入控制台；**零粘贴令牌入口**；刷新无 404 | NV-07 / B12 |
| V13-11 | **凭据纪律** | `git grep -n 'IB_DEFAULT_ADMIN_PASSWORD=' -- . \| grep -v REPLACE_ME`；`stat -c '%a' /etc/intelligentbase/ib-web.env` | 仓库零命中；env 文件 **600** | B19 |
| V13-12 | **日志纪律** | 抽查 nginx / waitress 访问日志 | 零 `Bearer `/`token=`/`password`/`api-key`；无问句正文 / 片段原文 | B14 |

### 13.9 R13 风险（增量）

| # | 风险 | 影响 | 缓解 |
|---|------|------|------|
| **R13-R1** | **`bcrypt` pin 漂移**（本机装到 5.0.0 ≠ `>=4,<5`） | 版本门失效；CI/生产不一致 | DEPLOY-011 强制核验版本 ∈ `[4,5)`；落不到即暂停上报（§1.3 R13-D1） |
| **R13-R2** | **HTTPS 证书链问题** | 浏览器拒访；HSTS 开启时无法降级排障 | 自签下**不启用 HSTS**；内网 CA 根证书预置到客户端信任库（§7.5.1 / B15） |
| **R13-R3** | **nginx 遗漏 `Authorization` 透传 / `proxy_buffering off`** | 全站 401 / 流式静默失效 | D-2 / D-3 硬门 + V13-4 / V13-1 复验（§13.4） |
| **R13-R4** | **默认管理员初始口令泄露**（误提交 / 误回显） | 高危凭据事故 | 仅 0600 注入；V13-11 / B19 零命中扫描；若曾误提交 → **改口令不足以消除影响，须认定泄露并轮换**（checklists B19 警告） |
| **R13-R5** | **登录限速（IP 维度）条件性未启用**（OQ-IB-12/13 未裁决；DEFECT-R13-01 已修复但功能键仍注释） | 暴力破解面 | 保持两键**成对**；裁决后启用；checklists B18 的 429 分支（[TBD-T22]） |
| **R13-R6** | **业务端口误对外** | 明文 / 未授权直连 | `ib-web` 仍绑 `127.0.0.1:18080`；Qdrant 6333 / ib-embed 8100 仅回环；nginx 为唯一对外入口（纵深防御第一层） |

---

## 14. REV-14 增量：全局管理员「当前项目」选择与 `X-IB-Project` 传播（前端产物替换 + 后端新端点，**无迁移**）

> **本节为 REV-14 增量（INV-GROUP_E-INTELBASE-005），仅计划** —— **未连接、未触碰目标机 `192.168.31.133`**；**所有命令须 PM CONFIRM 后执行**。
> 依据：`architecture_design.md` **1.6.0/REV-14**（**ADR-28** 项目上下文的选择与传播 + §2.0.5 R14 影响复核表）/ `module_design.md` **1.6.0/REV-14**（**IFC-IB-333~336**）/ `tech_stack.md` **1.4.0/REV-13（NO_CHANGE）** / `implementation_plan.md` **2.9.0/R14** / `test_report.md` **1.10.0/R14** §19 / `docs/phase_status.md`（GR-B-007 / GR-C-010 / GR-D-011 均 PASS_WITH_CONDITIONS）/ `src/ibweb/{views,urls}.py`、`src/frontend/**`（均**只读**）。

### 14.1 R14 交付物清单

| 交付物 | 路径 | 性质 / 交付方式 |
|--------|------|-----------------|
| 后端项目枚举端点 | `src/ibweb/views.py`（新增 `projects_endpoint`，IFC-IB-333）、`src/ibweb/urls.py`（新增 `GET /api/projects` 路由） | 代码（**`git pull`** 交付；**无 schema 变更、无 DB 迁移**） |
| 前端项目上下文 store | `src/frontend/src/stores/project.ts`（新增，IFC-IB-335） | 代码（`git pull` 交付） |
| 前端单点注入 + 接线 | `src/frontend/src/api/client.ts`、`src/frontend/src/app/env.ts`、`src/frontend/src/layouts/ConsoleLayout.vue`、`src/frontend/src/main.ts`（IFC-IB-336） | 代码（`git pull` 交付） |
| 前端构建产物 | `src/frontend/dist/`（**不入 git**，`npm run build` 产出） | **构建产物**（目标机构建后发布到 nginx 静态根） |
| 离线自检增量 | `src/scripts/selfcheck.py`（R14 两条用例，总计 **47/47**） | 代码 / CI 内跑（**不属部署动作**） |
| 测试增量 | `tests/integration/test_project_context_int_r14.py`、`src/frontend/tests/frontend.smoke.test.js` | 测试（**不属部署动作**，CI 内跑） |

### 14.2 变更类型判定（**关键**）

| 维度 | 判定 | 依据 |
|------|------|------|
| **DB / schema 迁移** | **无** | 项目列表数据源 = 组合根 `Deps.projects`（`IB_CONFIG_FILE` 的 `projects.<project_id>` 经 `_seed_projects` 装配）——**不新增表、不经 ORM、无 DDL**（ADR-28 / IFC-IB-333）。R13 的 `003_accounts.sql` **不涉及**，**不新增迁移脚本**。 |
| **新第三方依赖** | **无** | `tech_stack.md` **NO_CHANGE**（1.4.0/REV-13）：项目枚举走既有 Django + DRF；前端 store 沿用既有 `vue` 模块级 `reactive`（**不引 Pinia**）；SSE 沿用既有 `fetch` 读流。`package.json` / `package-lock.json` **零改动** → **无需 `npm install` 新增依赖**，仅需既有 `npm ci` + `npm run build`。 |
| **新环境变量键** | **无** | `IB-*` 键名**无新增**；`X-IB-Project` 是**请求头**、**非配置键、非凭据**。R13 的 9 键保持不动。 |
| **systemd 单元 / nginx 站点** | **无改动** | 四自研 unit 与 nginx 站点（C-02 / §7.5.1）**逐字不变**；`GET /api/projects` 由既有 `location /api/` 反代覆盖，**无需改站点**。 |
| **后端进程形态** | **仅滚动重启 `ib-web`** | 新增端点属 `ib-web`（Waitress）承载；`ib-worker` / `ib-embed` / `qdrant` **代码路径未变 → 无需重启**（见 §14.3 DEPLOY-020 理由）。 |
| **前端** | **重建 + 替换 `dist/` 静态产物** | 前端源码改动须 `npm ci && npm run build` 产新 `dist/`，由 nginx（§7.5 / C-02）托管。 |
| **交付方式** | **仅 `git pull`** | 冻结决策 ⑧；**禁 scp / pscp / rsync**。前端 `dist/` 由**目标机构建**产出（无跨机传输产物），与既有部署记录一致（`deployment_report.md` §8/§10：目标机 `npm ci` + `npm run build` → `/var/www/intelligentbase/`）。 |

> **一句话**：纯代码增量（后端新端点 + 前端改动）——**无迁移、无新依赖、无新 env 键、无 unit / 站点改动**；**风险面 ≈ 「替换 `dist/` + 重启 `ib-web`」**。

### 14.3 正向部署步骤（DEPLOY-017 ~ DEPLOY-021）

> 前置：DEPLOY-001~016 已按 §10.1 / §13.6 完成且全绿。**每步失败即从该步逆序回滚**（§14.4）。**不在本轮执行**——须 PM 的 `PRODUCTION_DEPLOY_CONFIRM=true`。

---
**DEPLOY-017: 代码交付（`git pull` 到含 R14 的 commit）**
- **组件**：全部（后端 + 前端源码）
- **操作**：`cd /opt/intelligentbase && sudo git fetch --prune origin && sudo git checkout main && sudo git pull --ff-only`；随后 `git -C /opt/intelligentbase rev-parse HEAD` 核对 commit。
- **预期结果**：`HEAD` == 预期 R14 commit（可追溯，§8）；`git status` 工作树干净。
- **对应回滚**：ROLLBACK-017
- **备注**：**仅 `git pull`**——禁 scp / pscp / rsync（冻结决策 ⑧）。`dist/` 不入 git（`.gitignore`），故 pull 不含前端产物。

---
**DEPLOY-018: 前端重建（`npm ci` + `npm run build`）**
- **组件**：前端（MOD-IB-24）
- **操作**：`cd /opt/intelligentbase/src/frontend && npm ci && npm run build`（`build` = `vue-tsc --noEmit && vite build`）。
- **预期结果**：`vue-tsc` **零错**；`vite build` 成功；`src/frontend/dist/index.html` + `dist/assets/*` 产出。
- **对应回滚**：ROLLBACK-018
- **备注**：`package.json` / `package-lock.json` **零改动** → `npm ci` 仅按既有锁复现，**不新增依赖**（与 R10 的 `EUSAGE` 教训对齐：锁须同步，本增量未动锁）。

---
**DEPLOY-019: 发布新 `dist/` 到 nginx 静态根（原子目录替换）**
- **组件**：系统 nginx 静态根（C-02；`/var/www/intelligentbase/`）
- **操作**（**本机文件操作，非跨机传输**；须 PM CONFIRM 后执行）：
  ```bash
  # 先备份旧产物，再原子替换（避免残留旧哈希资源 → 白屏）
  sudo rm -rf /var/www/intelligentbase.prev && sudo mv /var/www/intelligentbase /var/www/intelligentbase.prev
  sudo install -d -o www-data -g www-data /var/www/intelligentbase
  sudo cp -a /opt/intelligentbase/src/frontend/dist/. /var/www/intelligentbase/
  ```
- **预期结果**：`/var/www/intelligentbase/index.html` 与 `assets/` 为新构建；旧产物留存于 `/var/www/intelligentbase.prev`（回滚用）。
- **对应回滚**：ROLLBACK-019
- **备注**：**不用 rsync / scp**（冻结决策 ⑧）——构建在目标机进行，产物**本机发布**；站点文件未改，故**不涉 `nginx -t`**（若同批动了站点则须先 `nginx -t`，见 D-2）。

---
**DEPLOY-020: 后端滚动重启 `ib-web.service`（Waitress）**
- **组件**：`ib-web`（MOD-IB-23；承载 `GET /api/projects`）
- **操作**：`sudo systemctl restart ib-web`；随后 `systemctl is-active ib-web` 与 `journalctl -u ib-web -n 30 --no-pager` 抽查启动日志。
- **预期结果**：`ib-web` **active**；启动日志含 `Serving on http://127.0.0.1:18080`、**无鉴权 / 装配报错**；`GET /healthz` = 200。
- **对应回滚**：ROLLBACK-020
- **备注**：**不重启 `ib-worker` / `ib-embed` / `qdrant`**——理由：① 本增量**未改**这三者的代码路径（`views.py` 属 `ib-web`；`ib-worker` 未改；`ib_embed` / Qdrant 未改）；② `ib-web.service` 对 `qdrant` / `ib-embed` 为 `After=` + `Wants=`（**非 `Requires`**），重启 `ib-web` 不影响下游；③ `GET /api/projects` 数据源 `Deps.projects` 在 `ib-web` 进程内装配，与 `ib-worker` / `ib-embed` 无关。**除非** PM 同时批准 R14 以外的变更，否则**不扩大重启面**（最小影响原则）。

---
**DEPLOY-021: 部署后验证（§14.5 全部条目）**
- **组件**：端到端（HTTP / SSE / 前端）
- **操作**：逐条执行 §14.5 验证清单（含 admin 选项目后 `GET /api/config/definition` 由 **503 转 200** 的**直接验收**）。
- **预期结果**：§14.5 全部条目标注 SUCCESS。
- **对应回滚**：ROLLBACK-021（验证失败 → 按 §14.4 逆序回滚）
- **备注**：验证须**离线可判**（curl / 服务端读取，不依赖浏览器 UI 手测）。

---

### 14.4 回滚步骤（ROLLBACK-017 ~ ROLLBACK-021；**逆序执行**）

> **逆序**：最后一个部署的组件最先回滚（021 → 020 → … → 017）。**本增量无 DB 迁移 → 回滚不涉数据迁移**（不丢数据、不需 `DROP TABLE` / 台账快照恢复）。

---
**ROLLBACK-021: 撤销验证（逆 DEPLOY-021）**
- **回滚操作**：**无独立副作用**——随 ROLLBACK-017~020 一并回退（代码 / 产物 / 重启）。若验证暴露的是前端产物问题，优先走 ROLLBACK-019。
- **预期结果**：系统回到上一版行为。

---
**ROLLBACK-020: 回退 `ib-web` 至上一版（逆 DEPLOY-020）**
- **回滚操作**：`git checkout <上一版已部署 commit>`（见 ROLLBACK-017）后 `sudo systemctl restart ib-web`。
- **预期结果**：`ib-web` active 且运行**上一版代码**；`GET /api/projects` 在旧代码下返回 **404**（端点不存在，旧行为）。
- **备注**：与 ROLLBACK-017 联动（先回代码再重启）。

---
**ROLLBACK-019: 恢复上一版 `dist/`（逆 DEPLOY-019）**
- **回滚操作**：
  ```bash
  sudo rm -rf /var/www/intelligentbase && sudo mv /var/www/intelligentbase.prev /var/www/intelligentbase
  ```
- **预期结果**：nginx 静态根回到上一版产物；`/` 返回上一版 `index.html` 与哈希资源（**资源与 `index.html` 同版，不白屏**）。
- **备注**：**不动 nginx 站点文件**（本增量未改站点）→ **无需 `nginx -t` / `reload`**。

---
**ROLLBACK-018: 丢弃新构建产物（逆 DEPLOY-018）**
- **回滚操作**：`rm -rf /opt/intelligentbase/src/frontend/dist`（构建产物，可重生成）；代码回滚见 ROLLBACK-017。
- **预期结果**：无遗留新产物；再次部署时可重新构建。

---
**ROLLBACK-017: 代码回退到上一版已部署 commit（逆 DEPLOY-017）**
- **回滚操作**：`cd /opt/intelligentbase && sudo git checkout <上一版已部署 commit>`（例如 R13 的 `9e75c61`）→ `sudo systemctl restart ib-web`。
- **预期结果**：`git rev-parse HEAD` == 上一版 commit；`ib-web` 运行旧代码；既有认证契约（改密态 / 角色 / `?token=` 4xx / 零 `Set-Cookie`）**不受影响**。
- **备注**：**无迁移** ⇒ 旧代码可**直接**启动（R14 未新增表 / 列，回退无残留 DDL 依赖）；`X-IB-Project` 头在旧代码下被忽略（旧前端也不发头）。

---
> **回滚数据安全结论**：R14 **零 DB / schema 变更**（§14.2）——回滚仅涉及「代码 + 静态产物 + 重启」，**不触碰台账 SQLite、Qdrant collection、Blob 目录、EnvironmentFile**，**无数据丢失风险**，**无需离线快照**（对照 §13.7 的 `[MANUAL_ROLLBACK_REQUIRED]`——R14 无此类项）。

### 14.5 部署后验证清单（V14-1 ~ V14-9；**实测口径**）

> 全部为**离线可判**（curl / 服务端读取）；`<host>` 与 `<令牌>` 由执行人注入（令牌**不回显、不入日志**，checklists B14）。

| # | 检查项 | 检查方法（命令 / URL） | 成功标准 |
|---|--------|----------------------|----------|
| **V14-1** | **端点已注册** | `curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer <令牌>" https://<host>/api/projects` | **200**（未认证 → 401；`?token=` → 4xx） |
| **V14-2** | **admin 见全部项目** | 以 **admin** 令牌 `GET /api/projects` | `items` = **全部已登记项目**；未选定当前项目时全部 `is_current=false` |
| **V14-3** | **ops 仅见自身** | 以 **ops** 令牌 `GET /api/projects` | `items` **长度恒为 1** 且 = 该 ops 绑定项目（`is_current=true`）；**不枚举他项目** |
| **V14-4** | **回归修复直接验收**（核心） | ① admin **无头** `GET /api/config/definition` → 记基线；② admin 带 `X-IB-Project: <项目>` 再 `GET /api/config/definition` | ① **503**（fail-closed）；② **200**（**503 → 200**，R13 回归缺陷修复的**直接证据**） |
| **V14-5** | **ops 跨项目被拒** | ops 令牌带 `X-IB-Project: <非自身项目>` `GET /api/config/definition` | **403 `project_mismatch`** |
| **V14-6** | **未选项目仍 fail-closed（实测口径，逐端点陈述）** | admin **无头**分别请求：`/api/config/definition`、`/api/files`（GET）、`/api/chat/stream?q=…&session_id=…`、`/api/rebuild` | **实测**：`/api/config/definition` = **503**；`/api/files` GET = **200 且 `items` 为空**（零匹配，无数据泄露）；`/api/chat/stream` 与 `/api/rebuild` = **500**（R13 既有行为，见 R14-OBS-02）。**共同判据 = 不返回任何项目的业务数据**（**不得**笼统写成「全部 503」） |
| **V14-7** | **前端随 SSE 携带 `X-IB-Project`** | 浏览器抓包 / 前端行为用例：admin 选定项目后发起 `GET /api/chat/stream`（SSE，`fetch` 读流） | SSE 请求头含 `X-IB-Project: <当前项目>`（`chatStream` / `chatResume` 同经 `client.ts` 的 `headers()` 注入）；**不含 `?token=`**；响应 `Content-Type: text/event-stream` |
| **V14-8** | **认证契约零破坏** | 登录 → `/api/auth/me`；各端点附 `?token=`；检查响应头 | 登录 200 且 **零 `Set-Cookie`**；`?token=` **全 4xx**；改密态仍 **403 `password_change_required`** |
| **V14-9** | **前端可用（人工）** | 浏览器 `https://<host>/`：admin 登录 → 侧栏项目选择器出现 → 选项目 → 切至问答 / 文件 / 重建 / 可视化配置页 | 四类项目级页面可用；切换项目后**页面重挂载**（`<router-view :key>`，无旧项目串项显示）；ops 侧栏为**只读**项目标签、**无选择器** |

> **口径纪律（重要）**：V14-6 必须以**实测口径**逐端点陈述（`503` / `200 空` / `500` 三种并存），**不得**笼统写「全部 503」——此系 `test_report.md` §19.5 **R14-OBS-02** 的正式更正：`/api/chat/stream` 与 `/api/rebuild` 返回 **500** 是 **R13 既有**行为（`error_response` 对 `IbError` 统一映射 500），R14 **未改**该路径；fail-closed 仍成立（不返回任何项目数据）。
> **SSE 判据**：`EventSource` **不能**设自定义头，本项目既有实现已改用 `fetch` 读流，故 SSE 携带 `X-IB-Project` **可行**（ADR-28 / ADR-11）；`proxy_buffering off`（§7.5 / 硬门 **D-3**）仍为该链路的功能正确性硬条件。

### 14.6 风险与前置（承前挂账，如实结转）

| # | 项 | 状态 / 处置 |
|---|----|-------------|
| **R14-P0-1** | **CRED-01（未提交工作包）** | **未闭合，连续结转**（GR-B-007 → GR-C-010 → GR-D-011）。R14 改动集（13 modified + 2 untracked + `docs/rev14_project_context_apply_package.md`）**仍在工作区未提交**；**PHASE_11 部署的前置 = 先提交并 push**，且提交时**不得**把未跟踪的工作包（含 R13 的 `docs/rev13_auth_ui_apply_package.md`，其含口令字面量）**按原样纳入**。**本代理本轮未 commit / push / `git add`**（越权）。 |
| **R14-P0-2** | **git remote 与目标机可达性（原 B-01~B-03）** | 既有部署（`deployment_report.md` §7/§8/§9/§10）已**实证** `git pull --ff-only` 与 `systemctl restart` 在目标机可用 → 原 §1.1 的 **B-01 / B-02 / B-03 在实务上已闭合**（本计划仍**保留其原始登记、不擅改**）。**前置**：R14 的 commit **须已 push 到目标机所拉取的 remote/main**，否则 `git pull` 拉不到 R14。 |
| **R14-P0-3** | **目标机 Node / npm 可用性** | 既有部署（§8/§10）已在目标机执行 `npm ci && npm run build` 成功 → Node 可用。**前置**：PHASE_11 预检确认 `node -v` / `npm -v` 仍可用（若目标机环境变更则须先补装）。 |
| **R14-P1-1** | **B-04 `FND-GROUP-D-03`（MAJOR，blob 孤儿）** | **未闭合**（`docs/phase_status.md` 建议阻塞 PHASE_11）。R14 **不涉及**该路径；但作为 PHASE_11 的**总前置**须由 PM 裁决（修复或书面接受风险），**不因 R14 而被掩盖**。 |
| **R14-P1-2** | **B-05 / B-06（`ib-embed` 运行时三选一 / bge-m3 权重）** | **部分闭合 / 未闭合**（承前）。R14 **不涉及** embedding 链路；PHASE_11 的总前置不变。 |
| **R14-P1-3** | **R14-OBS-01 / 02 / 03**（LOW） | 承 GROUP_D 登记：① `headers()` 的 `extra` 透传不变式**仅在 provider 非空时成立**（**无生产调用点触发**）；② 未选项目时部分端点 **500**（R13 既有，见 V14-6 口径）；③ 其余观测。**均非阻塞**，登记不修。 |
| **R14-P1-4** | **R14 OPEN ITEM（需求侧缺口）** | 「项目选择 UX」与「`GET /api/projects`」**无独立 REQ / AC**（ADR-28 / `architecture_design.md` §10.1 R14 行 / `module_design.md` §9.8）——**登记不发明**，待 **GROUP_A** 裁决；**不阻塞部署**（可映射至 AC-IB-24-03 / AC-IB-24-02 / REQ-FUNC-IB-31 / REQ-FUNC-IB-23）。 |
| **R14-P1-5** | **前端缓存与白屏** | 部署新 `index.html` 指向新哈希 `assets/*`；若旧 `index.html` 被缓存 + 旧哈希资源被删 → 白屏。**缓解**：§7.5.1 的 `location = /index.html { Cache-Control: no-store }` + `/assets/` 长缓存（既有站点已含，R14 不改）；ROLLBACK-019 的**整目录替换**（非增量拷贝）亦消除残留旧哈希。 |
| **R14-P1-6** | **`X-IB-Project` 未知项目名** | 服务端对全局主体**不校验项目存在性**（`effective_project` 即为头值），项目级端点因此 fail-closed。**不阻塞**；V14-6 已覆盖（`p_ghost` → 项目级端点 503）。 |

---

## 附：本轮的自我约束声明

- 本文件为**计划**，**未执行任何目标机写操作**；**未连接** `192.168.31.133`；**未** SSH / rsync / scp / apt / pip / systemctl；**未触碰** `tests/`、`architecture/`、`requirements/`、`docs/phase_status.md`（PM 独占）、FreeArk 仓库（严格只读）。
- **src/ 仅按本轮授权改动两处**：① 新增 `src/deploy/ib-worker.env.example`（纯占位符，键集与 `env.example` 逐键一致，未新增/改名任何键）；② `src/deploy/systemd/qdrant.service` 的 `ExecStart` **一行**（统一为 `/usr/bin/qdrant`）。其余 `src/` 一律只读。
- 所有命令均为**计划内容**，标注「须 PM CONFIRM 后执行」。
- 全文**不含任何真实凭据 / 口令 / 令牌**；SSH 口令以「日后经环境变量注入」表述；主机指纹为**非 secret** 的 host key 校验值，按任务要求登记。
- **PHASE_11（实际生产部署）保持 PENDING，禁止执行**，直至收到 PM 的 `PRODUCTION_DEPLOY_CONFIRM=true`（且建议先闭合 `FND-GROUP-D-03`）。
- **REV-13 增量边界（前轮，INV-GROUP_E-INTELBASE-004）**：本代理**未连接、未触碰** `192.168.31.133`；**未执行**任何 SSH / 写操作 / 安装 / 服务启停 / `nginx` 写；**未 commit / push**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md`；**未触发 PHASE_11**（**未**自赋 `PRODUCTION_DEPLOY_CONFIRM`）。§13 **只登记计划与回滚**，全部命令须 PM CONFIRM 后执行。
- **REV-14 增量边界（本轮，INV-GROUP_E-INTELBASE-005）**：本代理**未连接、未触碰** `192.168.31.133`；**未执行**任何 SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（含 R14 交付物，全程只读）/ `tests/**` / 设计真源四文档 / `docs/phase_status.md` / `docs/test_*.md`；**未触发 PHASE_11**，且**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**（本代理**未**、也**不得**自赋）。**本轮仅改两个文档**：本文件（`deployment_plan.md` 1.2.0 → **1.3.0/REV-14**）与 `docs/cicd_pipeline.md`（1.2.0 → **1.3.0/REV-14**），另同步 `.github/workflows/ci.yml` 的**注释基线标签**（239 → 245 / 123 → 129 / 13 → 21，纯注释、不改 step 逻辑）。§14 **只登记计划与回滚**，全部命令须 PM CONFIRM 后执行。

---

## 修订记录（Revision History）

| 版本 | 轮次 | 日期 | 调用 ID | 变更摘要 | 依据事实 |
|------|------|------|---------|----------|----------|
| 1.0.0 | PHASE_10 首版 | 2026-09-26 | INV-GROUP_E-INTELBASE-001 | 首版（GR-E-001 = PASS_WITH_CONDITIONS，**对该 R4 前版本有效**） | architecture / module_design / tech_stack / ib_embed 契约 / `src/deploy/**` |
| 1.1.0 | GROUP_E / R4（REV-04-3） | 2026-09-26 | INV-GROUP_E-INTELBASE-002 | **C-02**：§7 改题 + 新增 §7.5 nginx（第 5 交付组件）；§10.1 DEPLOY-009 与 §10.2 补 nginx 行。**C-03**：§7.4 / §7.6 改用新增的 `ib-worker.env.example`。**C-04**：§7.1 / §3.2 / §3.5 统一 Qdrant 二进制路径。**C-05**：新增 §8.1 软链方案。**C-06**：§6.1 重写为有序决策树。**B-05**：§1.1 / §2.2 / §4.2 反映 `src/requirements-embed.txt`。§1.2 C-02~C-06 标状态；§11 / §12 更新；status → REVISED_PENDING_REVIEW | `settings.py` 无 `STATIC_ROOT`（已核验）；`vite.config.ts` 生产注释（反代 127.0.0.1:18080）；`ib-worker.service:42`；`qdrant.service:35`；`ib-embed.service`（WorkingDirectory/ExecStart）；`src/requirements-embed.txt` |
| **1.2.0** | **GROUP_E / REV-13** | **2026-10-06** | **INV-GROUP_E-INTELBASE-004** | **REV-13 增量（认证 / 会话 / 多项目运维账户 / Claude 风格可商用前端 / HTTPS）**：① header 补 revision=REV-13、上游输入升 R13、新增「REV-13 增量声明 + 门控前置备注」；② 新增 **§1.3**（R13 部署前实测项 R13-D1~D5）；③ 新增 **§7.5.1**（HTTPS/TLS 终止站点，以 `src/deploy/nginx/intelligentbase.conf.example` 为准 + 8 项新增硬条件 + HSTS 纪律）；④ §10.1 补 DEPLOY-011~016 / ROLLBACK-011~016 行（明细见 §13）；⑤ 新增 **§13**「REV-13 增量部署面」（13.1 交付物 / 13.2 bcrypt+003 迁移 / 13.3 九键环境变量（0600 注入，含 `IB_DEFAULT_ADMIN_PASSWORD`）/ 13.4 nginx HTTPS / 13.5 令牌纪律 / 13.6 正向步骤 DEPLOY-011~016 / 13.7 回滚 ROLLBACK-011~016 / 13.8 验证 V13-1~12 / 13.9 风险 R13-R1~R6）；⑥ 附自检补 R13 边界；status → REVISED_PENDING_REVIEW | `architecture_design.md` 1.5.0/REV-13（ADR-18~27）；`module_design.md` 1.5.0/REV-13（IFC-IB-309~332）；`tech_stack.md` 1.4.0/REV-13（§1.4 / §2.2 / §4.5）；`test_report.md` 1.9.0/§18；`src/deploy/migrations/003_accounts.sql`；`src/deploy/nginx/intelligentbase.conf.example`；`src/deploy/env.example`（R13 键）；`src/deploy/checklists.txt` [B15]~[B20]；`src/requirements.txt`（`bcrypt>=4,<5`）；`docs/phase_status.md`（GR-B-006 / GR-C-009 / GR-D-010） |
| **1.3.0** | **GROUP_E / REV-14** | **2026-10-06** | **INV-GROUP_E-INTELBASE-005** | **REV-14 增量（R13 回归缺陷修复：全局管理员「当前项目」选择与 `X-IB-Project` 传播）**：① header 补 revision=REV-14、版本 1.2.0→**1.3.0**、上游输入升 R14、新增「REV-14 增量声明 + R14 变更面 + 门控前置备注」；② §10.1 补 DEPLOY-017~021 / ROLLBACK-017~021 行 + 逆序纪律补 R14 句；③ 新增 **§14**「REV-14 增量部署面」（14.1 交付物 / **14.2 变更类型判定：无迁移·无新依赖·无新 env 键·无 unit/站点改动** / 14.3 正向步骤 DEPLOY-017~021（`git pull` → `npm ci && npm run build` → 发布新 `dist/` → 重启 `ib-web`，**不重启 `ib-worker`/`ib-embed`/`qdrant` 并给理由**）/ 14.4 回滚 ROLLBACK-017~021（逆序，**不涉数据迁移**）/ **14.5 验证 V14-1~9（含 admin 选项目后 `/api/config/definition` 503→200 直接验收；未选项目逐端点实测口径：config/definition 503 / files 200 空 / chat/stream 与 rebuild 500，不得笼统「全部 503」）** / 14.6 风险与前置（CRED-01 结转 + B-01~B-03 实务已闭合 + B-04/B-05/B-06 承前 + R14-OBS + OPEN ITEM））；④ 附自检补 R14 边界；status → REVISED_PENDING_REVIEW（待 GR-E-005） | `architecture_design.md` 1.6.0/REV-14（ADR-28 / §2.0.5）；`module_design.md` 1.6.0/REV-14（IFC-IB-333~336）；`tech_stack.md` 1.4.0/REV-13（NO_CHANGE）；`implementation_plan.md` 2.9.0/R14；`test_report.md` 1.10.0/R14 §19（Python 245 / 前端 21 / selfcheck 47）；`docs/phase_status.md`（GR-B-007 / GR-C-010 / GR-D-011）；`src/ibweb/{views,urls}.py`；`src/frontend/src/{stores/project.ts,api/client.ts,app/env.ts,layouts/ConsoleLayout.vue,main.ts}` |

> 本修订为**纯文档 / 部署产物修订**：**未执行**任何部署步骤，**未连接、未触碰**目标机 `192.168.31.133`。
> **1.2.0（REV-13）本轮边界**：**未连接、未触碰**目标机；**未 commit / push**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md`；**未触发 PHASE_11**。R13 轮次**未改任何 `src/` 交付物**（R13 交付物由 GROUP_C 产出，本代理只读引用）。
> **1.3.0（REV-14）本轮边界（INV-GROUP_E-INTELBASE-005）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何 SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md` / `docs/test_*.md`；**未触发 PHASE_11**，**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**（PHASE_11 保持冻结）。本轮**仅改两个文档**（`deployment_plan.md` / `cicd_pipeline.md`，均 1.2.0 → **1.3.0/REV-14**）+ 同步 `.github/workflows/ci.yml` 的**注释基线标签**（纯注释，不改 step 逻辑）。
