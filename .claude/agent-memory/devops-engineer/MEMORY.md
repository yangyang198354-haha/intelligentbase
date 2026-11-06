# devops-engineer 项目记忆 — intelligentbase
> 2026-10-24 由旧 TRAE 知识库（.trae/skills/sdlc-devops-engineer/knowledge_base/）与 PM 旧条目中的运维部分迁移，按协议 §M 重新蒸馏；明细见 project_workspace/_kb_distillation/distill_20261024T1624.md。部署操作细节以 .claude/skills/ib-prod-deploy/SKILL.md 为准。

## 已验证
- [M-DE-001] systemd unit / env 模板 / checklists 与架构文档的漂移不会被测试发现，写部署计划时逐条交叉比对：二进制路径（qdrant 已统一 /usr/bin）、同一约束的多处数值（ib-embed `MemoryMax=2560M` ↔ `IB_EMBED_MEMORY_LIMIT_MB`）、WorkingDirectory 与包落点、引用的 env 模板是否存在 — conf 0.8 · 证据 GR-E-002 · 首见 2026-09-26 · 命中 2
- [M-DE-002] 部署后验证要直连依赖、防静默降级：ib-embed `/healthz` 须 `model_loaded=true` 且 dim 正确，冷热路径都真返回向量；OCR 引擎须是 RapidOcrEngine 而非 NullOcrEngine；扫描件整篇 0 字且无 WARNING 视为缺陷 — conf 0.6 · 证据 GR-E（NV-01~08 映射 checklists） · 首见 2026-09-26 · 命中 1
- [M-DE-003] 修订计划后同步 src/deploy/checklists.txt 等执行产物，否则执行时新验证项不会跑；nginx 是必需组件（settings 无 STATIC_ROOT，dist 不由 Django 托管），对外端口不得与 ib-web 回环口 18080 冲突 — conf 0.6 · 证据 GR-E-002 · 首见 2026-09 · 命中 1
- [M-DE-004] 新建 env 模板的键集须与既有模板逐键 diff 一致（`diff <(grep -oE '^IB_[A-Z_]+' a|sort) <(grep -oE '^IB_[A-Z_]+' b|sort)`），并声明未新增/改名键 — conf 0.6 · 证据 GR-E-002（ib-worker.env.example） · 首见 2026-09 · 命中 1
- [M-DE-005] ib-embed unit 的 `WorkingDirectory=/opt/ib-embed` 与仓库包位置 src/ib_embed 不一致时用软链（`ln -sfn`）保唯一真源，不复制第二份源码；验证 `python -c "import ib_embed; print(ib_embed.__file__)"` 指向源 — conf 0.6 · 证据 GR-E-002 · 首见 2026-09 · 命中 1
- [M-DE-006] AVX2 / SIGILL 风险按有序决策树处理，目标机最小探针优先（独立进程里 import + 一次真实推理）；逐链路写挂掉时的症状（embedding 挂 → healthz 仍 200 但 model_loaded=false → 检索静默降级） — conf 0.6 · 证据 TBD-T18 · 首见 2026-09 · 命中 1
- [M-DE-007] 文书订正一律追加式：原命令逐字保留并加"【订正前 · 不可运行】"前缀；写"等价"必须实测逐项比对（曾因缺 `backup=False` 多产出 root 属主 .bak）；只存在于 EnvironmentFile 的键（IB_LEDGER_PATH、IB_DEFINITION_DOC_PATH）在交互 shell 中为空，备份命令写字面路径 — conf 0.6 · 证据 GR-E-007 · 首见 2026-10 · 命中 1
- [M-DE-008] checklists 新增 `[Bn]` 项时同步 selfcheck 签署行断言（B1–Bn），否则 selfcheck 少一项（REV-21 引入 B27 后 51/52） — conf 0.6 · 证据 commit 4f4ad5e · 首见 2026-10-17 · 命中 1
- [M-DE-009] 判断"某服务是否需重启"不能只看 module_design：ib-worker 经 django.setup() → apps.py ready() → build_deps() 与 ib-web 共用组合根，组合根里的副作用（如 MCP supervisor.start()）在 worker 重启时同样触发；计划里把跨进程副作用列为开放问题 — conf 0.8 · 证据 GR-E1-001-F01 / DEF-R29-008 / apps.py:49 · 首见 2026-11-05 · 命中 3
- [M-DE-010] 前端 lock 未变时部署只 `npm run build`，不照 checklists 的 `npm ci`（会删重建 node_modules，触碰画像 P7）；追加 env 密钥用 `printf '\nK=%s\n' "$V" | sudo tee -a file >/dev/null`，首个 `\n` 防文件末尾无换行造成拼接，核验只看行数/长度/键总数+1/stat — conf 0.6 · 证据 GR-E1-001-F02（checklists B30(3) 与 SKILL §5.2 冲突） · 首见 2026-11-05 · 命中 1
- [M-DE-011] 目标机核对"某进程有无某命名 Python 线程"：CPython ≤3.13 的 `/proc/<pid>/task/*/comm` 不含 threading 线程名（且限 15 字节），改用线程数差分、Python ≥3.14 的 comm 或用户侧 py-spy；对未重启旧进程的核对是平凡成立，须如实标注 — conf 0.6 · 证据 GR-E1-002 / supervisor.py:78-88 / 本机实测 · 首见 2026-11-06 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-DE-001] 往 checklists.txt 追加 [Bn] 时，selfcheck.py（约 :3535）断言子串 "B1–B27" 在文件中：保留旧签署行、另起一行写新项，避免越权改 selfcheck；并建议 software-developer 后续把断言扩到新号 — 自记 2026-10-24 · 证据 R25 E1（selfcheck 实跑仍 53/54）
- [P-DE-002] 迁移前基线查询不得引用迁移新增的列/表；台账只读查询用 `sudo -u ib-web … file:…?mode=ro`（不用 root）；远端 `pgrep -f` 会匹配 ssh 命令自身，用 `[i]bweb` 括号写法 — 自记 2026-10-24 · 证据 R25 E1 计划推演
- [P-DE-004] 改 ci.yml 迁移门后，用 yaml.safe_load 抽出该 step 的 run 脚本、在 venv 里原样执行，再对副本做反例变异（如删 IF NOT EXISTS）确认门会失败；热生效探针 hot_effect_probe.py 只核对版本一致与耗时分布，不测"发布到生效"的收敛时间，计划中须如实写明边界；目标机跑 selfcheck 用 git archive 的临时导出，避免在部署树写文件 — 自记 2026-10-27 · 证据 R26 E1
- [P-DE-005] "纯前端"增量的部署区间 ANCHOR..DEPLOY_COMMIT 可能夹带其他提交的后端文件（R27 区间含 6bfdef4 改 src/ib/runtime/cache.py）：E1 用 `git diff --name-only <上一已批准提交> <待部署>` 核对，计划里做 PRE 分类门（A 纯前端 / B 夹带后端运行时 / C 迁移或依赖），目标机 HEAD 不可假定时尤其必要 — 自记 2026-10-31 · 证据 R27 E1（git diff bb3ac4b 1dde3d4 -- src）
- [P-DE-003] 远端命令要用本地变量：`ssh host bash -s -- "$A" "$B" <<'EOF'`（heredoc 单引号定界，远端用 $1 $2），比双引号转义稳；markdown 里嵌在列表项中的 heredoc 代码块要顶格，否则粘贴时 EOF/python 缩进失效 — 自记 2026-10-24 · 证据 R25 E1 自检
- [P-DE-006] 增量新增"工具/授权类"配置能力时，代码回滚前须先在新代码下清除已保存的该类授权：旧代码定义校验对未知工具报 `tool_grant_tool_unknown`（definition.py:531），项目会加载失败；回滚计划里放 ROLLBACK-000（用户经配置页"版本→回滚"）并以只读脚本核验命中 0 — 自记 2026-11-04 · 证据 R28 E1（src/ib/config/definition.py:531）
