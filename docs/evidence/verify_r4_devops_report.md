# 独立只读核验报告 —— GROUP_E / PHASE_10 R4 文档修订

- 调用 ID（被检）：`INV-GROUP_E-INTELBASE-002`（devops-engineer）
- 核验方：独立只读 verifier（本文件作者）
- 核验时间：2026-09-26 09:11–09:25（本地）
- 被检对象：`docs/deployment_plan.md`(1.1.0)、`docs/cicd_pipeline.md`(1.1.0)、
  `src/deploy/ib-worker.env.example`(新增)、`src/deploy/systemd/qdrant.service`(改 1 行)、
  `.claude/agents/knowledge_base/devops_engineer/`(KB)
- 复现探针：`docs/evidence/verify_r4_devops_scan.py`（只读；无网络）
- 原始输出：`docs/evidence/verify_r4_devops_scan.log`（EXIT=1，唯一 FAIL 项 = 本报告 F-1）
- 纪律：核验期**未连接** `192.168.31.133`，**未改**任何被检文件，**未改** FreeArk（只读 `git status`）。

---

## 1. 结论摘要

| # | 核验项 | 判定 |
|---|--------|------|
| 1 | `src/` 改动面收敛（仅两处） | **CONFIRMED** |
| 2 | 键集/值逐键一致 + 仅占位符 | **CONFIRMED** |
| 3 | 凭据扫描（4 文件） | **CONFIRMED**（4 处 `token=` 命中均为「禁用形态」文档表述） |
| 4 | `phase_status.md` 未被 devops 改动 | **CONFIRMED** |
| 5 | `docs/` 改动面收敛 | **CONFIRMED** |
| 6 | `file_header` 未越权（无 APPROVED） | **CONFIRMED** |
| 7 | 文档事实一致性（5 条抽查 + 4 条行号引用） | **CONFIRMED**（另见 F-2 MINOR） |
| 8 | 未触目标机 | **NOT_FULLY_DETERMINABLE**（间接证据全部指向「未接触」） |
| 9 | FreeArk 只读 | **CONFIRMED** |
| — | devops 自述「改动 18 处定点修订」 | **NOT_FULLY_DETERMINABLE**（无 git、无 1.0.0 基线副本） |

**总判定：PASS_WITH_MINOR**（纪律全清；发现 1 项实质引用不一致 F-1 + 2 项 MINOR F-2/F-3，均**非越界**、**非凭据**、**非目标机接触**）。

---

## 2. 逐项证据

### 1. `src/` 改动面 —— CONFIRMED

```
$ find src -type f -newermt "2026-09-26 09:00" -not -path '*__pycache__*'
src/deploy/systemd/qdrant.service     09:09:18
src/deploy/ib-worker.env.example      09:09:15
（计数 = 2）
$ find src -type f -newermt "2026-09-26 08:47" ...   ← 窗口放宽 1 小时余
（计数仍 = 2，无第三处）
```

`src/**` mtime 降序第 3 条已是 `src/requirements-embed.txt`(08:46:02)，**早于 devops 首产物 23 分钟**，
且 `phase_status.md` 把该文件记在 GROUP_C R4（`INV-GROUP_C-INTELBASE-004`）名下 —— 即
`requirements-embed.txt` **不是** devops 本轮产物（doc 中「（R4 新增）」指 GROUP_C 的 R4）。
未发现任何第三处 `src/` 变动，**无违规**。

### 2. 键集 / 值逐键一致 —— CONFIRMED

```
env.example        键数 = 27
ib-worker.example  键数 = 27
A-B 差集 = []      B-A 差集 = []      键+值 全等 = True
```

值面：6 个 `<REPLACE_ME_*>` 占位符（`IB_DJANGO_SECRET_KEY` / `IB_ALLOWED_HOSTS` /
`IB_LLM_API_KEY` / `IB_AUTHZ_POLICY_MODULE` / `IB_SERVICE_TOKEN` / `IB_OFFLINE_TOKEN`），
其余 21 个为安全默认（`0` / `file` / `INFO` / `127.0.0.1:6333` / `127.0.0.1:8100` / `deepseek-chat` 等），
**逐值与 `env.example` 全等**，无任何真实值残留。结论比 devops 自述更强（自述只说「键集一致」，实测是**键+值全等**）。

### 3. 凭据扫描 —— CONFIRMED（无凭据）

| 文件 | 命中 |
|------|------|
| `docs/deployment_plan.md` | `token_assign_realval` × 4 |
| `docs/cicd_pipeline.md` | ALL ZERO |
| `src/deploy/ib-worker.env.example` | ALL ZERO |
| `src/deploy/systemd/qdrant.service` | ALL ZERO |

`sk-…` / `ghp_` / `AKIA` / `-----BEGIN … PRIVATE KEY` / `password=` / `passwd=` /
`IB_SSH_PASS=` / `Bearer <literal>` / `ssh-rsa AAAA` **全部 0 命中**。
4 处 `token=` 经逐行核对**全部是「禁止形态」的文档表述**（L494「禁 ?token=」、L516 日志纪律、
L589 B10「?token= 必须 4xx」、L593 B14 日志抽查），**不含任何值**，非泄漏。
`192.168.31.133` 出现 5 次（plan 4 / cicd 1），**全部是「目标机」标注或「未连接目标机」声明**，
**无任何 `口令/令牌=IP` 形式的赋值**。**本报告不复述任何疑似凭据值（本项本无值可复述）。**

### 4. `docs/phase_status.md` 未被 devops 改动 —— CONFIRMED

```
ElementTree 解析: OK，根 tag = phase_status
gate_review 计数 = 12
id = [GR-A-001, GR-B-001..003, GR-C-001..004, GR-D-001..003, GR-E-001]
GR-C-004 在列 = True ; GR-D-003 在列 = True ; GR-E-002 在列 = False
log 计数 = 87 ; input 计数 = 23
GROUP_C gate_decision = R4_PASS（GR-C-004；…）
GROUP_E gate_decision = PHASE_10_PASS_WITH_CONDITIONS（GR-E-001，…待出 GR-E-002）
GROUP_E/PHASE_10 status = IN_PROGRESS  r4_invocation_id = INV-GROUP_E-INTELBASE-002
GROUP_E/PHASE_11 status = PENDING     r4_invocation_id = None
```

**关键时间证据**：`phase_status.md` mtime = `09:06:27`，**早于 devops 首产物** `09:09:06`。
内容上唯一与本轮相关的新增条目是 `PM_INVOKE_AGENT / DISPATCHED / INV-GROUP_E-INTELBASE-002`
（PM 的派发记录，非 devops 动作）。**未发现 devops 写入的任何内容；无预期外字段**，
`retry_counters` 仍为 5 组 `counter`（GROUP_E count=0），子元素结构未变。
`GR-E-002` 字符串仅作为「待出」出现在文本中，**未出现自签发的 `gate_review` 元素** —— 未抢发门控。

### 5. `docs/` 改动面 —— CONFIRMED

窗口内（>=09:00）`docs/` 变动 = `deployment_plan.md`、`cicd_pipeline.md`、`phase_status.md`(PM)、
`docs/evidence/verify_r4_*.{log,py}`(前一轮 verifier 的既存证据)。
`tech_stack.md` / `module_design.md` / `architecture_design.md` / `test_plan.md` /
`test_report.md` / `requirements_spec.md` / `user_stories.md` **均未在本轮窗口内被改**。

### 6. `file_header` 未越权 —— CONFIRMED

两份文档头部 `status` = `**REVISED_PENDING_REVIEW**（R4 修订；GR-E-001 对 R4 前版本有效，
待 PM 重新门控 GR-E-002）`；**全文 `APPROVED` 0 命中**；头部 `调用 ID` 均为
`INV-GROUP_E-INTELBASE-002`（`…-001` 仅出现在 v1.0.0 修订记录行，属正确引用）。

### 7. 文档事实一致性抽查 —— CONFIRMED（含 2 项 MINOR）

| 抽查项 | 实测 | 判定 |
|--------|------|------|
| §7.5 反代目标 = `127.0.0.1:18080` ↔ `ib-web.service` `--port=18080` | L51 `--port=18080` 一致 | **CONFIRMED** |
| §7.5 内部自洽（nginx 不得用 18080，EADDRINUSE 与 Waitress 冲突） | §7.5 表格行 + nginx 骨架 `listen 80 # 不得用 18080` 自洽 | **CONFIRMED** |
| §1.2 C-02 ↔ §7.5 | C-02 只列职责并**指向** §7.5（`/api`+`/healthz`→18080、`proxy_buffering off`、`proxy_read_timeout`），**无矛盾** | **CONFIRMED** |
| §6.1 C-06：OCR 与 embedding **两条链路合并评估** | L275「风险同源，须一次性合并评估」（`OCR 链路`+`embedding 链路`）+ 症状对照表 | **CONFIRMED** |
| §6.1 给出**目标机最小探针** | L283–292 步骤 (0) 先跑探针（`import onnxruntime` / `import torch` + 一次真实推理），明令「开发机结果不得替代」 | **CONFIRMED** |
| §1.2 **C-01 仍未闭合** | C-01 行**无 ✅**；§12.2 O-07 明写「C-01，仍待 PM 定」 | **CONFIRMED（未被私标闭合）** |
| C-04 叙述 ↔ 实际 unit | `qdrant.service:35` = `ExecStart=/usr/bin/qdrant --config-path …`，与 `architecture_design.md:208`、`tech_stack.md:209` 一致；全仓**无残留** `/usr/local/bin/qdrant`（仅 §3.5 修正叙述与 devops KB 提及） | **CONFIRMED** |

**行号引用全部正确**：`ib-web.service:51`（`--port=18080`）、`ib-worker.service:42`
（`EnvironmentFile=…/ib-worker.env`）、`qdrant.service:35`（ExecStart）、
`vite.config.ts:10`（生产 nginx 反代 127.0.0.1:18080 注释）—— 4/4 命中。
另核验：`settings.py` 确无 `STATIC_ROOT/STATICFILES`（C-02 依据成立）；
`ib-embed.env.example` 确为 **11** 个 `IB_EMBED_*` 键（§7.2 断言成立）。

### 8. 未触目标机 —— NOT_FULLY_DETERMINABLE

探针自身不发起网络连接；事后残留检查结果：

- `intelligentbase` 内**无**任何 `ssh/scp/rsync/plink/pscp` 命名文件或脚本（0 命中）；
- 无 `ssh/scp/rsync` 进程在跑（`tasklist` 0 命中）；
- `~/.ssh/known_hosts` mtime = `2026-09-26 00:18:08`（**早于本轮窗口**；含 `192.168.31.133`
  → 历史轮次已学习过主机键，与 plan 中「指纹已实测回填」相符）；
- 被检 4 文件内容**全部为计划态**（命令均标「须 PM CONFIRM 后执行」）。

**判定**：所有**可获得**的间接证据都指向「本轮未接触目标机」，但核验期无审计钩子、
无 ssh 客户端侧日志留存，**无法排除窗口内一次「已建立即断开」的连接** →
如实标为 **NOT_FULLY_DETERMINABLE**（不作 CONFIRMED）。

### 9. FreeArk 只读 —— CONFIRMED

`git -C …\FreeArk status --porcelain` → 15 行，**全部 `??`**；含 ` M`/`M `/`A `/`D ` 的**行数 = 0**。
且该 `??` 集合与会话起始快照**逐条相同**，说明本轮不但未改 FreeArk，连未跟踪文件都无新增。

---

## 3. 新发现

### F-1（**MEDIUM**，plan↔artifact 引用不一致，未登记）—— checklists 未同步 C-02

- `deployment_plan.md` §11.2 **B12** 断言：「**B12**：四自研单元 active + **nginx `nginx -t` 通过且
  站点含 `proxy_buffering off`（C-02）** + `/healthz`=200 + 前端产物就位」；
  §11.1 NV-08/NV-07 把 nginx 证据挂在「对齐 checklists 条目 **B12**」下，§11 标题亦称「对齐 `checklists.txt`」。
- 但 `src/deploy/checklists.txt`（mtime 07:57:41，**不在本轮窗口**）`[B12]` 原文为：
  ```
  [B12] 四个 unit 与静态资源
      $ systemctl is-active qdrant ib-embed ib-web ib-worker
      $ curl … http://127.0.0.1:18080/healthz
      [ ] 四个服务均 active
      [ ] /healthz 返回 200
      [ ] 前端构建产物已就位且由 ib-web 托管（npm run build 的 dist/ 已部署）
  ```
  全文 `nginx -t` / `proxy_buffering` **0 命中**，`nginx` 仅出现在 B10 日志纪律一句。
- **更矛盾的一点**：B12 写 `dist/`「**由 ib-web 托管**」，而本次 C-02 立论正是
  「`settings.py` 未配 `STATIC_ROOT`/staticfiles（已核验）→ `dist/` **不由 Django 托管**」，两处**直接冲突**。
- 影响：PHASE_11 若**照 checklists 执行**，nginx 与 SSE 不缓冲这两项**不会被验**——而 `proxy_buffering off`
  缺失恰是 C-02 引入 D-3 门所要防的「流式静默失效」。
- 缓解（部分）：`cicd_pipeline.md` §3.1 **D-2/D-3** 独立把 `nginx -t` 与 `grep proxy_buffering off`
  定为部署前硬门，故门并未完全落空。
- 性质：**非纪律越界**——devops 本轮**仅被授权改 2 个 src 文件**，`checklists.txt` 本就不在其授权面内；
  但**应在 §1/§12 登记为开放项或 PHASE_11 前置**，实际**未登记**，构成修订完整性缺口。

### F-2（MINOR）—— §1.2 C-01 括注「18080（nginx）」与 §7.5 硬约束冲突

`C-01` 原文「目标机 **18080（nginx）** 是否需对内网/外网开放？」把 18080 说成 nginx 端口，
而 §7.5 明令 nginx 对外**不得**用 18080（与 Waitress `127.0.0.1:18080` EADDRINUSE），骨架写 `listen 80`。
C-01 括注为 R4 前旧表述、未被本轮修订触及（C-01 应保持未闭合，但**表述应更正**）。
另：C-01 引「`checklists.txt` A3 强制」涵盖「Qdrant 6333 / ib-embed 8100」，而 A3 实际**只检 6333**（8100 未检）。

### F-3（MINOR）—— `cicd_pipeline.md` §2 测试基线落后一轮

§2 阶段 3/4/5/6 写 `55/55`、`集成 69→73`、`14/14`、**`142/142`（已自标「R3 基线」）**；
而本轮 GROUP_D R4 已把套件推到 **148**（单元 56 + 集成 78 + E2E 14，见 `test_report.md` §11 与
GR-D-003 门控「148=148+0+0+0」）。CI 成功标准仍挂在 R3 数字上。
阶段 6 明标「R3 基线」故非虚假陈述，但 R4 修订未刷新，属**陈旧基线**。

### F-4（INFO）—— 新增 src 交付物的作者归属

`src/deploy/ib-worker.env.example` 头部 `@author sub_agent_devops_engineer (R4 修订…)`，
与同目录其余模板的 `@author sub_agent_software_developer` 不同。因该文件系 devops 在
C-03 授权下**新增**，如实署名**恰当**；仅记录与既有模式的差异，供 module_design §5 键名契约
（§7.6 声明「新增键须先回设计文档评审」）对账时留意 —— 本次**未新增/改名任何键**，故无契约违背。

### F-5（INFO，不可判定）—— 「18 处定点修订」

intelligentbase **无 git 仓库**（`git status` → `fatal: not a git repository`），亦无 1.0.0 基线副本，
**无法**用 diff 复核「18 处」这一计数。可交叉核对的只有 §12/修订记录自述的编辑点枚举
（C-02 4 点 / C-03 2 / C-04 3 / C-05 1 / C-06 1 / B-05 3 / §1.2 状态 5 / §11-§12 2 ≈ 21 点，量级相符）。
标为 **NOT_FULLY_DETERMINABLE**，不据此判违规。

---

## 4. 复核意见

- devops 自述的**纪律性声明（改哪里 / 没改哪里 / 未触目标机 / 未自称 APPROVED / 无凭据）全部与实测相符**，
  其中「键集一致」实测比自述更强（键+值全等）。
- 唯一需 PM 处置的是 **F-1**：C-02 修订使 plan 与 `checklists.txt` 脱节，且该缺口**未被登记**。
  修 `checklists.txt` 超本轮授权，建议 PM 在 **GR-E-002** 门控时选择其一：
  ①单独立项补 `checklists.txt`（B12 增 nginx/`nginx -t`/`proxy_buffering off` 三条 + 更正「由 ib-web 托管」）；
  ②或把该缺口登记为 PHASE_11 前置开放项。
- F-2 建议随下一轮文档修订一并更正 C-01 括注（不改变 C-01 的**未闭合**状态）。
