# Project Profile — intelligentbase

> 由 pm-orchestrator 在**无人值守**画像引导中扫描仓库生成的**初稿**（status=DRAFT）。
> 写入 `.claude/agents/project_profile.md` 时权限被拒，故按 PM §2.4 暂存于此；**请用户确认后移动到 `.claude/agents/project_profile.md`**。
> 每条事实后注明出处；推断项标 `[推断]`，无法从仓库得出的标"未知"。
> **待用户确认的关键项汇总在文末「待确认」**。确认前 PM 不会启动任何 SDLC 流程。
> 本文件不含任何口令、令牌、私钥。

<file_header>
  <author_agent>pm-orchestrator(draft)</author_agent>
  <timestamp>2026-10-22T18:21:20+08:00</timestamp>
  <project_name>intelligentbase</project_name>
  <version>1.0.0</version>
  <status>DRAFT</status>
</file_header>

## P1. 项目概况
- 一句话描述：通用 RAG + 多智能体基础架构基座（本地知识库 + 检索增强 + 多智能体编排），独立于 FreeArk 演进。（README.md:3-5）
- 技术栈：

  | 层 | 技术 | 版本 | 出处 |
  |---|---|---|---|
  | 语言 | Python | >=3.11,<3.14；CI 用 3.12 | ci.yml:57,150-152 |
  | Web | Django + DRF，Waitress（主）/ Gunicorn（备），原生 SSE | Django>=5.0,<6.1；DRF>=3.15,<4.0 | src/requirements.txt |
  | 编排 | LangGraph + langchain-core + langchain-openai（DeepSeek） | langchain-openai **>=0.2,<0.3** | src/requirements.txt |
  | 向量库 | Qdrant（裸装 .deb，systemd） | qdrant-client>=1.7,<2.0 | README.md:9；src/deploy/systemd/qdrant.service |
  | Embedding | bge-m3，独立 `ib-embed` 服务（独立 venv，CPU-only） | 见 src/requirements-embed.txt | README.md:10 |
  | 存储 | SQLite WAL 台账 + sha256 blob store | — | README.md:38 |
  | 前端 | Vue 3 + Vite + TypeScript + Element Plus + vue-router + @vue-flow/core | 见 package.json / package-lock.json | src/frontend/package.json |
- 运行形态：Web 服务（ib-web）+ 后台 worker（ib-worker）+ embedding 推理服务（ib-embed）+ Qdrant + nginx 静态/反代。（.claude/skills/ib-prod-deploy/SKILL.md §3）
- 权威说明文档：README.md；docs/ 下 SDLC 产物（requirements_spec / architecture_design / module_design / deployment_plan 等）；生产部署：`.claude/skills/ib-prod-deploy/SKILL.md`。仓库无 CLAUDE.md。

## P2. 文档工作区
- `docs_root`: **`docs/`** `[推断]` —— 历史 SDLC 产物（phase_status.md、requirements_spec.md、delivery_report.md 等）均平铺在 `docs/`（git ls-files）。协议缺省为 `project_workspace/intelligentbase/`，**待用户确认**沿用哪个。
- `docs_layout`: **flat** `[推断]`（同上，docs/ 下无 requirements/ 等子目录）
- 是否入库：是（docs/ 已入库；`docs/evidence/*.log` 被忽略，.gitignore）
- 注意：既有 `docs/phase_status.md`（约 2168 行）为旧版套件格式（属性 `flow_mode`/`updated_at`，非协议 §G 结构）。新流程如沿用 docs/，需决定是续写还是视为 `legacy_baseline` 另起新状态文件 —— **待确认**。

## P3. 代码布局
- `code_mode`: in-repo（README.md 目录结构；src/ 已有完整代码）
- 代码目录：

  | 组件 | 目录 | 语言 |
  |---|---|---|
  | 框架无关核心 | src/ib/ | Python |
  | embedding 推理服务 | src/ib_embed/（不得被 `ib.*` import，C8 进程隔离） | Python |
  | Django Web | src/ibweb/（入口 src/manage.py） | Python |
  | 前端 | src/frontend/ | Vue 3 / TS |
  | 部署交付物 | src/deploy/（systemd、nginx 示例、env 示例、migrations、checklists） | ini / SQL / conf |
  | 脚本 | src/scripts/（selfcheck.py、backfill_prompts.py 等） | Python / TS |
- 测试位置约定：

  | 组件 | 新测试放在 | 命名 | 框架 |
  |---|---|---|---|
  | 后端单元 | tests/unit/ | test_*.py（历史惯例带修订号后缀如 `_r13`、`rev19_`） | pytest |
  | 后端集成 | tests/integration/ | 同上 | pytest |
  | 后端 E2E | tests/e2e/ | 同上 | pytest（离线，Django 测试客户端/回环端口） |
  | 前端 | src/frontend/tests/frontend.smoke.test.js | — | Node 20 内置 node:test |
  | SDLC 套件契约 | tests/agents/ | — | pytest（目录**刻意不放 conftest.py**，tests/agents/test_sdlc_suite_contract.py:9-13） |
- 公共夹具：tests/conftest.py（导入期设定离线环境变量；必须唯一）。
- 不可修改的目录：src/frontend/node_modules/、dist/（.gitignore）；bge-m3 权重目录（不入 git）。`.trae/` 为 TRAE 智能体套件复刻产物，是否允许 SDLC 子代理修改 —— 未知。

## P4. 命令（全部在开发机/CI 上运行，严禁连生产）
| 用途 | 工作目录 | 命令 | 备注 |
|---|---|---|---|
| 环境准备 | 仓库根 | `pip install -r src/requirements-offline.txt pytest pytest-cov`；环境变量 `PYTHONUTF8=1 IB_OFFLINE_MODE=1 IB_CONFIG_SOURCE=dict IB_LOG_LEVEL=ERROR DJANGO_SETTINGS_MODULE=ibweb.settings`（tests/conftest.py 会 setdefault） | ci.yml:40-68。**当前机器 python3 无 pytest（实测 2026-10-22），子代理不得自行安装 → 标 BLOCKED** |
| 静态/编译检查 | 仓库根 | `python -m compileall -q src` | ci.yml:72 |
| 迁移检查 | 仓库根 | ci.yml「Schema / migration check」内联脚本 | ci.yml:77-92 |
| 单元测试 | 仓库根 | `python -m pytest tests/unit -q` | 按目录分层 |
| 集成测试 | 仓库根 | `python -m pytest tests/integration -q` | |
| E2E 测试 | 仓库根 | `python -m pytest tests/e2e -q` | |
| 全量回归 | 仓库根 | `python -m pytest tests --cov=ib --cov=ibweb --cov=ib_embed -q` | 耗时未知 |
| 离线自检 | 仓库根 | `python src/scripts/selfcheck.py` | 任一 FAIL 非零退出（ci.yml:111） |
| 前端构建+测试 | src/frontend | `npm ci && npm run build && npm test` | 先 build 后 test（冒烟断言 dist/） |
| 套件契约 | 仓库根 | `python -m pytest tests/agents -q` | |
- README.md:54 写的 `cd src && python manage.py test` 与 CI 的 pytest 入口不同，**以 CI 为准** `[推断]`，待确认。
- 已知既有失败 / 基线来源：ci.yml 注释记录的最近基线为 REV-14 时 unit 95 / integration 129 / e2e 21 / full 245、0 skip/xfail（ci.yml:15）；此后 REV-15~24 已新增用例，**该数字已过时**，以实跑为准。
- 缺依赖时的处理：如实标 BLOCKED，不安装。

## P5. 质量判定
- FULL_FLOW `gate_mode`: threshold — unit_pass 0.80 / integration_pass 0.90 / critical_path 1.00 / coverage_min 无（CI 覆盖率"仅记录不设门"，ci.yml:106）
- INCREMENTAL `gate_mode`: baseline — 零新增失败（缺省；本项目已在维护期，增量为主）
- `inferred_max`: 0.20（缺省）

## P6. 开发约定
- 数据迁移：**手写 scoped SQL 迁移** `src/deploy/migrations/NNN_*.sql`，内容须与 `src/ib/ledger/schema.py` 生成器**逐字一致（单源）**；已存在的迁移不改，增量另立新号；须幂等（`IF NOT EXISTS`），由 `ib-web.service` 的 `ExecStartPre=python -m ibweb.bootstrap --ensure-schema` 自动应用；每个迁移写回滚说明。（006_llm_key.sql 头注释；ci.yml:74-92）不用 Django ORM / contrib.auth（src/requirements.txt bcrypt 段注释）。
- 鉴权与权限模型：自建账户体系（bcrypt 口令哈希，users/sessions 表，003_accounts.sql）；前端 `fetch` + `Authorization: Bearer`（README.md:15）；DRF 默认认证类为空、由项目自有 authz 处理（src/ibweb/settings.py:131-133，src/ibweb/authz.py）；项目隔离 collection-per-project + filter，`X-IB-Project` 头传播（README.md:37；ci.yml:13）。
- 代码风格 / lint：仓库内未发现 lint 配置（无 ruff/flake8/eslint 配置文件）—— 未知。
- 依赖管理：Python 依赖**下界+上界都写**（src/requirements.txt:3-5）；三份清单分工：requirements.txt（生产基座）/ requirements-offline.txt（离线自测，刻意不含云客户端、qdrant-client、OCR）/ requirements-embed.txt（ib-embed 独立 venv，torch 等**永不进**基座清单）；前端 package-lock.json 入库，`npm ci` 复现。
- 其他约定：
  - 离线测试纪律：测试一律 SQLite/内存/替身，不连 Qdrant、DeepSeek、真实 ib-embed 或任何外部网络（tests/conftest.py 文档串）。
  - 前端运行期禁止 CDN/外链字体；HTTP 只经 src/frontend/src/api/client.ts（无 axios）；路由 hash 模式（package.json `_comment`）。
  - 行尾统一 LF（.gitattributes）。
  - 仓库为 **PUBLIC**，`src/deploy/**` 与任何入库文件不得含真实凭据；自检 `deploy_templates_have_no_secrets` 会扫描（SKILL.md §9）。
  - 提交信息为 Conventional Commits 风格（`feat(scope):` / `fix(scope):` / `docs(phase):`，git log）。

## P7. 环境、CI 与部署
- 环境：

  | 环境 | 存在 | 访问方式（不含口令） | 部署需用户确认 | 备注 |
  |---|---|---|---|---|
  | dev/local | 是 | 本机离线（IB_OFFLINE_MODE=1） | 否 | 用户日常为 Windows/PowerShell（SKILL.md §2.3） |
  | CI | 是 | GitHub Actions `.github/workflows/ci.yml` | 否 | push/PR main + workflow_dispatch |
  | staging | **未发现** | — | — | 仓库与 skill 均无 staging 记录 —— 待确认 |
  | production | 是 | SSH 密钥认证到单台物理机（主机、用户、密钥名见 `.claude/skills/ib-prod-deploy/SKILL.md` §1–2） | **是** | Ubuntu，CPU-only |
- 部署方式：目标机 `git pull origin main` + `sudo -n systemctl restart <服务>`（仅 ib-web/ib-worker/ib-embed 三个 restart 免密）；前端在目标机 `npm run build` 后拷贝到 web root；**禁 scp / pscp / rsync** 传代码。（SKILL.md §1、§4、§5）
- 允许的部署策略：**recreate**（单机 systemd 重启）`[推断]`，无 rolling/blue-green/canary 基础设施。
- 构建产物管理：CI 上传 frontend dist + HEAD 为 Actions artifact（保留 30 天，ci.yml:176-189）；生产不使用该制品，在目标机本地构建。
- 运行单元与"改什么重启什么"：见 SKILL.md §6（前端不重启；ibweb/** → ib-web；worker/入库链路 → ib-worker；ib_embed → ib-embed；systemd unit 变更 / daemon-reload / env 文件 / nginx reload **由用户执行**；迁移随 ib-web 重启自动应用）。
- 目标机必须保留的本地状态：`/etc/intelligentbase/*.env`（0600，不得读取回显）、`/var/lib/intelligentbase/`（台账、blob、definition.json、prompts）、bge-m3 权重目录、Qdrant 数据、`/opt/intelligentbase/venv`、目标机前端 node_modules。（SKILL.md §1、§7.4）
- 回滚方式偏好：`git revert` 后 push 再在目标机 pull + 重启 `[推断]`（交付仅允许 git pull）；新增表迁移回滚为 DROP（迁移文件内说明）。—— 待确认。
- 部署后验证：`systemctl is-active ib-web ib-worker ib-embed`；`journalctl -u <svc> --since <真实启动时刻>`；线上代码版本判据 = 目标机 HEAD + 源文件 mtime 早于 ActiveEnterTimestamp（**不得用 .pyc 判断**）；定义文档文件态判据见 SKILL.md §7.4。
- CI 系统与配置文件：GitHub Actions，`.github/workflows/ci.yml`（10 阶段，fail-fast）。
- 部署相关配置文件：`src/deploy/systemd/*.service`、`src/deploy/nginx/intelligentbase.conf.example`、`src/deploy/*.env.example`、`src/deploy/config.example.json`、`src/deploy/checklists.txt`、`src/deploy/migrations/`。

## P8. 禁用项（门控时任一出现即 FAIL）
| 禁用的技术 / 操作 | 原因 / 出处 |
|---|---|
| Docker / 任何容器化（Dockerfile、docker-compose） | 物理机直部署，沿用 FreeArk 约束（README.md:39；ci.yml:139-148 硬门） |
| PyMuPDF / fitz | AGPL-3.0 许可合规（src/requirements.txt 解析段；ci.yml:132-137） |
| langchain-openai >= 0.3 | 0.3.x 删除内部函数致流式断流（src/requirements.txt；ci.yml:125-130） |
| torch / FlagEmbedding / transformers 进基座 requirements.txt；CUDA 版 torch / GPU 版 onnxruntime | 进程隔离与 CPU-only（src/requirements-embed.txt 头注释） |
| `ib.*` import `ib_embed` | C8 进程隔离（requirements-embed.txt；selfcheck `ib_embed_isolation`） |
| 用 scp / pscp / rsync 向生产传代码 | 交付仅 git pull（SKILL.md §1） |
| nginx 开启 http2；关闭 SSE 反代条件（proxy_buffering off / gzip off / proxy_read_timeout 300s） | 破坏 SSE（SKILL.md §8.6-8.7） |
| 多实例 ib-worker | 双 OOM（SKILL.md §8.9） |
| Channels / Redis 用于实时推送 | 架构选择原生 SSE（README.md:14,36）`[推断为禁用]` |
| axios、运行期 CDN / 外链资源 | package.json `_comment` |
| `printf '<口令>' \| sudo -S`、回显/读取 `/etc/intelligentbase/*.env` 值、凭据入库 | 凭据纪律（SKILL.md §9） |
| Python 版本超出 >=3.11,<3.14；bcrypt 超出 >=4,<5 | CI 版本门（ci.yml:114-152） |

## P9. 版本控制与远程操作权限
- 分支策略：单主干 `main`（CI 只对 main 触发；远端另有 origin/master，用途未知）。
- 谁执行 commit / push：**未知**。历史记录显示曾由子代理在"协调者授权"下提交并 push（docs/phase_status.md:23），但本套件协议缺省为"主会话在用户确认后执行"。`.claude/settings.json` 已把 `git push`、`ssh`、`scp` 设为 ask。—— **待确认**；确认前按协议缺省：子代理不 commit/push。
- 子代理是否可 ssh / 部署：否（缺省）；E2 获得用户本轮授权后，devops-engineer 可执行 SKILL.md §4.4/§5 中的 git pull 与三条免密 restart；daemon-reload、unit 安装、env 修改、nginx reload 一律由用户执行。
- 提交前必须通过的检查：与 CI 一致 `[推断]`：compileall、迁移检查、unit/integration/e2e/全量、selfcheck、版本门、前端 build+test。

## P10. 额外必读（PM 填入 required_reading）
| Agent | 额外文件 |
|---|---|
| system-architect | docs/architecture_design.md、docs/module_design.md（现有设计基线，INCREMENTAL 时） |
| software-developer | src/ib/ledger/schema.py（涉及迁移时）、src/scripts/selfcheck.py（了解自检范围） |
| test-engineer | tests/conftest.py、.github/workflows/ci.yml |
| devops-engineer | .claude/skills/ib-prod-deploy/SKILL.md、docs/deployment_plan.md、src/deploy/checklists.txt、.github/workflows/ci.yml |

---

## 待确认（无人值守运行，PM 未能询问；用户确认后改 status=APPROVED、version=1.0.0）
1. **文档工作区**：沿用 `docs/` + flat（与历史一致），还是改用协议缺省 `project_workspace/intelligentbase/` + nested？既有 `docs/phase_status.md` 为旧格式，续写还是作为 legacy_baseline？
2. **测试命令**：以 CI 的 `python -m pytest tests/...` 为准（而非 README 的 `manage.py test`）是否正确？当前开发机缺 pytest，由谁准备测试环境？
3. **环境**：是否确无 staging？生产部署一律需本轮授权（缺省如此）。
4. **回滚方式**：git revert + push + 目标机 pull/重启，是否认可？
5. **commit / push 执行者**：主会话在用户确认后执行，还是允许子代理在授权后提交？
6. **禁用项**：P8 中标 `[推断]` 的条目（Channels/Redis）是否成立；`.trae/` 是否允许修改；origin/master 分支用途。


## 沙箱试运行建议（2026-10-22，非用户确认；请逐项核对，确认后把 status 改为 APPROVED）
> 以下是沙箱测试时为跑通流程采用的选择，供确认时参考；基线数字来自测试机，换机器后以实跑为准。
- docs_root = `docs/sdlc/{project_name}/`，docs_layout = **flat**（沿用项目平铺习惯，但放在子目录里，不续写也不覆盖 `docs/` 下的旧 phase_status.md 与历史产物）。
- 测试命令：在仓库根目录 `python -m pytest tests -q`（conftest 已设定离线环境）；基线（2026-10-22 实跑）：436 passed。
- 环境与部署按 P7 推断；本次测试不授权部署。
- commit/push 由主会话在用户确认后执行；子代理不执行。
- 禁用项按 P8 确认。
