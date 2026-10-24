<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-10-23T23:16:18+08:00</timestamp>
  <project_name>trae-demo-wordfreq</project_name>
  <version>1.0.0</version>
  <input_files><file>sandbox/trae-demo-wordfreq/docs/architecture_design.md</file><file>sandbox/trae-demo-wordfreq/docs/requirements_spec.md</file><file>sandbox/trae-demo-wordfreq/docs/user_stories.md</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — trae-demo-wordfreq

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-001 | core | `sandbox/trae-demo-wordfreq/src/wordfreq/core.py`（新建） | 纯逻辑：分词、计数、排序、格式化、UTF-8 读取与组合执行 | REQ-FUNC-001…008、REQ-NFUNC-002/003；US-001…007 | 仅标准库 |
| MOD-002 | cli | `sandbox/trae-demo-wordfreq/src/wordfreq/__main__.py`（新建） | 参数解析、错误映射、stdout/stderr 与退出码 | REQ-FUNC-001…004、007、008；US-001…007 | MOD-001 |
| MOD-003 | package | `sandbox/trae-demo-wordfreq/src/wordfreq/__init__.py`（新建） | 公开 API 导出与版本号 | REQ-FUNC-001；US-001 | MOD-001 |

界面/服务：无。鉴权：无（本地单用户 CLI，不访问网络，见各接口"鉴权"字段）。

## 模块详情

### MOD-001 core — `src/wordfreq/core.py`

职责：所有可复用、可单测的业务逻辑。不读 stdin、不打印、不调用 `sys.exit`。

**IFC-001 `tokenize`**
```python
def tokenize(text: str, *, ignore_case: bool = False, min_length: int = 1) -> list[str]
```
- 语义：若 `ignore_case` 为真，先 `text.lower()`；用 `re.compile(r"[^\W_]+", re.UNICODE)` 提取词；过滤 `len(word) < min_length`。`min_length <= 1` 时等价于不过滤。
- 输入校验：`text` 必须是 `str`（类型错误由调用方/运行时暴露，不做静默转换）；`min_length` 为负或 0 时按 1 处理。
- 错误类型：无显式抛出；`TypeError` 由 Python 在类型不符时抛出。
- 鉴权：无需鉴权（纯函数，本地内存）。

**IFC-002 `count_words`**
```python
def count_words(text: str, *, ignore_case: bool = False, min_length: int = 1) -> collections.Counter[str]
```
- 语义：对 `tokenize` 结果计数；键为词，值为次数。
- 错误类型：同 IFC-001。
- 鉴权：无。

**IFC-003 `top_words`**
```python
def top_words(counter: collections.Counter[str], top: int = 10) -> list[tuple[str, int]]
```
- 语义：`top <= 0` 返回空列表；否则按 `(-count, word)` 排序后取前 `top` 项；词数不足时返回全部。
- 输入校验：`top` 为负数或 0 视为 0（返回空），不报错（architecture A-02）。
- 错误类型：无；`counter` 非 `Counter` 时行为未定义（内部调用方保证）。
- 鉴权：无。

**IFC-004 `format_report`**
```python
def format_report(items: collections.abc.Sequence[tuple[str, int]]) -> str
```
- 语义：每行 `f"{word}\t{count}"`，行间 `\n`，末尾**无**换行；空序列返回 `""`（PM 澄清 Q1 的固化契约）。
- 错误类型：无。
- 鉴权：无。

**IFC-005 `read_text`**
```python
def read_text(path: pathlib.Path) -> str
```
- 语义：`path.read_text(encoding="utf-8")`；显式 UTF-8，忽略平台默认编码。
- 错误类型：`FileNotFoundError` / `PermissionError` / `IsADirectoryError`（`OSError` 子类）；非法字节抛 `UnicodeDecodeError`。不在此层捕获（ADR-004）。
- 鉴权：无（本地文件系统权限）。

**IFC-006 `run`**
```python
def run(path: str | pathlib.Path, *, top: int = 10, ignore_case: bool = False, min_length: int = 1) -> str
```
- 语义：`read_text` → `count_words` → `top_words` → `format_report` 的组合。
- 错误类型：透传 IFC-005 的 `OSError` / `UnicodeDecodeError`。
- 鉴权：无。

### MOD-002 cli — `src/wordfreq/__main__.py`

职责：进程边界。唯一允许写 stdout/stderr、返回退出码的模块。

**IFC-007 `build_parser`**
```python
def build_parser() -> argparse.ArgumentParser
```
- 语义：`prog="wordfreq"`；位置参数 `path`（必填）；`--top`（`type=int`，默认 10）；`--ignore-case`（`store_true`）；`--min-length`（`type=int`，默认 1）。
- 输入校验：缺 `path`、`--top`/`--min-length` 非整数 → argparse 写 stderr 并 `SystemExit(2)`（与 REQ-FUNC-007 的退出码 2 一致）。
- 鉴权：无需鉴权（本地 CLI）。

**IFC-008 `main`**
```python
def main(argv: collections.abc.Sequence[str] | None = None) -> int
```
- 语义：解析参数 → 调 `run` → 若结果非空则 `print(result)` → 返回 0。捕获 `OSError` 与 `UnicodeDecodeError`：`print(f"wordfreq: error: {exc}", file=sys.stderr)` 并返回 2。
- 输出契约：正常时 stdout 仅包含 IFC-004 的文本 + 一次换行；错误时 stdout 为空、stderr 至少一行且含 `wordfreq` 前缀。
- 错误类型：不抛出（参数错误由 argparse 抛 `SystemExit`）。
- 鉴权：无。

**IFC-009 入口**：模块末尾 `if __name__ == "__main__": raise SystemExit(main())`，使 `python -m wordfreq PATH` 生效。

### MOD-003 package — `src/wordfreq/__init__.py`

**IFC-010 公开导出**
```python
__all__: list[str] = ["count_words", "format_report", "read_text", "run", "tokenize", "top_words"]
__version__: str = "1.0.0"
from .core import count_words, format_report, read_text, run, tokenize, top_words
```
- 语义：仅重导出 MOD-001 的公开函数，不含逻辑。
- 鉴权：无。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-001 | US-001 | MOD-001（IFC-006）、MOD-002（IFC-007/008）、MOD-003（IFC-010） |
| REQ-FUNC-002 | US-002 | MOD-002（IFC-007）、MOD-001（IFC-003） |
| REQ-FUNC-003 | US-003 | MOD-002（IFC-007）、MOD-001（IFC-001） |
| REQ-FUNC-004 | US-004 | MOD-002（IFC-007）、MOD-001（IFC-001） |
| REQ-FUNC-005 | US-005 | MOD-001（IFC-001） |
| REQ-FUNC-006 | US-005 | MOD-001（IFC-003） |
| REQ-FUNC-007 | US-006 | MOD-001（IFC-005）、MOD-002（IFC-008） |
| REQ-FUNC-008 | US-007 | MOD-001（IFC-005）、MOD-002（IFC-008） |
| REQ-NFUNC-001 | US-001…007 | 全部 MOD（仅标准库） |
| REQ-NFUNC-002 | US-005 | MOD-001（IFC-003/004） |
| REQ-NFUNC-003 | US-001 | MOD-001（IFC-001/002） |

## 依赖关系

```
MOD-002 (cli) --IFC-006--> MOD-001 (core)
MOD-003 (package) --IFC-001..006--> MOD-001 (core)
```

- MOD-001 不依赖任何内部模块（叶子）。
- 已检查：无循环依赖（`MOD-002 → MOD-001`、`MOD-003 → MOD-001`，无反向边）。
- 测试代码不进入模块依赖图；测试路径遵守画像 P3：`tests/unit/`、`tests/integration/`、`tests/e2e/`。

## 数据迁移

无。本项目不持久化任何数据，无表结构、无字段变更、无迁移脚本（画像 P6"数据迁移方式：无"）。

## 受影响的运行单元 / 构建

| 运行单元 | 位置 | 影响 | 操作 |
|---|---|---|---|
| CLI 进程 `python -m wordfreq` | dev/local | 新建 | 无需构建；直接运行源码 |
| pytest 进程 | dev/local | 新增测试 | `python -m pytest sandbox/trae-demo-wordfreq/tests -q` |
| 服务/定时任务/前端构建 | — | 无 | 画像 P7 声明无服务、无定时任务、无前端 |

无编译产物、无容器镜像、无部署配置（画像 P7"部署方式：无"；本轮 E1 只产出计划）。
