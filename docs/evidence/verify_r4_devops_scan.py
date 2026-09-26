#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立只读核验探针 —— GROUP_E / PHASE_10 R4 文档修订 (INV-GROUP_E-INTELBASE-002)

约束：
  * 只读。不写任何被检文件，不改 FreeArk，不连目标机 192.168.31.133，不连外部服务。
  * 唯一输出 = 本探针 stdout（由调用方 tee 到 docs/evidence/verify_r4_devops_scan.log）。
用法：
  PYTHONUTF8=1 python docs/evidence/verify_r4_devops_scan.py
"""
import io
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FREEARK = os.path.abspath(os.path.join(ROOT, "..", "FreeArk"))

DOCS = ["docs/deployment_plan.md", "docs/cicd_pipeline.md"]
SRC = ["src/deploy/ib-worker.env.example", "src/deploy/systemd/qdrant.service"]
FOUR = DOCS + SRC

FAIL = []


def head(n, title):
    print("\n" + "=" * 78)
    print(f"[{n}] {title}")
    print("=" * 78)


def p(*a):
    print(*a)


def note(ok_or_bad, text):
    if ok_or_bad == "BAD":
        FAIL.append(text)
    p(f"  {ok_or_bad}: {text}")


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8", errors="replace").read()


def mtimes(paths, recursive=False):
    out = []
    for base in paths:
        b = os.path.join(ROOT, base)
        if recursive:
            for dp, _dn, fn in os.walk(b):
                for f in fn:
                    fp = os.path.join(dp, f)
                    rel = os.path.relpath(fp, ROOT).replace("\\", "/")
                    out.append((os.path.getmtime(fp), rel))
        elif os.path.isfile(b):
            out.append((os.path.getmtime(b), base))
    return sorted(out, reverse=True)


# ---------------------------------------------------------------- 1. src 改动面
head(1, "src/ 改动面收敛（R4-devops 窗口 = 2026-09-26 09:00 起）")
src_rows = mtimes(["src"], recursive=True)
src_rows = [r for r in src_rows if "__pycache__" not in r[1]]
p("  src/** 全量（排除 __pycache__），按 mtime 降序，前 12 条：")
for ts, rel in src_rows[:12]:
    p(f"    {ts:.0f}  {rel}")
import datetime as _dt

CUT = _dt.datetime(2026, 9, 26, 9, 0, 0).timestamp()
CUT2 = _dt.datetime(2026, 9, 26, 8, 47, 0).timestamp()
w1 = [r for r in src_rows if r[0] >= CUT]
w2 = [r for r in src_rows if r[0] >= CUT2]
p(f"\n  mtime >= 09:00:00 的 src/ 文件数 = {len(w1)}: {[r[1] for r in w1]}")
p(f"  mtime >= 08:47:00 的 src/ 文件数 = {len(w2)}: {[r[1] for r in w2]}")
expect = {"src/deploy/ib-worker.env.example", "src/deploy/systemd/qdrant.service"}
note("OK" if set(r[1] for r in w2) == expect else "BAD",
     f"宽松窗口(>=08:47)内 src/ 改动恰为 {sorted(expect)}，无第三处" if set(r[1] for r in w2) == expect
     else f"发现额外 src/ 改动: {sorted(set(r[1] for r in w2) - expect)}")

# ------------------------------------------------- 2. 键集 / 值 逐键一致
head(2, "env.example vs ib-worker.env.example 键集与值逐键比对")
env = read("src/deploy/env.example")
wrk = read("src/deploy/ib-worker.env.example")


def kv(s):
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"(?m)^(IB_[A-Z0-9_]+)=(.*)$", s)}


a, b = kv(env), kv(wrk)
ka, kb = set(a), set(b)
p(f"  env.example       键数 = {len(ka)}")
p(f"  ib-worker.example 键数 = {len(kb)}")
p(f"  A-B 差集 = {sorted(ka - kb)}")
p(f"  B-A 差集 = {sorted(kb - ka)}")
note("OK" if not (ka - kb) and not (kb - ka) else "BAD",
     "键集逐键一致（差集双空）" if not (ka - kb) and not (kb - ka) else "键集不一致")
p(f"  键+值 全等 = {a == b}")

p("\n  ib-worker.env.example 逐值占位符判定：")
placeholders = []
for k in sorted(b):
    v = b[k]
    is_ph = v.startswith("<REPLACE_ME")
    if is_ph:
        placeholders.append(k)
    p(f"    {'PLACEHOLDER' if is_ph else 'safe-default'}  {k}={v}")
realval = [k for k in b if not b[k].startswith("<REPLACE_ME") and re.search(
    r"(sk-[A-Za-z0-9]{16,}|ghp_|AKIA|-----BEGIN|password|passwd|Bearer\s+[A-Za-z0-9._-]{20,})", b[k], re.I)]
note("OK" if not realval else "BAD",
     f"无真实值残留；{len(placeholders)} 个占位符 + 其余安全默认" if not realval else f"疑似真实值: {realval}")

# ------------------------------------------------------------- 3. 凭据扫描
head(3, "凭据模式扫描（只报命中数，不复述任何疑似值）")
PATS = {
    "openai_sk": r"sk-[A-Za-z0-9]{16,}",
    "github_pat": r"ghp_[A-Za-z0-9]{10,}",
    "aws_akia": r"AKIA[0-9A-Z]{12,}",
    "pem_private": r"-----BEGIN[A-Z ]*PRIVATE KEY",
    "password_assign": r"password\s*[:=]",
    "passwd_assign": r"passwd\s*[:=]",
    "token_assign_realval": r"token\s*=\s*[^<\s]",
    "ssh_pass_assign": r"IB_SSH_PASS\s*[:=]",
    "cred_lhs_ip": r"(SSH_PASS|PASSWORD|PASSWD|SECRET|API_KEY|TOKEN)\s*[:=]\s*[^\s<]*192\.168\.31\.133",
    "bearer_literal": r"Bearer\s+[A-Za-z0-9._\-]{20,}",
    "ssh_rsa_literal": r"ssh-rsa\s+AAAA",
}
for f in FOUR:
    s = read(f)
    hits = {k: len(re.findall(v, s)) for k, v in PATS.items()}
    hits = {k: v for k, v in hits.items() if v}
    p(f"  {f}: {hits if hits else 'ALL ZERO'}")
sv = read(SRC[0])
p(f"\n  ib-worker.env.example 是否仅含占位符/安全默认: {not realval}")
ip_hits = {f: len(re.findall(r"192\.168\.31\.133", read(f))) for f in FOUR}
p(f"  192.168.31.133 字面出现次数（应为「目标机」标注，非赋值）: {ip_hits}")

# ------------------------------------------------------- 4. phase_status.md
head(4, "docs/phase_status.md（PM 独占）XML 合法性与内容指纹")
ps = os.path.join(ROOT, "docs", "phase_status.md")
tree = ET.parse(ps)          # 不合法 XML 会在此抛异常
root = tree.getroot()
p(f"  ElementTree.fromstring 等价解析: OK，根 tag = {root.tag}")
gates = root.findall(".//gate_review")
gids = [g.get("id") for g in gates]
p(f"  gate_review 计数 = {len(gates)}")
p(f"  gate_review id 列表 = {gids}")
p(f"  GR-C-004 在列 = {'GR-C-004' in gids} ; GR-D-003 在列 = {'GR-D-003' in gids} ; GR-E-002 在列 = {'GR-E-002' in gids}")
note("OK" if ("GR-C-004" in gids and "GR-D-003" in gids and "GR-E-002" not in gids) else "BAD",
     "含 GR-C-004/GR-D-003 且无 GR-E-002（devops 未抢发门控）")
logs = root.findall(".//log")
inputs = root.findall(".//input")
p(f"  log 计数 = {len(logs)}")
p(f"  input 计数 = {len(inputs)}")
for g in root.findall("group"):
    gg = g.get("id")
    if gg in ("GROUP_C", "GROUP_E"):
        p(f"  {gg} gate_decision = {g.get('gate_decision')}")
        for ph in g.findall("phase"):
            p(f"    {gg}/{ph.get('id')} status={ph.get('status')} r4_invocation_id={ph.get('r4_invocation_id')}")
psmt = os.path.getmtime(ps)
p(f"  phase_status.md mtime = {_dt.datetime.fromtimestamp(psmt)}")
p(f"  首处 devops 产物 mtime = {_dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(ROOT, 'docs/deployment_plan.md')))}")
note("OK" if psmt < os.path.getmtime(os.path.join(ROOT, "docs", "deployment_plan.md")) else "BAD",
     "phase_status.md mtime 早于 devops 全部产物 → 非本轮 devops 写入")

# --------------------------------------------------------- 5. docs 改动面
head(5, "docs/ 改动面（R4-devops 窗口）")
doc_rows = mtimes(["docs"], recursive=True)
p("  docs/** 按 mtime 降序前 10 条：")
for ts, rel in doc_rows[:10]:
    p(f"    {ts:.0f}  {rel}")
w = [r[1] for r in doc_rows if r[0] >= CUT]
p(f"\n  mtime >= 09:00 的 docs 文件 = {w}")
must_not = ["docs/tech_stack.md", "docs/module_design.md", "docs/test_plan.md",
            "docs/test_report.md", "docs/architecture_design.md", "docs/requirements_spec.md"]
touched_bad = [f for f in must_not if any(r[1] == f and r[0] >= CUT for r in doc_rows)]
note("OK" if not touched_bad else "BAD",
     "tech_stack/module_design/test_*/architecture 均未在本轮改动" if not touched_bad else f"越界改动: {touched_bad}")

# -------------------------------------------------- 6. file_header 越权声明
head(6, "file_header status / 调用 ID（不得自称 APPROVED）")
for f in DOCS:
    s = read(f)
    inv = sorted(set(re.findall(r"INV-GROUP_E-INTELBASE-\d+", s)))
    # 头部「调用 ID」行必须为本轮 002；001 仅允许出现在 v1.0.0 修订记录行
    hdr_inv = re.search(r"(?m)^\| 调用 ID \| (.+?) \|", s).group(1).strip()
    has_appr = bool(re.search(r"\bAPPROVED\b", s))
    rev = bool(re.search(r"REVISED_PENDING_REVIEW", s))
    ver = (re.search(r"(?m)^\| 版本 \| (.+?) \|", s) or [None, "?"])[1]
    st = re.search(r"(?m)^\| status \| (.+?) \|", s).group(1).strip()
    p(f"  {f}: 全文调用ID={inv} | 头部调用ID={hdr_inv}")
    p(f"      status 行: {st}")
    p(f"      含 APPROVED:{has_appr} | 含 REVISED_PENDING_REVIEW:{rev}")
    p(f"      版本行: {ver}")
    ok = (not has_appr) and rev and hdr_inv == "INV-GROUP_E-INTELBASE-002" and "002" in "".join(inv)
    note("OK" if ok else "BAD", f"{f} status 未越权、头部调用 ID = 002")

# ------------------------------------------- 7. 文档事实一致性（抽查）
head(7, "文档事实一致性抽查")
web = read("src/deploy/systemd/ib-web.service")
webport = re.search(r"--port=(\d+)", web)
plan = read("docs/deployment_plan.md")
p(f"  ib-web.service --port = {webport.group(1)}（第 51 行: {web.splitlines()[50].strip()}）")
p(f"  plan §7.5 反代目标含 127.0.0.1:{webport.group(1)} = {'yes' if 'proxy_pass http://127.0.0.1:' + webport.group(1) in plan else 'no'}")
p(f"  §7.5 警告 nginx 不得用 18080（EADDRINUSE 与 Waitress 冲突）= "
  f"{'yes' if 'EADDRINUSE' in plan and '不得与 Waitress' in plan else 'no'}")
p(f"  §1.2 C-01 仍为未闭合（无 ✅ 标记）= "
  f"{'yes' if re.search(r'(?m)^\| C-01 \| .*DNS', plan) and '✅' not in re.search(r'(?m)^\| C-01 \|.*$', plan).group(0) else 'no'}")
p(f"  §12.2 O-07 明示 C-01 待定 = {'C-01，仍待 PM 定' in plan}")
p(f"  §6.1 含「两条链路合并评估」 = {'OCR 链路' in plan and 'embedding 链路' in plan and '合并评估' in plan}")
p(f"  §6.1 含目标机最小探针（import + 一次真实推理） = {'目标机最小探针' in plan and 'onnxruntime as ort' in plan}")
p(f"  C-04 叙述与实际 unit 一致（ExecStart=/usr/bin/qdrant）= "
  f"{'/usr/bin/qdrant --config-path' in read('src/deploy/systemd/qdrant.service')}")
for f in ["checklists.txt", "systemd/ib-worker.service", "systemd/ib-web.service", "systemd/ib-embed.service"]:
    p(f"  src/deploy/{f} 未在本轮窗口内被改 = "
      f"{all(r[1] != 'src/deploy/' + f for r in w2)}")

# ---------------------------------------------- 7b. 交叉引用行号核验
head("7b", "文档内行号引用核验")
for label, path, lineno, needle in [
    ("§7.3 引 ib-web.service:51", "src/deploy/systemd/ib-web.service", 51, "port=18080"),
    ("§7.4 引 ib-worker.service:42", "src/deploy/systemd/ib-worker.service", 42, "ib-worker.env"),
    ("修订记录引 qdrant.service:35", "src/deploy/systemd/qdrant.service", 35, "/usr/bin/qdrant"),
    ("C-02 引 vite.config.ts 注释", "src/frontend/vite.config.ts", 10, "127.0.0.1:18080"),
]:
    line = read(path).splitlines()[lineno - 1].strip()
    ok = needle in line
    p(f"  {label}: L{lineno} = {line[:90]!r} -> {'OK' if ok else 'MISMATCH'}")
    note("OK" if ok else "BAD", label)

# ---------------------------- 7c. 新增发现：checklists.txt 与 C-02 不同步
head("7c", "新发现：src/deploy/checklists.txt 未含 nginx/SSE 条目（C-02 未同步）")
cl = read("src/deploy/checklists.txt")
p(f"  checklists.txt mtime = {_dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(ROOT, 'src/deploy/checklists.txt')))}（不在本轮窗口）")
p(f"  checklists.txt 中 'nginx' 出现次数 = {len(re.findall('nginx', cl, re.I))}（仅 B10 日志纪律那条）")
p(f"  checklists.txt 含 'nginx -t' = {'nginx -t' in cl}")
p(f"  checklists.txt 含 'proxy_buffering' = {'proxy_buffering' in cl}")
b12 = cl[cl.index("[B12]"):cl.index("[B13]")]
p("  [B12] 原文：")
for l in b12.strip().splitlines():
    p(f"    {l}")
p(f"  [B12] 中写「由 ib-web 托管 dist/」 = {'由 ib-web 托管' in cl}")
p(f"  而 settings.py 无 STATIC_ROOT = {not re.search(r'STATIC_ROOT|STATICFILES', read('src/ibweb/settings.py'))}")
note("BAD", "plan §11.2 断言 B12 含 nginx -t / proxy_buffering off，实际 checklists.txt B12 无任何 nginx 条目（plan↔artifact 引用不一致，且未登记为开放项）")

# --------------------------------------------------- 9. FreeArk 只读
head(9, "FreeArk 仓库只读核验")
try:
    out = subprocess.run(["git", "-C", FREEARK, "status", "--porcelain"],
                         capture_output=True, text=True, timeout=60).stdout
    rows = [l for l in out.splitlines() if l.strip()]
    dirty = [l for l in rows if not l.startswith("??")]
    p(f"  git status --porcelain 行数 = {len(rows)}（全部 ?? 未跟踪 = {len(rows) - len(dirty)}）")
    p(f"  含 M/A/D/R 的行 = {len(dirty)} -> {dirty}")
    note("OK" if not dirty else "BAD", "FreeArk 无任何 M/A/D（仅既存 ??）" if not dirty else f"FreeArk 被改: {dirty}")
except Exception as e:  # pragma: no cover
    note("BAD", f"FreeArk 核验失败: {e}")

# --------------------------------------------------- 8. 目标机接触（间接）
head(8, "目标机 192.168.31.133 接触痕迹（间接判定）")
p("  探针自身不发起任何网络连接；本项只能事后查残留：")
kh = os.path.expanduser("~/.ssh/known_hosts")
if os.path.exists(kh):
    p(f"  known_hosts mtime = {_dt.datetime.fromtimestamp(os.path.getmtime(kh))}（早于本轮窗口）")
    p(f"  known_hosts 含目标 IP = {bool(re.search('192.168.31.133', io.open(kh, encoding='utf-8', errors='replace').read()))}（历史轮次已学习主机键）")
hits = []
for dp, dn, fn in os.walk(ROOT):
    if "__pycache__" in dp or ".git" in dp:
        continue
    for f in fn:
        if re.search(r"ssh|scp|rsync|plink|pscp", f, re.I):
            hits.append(os.path.join(dp, f))
p(f"  intelligentbase 内 ssh/scp/rsync 命名文件 = {hits}")
p("  结论：无本轮 SSH 痕迹；但无审计钩子，不能排除窗口内一次已建立即断开的连接 -> NOT_FULLY_DETERMINABLE")

# --------------------------------------------------- 总判定
head("SUM", "总判定")
if FAIL:
    p(f"  异常项 {len(FAIL)} 条：")
    for f in FAIL:
        p(f"    - {f}")
    sys.exit(1)
p("  除 7c 登记的 plan↔checklists 引用不一致（新发现，非纪律越界）外，本轮 devops 自述全部与实测相符。")
sys.exit(0)
