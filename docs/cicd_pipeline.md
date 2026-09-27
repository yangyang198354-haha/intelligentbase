<!--
  file_header（共享协议 Block B）
-->
| 字段 | 值 |
|------|-----|
| 文档 ID | DOC-IB-CICD-001 |
| 标题 | intelligentbase 智能知识库基座 —— CI/CD 流水线定义 |
| 产出代理 | devops-engineer (author_agent) |
| 调用 ID | INV-GROUP_E-INTELBASE-003 |
| 项目 | intelligentbase |
| 阶段 | GROUP_E / PHASE_10（部署计划配套；**仅定义，不执行**） |
| 版本 | 1.1.1（R10 修订；阶段9 接入前端 `npm test`，其余不动） |
| status | **REVISED_PENDING_REVIEW**（R10 修订；GR-E-001 对 R4 前版本有效、GR-E-002 对 1.1.0 有效，本次待 PM 重新门控） |
| 创建日期 | 2026-09-26 |
| 凭据纪律 | 本文件不含任何真实凭据；CI 凭据一律经 CI secret / 环境变量注入，不入仓库 |
| 前置 | **git 仓库与 remote 尚未建立**（见 `deployment_plan.md` §1.1 B-01）——本流水线在其闭合前**无法被触发** |

> 本文件是 `docs/deployment_plan.md` 的配套。**工具链均取自 `src/` 既有交付物**，未虚构工具：pytest（`tests/`）、`scripts/selfcheck.py`（离线自检）、`manage.py check`、`src/frontend` 的 `npm run build` 与 `npm test`（Node 20 内置 `node:test`）、`src/requirements*.txt`、`src/deploy/checklists.txt`。
> **本基座禁 Docker**（DR-03）——CI 使用**裸 runner / 虚拟环境**，不使用容器镜像作为交付物（见 §5）。

## 1. 流水线概览

```
[Source] → [Lint/Config] → [Unit] → [Integration] → [E2E] → [Version-Gate] → [Frontend Build+Test] → [Package Artifact]
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
| 2 | **Config** | 前阶段成功 | `python -m compileall -q src` | exit 0 | abort & notify |
| 3 | **Unit** | 前阶段成功 | `python -m pytest tests/unit -q` | **全通过**（基线 55/55=100%） | abort & notify |
| 4 | **Integration** | 前阶段成功 | `python -m pytest tests/integration -q` | **全通过**（基线 69→**73**/100%） | abort & notify |
| 5 | **E2E** | 前阶段成功 | `python -m pytest tests/e2e -q` | **全通过**（基线 14/14=100%） | abort & notify |
| 6 | **Full Suite + Coverage** | 前阶段成功 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | **142/142 通过、0 skip/xfail**（R3 基线）；覆盖率 **仅记录不设门**（当前 67%） | abort & notify |
| 7 | **Offline Selfcheck** | 前阶段成功 | `python src/scripts/selfcheck.py` | 全 `PASS`，exit 0（任一 `FAIL` 非零退出） | abort & notify |
| 8 | **Version Gate** | 前阶段成功 | 见 §3 | 全部断言通过 | abort & notify |
| 9 | **Frontend Build + Test** | 前阶段成功 | `cd src/frontend && npm ci && npm run build && npm test` | `vue-tsc --noEmit` 零错 + `vite build` 成功 + **前端冒烟测试（`node:test`）全通过** | abort & notify |
| 10 | **Package Artifact** | 前阶段成功 | 归档 `src/frontend/dist/` + 记录 `git rev-parse HEAD` | 产物归档、commit 可追溯 | abort & notify |

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

> 版本门是**部署路径与本地一致性**的守卫——`ibweb/composition.py` 在**装配期**也会对 `langchain-openai` 做 fail-fast 断言（test_report DEV-02 已实测该断言触发），CI 版本门是其**上游更早的一道**。

### 3.1 部署前硬门（PHASE_11 前置；非构建期）

> 下列门在**部署前**（**非**每次 push 的构建期）执行；任一不过则**不得进入部署**（abort & notify，不跳过）。

| # | 硬门 | 命令 | 判据 | 依据 |
|---|------|------|------|------|
| **D-1** | **ib-embed 依赖锁定回填** | 目标机 `sudo /opt/ib-embed/venv/bin/pip freeze > /opt/intelligentbase/requirements-embed.lock.txt`，并**回填部署记录** | 装出的**精确版本**（非区间）落档；`src/requirements-embed.txt` 的**区间不得当锁定值上线** | deployment_plan §1.1 B-05 / §4.2；`src/requirements-embed.txt`「版本 pin 的诚实性说明」 |
| **D-2** | **nginx 配置语法门** | `sudo nginx -t` | **exit 0**（配置语法合法）；**之后**方可 `systemctl reload nginx` | deployment_plan §7.5（C-02）/ §10.1 DEPLOY-009 |
| **D-3** | **SSE 不缓冲复验** | `grep -n "proxy_buffering off" /etc/nginx/sites-available/intelligentbase` | 命中（SSE 段缺此项 = 流式功能**静默失效**） | deployment_plan §7.5；`ib/streaming/__init__.py`（`X-Accel-Buffering: no` 为必需） |

> **D-1 理由**：`src/requirements-embed.txt` 明确其版本 pin 是**保守区间、不是锁定值**；上线前必须用目标机 `pip freeze` 回填精确版本，否则「部署记录里的版本」与「真实装到的版本」不可对账（区间当作锁定值是典型的**假锁定**）。
> **D-2 理由**：nginx 站点变更若带语法错误直接 `reload`，会让对外服务**立即不可用**；`nginx -t` 是 reload 的**硬前置**。**D-3** 是 C-02 引入的 SSE 正确性门（缺 `proxy_buffering off` 时问答被缓冲、首字节永不外发）。

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
| 凭据 | CI secret / 环境变量 | 环境变量 | `EnvironmentFile` 0600（**不入 git**） |

## 6. 阶段命令的失败处理策略（**总则**）

- **一律 abort-and-notify，不跳过、不 continue-on-error**。
- **禁止**任何「跳过失败继续部署」的策略（违反冻结决策与硬约束）。
- 重试：**仅**允许对**瞬时网络**类操作（如 `npm ci` / `pip install`）设**有限重试**（≤ 2），不对测试/门禁设自动重试（避免掩盖真失败）。

---

## 附：自检声明

- 本流水线**未执行**，为**定义**；CI 平台具体实现（GitHub Actions / GitLab CI / Jenkins）**待 PM 确认**（本文件不预设平台）。
- 所有命令均引用 `src/` 既有交付物，**未编造**工具或测试路径。
- 含**禁 Docker / 禁 PyMuPDF / `langchain-openai<0.3`** 三条硬门，与本项目冻结决策对齐。
- 本文件**不含任何真实凭据**。

---

## 修订记录（Revision History）

| 版本 | 轮次 | 日期 | 调用 ID | 变更摘要 | 依据事实 |
|------|------|------|---------|----------|----------|
| 1.0.0 | PHASE_10 首版 | 2026-09-26 | INV-GROUP_E-INTELBASE-001 | 首版（GR-E-001 = PASS_WITH_CONDITIONS，**对该 R4 前版本有效**） | 既有交付物（pytest / selfcheck / Requirements / frontend build / checklists） |
| 1.1.0 | GROUP_E / R4（REV-04-3） | 2026-09-26 | INV-GROUP_E-INTELBASE-002 | **最小修订**：新增 §3.1「部署前硬门」D-1（ib-embed 依赖 `pip freeze` 回填锁定）/ D-2（`nginx -t` 语法门）/ D-3（SSE `proxy_buffering off` 复验）；§5 矩阵「Prod 运行形态」补系统 nginx；其余不动 | `src/requirements-embed.txt`「区间非锁定值」；`deployment_plan.md` §7.5（C-02）/ §4.2 |
| 1.1.1 | GROUP_E / R10（REV-10-2） | 2026-09-27 | INV-GROUP_E-INTELBASE-003 | **最小修订**：阶段9 定义更新为「`vue-tsc` 零错 + `vite build` + 前端冒烟测试（`node:test`）」——命令追加 `npm test`（与 `.github/workflows/ci.yml` 阶段9 逐字同步）；§1 概览补「Build+Test」；新增阶段9 说明（先建后测顺序理由 + 锁同步回归闸的强制力）；其余不动 | GR-C-007 / R10：`src/frontend/package.json` 新增 `"test": "node --test"`、`src/frontend/tests/frontend.smoke.test.js`（6 例）；协调者裁决「阶段9 接入 `npm test`」 |

> 本文件为**定义**，**未执行**；不含任何真实凭据。
