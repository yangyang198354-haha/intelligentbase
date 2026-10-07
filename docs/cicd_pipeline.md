<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-CICD-001 |
| 标题 | intelligentbase 智能知识库基座 —— CI/CD 流水线定义 |
| 产出代理 | devops-engineer (author_agent) |
| 调用 ID | INV-GROUP_E-INTELBASE-006（**REV-18 增量**；前序 -005 / -004 / -002 / -003） |
| 项目 | intelligentbase |
| 阶段 | GROUP_E / PHASE_10（部署计划配套；**仅定义，不执行**） |
| revision | **REV-18**（系统管理三分：项目注册表 CRUD / 唯一运维账号 / LLM Key 管理（载体 = DB）/ 项目域资料上传——**含 2 个新迁移 `005_projects.sql` / `006_llm_key.sql`（`kb_default` 前向数据迁移）+ 2 个新 env 键；无新第三方依赖**） |
| 版本 | **1.4.0**（REV-18 增量；同步 REV-18 测试基线 Python **351** / 前端 **35** / selfcheck **51**） |
| status | **APPROVED**（**GR-E-006 = PASS_WITH_CONDITIONS**，经协调者独立核验并由用户 2026-10-07 接受；GR-E-005 对 1.3.0/REV-14 有效、GR-E-004 对 1.2.0/REV-13 有效、GR-E-003 对 1.1.1/R10 有效、GR-E-002 对 1.1.0 有效、GR-E-001 对 R4 前版本有效）。**GR-E-006 协调者复核订正**：§2 后「R18 基线同步说明」的 REV-18 前端增量由 `+14` 改为 `+6`（29 → 35；原值算术有误）。§9.2 基线表本即正确（35/35），未改 |
| 创建日期 | 2026-09-26 |
| 更新日期 | 2026-10-07（REV-18 增量） |
| 凭据纪律 | 本文件不含任何真实凭据；CI 凭据一律经 CI secret / 环境变量注入，不入仓库 |
| 前置 | **git 仓库与 remote 尚未建立**（见 `deployment_plan.md` §1.1 B-01）——本流水线在其闭合前**无法被触发** |

> 本文件是 `docs/deployment_plan.md` 的配套。**工具链均取自 `src/` 既有交付物**，未虚构工具：pytest（`tests/`）、`scripts/selfcheck.py`（离线自检）、`manage.py check`、`src/frontend` 的 `npm run build` 与 `npm test`（Node 20 内置 `node:test`）、`src/requirements*.txt`、`src/deploy/migrations/*.sql`、`src/deploy/checklists.txt`。
> **本基座禁 Docker**（DR-03）——CI 使用**裸 runner / 虚拟环境**，不使用容器镜像作为交付物（见 §5）。
> **REV-13 增量声明（前轮，INV-GROUP_E-INTELBASE-004）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未 commit / push**；**未触发 PHASE_11**。R13 增量见 **§2 阶段表基线修正 / §3 硬门 / §3.2 迁移门 / §7 端到端问答 smoke**；工作流落地文件 `.github/workflows/ci.yml` **已在仓库存在**并增量更新（见 §8）。
>
> **REV-14 增量声明（前轮，INV-GROUP_E-INTELBASE-005）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push**；**未触发 PHASE_11**（该轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**）。
> **R14 变更面对 CI 的影响**：R14 为**纯代码增量**（后端新增 `GET /api/projects`、前端 `projectContext` store + `client.ts` 单点注入 `X-IB-Project`）——**无迁移、无新依赖、无新 env 键、无 `package.json` / `package-lock.json` 改动**。故本流水线的**阶段结构（10 阶段）与硬门集合均不变**，仅需 ① **同步测试基线**（Python **245** = unit 95 / integration 129 / e2e 21；前端冒烟 **21**；selfcheck **47/47**）与 ② **版本标识升位**。CI 命令本身**计数无关**（`pytest tests/unit -q` 对 239 与 245 同样判「全绿」），故 R14 对 CI 是**标签/注释层同步**，**不新增 / 不删除任何 step**。工作流落地 `.github/workflows/ci.yml` 同步其**注释基线标签**（见 §8）。

> **REV-18 增量声明（本轮，INV-GROUP_E-INTELBASE-006）**：本文件为 **PHASE_10 定义层增量**——**仅定义，未执行**；**未连接、未触碰目标机 `192.168.31.133`**；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未触发 PHASE_11**（本轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**）。**本轮仅更新两个文档**（本文件 `cicd_pipeline.md` 1.3.0 → **1.4.0/REV-18** 与 `docs/deployment_plan.md` 1.3.0 → **1.4.0/REV-18**），**未改 `.github/workflows/ci.yml`**（R18 无 CI 逻辑改动，仅**如实登记** §3.2 迁移门未覆盖 `005`/`006`）。R18 增量见 **§2 基线同步 / §3 版本门 / §3.2 迁移门登记 / §5 矩阵 / §7 smoke / §8 工作流 / §9 增量节**。
> **R18 变更面对 CI 的影响（关键）**：R18 为**代码 + 2 迁移 + 2 env 键**增量（项目注册表 CRUD / 唯一运维账号 / LLM Key 管理（载体 = DB）/ 项目域资料上传 `kb_id ≡ project_id` 推导），**零新第三方依赖（`tech_stack.md` NO_CHANGE）、零新增模块（仍 26）、零新增依赖边、无 unit / nginx 站点改动、无 `package.json` / `package-lock.json` 改动**。故本流水线的**阶段结构（10 阶段）与硬门集合均不变**，仅需 ① **同步测试基线**（Python **351** = unit **157** / integration **170** / e2e **24**，0 skip/xfail；前端冒烟 **35**；selfcheck **51/51**）与 ② **版本标识升位**。**须如实登记**：R18 的两个新迁移 `005_projects.sql` / `006_llm_key.sql` **未纳入 §3.2 迁移门**（该门当前**只覆盖 `003_accounts.sql`**）——这是**本轮已知的 CI 覆盖缺口**（见 §3.2 / §9.3），**不得**当作「已覆盖」隐性略过。**本代理未改 `.github/workflows/ci.yml`**（超出本轮授权面），建议随下轮授权扩展。

## 1. 流水线概览

```
[Source] → [Config+Schema] → [Unit] → [Integration] → [E2E] → [Version-Gate] → [Frontend Build+Test] → [Package Artifact]
                 │                                                                              │
                 └────────────────── 任一失败 → Abort & Notify（不进入后续阶段）────────────┘
```

**触发条件**：
- `push` 到 `main`（沿用 FreeArk 纪律：直接提交 main，不开分支+PR）→ 跑**全量**。
- `pull_request`（若未来启用）→ 跑**全量**。
- 手动触发（`workflow_dispatch`）→ 供 PHASE_11 部署前复跑。

## 2. 阶段定义表

| # | 阶段 | 触发条件 | 命令（**均取自既有交付物**） | 成功标准 | 失败处理 |
|---|------|----------|------------------------------|----------|----------|
| 1 | **Source** | push / PR | `git checkout` / `git fetch` | 拉取成功 | abort & notify |
| 2 | **Config + Schema Check** | 前阶段成功 | `python -m compileall -q src` + **迁移/模式检查**（见 §3.2） | 两者 exit 0 | abort & notify |
| 3 | **Unit** | 前阶段成功 | `python -m pytest tests/unit -q` | **全通过**（**基线 157/157 = 100%**，**R18**；R14 为 95） | abort & notify |
| 4 | **Integration** | 前阶段成功 | `python -m pytest tests/integration -q` | **全通过**（**基线 170/170 = 100%**，**R18**；R14 为 129，R1 为 123） | abort & notify |
| 5 | **E2E** | 前阶段成功 | `python -m pytest tests/e2e -q` | **全通过**（**基线 24/24 = 100%**，**R18**；含**端到端问答 smoke**，见 §7） | abort & notify |
| 6 | **Full Suite + Coverage** | 前阶段成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | **351/351 通过、0 skip/xfail**（**R18** 基线 = unit 157 + integration 170 + e2e 24）；覆盖率 **仅记录不设门** | abort & notify |
| 7 | **Offline Selfcheck** | 前阶段成功 | `python src/scripts/selfcheck.py` | 全 `PASS`，exit 0（任一 `FAIL` 非零退出） | abort & notify |
| 8 | **Version Gate** | 前阶段成功 | 见 §3 | 全部断言通过 | abort & notify |
| 9 | **Frontend Build + Test** | 前阶段成功 | `cd src/frontend && npm ci && npm run build && npm test` | `vue-tsc --noEmit` 零错 + `vite build` 成功 + **前端冒烟测试（`node:test`）35/35 全通过**（**R18**；R14 为 21，R13 为 13） | abort & notify |
| 10 | **Package Artifact** | 前阶段成功 | 归档 `src/frontend/dist/` + 记录 `git rev-parse HEAD` | 产物归档、commit 可追溯 | abort & notify |

> **R13 基线修正说明（关键）**：本表旧值（unit 55 / integration 69→73 / e2e 14 / full 142 / 前端 6）**已作废**。**以实测为准**：全量 Python 用例 **239**（unit **95** / integration **123** / e2e **21**），**0 skip / 0 xfail**；前端冒烟层 **13**（**独立一层，不并入 239 算术**——跨运行时 / 跨框架）。**依据**：`docs/phase_status.md`（REV-13，GROUP_D **GR-D-010 APPROVED，condition_1「DEFECT-R13-01 已修复并独立复跑闭合」**）+ `docs/test_report.md` 1.9.0 §18（collect 口径 239；其文件副本仍记 238 pass / 1 fail，系**闭合后未回写**的同源副本，**以 phase_status 闭合结论为准**）。
> **阶段2 说明（R13 增量）**：阶段2 在 `compileall` 之外追加 **迁移/模式检查**（§3.2）——校验 `src/deploy/migrations/003_accounts.sql` 语法合法且**幂等可重放**（对齐 checklists B20），并复核其与 `ib/ledger/schema.py::account_ddl_script()` **单源一致**。

> **R14 基线同步说明（本轮，关键）**：R14（R13 回归缺陷修复）新增 Python **3** 条（`tests/integration/test_project_context_int_r14.py`，TC-INT-126~128）+ 前端 **4** 条（`frontend.smoke.test.js` 用例 18~21）；integration **126 → 129**、前端冒烟 **17 → 21**，unit（95）/ e2e（21）不变 → **全量 Python 242 → 245**。**依据**：`docs/test_report.md` **1.10.0 / §19**（`245/245` 全绿、`0 skip/xfail/blocked`、EXIT=0；前端 `21/21`；`selfcheck.py` `47/47`）+ `docs/phase_status.md` **GR-D-011 = PASS_WITH_CONDITIONS**（四项数值 PASS 标准 SATISFIED）。**备注**：R14 用例撞号（GROUP_C 的 TC-INT-120~122 与 R13 既有占号冲突）已由 test-engineer 更正为 **TC-INT-123~125**（**计数中性**，见 test_report §19.5 R14-DEF-01）；既有编号 105~122 **一字未动**。R14 对 CI 为**标签层同步**——命令计数无关，**不新增 / 不删除 step**。

> **R18 基线同步说明（本轮，关键）**：R18（系统管理三分 + 项目 CRUD 软删 + 顺序依赖 + 唯一运维账号 + LLM Key 管理 + 项目域资料上传）相对 **REV-17**（327 = unit 149 / integration 154 / e2e 24）新增 **unit +8 / integration +16 / e2e +0 = Python 全量 +24**，前端冒烟 **+6**（29 → **35**）。**分层实测（`pytest -q --collect-only` 逐层）**：`tests/unit` = **157**、`tests/integration` = **170**、`tests/e2e` = **24** ⇒ 157 + 170 + 24 = **351** ✓。**依据**：`docs/test_report.md` **1.14.0 / §23**（`351/351` 全绿、`0 skip / 0 xfail / 0 blocked`、EXIT=0，`docs/evidence/groupd_r18_pytest_final.log`）+ `docs/phase_status.md` **GR-D-015 = PASS_WITH_CONDITIONS**（用户 2026-10-07 接受，四项数值 PASS 标准 SATISFIED）。**R18 测试文件**：新建 `tests/unit/test_rev18_system_mgmt_unit.py`（TC-UNIT-R18-001~008）+ `tests/integration/test_rev18_system_management_int.py`（GROUP_C 首跑 TC-INT-148~153）+ `tests/integration/test_rev18_system_management_extra_int.py`（TC-INT-154~162，补 HTTP 契约缺口）；前端冒烟 `src/frontend/tests/frontend.smoke.test.js` 追加**第 35 例**（既有 34 例未改）。**selfcheck** `51/51`（**R17 起即 51**，R18 **未新增**自检项，命令不变）。**备注**：R18 用例**未撞号**（R14-DEF-01 的撞号问题本轮未复现）；**e2e 层计数不变**（R18 的 e2e 相关断言在 `tests/e2e/test_user_journeys.py` 内**增强既有 TC-E2E-001** —— 断言上传 `kb_id ≡ project_id` 推导，**计数中性**）。R18 对 CI 为**标签层同步 + 一迁移门如实登记**——命令计数无关，**不新增 / 不删除 step**。

> **阶段9 说明（R10 增量）**：阶段9 在 `npm run build` **之后**追加 `npm test`——前端冒烟测试（`src/frontend/tests/frontend.smoke.test.js`，Node 20 内置 `node:test`，**零新增依赖**）。其**必须在 build 之后**运行：用例 6 断言 `dist/` 构建产物内容，属「先建后测」的前置条件顺序。该测试含「`package-lock.json` 与 `package.json` 同步」回归闸——正是 R10 中 `npm ci` 因锁失同步而 `EUSAGE` 失败的根因守卫；接入流水线后该回归守卫方具备**强制力**（此前仅本地可跑）。

> **测试纪律（来源 `CLAUDE.md` / tech_stack §1）**：所有测试必须**离线**跑（`IB_OFFLINE_MODE=1`；外部依赖一律替身）；**严禁连接任何生产 / 外部数据库**；测试使用 SQLite 内存库。CI runner 无须网络访问外部服务（仅需 PyPI / npm registry）。

## 3. 版本门（Version Gate，**硬断言**）

| 断言 | 命令 | 判据 | 依据 |
|------|------|------|------|
| `langchain-openai < 0.3` | `python -c "import importlib.metadata as m; print(m.version('langchain-openai'))"` | **< 0.3** | 冻结决策 ⑤；0.3.x 删 `_convert_chunk_to_generation_chunk` 致流式断流 |
| **禁 PyMuPDF / fitz** | `python -c "import importlib.util as u; print(u.find_spec('fitz'), u.find_spec('pymupdf'))"` | **两者均 None** | ADR-06 / 冻结决策 ④ |
| **禁 Docker** | `command -v docker`（应为空）+ 仓库内无 `Dockerfile`/`docker-compose*` | 无命中 | DR-03 |
| Python 版本 | `python -V` | `>=3.11,<3.14`（CI 目标 **3.12**） | tech_stack §1 |
| 无 `pytest`+`unittest` 混杂误用 | 测试命令统一 pytest | 与实际套件一致 | tech_stack「测试框架」行 |
| `langchain-core` 区间 | `python -c "import importlib.metadata as m; print(m.version('langchain-core'))"` | **`>=0.3,<2.0`** | 冻结决策 ⑤ / `requirements.txt` |
| **`bcrypt` 区间**（R13） | `python -c "import importlib.metadata as m; print(m.version('bcrypt'))"` | **`>=4,<5`** | DR-11 / IFC-IB-311 / `requirements.txt`（对齐 `phase_status` MINOR-R13-03） |
| **前端零运行时 CDN**（R13） | 前端冒烟用例（**R18 后共 35 例**；R14 为 21）：源码与 `dist/` 无外网引用 | 零外网引用 | DR-13 / AC-IB-17-06；`tech_stack` §4.5 |
| **凭据零命中**（R13） | `git grep -nE 'IB_DEFAULT_ADMIN_PASSWORD=' -- . \| grep -v REPLACE_ME`（期望空）+ `scripts/selfcheck.py` 的 `deploy_templates_have_no_secrets` | **零命中** | C-IB-09 / REQ-NFR-IB-15 / checklists B19 |

> 版本门是**部署路径与本地一致性**的守卫——`ibweb/composition.py` 在**装配期**也会对 `langchain-openai` 做 fail-fast 断言（test_report DEV-02 已实测该断言触发），CI 版本门是其**上游更早的一道**。
>
> **`bcrypt` 门（R13）**：`requirements.txt` 与 `requirements-offline.txt` 均 pin `bcrypt>=4,<5`；CI 经 `requirements-offline.txt` 安装，故断言在 CI 直接可判。**注意**：CI 基线（如 GitHub runner / 本机）曾实测装到 **5.0.0** —— 若断言失败即**阻断**，这正是本门的意义（部署前须把目标机落到 4.x 或由 PM 裁决放宽 pin，见 `deployment_plan.md` §1.3 R13-D1）。

### 3.1 部署前硬门（PHASE_11 前置；非构建期）

> 下列门在**部署前**（**非**每次 push 的构建期）执行；任一不过则**不得进入部署**（abort & notify，不跳过）。

| # | 硬门 | 命令 | 判据 | 依据 |
|---|------|------|------|------|
| **D-1** | **ib-embed 依赖锁定回填** | 目标机 `sudo /opt/ib-embed/venv/bin/pip freeze > /opt/intelligentbase/requirements-embed.lock.txt`，并**回填部署记录** | 装出的**精确版本**（非区间）落档；`src/requirements-embed.txt` 的**区间不得当锁定值上线** | deployment_plan §1.1 B-05 / §4.2；`src/requirements-embed.txt`「版本 pin 的诚实性说明」 |
| **D-2** | **nginx 配置语法门** | `sudo nginx -t` | **exit 0**（配置语法合法）；**之后**方可 `systemctl reload nginx` | deployment_plan §7.5（C-02）/ §10.1 DEPLOY-009 |
| **D-3** | **SSE 不缓冲复验** | `grep -n "proxy_buffering off" /etc/nginx/sites-available/intelligentbase` | 命中（SSE 段缺此项 = 流式功能**静默失效**） | deployment_plan §7.5 / §7.5.1；`ib/streaming/__init__.py`（`X-Accel-Buffering: no` 为必需） |
| **D-4** | **账户迁移幂等复验**（R13） | 目标机 `python -m ibweb.bootstrap --ensure-schema` **连跑两次** | 两次均 exit 0；`users`/`sessions` 存在且无重复 | deployment_plan §13.2；checklists **B20** |
| **D-5** | **HTTPS 生效 + 零 Cookie**（R13） | `curl` 探测 `http(s)://<host>/healthz` 与各端点 `Set-Cookie` | http = 301（或 444）/ https = 200；**零 `Set-Cookie`** | deployment_plan §13.4 / §13.5；checklists **B15 / B16** |
| **D-6** | **令牌纪律复验**（R13） | 各端点附 `?token=` / 检查 `Authorization` 透传 | `?token=` **全 4xx**；`Authorization: Bearer` 可用 | deployment_plan §13.5；checklists **B17**；DR-10 |

> **D-4~D-6 理由（R13）**：账户 / 会话 / HTTPS 是 R13 新增的**生产可用性前提**。迁移不幂等 → 重启即失败；HTTPS 未生效 / 出现 Cookie → 传输层契约破坏；`?token=` 未拒 → 令牌进访问日志（FreeArk 实际泄露史）。三者均为**部署后不可静默接受**的硬门。

> **D-1 理由**：`src/requirements-embed.txt` 明确其版本 pin 是**保守区间、不是锁定值**；上线前必须用目标机 `pip freeze` 回填精确版本，否则「部署记录里的版本」与「真实装到的版本」不可对账（区间当作锁定值是典型的**假锁定**）。
> **D-2 理由**：nginx 站点变更若带语法错误直接 `reload`，会让对外服务**立即不可用**；`nginx -t` 是 reload 的**硬前置**。**D-3** 是 C-02 引入的 SSE 正确性门（缺 `proxy_buffering off` 时问答被缓冲、首字节永不外发）。

### 3.2 迁移 / 模式门（Schema Gate，**构建期**；R13 增量）

> 与阶段 2 并跑。校验手写 scoped 迁移 **语法合法 + 幂等可重放 + 与代码单源一致**（对齐 checklists **B20**）。仅用标准库（runner 无需 `sqlite3` CLI）。

```bash
# 1) 003_accounts.sql：语法合法 + 幂等重放（CREATE ... IF NOT EXISTS）
python - <<'PY'
import sqlite3, pathlib
sql = pathlib.Path("src/deploy/migrations/003_accounts.sql").read_text(encoding="utf-8")
con = sqlite3.connect(":memory:")
con.executescript(sql)                 # 首次应用
con.executescript(sql)                 # 幂等重放（无副作用即通过）
names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
assert {"users", "sessions"} <= names, names
print("PASS: 003_accounts.sql 语法合法且幂等")
PY

# 2) 单源一致：迁移快照 == 代码生成器（ib/ledger/schema.py::account_ddl_script()）
#    注：快照按可读性重排过缩进，故折叠空白后再比对（不做逐字缩进断言）。
python -c "import sys; sys.path.insert(0,'src'); from ib.ledger.schema import account_ddl_script; import pathlib; snap=pathlib.Path('src/deploy/migrations/003_accounts.sql').read_text('utf-8'); norm=lambda s:''.join(s.split()); assert norm(account_ddl_script()) in norm(snap), '003 与代码生成器不一致'; print('PASS: 单源一致')"
```

> **判据**：两步均 exit 0。**失败处理 = abort & notify**（迁移不可重放 / 与代码漂移，直接阻断，不得跳过）。
>
> **为何 CI 可判**：`003_accounts.sql` 是 `ib/ledger/schema.py::account_ddl_script()` 的**增量快照**（单源不变）；本门把「迁移快照与代码漂移」这一典型静默缺陷变成**构建期显式失败**。

> **R18 增量登记（如实，不隐）**：R18 新增的 `src/deploy/migrations/005_projects.sql`（项目注册表 + `kb_default` 前向数据迁移）与 `006_llm_key.sql`（LLM Key 单行表）**当前未纳入本迁移门** —— 本门脚本**只覆盖 `003_accounts.sql`**，`.github/workflows/ci.yml` 阶段 2 的迁移检查**同样只校验 `003`**。这是**本轮已知的 CI 覆盖缺口**，**不得**当作「已覆盖」隐性略过（本代理**未改** `ci.yml`，见 §9.3）。**为何本轮不就地扩展**：① 改本门脚本与 `.github/workflows/ci.yml` **超出本轮授权面**（本轮只改两文档）；② `005` 的可重放门**需先应用 001 基座 DDL**（`kbs` 表由 `001` 建）方可 `executescript` 重放 —— 直接把 `005` 丢进 `:memory:` 会因缺 `kbs` 失败；`006` 无此依赖（纯 `CREATE TABLE IF NOT EXISTS`）。**建议（下轮授权）**：把 `005`/`006` 纳入本门（判据 = `schema.py::ensure_schema()` 于 `:memory:` 连跑两次 exit 0 + `kb_default` 归零 + `llm_key` 单行表存在），并同步 `ci.yml` 阶段 2。**同源登记**：`deployment_plan.md` §15.2 / §15.9。

## 4. Artifact 管理规则

- **命名格式**：`ib-<git-short-sha>-<CI-run-id>`；内含 `dist/`（前端静态产物）+ `HEAD` 文件（commit 全哈希）。
- **存储位置**：CI 制品库（**须确认可达**；见 deployment_plan §1.1 B-03）。
- **晋升条件**：全 10 阶段**绿色**才产出制品；**staging → prod 的「晋升」不在此流水线内**——本基座用「`git pull` + systemd 重启」交付（ADR-03），CI 制品**仅作前端 `dist/` 与可追溯凭据**，**不得**以制品分发替代 `git pull`（冻结决策 ⑧ 禁逐文件上传）。
- **保留**：至少保留最近 30 个制品。

## 5. 环境配置矩阵

| 配置项 | CI / Dev | Staging | Prod（`192.168.31.133`） |
|--------|----------|---------|--------------------------|
| 运行形态 | 裸 runner / venv（**无 Docker**） | venv | venv + systemd（**4 自研 unit**）+ **系统 nginx**（反代 / 静态前端；见 `deployment_plan.md` §7.5 / C-02） |
| 向量库 | `InMemoryVectorStore`（替身） | 真实 Qdrant（如启用） | 真实 Qdrant（`.deb` 裸装，**仅回环**） |
| Embedding | `FakeEmbedder` / `inproc` | `ib-embed`（真实 bge-m3） | `ib-embed`（真实 bge-m3，**CPU-only**） |
| LLM | `FakeLlmProvider` / `StubLlmProvider` | DeepSeek（测试 key） | DeepSeek（真实，**数据外发已在配置层声明**） |
| OCR | `NullOcrEngine` / 不装 | rapidocr（真装） | rapidocr + onnxruntime（**CPU 版**） |
| 台账 | SQLite 内存 / 临时文件 | SQLite | SQLite WAL（`/var/lib/intelligentbase/ledger/`） |
| `IB_OFFLINE_MODE` | `1` | `0` | **`0`（生产必须为 0；`1` 会全切替身，知识库永远为空却「看起来正常」）** |
| **账户 / 会话**（R13） | `MemoryAccountStore`（`IB_ACCOUNT_BACKEND=memory`，离线替身） | `sqlite` | **`sqlite`**（复用同一 SQLite 台账文件；误设 `memory` 表现为「重启即要重建账户」） |
| **项目注册表**（R18） | `memory` 替身（`IB_PROJECT_REGISTRY_BACKEND=memory`） | `sqlite` | **`sqlite`**（复用同一台账库文件 `projects` 表；误设 `memory` 表现为「项目全部消失、账号绑定失效」，**而非报错**——**两键均有默认值 `sqlite`，无缺失失败模式**） |
| **LLM Key 载体**（R18） | `memory` 替身（`IB_LLM_KEY_BACKEND=memory`） | `sqlite` | **`sqlite`**（复用同一台账库文件 `llm_key` 单行表；**本键只选后端、不承载 Key 值** —— Key 取值**只经 `PUT /api/llm-key`** 写入 DB，**绝不进 `.env` / git / 命令行**，见 checklists B22/B23） |
| **认证载体**（R13） | 测试替身（离线令牌） | `Authorization: Bearer`（**无 Cookie**） | `Authorization: Bearer`；**`IB_AUTHZ_POLICY_MODULE=ibweb.accounts.policy`**（或接入方模块；未配置 → 启动失败） |
| **HTTPS / TLS 终止**（R13） | 不涉及（本地 http） | 内网自签 / CA（可选） | **nginx `443 ssl`（TLSv1.2/1.3）+ `80→301`**；证书 / 私钥**不进仓库**（私钥 0600） |
| 凭据 | CI secret / 环境变量 | 环境变量 | `EnvironmentFile` 0600（**不入 git**；含 `IB_DEFAULT_ADMIN_PASSWORD`，全占位符） |

## 6. 阶段命令的失败处理策略（**总则**）

- **一律 abort-and-notify，不跳过、不 continue-on-error**。
- **禁止**任何「跳过失败继续部署」的策略（违反冻结决策与硬约束）。
- 重试：**仅**允许对**瞬时网络**类操作（如 `npm ci` / `pip install`）设**有限重试**（≤ 2），不对测试/门禁设自动重试（避免掩盖真失败）。

---

## 7. 端到端问答 smoke（**提问 → 检索 → 作答**；用户期望项，R13 核对并登记）

> **需求**：CI 必须具备一条**提问 → 检索 → 作答**的端到端冒烟项。**核对结论：已存在**于 E2E 层（阶段 5 自动覆盖），本轮**明确登记**如下。

| 项 | 值 |
|----|-----|
| **用例** | `tests/e2e/test_user_journeys.py::test_TC_E2E_001_import_then_rag_answer`（US-IB-01 导入 + **US-IB-08 带来源的检索增强回答**，关键路径） |
| **覆盖链路** | 上传文档 → worker 处理至 `indexed` → **检索命中该文档**（`degraded=False`，`hits` 含 `doc_id`）→ **SSE 问答**（`/api/chat/stream?q=…`）产出 `event: content` + `event: done` |
| **运行位置** | 阶段 5（`python -m pytest tests/e2e -q`）—— **其余 20 条 E2E 一并跑**；阶段 6 全量再覆盖一次 |
| **判据** | 全通过（**R18 后 `351/351`**，0 skip/xfail；R14 为 `245/245`）；**离线跑**（`IB_OFFLINE_MODE=1`，LLM / 向量库 / Embedding 用替身） |
| **R13 附加** | R13 E2E（`tests/e2e/test_accounts_journeys_r13.py`：TC-E2E-020 管理员→运维台全账户旅程 / TC-E2E-021 零粘贴令牌旁路）**同为关键路径**，阶段 5 一并覆盖 |
| **R14 附加** | **R14 回归修复的 CI 层守卫**在**集成层**（阶段 4）：`tests/integration/test_project_context_int_r14.py`（TC-INT-123~128：`GET /api/projects` 授权口径 / admin 选项目后 `/api/config/definition` 503→200 / ops 跨项目 403 / 未知头 fail-closed / 写方法 405）+ **前端层**（阶段 9；TC-FE-018~021：注入 fail-closed / 单项目预选 / ops 不可切换 / provider 优先）。**提示**：真实浏览器端到端（admin 于 UI 选项目）由 `deployment_plan.md` §14.5 **V14-9** 在**部署后**覆盖，**不在 CI 内**（CI 不触网、不装浏览器） |
| **R18 附加** | **R18 的 e2e 层断言增强既有 TC-E2E-001**（`tests/e2e/test_user_journeys.py`）：断言 HTTP 上传落库 **`kb_id ≡ project_id` 推导**（IFC-IB-375 / ADR-41），**计数中性**。R18 **新端点契约**的 CI 守卫在**集成层**（阶段 4）：`tests/integration/test_rev18_system_management_int.py`（TC-INT-148~153）+ `tests/integration/test_rev18_system_management_extra_int.py`（TC-INT-154~162：1:N 多账号 / **422 先于 400·409 的错误码判定顺序** / 项目软删不级联账号·保留账本 / 未配置态 `masked == ""` / **审计只记 outcome 不含密钥** / **任何响应体（含错误体）不含明文** / D-R18-01 边界清晰）；**前端层**（阶段 9，第 35 例）核对三子域 IA + 「资料管理」(files) **保持独立顶级**。**提示**：真实 **LLM Key 提交与重启生效**由 `deployment_plan.md` §15.3 **DEPLOY-031** / §15.8 在**部署后**覆盖，**不在 CI 内**（CI 不触网、不含真实凭据） |

> **纪律**：本 smoke 为**离线替身**冒烟（验证编排与端到端链路**接线正确**），**不是**真实 DeepSeek 调用。真实云端调用属**部署后**冒烟（`deployment_plan.md` §9 / checklists B7），**不在 CI 内**（CI 不触网、不外发数据）。

## 8. 工作流落地（GitHub Actions，**增量更新**）

> **平台已选定**：GitHub Actions（`.github/workflows/ci.yml` **已存在于仓库**）。本轮为**增量更新**（非新建）：**未 commit / push**。

| 项 | 值 |
|----|-----|
| 文件 | `.github/workflows/ci.yml` |
| Runner | `ubuntu-24.04`；**Python 3.12**（`actions/setup-python@v5`）；**Node 20**（`actions/setup-node@v4`） |
| 触发 | `push` main / `pull_request` main / `workflow_dispatch`（供 PHASE_11 部署前复跑） |
| 能力映射 | **build & test（Python 3.12）覆盖 REV-13 / REV-14 / REV-18 测试**：阶段 3/4/5/6 直接跑 `tests/{unit,integration,e2e}` → 自动纳入 R13 用例（`tests/**/*_r13.py`）、**R14 用例**（`tests/integration/test_project_context_int_r14.py`，TC-INT-123~128）与 **R18 用例**（`tests/unit/test_rev18_system_mgmt_unit.py`，TC-UNIT-R18-001~008；`tests/integration/test_rev18_system_management_int.py` + `_extra_int.py`，TC-INT-148~162）；阶段 9 跑前端 `npm ci && npm run build && npm test` → 纳入 R13 前端冒烟 7 例（TC-FE-007~013）、**R14 前端冒烟 4 例（TC-FE-018~021）** 与 **R18 前端冒烟（第 35 例）** |
| **R13 增量更新** | ① **阶段2**：新增 **Schema/迁移检查** step（§3.2 脚本，纯标准库）；② **基线标签修正**（unit 95 / integration 123 / e2e 21 / full 239 / 前端 13）；③ `bcrypt` 经 `requirements-offline.txt` **已在安装步骤内**（`bcrypt>=4,<5`），无需额外 step；④ **硬门**保持（禁 Docker / 禁 PyMuPDF / `langchain-openai<0.3` 与 `langchain-core>=0.3,<2.0` / Python 范围 / 仓库无容器交付物）；⑤ **凭据零命中**由阶段 7 `selfcheck.py`（`deploy_templates_have_no_secrets`）承担 |
| **R14 增量更新** | **标签/注释层同步（不新增、不删除 step、不改任何 `run` 命令）**：① **基线标签修正**（integration 123 → **129**、full 239 → **245**、前端 13 → **21**；unit 95 / e2e 21 不变）；② 阶段 7 `selfcheck.py` 现覆盖 **47/47**（含 R14 两条：`r14_project_context` 端点授权口径 + `r14_frontend_project_discipline` 单点注入 / SSE 覆盖；**计数无关**，命令不变）；③ R14 **无迁移 / 无新依赖** → **阶段2 的迁移门脚本不变**（`003_accounts.sql` 仍为唯一迁移快照）；④ R14 **无 `package.json` / `package-lock.json` 改动** → 阶段9 `npm ci` 的锁同步回归闸**不受影响**（R10 `EUSAGE` 守卫继续有效）；⑤ **硬门集合不变** |
| **R18 增量更新**（本轮） | **标签/注释层同步 + 一迁移门如实登记（不新增、不删除 step、不改任何 `run` 命令）**：① **基线标签修正**（unit 95 → **157**、integration 129 → **170**、e2e 21 → **24**、full 245 → **351**、前端 21 → **35**）；② 阶段 7 `selfcheck.py` 现为 **51/51**（**计数无关**，命令不变；R17 起即 51，R18 未新增自检项）；③ **⚠ R18 的 `005_projects.sql` / `006_llm_key.sql` 未纳入阶段 2 迁移门**（该门**只覆盖 `003_accounts.sql`）—— **本轮已知 CI 覆盖缺口**；**本代理未改 `.github/workflows/ci.yml`**（超本轮授权面），建议随下轮授权扩展（详见 §3.2 / §9.3）；④ R18 **无 `package.json` / `package-lock.json` 改动** → 阶段9 `npm ci` 的锁同步回归闸**不受影响**（R10 `EUSAGE` 守卫继续有效）；⑤ **硬门集合不变**（含 **`bcrypt>=4,<5` 门**保留，见 §3 / §9.4） |
| 纪律 | 任一 step 失败即 **abort**（原生 fail-fast，后续 step 自动跳过）；**不** `continue-on-error` |

> **注**：CI 的「禁 Docker」判据**只**校验「仓库不含 `Dockerfile` / `docker-compose*`」（GitHub 托管 runner 自带 docker CLI，`command -v docker` 会恒假阳性）；目标机的 `command -v docker` 空判据属**部署机硬门**，不在 CI。

---

## 9. REV-18 增量节（系统管理三分 / 项目 CRUD 软删 / LLM Key 管理（载体 = DB）/ 项目域资料上传）

> 本节为 **REV-18 增量**（INV-GROUP_E-INTELBASE-006）。**仅定义，未执行**；**未连接、未触碰目标机**。配套部署面见 `deployment_plan.md` **§15**；本节与 §2 / §3 / §3.2 / §5 / §7 / §8 的 R18 增量补注**同源一致**。

### 9.1 R18 对 CI 的净影响（结论：**零 step 改动**）

| 维度 | R18 值 | 对 CI 的影响 |
|------|--------|--------------|
| **阶段结构** | 10 阶段**不变** | **不新增 / 不删除 step** |
| **硬门集合** | **不变**（含 **`bcrypt>=4,<5` 门保留**） | 版本门命令逐字不变 |
| **测试基线** | Python **351** = unit 157 / integration 170 / e2e 24；前端 **35**；selfcheck **51** | **标签/注释层同步**（命令**计数无关**） |
| **迁移** | 新增 `005_projects.sql` / `006_llm_key.sql` | **⚠ 未纳入阶段 2 迁移门**（见 §9.3，**缺口登记**） |
| **第三方依赖** | **零新增**（`tech_stack.md` NO_CHANGE；复用 stdlib `sqlite3`） | 阶段 2 / 9 安装步骤**不变** |
| **锁文件** | `package.json` / `package-lock.json` **零改动** | 阶段 9 `npm ci` 锁同步回归闸**不受影响** |
| **env 键** | **+2**（`IB_PROJECT_REGISTRY_BACKEND` / `IB_LLM_KEY_BACKEND`，**均有默认值 `sqlite`、无缺失失败模式**，**不进** `IB_ENV_KEYS` 核心装配开关） | 对 CI **无影响**（CI 用离线内存替身） |
| **模块 / 端口 / 依赖边** | 模块**仍 26**；端口 17 → **19**；**零新增依赖边** | 对 CI **无影响** |

### 9.2 基线（R18 口径）

```
[Source] → [Config+Schema] → [Unit 157] → [Integration 170] → [E2E 24] → [Full 351] → [Selfcheck 51] → [Version-Gate] → [Frontend 35] → [Artifact]
```

| 层 | R18 基线 | 依据 |
|----|----------|------|
| Python 全量 | **351/351**（unit **157** / integration **170** / e2e **24**），0 skip/xfail/blocked | `test_report.md` 1.14.0 §23（`groupd_r18_pytest_final.log`） |
| 前端冒烟（独立层） | **35/35** | 同上（`frontend.smoke.test.js`，第 35 例 R18 新增） |
| 离线自检 | **51/51** | 同上（`groupd_r18_selfcheck_final.log`；R17 起即 51） |

### 9.3 已知缺口：迁移门未覆盖 `005` / `006`（**如实登记**）

- 阶段 2 的迁移门脚本（§3.2）**只覆盖 `003_accounts.sql`**；`.github/workflows/ci.yml` 阶段 2 的迁移检查**同样只校验 `003`**。
- **R18 的 `005_projects.sql` / `006_llm_key.sql` 未被该门覆盖** —— 这是**本轮已知的 CI 覆盖缺口**，**不得**当作「已覆盖」。
- **为何不就地扩展**：① 改本门脚本与 `ci.yml` **超出本轮授权面**（本代理本轮只改 `docs/deployment_plan.md` / `docs/cicd_pipeline.md`）；② `005` 的可重放门**需先应用 001 基座 DDL**（`kbs` 表由 `001` 建），直接 `executescript('005')` 于 `:memory:` 会因缺 `kbs` 失败。
- **建议（下轮授权）**：判据 = `schema.py::ensure_schema()` 于 `:memory:` **连跑两次 exit 0** + `SELECT COUNT(*) FROM documents WHERE kb_id='kb_default'` = 0 + `llm_key` 单行表存在；并同步 `ci.yml` 阶段 2。
- **同源登记**：`deployment_plan.md` §15.2 / §15.9。

### 9.4 版本门集合（R18 复核：**不变**）

§3 的硬断言**逐条保留**：`langchain-openai < 0.3`、**禁 PyMuPDF / fitz**、**禁 Docker**、Python `>=3.11,<3.14`、`langchain-core >=0.3,<2.0`、**`bcrypt >=4,<5`（保留）**、**前端零运行时 CDN**（R18 后共 **35** 例）、**凭据零命中**。R18 **未新增、未删除**任何版本门；`bcrypt` 门因 `requirements*.txt` **零改动**而继续有效。

### 9.5 R18 相关测试文件（CI 覆盖映射）

| 文件 | 层 | 阶段 | 用例 |
|------|-----|------|------|
| `tests/unit/test_rev18_system_mgmt_unit.py` | unit | 阶段 3 | TC-UNIT-R18-001~008（`LlmKeyStatus` 无明文字段 / `llm_key` 单行表 + 006 单源 / `LlmKeyStore` 双实现一致 / 项目注册表软删·seed·端口形状 / **005 单源 + `kb_default` 前向迁移幂等** / **ADR-39 Option C 启动语义** / `users.project_id` 无 UNIQUE） |
| `tests/integration/test_rev18_system_management_int.py` | integration | 阶段 4 | GROUP_C 首跑 TC-INT-148~153 |
| `tests/integration/test_rev18_system_management_extra_int.py` | integration | 阶段 4 | TC-INT-154~162（1:N 多账号 / 422 先于 400·409 / 软删不级联·保留账本 / 未配置态 `masked==""` / 审计不含密钥 / 错误体不含明文 / D-R18-01 边界 / 资料项目域隔离） |
| `tests/e2e/test_user_journeys.py`（**增强既有 TC-E2E-001**） | e2e | 阶段 5 | 上传落库 **`kb_id ≡ project_id` 推导**（计数中性） |
| `src/frontend/tests/frontend.smoke.test.js`（**追加第 35 例**） | 前端 | 阶段 9 | `LlmKeyStatus` 无明文字段 + `files` 保持独立顶级（ADR-42） |

### 9.6 未在 CI 内、须**部署后**覆盖的 R18 项

| 项 | 归属 |
|----|------|
| **LLM Key 提交（`PUT /api/llm-key`）+ 重启生效**（`configured=true` / 启动日志 `llm_configured=true`） | `deployment_plan.md` §15.3 DEPLOY-031 / §15.8 |
| **承载库文件 0600 + 属主对齐服务账号**（checklists B22） | `deployment_plan.md` §15.8 |
| **Key 不进 git / 不进 shell history / 不进命令行**（checklists B23） | `deployment_plan.md` §15.8 |
| **ADR-39 调用期 fail-closed 文本**（缺 Key 非致命 + 其余必需项仍 fail-fast） | `deployment_plan.md` §15.7 / §15.8 |
| **`005` 迁移在既有生产库上的实际行为**（CI 只在 `:memory:` 跑，不跑真机库） | `deployment_plan.md` §15.2 / §15.3 DEPLOY-024~025 |
| **`TBD-T26` / `TBD-T27` 容量 / 时延真机结论** | `deployment_plan.md` §15.8（**未实测前不得给结论**） |

---


## 附：自检声明

- 本流水线**未执行**，为**定义**；CI 平台具体实现 = **GitHub Actions**（`.github/workflows/ci.yml` 已存在并本轮增量更新，见 §8）。
- 所有命令均引用 `src/` 既有交付物，**未编造**工具或测试路径。
- 含**禁 Docker / 禁 PyMuPDF / `langchain-openai<0.3`** 三条硬门，另加 **`langchain-core>=0.3,<2.0` / `bcrypt>=4,<5` / 前端零运行时 CDN / 凭据零命中** 与 **迁移幂等门**，与本项目冻结决策对齐。
- 本文件**不含任何真实凭据**。
- **REV-13 增量边界（前轮，INV-GROUP_E-INTELBASE-004）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH；**未 commit / push**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md`；**未触发 PHASE_11**。该轮仅更新本文件与 `.github/workflows/ci.yml`（CI/CD 配置）。
- **REV-14 增量边界（前轮，INV-GROUP_E-INTELBASE-005）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码 / `tests/**` / 设计真源四文档 / `docs/phase_status.md` / `docs/test_*.md`；**未触发 PHASE_11**，且该轮 `special_instructions` **不含 `PRODUCTION_DEPLOY_CONFIRM`**。该轮仅更新本文件（1.2.0 → **1.3.0/REV-14**）、`docs/deployment_plan.md` 与 `.github/workflows/ci.yml` 的**注释基线标签**（纯注释，不改 step 逻辑）。
- **REV-18 增量边界（本轮，INV-GROUP_E-INTELBASE-006）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R18 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未触发 PHASE_11**，且**本轮 `special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`**。本轮仅更新**两个文档**（本文件 1.3.0 → **1.4.0/REV-18** 与 `docs/deployment_plan.md` 1.3.0 → **1.4.0/REV-18**），**未改 `ci.yml`**（R18 无 CI 逻辑改动，仅**如实登记** §3.2/§9.3 迁移门未覆盖 `005`/`006`）。

---

## 修订记录（Revision History）

| 版本 | 轮次 | 日期 | 调用 ID | 变更摘要 | 依据事实 |
|------|------|------|---------|----------|----------|
| 1.0.0 | PHASE_10 首版 | 2026-09-26 | INV-GROUP_E-INTELBASE-001 | 首版（GR-E-001 = PASS_WITH_CONDITIONS，**对该 R4 前版本有效**） | 既有交付物（pytest / selfcheck / Requirements / frontend build / checklists） |
| 1.1.0 | GROUP_E / R4（REV-04-3） | 2026-09-26 | INV-GROUP_E-INTELBASE-002 | **最小修订**：新增 §3.1「部署前硬门」D-1（ib-embed 依赖 `pip freeze` 回填锁定）/ D-2（`nginx -t` 语法门）/ D-3（SSE `proxy_buffering off` 复验）；§5 矩阵「Prod 运行形态」补系统 nginx；其余不动 | `src/requirements-embed.txt`「区间非锁定值」；`deployment_plan.md` §7.5（C-02）/ §4.2 |
| 1.1.1 | GROUP_E / R10（REV-10-2） | 2026-09-27 | INV-GROUP_E-INTELBASE-003 | **最小修订**：阶段9 定义更新为「`vue-tsc` 零错 + `vite build` + 前端冒烟测试（`node:test`）」——命令追加 `npm test`（与 `.github/workflows/ci.yml` 阶段9 逐字同步）；§1 概览补「Build+Test」；新增阶段9 说明（先建后测顺序理由 + 锁同步回归闸的强制力）；其余不动 | GR-C-007 / R10：`src/frontend/package.json` 新增 `"test": "node --test"`、`src/frontend/tests/frontend.smoke.test.js`（6 例）；协调者裁决「阶段9 接入 `npm test`」 |
| **1.2.0** | **GROUP_E / REV-13** | **2026-10-06** | **INV-GROUP_E-INTELBASE-004** | **REV-13 增量**：① header 补 revision=REV-13 / 上游输入；新增「REV-13 增量声明」；② **§2 阶段表基线修正**（旧 55/69/14/142/前端 6 → **unit 95 / integration 123 / e2e 21 / full 239 / 前端 13**，0 skip/xfail；依据 phase_status GR-D-010 闭合 + test_report §18 collect 口径）；阶段2 扩展为 **Config + Schema Check**；③ **§3 版本门**补 `langchain-core` / **`bcrypt>=4,<5`** / 前端零 CDN / 凭据零命中 四行；④ 新增 **§3.2 迁移/模式门**（003_accounts.sql 语法 + 幂等 + 与代码生成器单源一致，纯标准库）；⑤ **§3.1 部署前硬门**补 **D-4 / D-5 / D-6**（迁移幂等 / HTTPS+零 Cookie / 令牌纪律）；⑥ §5 矩阵补 R13 行（账户/会话、认证载体、HTTPS/TLS）；⑦ 新增 **§7 端到端问答 smoke**（登记 TC-E2E-001 提问→检索→作答）；⑧ 新增 **§8 工作流落地**（GitHub Actions `ci.yml` 增量更新映射）；status → REVISED_PENDING_REVIEW | `docs/phase_status.md`（GR-B-006 / GR-C-009 / GR-D-010）；`docs/test_report.md` 1.9.0 §18；`src/deploy/migrations/003_accounts.sql`；`src/requirements.txt`（`bcrypt>=4,<5`）；`src/requirements-offline.txt`；`tests/e2e/test_user_journeys.py`（TC-E2E-001）；`tests/e2e/test_accounts_journeys_r13.py`；`src/frontend/tests/frontend.smoke.test.js`（13 例）；`.github/workflows/ci.yml` |
| **1.3.0** | **GROUP_E / REV-14** | **2026-10-06** | **INV-GROUP_E-INTELBASE-005** | **REV-14 增量（标签/注释层同步，不新增 / 不删除 step）**：① header 补 revision=REV-14 / 版本 1.2.0→**1.3.0**；新增「REV-14 增量声明 + R14 变更面对 CI 的影响」；② **§2 阶段表基线同步**（integration 123 → **129**、full 239 → **245**、前端 13 → **21**；unit 95 / e2e 21 不变）+ 新增「R14 基线同步说明」（含 R14-DEF-01 撞号更正计数中性说明）；③ §3 版本门「前端零运行时 CDN」行注更新为 R14 后 21 例；④ §7 端到端 smoke 判据改 `245/245` + 新增「R14 附加」（CI 层守卫在集成/前端层；真实浏览器端到端属部署后 V14-9，不在 CI）；⑤ §8 工作流落地「能力映射」补 R14 用例 + 新增「R14 增量更新」行（基线标签 / selfcheck 47 / 无迁移→迁移门不变 / 无锁改动→锁同步闸不受影响 / 硬门集合不变）；⑥ 附自检补 R14 边界；status → REVISED_PENDING_REVIEW（待 GR-E-005） | `docs/test_report.md` 1.10.0/R14 §19（Python 245 = unit 95 + integration 129 + e2e 21；前端 21；selfcheck 47/47）；`docs/phase_status.md` GR-D-011；`docs/deployment_plan.md` 1.3.0/REV-14 §14；`tests/integration/test_project_context_int_r14.py`（TC-INT-123~128）；`src/frontend/tests/frontend.smoke.test.js`（21 例）；`src/scripts/selfcheck.py`（47/47） |
| **1.4.0** | **GROUP_E / REV-18** | **2026-10-07** | **INV-GROUP_E-INTELBASE-006** | **REV-18 增量（标签层同步 + 一迁移门如实登记，不新增 / 不删除 step）**：① header 补 revision=REV-18 / 版本 1.3.0→**1.4.0**；新增「REV-18 增量声明 + R18 变更面对 CI 的影响」；② **§2 阶段表基线同步**（unit 95 → **157**、integration 129 → **170**、e2e 21 → **24**、full 245 → **351**、前端 21 → **35**）+ 新增「R18 基线同步说明」（分层实测 157+170+24=351；R18 测试文件清单；e2e 计数中性说明）；③ §3 版本门「前端零运行时 CDN」行注更新为 R18 后 35 例（版本门集合**不变**，**`bcrypt` 门保留**）；④ **§3.2 迁移门新增「R18 增量登记」**（`005`/`006` **未纳入**，如实登记缺口）；⑤ §5 矩阵补 R18 两行（项目注册表 / LLM Key 载体）；⑥ §7 端到端 smoke 判据改 `351/351` + 新增「R18 附加」；⑦ §8 工作流落地「能力映射」补 R18 用例 + 新增「R18 增量更新」行；⑧ **新增 §9 REV-18 增量节**（9.1 净影响 / 9.2 基线 / **9.3 已知缺口：迁移门未覆盖 `005`/`006`** / 9.4 版本门集合不变 / 9.5 测试文件映射 / 9.6 须部署后覆盖项）；⑨ 附自检补 R18 边界；status → REVISED_PENDING_REVIEW（待 GR-E-006） | `docs/test_report.md` 1.14.0/REV-18 §23（Python **351** = unit 157 + integration 170 + e2e 24，0 skip/xfail，`groupd_r18_pytest_final.log`；前端 **35**；selfcheck **51/51**，`groupd_r18_selfcheck_final.log`）；`docs/phase_status.md` GR-D-015（用户 2026-10-07 接受）；`docs/deployment_plan.md` 1.4.0/REV-18 §15；`tests/unit/test_rev18_system_mgmt_unit.py`（TC-UNIT-R18-001~008）；`tests/integration/test_rev18_system_management_int.py`（TC-INT-148~153）+ `test_rev18_system_management_extra_int.py`（TC-INT-154~162）；`src/frontend/tests/frontend.smoke.test.js`（35 例）；`src/deploy/migrations/{005_projects,006_llm_key}.sql`；`.github/workflows/ci.yml`（**未改**，仅登记 §3.2 迁移门未覆盖 `005`/`006`） |

> 本文件为**定义**，**未执行**；不含任何真实凭据。**1.2.0（REV-13）未连接、未触碰目标机，未 commit / push，未触发 PHASE_11**。
> **1.3.0（REV-14）边界（INV-GROUP_E-INTELBASE-005）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` / `tests/**` / 设计真源四文档 / `docs/phase_status.md` / `docs/test_*.md`；**未触发 PHASE_11**（`special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`）。
> **1.4.0（REV-18）本轮边界（INV-GROUP_E-INTELBASE-006）**：**未连接、未触碰**目标机 `192.168.31.133`；**未执行**任何部署 / SSH / 连接 / 写操作 / 安装 / 服务启停 / `nginx` 写 / 文件上传 / 迁移；**未执行 `scp` / `pscp` / `rsync`**；**未 commit / push / `git add`**；**未改** `src/**` 实现代码（R18 交付物全程只读引用）/ `tests/**` / 设计真源文档 / `docs/{implementation_plan,test_report,phase_status}.md` / `.github/workflows/ci.yml`；**未触发 PHASE_11**（`special_instructions` 不含 `PRODUCTION_DEPLOY_CONFIRM`，PHASE_11 保持冻结）。本轮**仅改两个文档**：本文件（1.3.0 → **1.4.0/REV-18**）与 `docs/deployment_plan.md`（1.3.0 → **1.4.0/REV-18**）。
