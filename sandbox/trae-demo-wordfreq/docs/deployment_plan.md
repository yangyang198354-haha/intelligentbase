<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-10-23T23:31:44+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/architecture_design.md</file><file>sandbox/trae-demo-wordfreq/docs/module_design.md</file><file>sandbox/trae-demo-wordfreq/docs/tech_stack.md</file><file>sandbox/trae-demo-wordfreq/docs/implementation_plan.md</file><file>sandbox/trae-demo-wordfreq/docs/unit_test_report.md</file><file>sandbox/trae-demo-wordfreq/docs/integration_test_report.md</file><file>sandbox/trae-demo-wordfreq/docs/e2e_test_report.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — trae-demo-wordfreq

> **本轮不执行 E2**：仅产出计划。未获得用户在当轮的部署授权，且画像 P7 声明"部署方式：无"。
> 计划中的命令均为 dev/local 的可执行示例，执行前必须先通过预检清单。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| MOD-001 core | `sandbox/trae-demo-wordfreq/src/wordfreq/core.py` | 无 | 无（纯 Python 源码，`compileall` 仅校验） | 无 |
| MOD-002 cli | `sandbox/trae-demo-wordfreq/src/wordfreq/__main__.py` | 无 | 无 | 无 |
| MOD-003 package | `sandbox/trae-demo-wordfreq/src/wordfreq/__init__.py` | 无 | 无 | CLI 进程按需启动，无常驻服务 |
| 测试 | `tests/unit`、`tests/integration`、`tests/e2e`、`conftest.py`、`pytest.ini` | 无 | 无 | 不部署（仅 CI 使用） |

- 数据迁移：**无**（module_design"数据迁移：无"）。
- 无容器、无服务、无定时任务、无前端构建（画像 P7、P8）。

## 目标环境与策略

- **目标环境：dev/local**（画像 P7 唯一存在的环境；staging / production 不存在，不设计）。
- **策略：recreate**（画像 P7 允许的唯一策略）。
  - 理由：单进程 CLI、无冗余实例、无并发请求；"重建目录 + 复制源码"是最小且可逆的方式。
  - 预计停机：**0 秒**（没有常驻服务在运行；CLI 在每次调用时启动）。
- 安装位置（本文统一变量）：
  - `$TARGET = Join-Path $env:LOCALAPPDATA "wordfreq-demo"`（用户级目录，不触碰系统目录）
  - 运行方式：`$env:PYTHONPATH = $TARGET; python -m wordfreq ...`
- 权限：仅当前用户可写；无需管理员权限。

## 预检清单

| # | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| PRE-01 | 测试门控已通过（GROUP_D APPROVED） | `python -m pytest sandbox/trae-demo-wordfreq/tests -q` | 退出码 0；`17 passed`（unit 10 / int 4 / e2e 3） |
| PRE-02 | 待部署源码快照固定（画像 P9 不执行 commit/push） | `Get-FileHash sandbox/trae-demo-wordfreq/src/wordfreq/*.py -Algorithm SHA256` | 3 个哈希写入部署记录；部署期间源码未变动 |
| PRE-03 | 回滚锚点已记录 | `$TARGET = Join-Path $env:LOCALAPPDATA "wordfreq-demo"; Test-Path $TARGET` | 存在 → 记录完整文件清单与哈希；不存在 → 锚点记为 `ABSENT(greenfield)` |
| PRE-04 | 目标目录无未知本地状态 | `if (Test-Path $TARGET) { Get-ChildItem $TARGET -Recurse -File \| Where-Object { $_.FullName -notlike "*\wordfreq\*" } }` | 输出为空；否则停止并上报（画像 P7 声明无必须保留的本地状态） |
| PRE-05 | Python 版本满足 3.11+ | `python --version` | 主版本 = 3，次版本 ≥ 11 |
| PRE-06 | 磁盘空间充足 | `(Get-PSDrive $env:SystemDrive.TrimEnd(':')).Free` | ≥ 100 MB [INFERRED]（本项目源码 < 1 MB） |
| PRE-07 | 无数据迁移 | — | 无迁移脚本/无数据库（module_design"数据迁移：无"） |
| PRE-08 | 目标机本地状态不被触碰 | 审查 DEPLOY-002 命令 | 仅写 `$TARGET` 与同级的 `$TARGET.bak-<STAMP>`；不写仓库、不写系统目录 |

## 部署步骤

统一变量（执行前在**同一会话**中定义并 echo 核对）：

```powershell
$TARGET = Join-Path $env:LOCALAPPDATA "wordfreq-demo"
$STAMP  = Get-Date -Format "yyyyMMddTHHmmss"
Write-Output "TARGET=$TARGET"; Write-Output "STAMP=$STAMP"
```

### DEPLOY-001: 记录回滚锚点与源码哈希

- 组件：无（只读预检）
- 位置：开发机（dev/local）
- 命令：

```powershell
$SRC = Join-Path (Get-Location) "sandbox/trae-demo-wordfreq/src/wordfreq"
Get-FileHash "$SRC/*.py" -Algorithm SHA256 | Format-Table Path, Hash
if (Test-Path $TARGET) { Get-ChildItem $TARGET -Recurse -File | Select-Object FullName, Length, LastWriteTime }
else { Write-Output "ANCHOR=ABSENT(greenfield)" }
```

- 预期：输出 3 个源码哈希；目标目录存在时列出全部文件，不存在时打印 `ANCHOR=ABSENT(greenfield)`。
- 回滚：ROLLBACK-001

### DEPLOY-002: 备份旧目录并复制新源码（recreate）

- 组件：MOD-001/002/003（`architecture_design.md` 部署视图：单次 CLI 进程）
- 位置：开发机（dev/local）
- 命令：

```powershell
if (Test-Path $TARGET) { Move-Item -LiteralPath $TARGET -Destination "$TARGET.bak-$STAMP" }
New-Item -ItemType Directory -Path $TARGET -Force | Out-Null
Copy-Item -LiteralPath "$SRC\*" -Destination $TARGET -Recurse -Force
Get-ChildItem $TARGET -File | Select-Object Name, Length
```

- 预期：`$TARGET` 下出现 `__init__.py`、`__main__.py`、`core.py` 三个文件；若原先存在安装目录，则原目录被整体移动到 `$TARGET.bak-$STAMP`（未删除、未覆盖）。
- 回滚：ROLLBACK-002

### DEPLOY-003: 部署后冒烟（临时文件，唯一命名）

- 组件：CLI 端到端可用性
- 位置：开发机（dev/local）
- 命令：

```powershell
$SMOKE = Join-Path $env:TEMP ("wordfreq-smoke-" + [guid]::NewGuid().ToString("N") + ".txt")
Set-Content -LiteralPath $SMOKE -Value "alpha beta alpha" -Encoding utf8
$env:PYTHONPATH = $TARGET
python -m wordfreq $SMOKE
python -m wordfreq --help
Write-Output "SMOKE_FILE=$SMOKE"
```

- 预期：第一条命令输出两行 `alpha\t2`、`beta\t1` 且退出码 0；`--help` 退出码 0；`SMOKE_FILE` 路径被记录。
- 回滚：ROLLBACK-003

## 回滚步骤（逆序）

### ROLLBACK-003: 回滚 DEPLOY-003（删除冒烟临时文件）

- 类型：正式回滚（仅清理本次创建的临时文件）
- 命令：

```powershell
# $SMOKE 取自 DEPLOY-003 输出；执行前用 Test-Path 与文件名前缀双重核验
$SMOKE = "<粘贴 DEPLOY-003 输出的 SMOKE_FILE 完整路径>"
if ((Test-Path $SMOKE) -and ((Split-Path $SMOKE -Leaf) -like "wordfreq-smoke-*.txt")) { Remove-Item -LiteralPath $SMOKE -Force }
```

- 变量取值与核验：`$SMOKE` 必须来自 DEPLOY-003 的 `SMOKE_FILE=` 输出；执行前确认前缀匹配，避免误删其他文件。
- 预期：临时文件不存在；对产品目录无影响。

### ROLLBACK-002: 回滚 DEPLOY-002（恢复旧目录 / 移除新目录）

- 类型：正式回滚
- 命令：

```powershell
# $TARGET 与 $STAMP 来自部署会话；执行前 echo 核对
if (Test-Path "$TARGET.bak-$STAMP") {
  Remove-Item -LiteralPath $TARGET -Recurse -Force
  Move-Item -LiteralPath "$TARGET.bak-$STAMP" -Destination $TARGET
  Write-Output "RESTORED=$TARGET"
} elseif (Test-Path $TARGET) {
  # 锚点为 ABSENT(greenfield)：只删除本次创建的目录
  Remove-Item -LiteralPath $TARGET -Recurse -Force
  Write-Output "REMOVED_NEW=$TARGET"
} else {
  Write-Output "NOOP_ALREADY_ABSENT"
}
```

- 变量取值与核验：
  - `$STAMP` 必须与 DEPLOY-002 使用的值完全一致（部署记录中登记）；执行前 `Write-Output "TARGET=$TARGET STAMP=$STAMP"` 核对。
  - 若锚点为 `ABSENT`，删除前确认 `Get-ChildItem $TARGET` 只含本次复制的 3 个文件。
- 预期：旧版本目录恢复；或新目录被移除且目标机回到部署前状态。
- 说明：不使用 `git reset --hard` / `git clean` / `git stash` / 覆盖式同步；只操作 `$TARGET` 及其备份，不触碰仓库与用户其他文件。

### ROLLBACK-001: 回滚 DEPLOY-001（无变更）

- 类型：无操作
- 命令：`Write-Output "NOOP: DEPLOY-001 为只读操作"`；如需，删除本次写入的锚点记录（仅记录文本）。
- 变量取值与核验：无。
- 预期：无系统变更。

## 不可逆步骤汇总

- **无**。没有数据迁移、没有外部系统调用、没有通知发送、没有删除既有数据。
- `Move-Item` 到 `$TARGET.bak-$STAMP` 保留旧目录；`Remove-Item` 仅作用于本次创建或明确核验过的路径。
- 无 `[MANUAL_ROLLBACK_REQUIRED]` 项。

## 部署后验证

| # | 检查项 | 命令/方法 | 成功标准 |
|---|---|---|---|
| VER-01 | CLI 可加载 | `$env:PYTHONPATH = $TARGET; python -m wordfreq --help` | 退出码 0，输出含 `usage: wordfreq` |
| VER-02 | 基础词频 | 对 `alpha beta alpha` 运行 | stdout 为 `alpha\t2`、`beta\t1`，退出码 0 |
| VER-03 | 选项生效 | `--ignore-case --min-length 5` 对 `Alpha alpha ALPHA gamma` | 输出 `alpha\t3`、`gamma\t1`，退出码 0 |
| VER-04 | 错误退出码 | 对不存在路径运行 | 退出码 2，stderr 含 `wordfreq: error:`，stdout 为空 |
| VER-05 | 版本号 | `python -c "import wordfreq; print(wordfreq.__version__)"`（`PYTHONPATH=$TARGET`） | 输出 `1.0.0` |
| VER-06 | 日志/错误无新异常 | 检查上述命令 stderr | 除 VER-04 的预期错误外，stderr 为空 |
| VER-07 | 外部可达性 | 不适用（本地 CLI 无网络端口） | — |

- 任意一项失败 → 按 ROLLBACK-003 → ROLLBACK-002 → ROLLBACK-001 逆序回滚，并报告 `DEPLOYED_WITH_ISSUES` 或 `ROLLED_BACK`（见 devops 规则 7）。
- 部署记录必须登记：源码 SHA256（PRE-02）、回滚锚点（PRE-03）、`$STAMP`、最终状态。
