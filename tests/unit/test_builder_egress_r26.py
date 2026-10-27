"""[REV-26 / GROUP_D] MOD-R26-11 `EgressGuard`：Builder 云端外发的单点（白名单载荷 / 秘钥拦截 / 审计先行 / 限时 / 线程池满）。

溯源：US-030（AC-030-01~05）、US-024（AC-024-06/07）、US-028（AC-028-03）、REQ-NFUNC-014、C-R26-11、REQ-NFUNC-015。
层级：单元（completer 为注入的替身；审计为内存审计存储）。
"""

from __future__ import annotations

import dataclasses
import json
import threading

import pytest

from ib.builder.egress import (
    BUILDER_INSTRUCTION_MAX_CHARS,
    BUILDER_REQUIREMENT_MAX_CHARS,
    EGRESS_PAYLOAD_MAX_BYTES,
    EgressGuard,
    OutboundPayload,
    check_requirement,
    contains_secret_pattern,
    render_user_message,
)
from ib.builder.types import (
    AgentDigest,
    AgentDraft,
    BuilderBusy,
    BuilderUnavailable,
    EgressRejected,
    ProjectContext,
)
from ib.ledger.config_audit import MemoryConfigAuditStore

CANARY_DOC = "CANARY-DOC-001"
CANARY_SESSION = "CANARY-SESSION-001"
PLACEHOLDER_KEY = "sk-" + "TESTPLACEHOLDER0123456789"  # 占位测试 Key（非真实凭据），形似密钥以验证拦截


def _guard(completer, audit=None, **kw):
    return EgressGuard(completer=completer, audit=audit or MemoryConfigAuditStore(), clock=lambda: "2026-10-27T00:00:00Z", **kw)


def _payload(**kw):
    kw.setdefault("kind", "generate")
    return OutboundPayload(**kw)


def test_TC_UNIT_R26_210_payload_fields_are_exactly_the_whitelist():
    """US-030 / AC-030-01：载荷类型的字段集 = 白名单（需求/意见、项目摘要、被选 agent、评审项）；类型里没有会话/资料正文/账号/审计字段。"""
    names = {f.name for f in dataclasses.fields(OutboundPayload)}
    assert names == {"kind", "requirement_text", "instruction_text", "project_digest", "selected_agent", "rubric_items"}
    ctx_fields = {f.name for f in dataclasses.fields(ProjectContext)}
    assert ctx_fields == {"project_id", "agents", "tools", "folders", "constraints"}
    assert {f.name for f in dataclasses.fields(AgentDigest)} == {"name", "cn_label", "keywords", "exemplars"}, "摘要不含提示词全文"


def test_TC_UNIT_R26_211_canaries_never_reach_the_wire_and_project_id_not_sent():
    """US-030 / AC-030-01、US-028 / AC-028-03：项目资料/会话标记串（canary）与 project_id 不出现在发往云端的载荷里；
    其他 agent 的提示词（CANARY-PROMPT-002）也不在：摘要类型根本不携带提示词。"""
    sent = []
    g = _guard(lambda system, user, *, temperature, timeout_s: sent.append((system, user)) or "{}")
    ctx = ProjectContext(project_id="p_secret_id", agents=(AgentDigest("other", "其他", ("kw",), ()),))
    for kind in ("generate", "optimize"):
        g.send(_payload(kind=kind, requirement_text="做一个客服助手", project_digest=ctx), system="SYS", project_id="p_secret_id", actor="u")
    assert len(sent) == 2
    for _system, user in sent:
        for canary in (CANARY_DOC, CANARY_SESSION, "CANARY-PROMPT-002", "p_secret_id"):
            assert canary not in user
        assert set(json.loads(user)) <= {"kind", "requirement", "instruction", "project", "agent", "rubric_items"}
        assert not contains_secret_pattern(user)


def test_TC_UNIT_R26_212_secret_pattern_in_any_text_blocks_send_and_audit():
    """US-030 / AC-030-01：需求/意见/草案文本/摘要里出现密钥样式串 → EgressRejected，既不审计也不外发。"""
    sent, audit = [], MemoryConfigAuditStore()
    g = _guard(lambda *a, **k: sent.append(1) or "{}", audit)
    draft = AgentDraft("a", "标签", f"提示词含 {PLACEHOLDER_KEY}", "fb", (), (), False, False, (), (), (), 4, "generated")
    for p in (_payload(requirement_text=f"请使用 {PLACEHOLDER_KEY}"), _payload(kind="optimize", instruction_text="password=hunter2xyz"),
              _payload(kind="judge", selected_agent=draft)):
        with pytest.raises(EgressRejected) as ei:
            g.send(p, system="S", project_id="p", actor="u")
        assert ei.value.code == "egress_secret_detected"
    assert sent == [] and audit.list_by_project("p", limit=10) == ()


@pytest.mark.parametrize("text,hit", [
    ("sk-" + "A" * 20, True), ("ghp_" + "a" * 24, True), ("github_pat_" + "b" * 24, True), ("AKIA" + "A" * 16, True),
    ("-----BEGIN RSA PRIVATE KEY-----", True), ("api_key = abcd1234", True), ("普通的需求描述，没有任何密钥", False),
    ("sk-short", False),
])
def test_TC_UNIT_R26_213_secret_scanner_patterns(text, hit):
    """凭据模式扫描：典型形态命中，普通文本不误拦。"""
    assert contains_secret_pattern(text) is hit


def test_TC_UNIT_R26_214_audit_first_and_categories_only_no_text():
    """US-030 / AC-030-02：每次外发恰好 1 条审计（action=builder.egress），含类别清单与字节数；不含需求描述原文与提示词全文。"""
    audit = MemoryConfigAuditStore()
    seen_at_send = []
    g = _guard(lambda s, u, **k: seen_at_send.append(len(audit.list_by_project("p", limit=10))) or "{}", audit)
    secret_req = "客服助手需求独特文本-XYZ-12345"
    g.send(_payload(requirement_text=secret_req), system="S", project_id="p", actor="alice")
    assert seen_at_send == [1], "审计先于外发写入"
    (row,) = audit.list_by_project("p", limit=10)
    assert (row.action, row.actor, row.result) == ("builder.egress", "alice", "saved")
    assert "kind:generate" in row.object_summary and "cat:requirement_text" in row.object_summary
    assert any(s.startswith("bytes:") for s in row.object_summary)
    assert secret_req not in str(row)


def test_TC_UNIT_R26_215_audit_failure_cancels_send():
    """审计先行：审计写不进 → BuilderUnavailable(audit_failed)，不发送。"""
    class BadAudit:
        def record(self, entry):
            raise RuntimeError("down")

    sent = []
    g = _guard(lambda *a, **k: sent.append(1) or "{}", BadAudit())
    with pytest.raises(BuilderUnavailable) as ei:
        g.send(_payload(requirement_text="x"), system="S", project_id="p", actor="u")
    assert ei.value.reason == "audit_failed" and sent == []


def test_TC_UNIT_R26_216_timeout_returns_readable_error_within_limit():
    """US-030 / AC-030-04：云端请求永不返回 → 在时限内以 timeout 错误结束（此处 0.3 s 代替 60 s；60 s 为目标机验证项）。"""
    release = threading.Event()
    g = _guard(lambda *a, **k: release.wait(5) and "{}", timeout_s=0.3)
    import time

    t0 = time.monotonic()
    with pytest.raises(BuilderUnavailable) as ei:
        g.send(_payload(requirement_text="x"), system="S", project_id="p", actor="u")
    release.set()
    assert ei.value.reason == "timeout" and time.monotonic() - t0 < 3


def test_TC_UNIT_R26_217_unconfigured_key_and_network_errors_classified():
    """US-030 / AC-030-03：未配置 LLM Key → llm_unconfigured（文案含“尚未配置 LLM Key”）；网络错误 → network；4xx → rejected。"""
    def unconfigured(*a, **k):
        raise RuntimeError("LLM 未配置（Key 未设置）")

    with pytest.raises(BuilderUnavailable) as e1:
        _guard(unconfigured).send(_payload(requirement_text="x"), system="S", project_id="p", actor="u")
    assert e1.value.reason == "llm_unconfigured" and "尚未配置 LLM Key" in str(e1.value)

    def net(*a, **k):
        raise ConnectionError("boom")

    with pytest.raises(BuilderUnavailable) as e2:
        _guard(net).send(_payload(requirement_text="x"), system="S", project_id="p", actor="u")
    assert e2.value.reason == "network"

    class Http4xx(Exception):
        status_code = 401

    def rejected(*a, **k):
        raise Http4xx("nope")

    with pytest.raises(BuilderUnavailable) as e3:
        _guard(rejected).send(_payload(requirement_text="x"), system="S", project_id="p", actor="u")
    assert e3.value.reason == "rejected"


def test_TC_UNIT_R26_218_pool_full_returns_busy_not_queue():
    """线程池满 → BuilderBusy（不排队、不超发）。"""
    block = threading.Event()
    g = _guard(lambda *a, **k: block.wait(5) and "{}", pool_size=1, timeout_s=5)
    t = threading.Thread(target=lambda: g.send(_payload(requirement_text="1"), system="S", project_id="p", actor="u"))
    t.start()
    for _ in range(100):
        if not g._slots.acquire(blocking=False):
            break
        g._slots.release()
        threading.Event().wait(0.02)
    with pytest.raises(BuilderBusy):
        g.send(_payload(requirement_text="2"), system="S", project_id="p", actor="u")
    block.set()
    t.join(5)


def test_TC_UNIT_R26_219_requirement_validation_blank_and_too_long():
    """US-024 / AC-024-07：空/纯空白需求 → requirement_empty；超长 → requirement_too_long；边界恰好上限通过。"""
    for blank in ("", "   \n\t "):
        with pytest.raises(EgressRejected) as ei:
            check_requirement(blank)
        assert ei.value.code == "requirement_empty"
    with pytest.raises(EgressRejected) as e2:
        check_requirement("x" * (BUILDER_REQUIREMENT_MAX_CHARS + 1))
    assert e2.value.code == "requirement_too_long"
    assert check_requirement("  " + "x" * BUILDER_REQUIREMENT_MAX_CHARS + "  ") == "x" * BUILDER_REQUIREMENT_MAX_CHARS
    assert BUILDER_INSTRUCTION_MAX_CHARS == 1000


def test_TC_UNIT_R26_220_payload_size_cap():
    """规模上限：序列化后超过 64 KiB → egress_payload_too_large，不外发。"""
    ctx = ProjectContext(project_id="p", agents=tuple(AgentDigest(f"a{i}", "标签" * 5, tuple(f"kw{j}" for j in range(20)),
                                                                   tuple("例句" * 50 for _ in range(10))) for i in range(60)))
    assert len(render_user_message(_payload(project_digest=ctx)).encode()) > EGRESS_PAYLOAD_MAX_BYTES
    sent = []
    with pytest.raises(EgressRejected) as ei:
        _guard(lambda *a, **k: sent.append(1) or "{}").send(_payload(project_digest=ctx), system="S", project_id="p", actor="u")
    assert ei.value.code == "egress_payload_too_large" and sent == []
