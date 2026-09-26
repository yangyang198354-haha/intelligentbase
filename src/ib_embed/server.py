"""
@module MOD-IB-26
@implements IFC-IB-266 POST /embed（请求/响应结构、保序、绝不部分向量）
            IFC-IB-267 维度权威性（响应中的 dim 为实测值，非配置回声）
            IFC-IB-268 错误码表 + 统一错误体 + 4xx/5xx 分类不变式
            IFC-IB-269 GET /healthz（永不抛、永不 5xx）
            IFC-IB-270 POST /warmup（幂等；加载失败快速失败而非挂死）
            IFC-IB-271 POST /descriptor（五字段与 EmbedderDescriptor 一致）
            IFC-IB-272 批上限（回显 max_batch）与截断保前缀
            IFC-IB-273 冷/热单一落点：**服务端不区分冷热**（无状态 HTTP）
@depends —
@author sub_agent_software_developer

`ib-embed` 常驻 HTTP 服务（MOD-IB-26）——契约唯一落点见 docs/ib_embed_service_contract.md。

设计取舍（与契约逐条对齐）：

* **只用标准库**（`http.server`）：本服务是**本机内网单用途**进程，无鉴权、无 TLS、
  无反向代理需求；引入 ASGI/WSGI 框架只会把「本服务的依赖面」与「业务基座」耦合，
  而 ADR-02 恰恰要求它**独立、可单测、可替换**。零三方依赖 ⇒ systemd 裸装最省事。
* **服务端不区分冷热**（IFC-IB-273）：本文件**没有**任何 `cold_*` / `hot_*` 分支。
  冷路径「愿意等」体现为**客户端**的长超时 + 多重试，服务端只提供「有界队列」这一件事。
* **有界并发 + 有界队列 + 快速失败**（ADR-02）：排队会把「慢」放大为「全链路超时」，
  故超限一律 `503 overloaded` 并回显 `retry_after_s`，**绝不**无界排队。
* **绝不返回部分向量**（IFC-IB-266 §3.2）：长度不符会让客户端直接判为依赖不可用，
  故「整体成功 / 整体错误」是服务端的硬语义。
* **正文不入日志、不入错误体**：`detail` 一律为**固定短语**，不回显 `texts` 内容。
"""

from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping, Sequence

from .config import ConfigError, EmbedConfig, load_config
from .runtime import (
    InferenceUnavailable,
    RuntimeBatch,
    RuntimePort,
    UnavailableRuntime,
    load_runtime,
)

__all__ = [
    "INFERENCE_BUDGET_S",
    "MAX_BODY_BYTES",
    "QUEUE_WAIT_S",
    "EmbedService",
    "Response",
    "build_http_server",
    "main",
    "serve",
]

logger = logging.getLogger("ib_embed")

# --- 实现常量（**不是配置键**；契约 §9 的键清单是封闭的，不得为服务端补超时/重试键）--- #

#: 单批推理预算（秒）。超过即 `504 inference_timeout`（IFC-IB-268 唯一以 5xx 表示的
#: 「暂时故障」；客户端冷路径计入重试预算、热路径 1 次重试后降级）。
INFERENCE_BUDGET_S: float = 60.0

#: 排队等待上限（秒）。**不是**「服务端冷热超时」——它只保证「排队中的线程会退出」，
#: 使超限可快速失败；真正的冷/热超时仍在客户端（IFC-IB-273）。
QUEUE_WAIT_S: float = 30.0

#: 请求体上限（字节）。批上限已被 `IB_EMBED_MAX_BATCH` 约束，此处仅防「畸形巨额体」
#: 打挂进程（输入校验：边界检查，见安全约束 SC-2）。
MAX_BODY_BYTES: int = 8 * 1024 * 1024

_VALID_MODES = ("document", "query")

#: 统一错误体的固定短语（**不含正文、不含路径**）。
_DETAIL = {
    "invalid_request": "请求体非法",
    "batch_too_large": "单批条数超过服务端上限",
    "model_mismatch": "请求的模型标识与已加载模型不一致",
    "model_not_ready": "模型权重尚未加载完成",
    "overloaded": "服务端并发与队列均已满",
    "inference_timeout": "服务端推理超出预算",
    "internal_error": "服务端内部错误",
    "not_found": "未知路径",
}


@dataclass(frozen=True, slots=True)
class Response:
    """一次请求的终局（HTTP 状态 + 统一错误体 / 业务体）。"""

    status: int
    body: dict[str, Any]
    headers: Mapping[str, str] | None = None


def _error(code: str, status: int, **extra: Any) -> Response:
    body: dict[str, Any] = {"code": code, "detail": _DETAIL.get(code, code)}
    body.update(extra)
    return Response(status=status, body=body)


# --------------------------------------------------------------------------- #
# 服务内核（**不依赖 socket**，故可离线单测）
# --------------------------------------------------------------------------- #


class EmbedService:
    """`/embed`、`/healthz`、`/warmup`、`/descriptor` 的语义内核。

    与 HTTP 层分离的理由：**线协议的一致性必须在无 socket 的情况下可测**
    （C5：离线单测不得联网；且 `port_conformance` 式的对拍需要直接调用语义层）。
    """

    def __init__(self, cfg: EmbedConfig, runtime: RuntimePort) -> None:
        self._cfg = cfg
        self._runtime = runtime
        #: 有界并发：同时进入**推理**的请求数。
        self._slots = threading.BoundedSemaphore(cfg.max_concurrency)
        self._lock = threading.Lock()
        self._admitted = 0
        self._inflight = 0
        self._warm = False
        self._last_elapsed_ms = 0

    # --- 容量与可观测（AC-IB-13-02：降级必须可观测）--- #

    @property
    def capacity(self) -> int:
        """在途 + 排队的**总**准入上限（MAX_CONCURRENCY + QUEUE_DEPTH）。"""
        return self._cfg.max_concurrency + self._cfg.queue_depth

    def queue_depth(self) -> int:
        with self._lock:
            return max(0, self._admitted - self._inflight)

    def inflight(self) -> int:
        with self._lock:
            return self._inflight

    def _admit(self) -> bool:
        with self._lock:
            if self._admitted >= self.capacity:
                return False
            self._admitted += 1
            return True

    def _release_admit(self) -> None:
        with self._lock:
            self._admitted = max(0, self._admitted - 1)

    def _enter(self) -> None:
        with self._lock:
            self._inflight += 1

    def _leave(self) -> None:
        with self._lock:
            self._inflight = max(0, self._inflight - 1)

    def _retry_after_s(self) -> int:
        """由**最近一次真实推理耗时**推回退建议（下限 1s，上限 30s）。"""
        return min(30, max(1, int(round(self._last_elapsed_ms / 1000.0)) or 1))

    # --- GET /healthz（IFC-IB-269）--- #

    def healthz(self) -> Response:
        """**永不抛、永不 5xx** —— 客户端 `health()` 依赖此性质。"""
        try:
            loaded = bool(self._runtime.is_loaded())
        except Exception:  # noqa: BLE001 - 健康检查必须给出结论而非异常
            loaded = False
        with self._lock:
            warm = self._warm
        detail = "就绪" if loaded else self._unavailable_reason()
        body: dict[str, Any] = {
            "ok": loaded,
            "detail": detail,
            "model_id": self._cfg.model_id,
            "dim": self._cfg.dim,
            "model_loaded": loaded,
            "warm": bool(warm and loaded),
            "queue_depth": self.queue_depth(),
            "inflight": self.inflight(),
        }
        if loaded:
            try:
                body["dim"] = int(self._runtime.descriptor().dim)
            except Exception:  # noqa: BLE001 - 自述失败不影响健康结论
                pass
        return Response(status=200, body=body)

    def _unavailable_reason(self) -> str:
        """可读的未就绪原因：**不含路径细节、不含正文**。"""
        runtime = self._runtime
        if isinstance(runtime, UnavailableRuntime) and runtime.reason:
            return runtime.reason
        reason = getattr(runtime, "reason", None)
        if isinstance(reason, str) and reason:
            return reason
        return "模型权重尚未加载完成"

    # --- POST /warmup（IFC-IB-270）--- #

    def warmup(self) -> Response:
        """幂等预热。已加载 → 立即返回（不重复加载）。失败 → **快速失败**（500）而非挂死。"""
        try:
            loaded_ms = int(self._runtime.load())
        except InferenceUnavailable:
            logger.warning("model load unavailable code=internal_error")
            return _error("internal_error", 500)
        except Exception as exc:  # noqa: BLE001
            logger.error("model load failed code=internal_error exc=%s", type(exc).__name__)
            return _error("internal_error", 500)
        with self._lock:
            self._warm = True
        return Response(
            status=200, body={"ok": True, "loaded_ms": loaded_ms, "model_id": self._cfg.model_id}
        )

    # --- POST /descriptor（IFC-IB-271）--- #

    def descriptor(self) -> Response:
        """模型自述；字段名与 MOD-IB-01 `EmbedderDescriptor` **逐字段一致**。

        未加载时回落**配置声明值**（客户端本就有同样的回落语义，二者不冲突）；
        已加载时 `dim` 为**实测权威值**（IFC-IB-267）。
        """
        try:
            desc = self._runtime.descriptor()
            return Response(
                status=200,
                body={
                    "model_id": desc.model_id,
                    "dim": int(desc.dim),
                    "normalized": bool(desc.normalized),
                    "max_tokens": int(desc.max_tokens),
                    "device": str(desc.device),
                },
            )
        except Exception:  # noqa: BLE001 - 未加载/自述不可用 → 回落配置
            return Response(
                status=200,
                body={
                    "model_id": self._cfg.model_id,
                    "dim": self._cfg.dim,
                    "normalized": True,
                    "max_tokens": self._cfg.max_tokens,
                    "device": "cpu",
                },
            )

    # --- POST /embed（IFC-IB-266 / 267 / 272）--- #

    def embed(self, payload: Any) -> Response:
        # 1) 请求体结构（边界 + 类型 + 枚举；**不回显正文**）
        if not isinstance(payload, dict):
            return _error("invalid_request", 400)
        texts = payload.get("texts")
        if not isinstance(texts, list) or not texts:
            return _error("invalid_request", 400)
        if not all(isinstance(item, str) for item in texts):
            return _error("invalid_request", 400)
        mode = payload.get("mode")
        if mode not in _VALID_MODES:
            return _error("invalid_request", 400)
        model = payload.get("model")
        if not isinstance(model, str) or not model:
            return _error("invalid_request", 400)

        # 2) 单模型常驻：跨模型请求一律 409，不做运行时换模型（ADR-02）
        if model != self._cfg.model_id:
            return _error("model_mismatch", 409)

        # 3) 批上限：回显 max_batch 使「客户端 cold_batch > 服务端 MAX_BATCH」一眼可定位（IFC-IB-272）
        if len(texts) > self._cfg.max_batch:
            return _error("batch_too_large", 400, max_batch=self._cfg.max_batch)

        # 4) 未就绪 → 503（冷路径重试有效；热路径不重试直接降级）
        if not self._runtime.is_loaded():
            return _error("model_not_ready", 503)

        # 5) 准入：超限**快速失败**，绝不无界排队
        if not self._admit():
            return self._overloaded()

        acquired = self._slots.acquire(timeout=QUEUE_WAIT_S)
        if not acquired:
            self._release_admit()
            return self._overloaded()

        self._enter()
        holder: dict[str, Any] = {}

        def _work() -> None:
            try:
                started = time.perf_counter()
                batch = self._runtime.embed(
                    list(texts), batch_size=len(texts), max_tokens=self._cfg.max_tokens
                )
                holder["batch"] = batch
                self._last_elapsed_ms = int((time.perf_counter() - started) * 1000)
            except InferenceUnavailable as exc:
                holder["unavailable"] = str(exc)
            except Exception as exc:  # noqa: BLE001 - 未分类异常 → 500（5xx=重试可能有用）
                holder["internal"] = type(exc).__name__
            finally:
                # 槽位与准入信用由**真正完成推理的线程**释放：
                # 若外层已超时返回 504，容量直到真实完成前都保持占用 —— 账目诚实。
                self._leave()
                self._slots.release()
                self._release_admit()

        worker = threading.Thread(target=_work, name="ib-embed-infer", daemon=True)
        worker.start()
        worker.join(INFERENCE_BUDGET_S)
        if worker.is_alive():
            logger.warning("inference exceeded budget code=inference_timeout")
            return _error("inference_timeout", 504)

        if "unavailable" in holder:
            logger.warning("runtime unavailable code=model_not_ready")
            return _error("model_not_ready", 503)
        if "internal" in holder:
            logger.error("runtime failure code=internal_error exc=%s", holder["internal"])
            return _error("internal_error", 500)

        batch = holder.get("batch")
        if not isinstance(batch, RuntimeBatch) or len(batch.vectors) != len(texts):
            # 「绝不返回部分向量」：数量不符只能整批报错
            logger.error("vector count mismatch code=internal_error")
            return _error("internal_error", 500)
        return self._ok(batch, count=len(texts))

    def _ok(self, batch: RuntimeBatch, *, count: int) -> Response:
        vectors = [list(vec) for vec in batch.vectors]
        dim = len(vectors[0]) if vectors else self._cfg.dim
        for vec in vectors:
            if len(vec) != dim:
                # 维度参差 = 权重/后处理缺陷 → 绝不上抛「不可解释的向量」
                logger.error("ragged vector dims code=internal_error")
                return _error("internal_error", 500)
        body: dict[str, Any] = {
            "vectors": vectors,
            "dim": dim,
            "model_id": self._cfg.model_id,
            "normalized": True,
            "count": count,
            "elapsed_ms": int(self._last_elapsed_ms),
        }
        if batch.truncated_indices:
            body["truncated_indices"] = list(batch.truncated_indices)
        with self._lock:
            self._warm = True
        return Response(status=200, body=body)

    def _overloaded(self) -> Response:
        return _error("overloaded", 503, retry_after_s=self._retry_after_s())


# --------------------------------------------------------------------------- #
# HTTP 层（薄：只做路由、体积校验、JSON 解析与序列化）
# --------------------------------------------------------------------------- #


def _handler_factory(service: EmbedService) -> type[BaseHTTPRequestHandler]:
    class _Handler(BaseHTTPRequestHandler):
        server_version = "ib-embed/1.0"
        protocol_version = "HTTP/1.1"

        # --- 日志卫生：**不记录查询串**（禁用 `?token=` 类隐式凭据的泄漏面），不记录正文 --- #
        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
            logger.debug("http %s", fmt % args)

        def log_error(self, fmt: str, *args: Any) -> None:  # noqa: A003
            logger.debug("http_error %s", fmt % args)

        # --- 工具 --- #

        def _send(self, response: Response) -> None:
            raw = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
            self.send_response(response.status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            for key, value in (response.headers or {}).items():
                self.send_header(key, value)
            if response.status == 503 and "retry_after_s" in response.body:
                self.send_header("Retry-After", str(response.body["retry_after_s"]))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(raw)

        def _read_json(self) -> Any:
            try:
                length = int(self.headers.get("Content-Length") or "0")
            except ValueError:
                return _INVALID
            if length <= 0 or length > MAX_BODY_BYTES:
                return _INVALID
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _INVALID

        @property
        def _route(self) -> str:
            # 丢弃查询串（本服务无查询参数；保留它会为日志/凭据面留缝）
            return self.path.split("?", 1)[0].rstrip("/") or "/"

        # --- 路由 --- #

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 约定
            if self._route == "/healthz":
                self._send(service.healthz())
            else:
                self._send(_error("not_found", 404))

        def do_HEAD(self) -> None:  # noqa: N802
            if self._route == "/healthz":
                self._send(service.healthz())
            else:
                self._send(_error("not_found", 404))

        def do_POST(self) -> None:  # noqa: N802
            route = self._route
            if route not in ("/embed", "/warmup", "/descriptor"):
                self._send(_error("not_found", 404))
                return
            if route == "/warmup":
                self._send(service.warmup())
                return
            if route == "/descriptor":
                self._send(service.descriptor())
                return
            payload = self._read_json()
            if payload is _INVALID:
                self._send(_error("invalid_request", 400))
                return
            self._send(service.embed(payload))

    return _Handler


class _Invalid:
    """哨兵：与任何合法 JSON 载荷都不同（`None` 是合法 JSON，故不能用它当哨兵）。"""


_INVALID = _Invalid()


def build_http_server(
    cfg: EmbedConfig, runtime: RuntimePort, *, host: str | None = None, port: int | None = None
) -> ThreadingHTTPServer:
    """构造（未启动的）HTTP 服务器；`port=0` 时由内核分配（离线冒烟测试用）。"""
    service = EmbedService(cfg, runtime)
    httpd = ThreadingHTTPServer((host or cfg.host, cfg.port if port is None else port), _handler_factory(service))
    httpd.daemon_threads = True
    return httpd


def serve(cfg: EmbedConfig, runtime: RuntimePort, *, host: str | None = None, port: int | None = None) -> None:
    httpd = build_http_server(cfg, runtime, host=host, port=port)
    logger.info(
        "ib-embed 启动 host=%s port=%s model_id=%s dim=%s max_concurrency=%s queue_depth=%s",
        host or cfg.host,
        cfg.port if port is None else port,
        cfg.model_id,
        cfg.dim,
        cfg.max_concurrency,
        cfg.queue_depth,
    )
    httpd.serve_forever()


def main(argv: Sequence[str] | None = None) -> int:
    """入口（systemd `ExecStart=... -m ib_embed.server --host … --port …`）。

    启动纪律：
      * 配置非法/缺失 → **非零码退出 + 只报键名**（IFC-IB-263，与 MOD-IB-25 同纪律）；
      * 权重加载成功但**维度**与 `IB_EMBED_DIM` 不符 → 非零码退出（契约 §4.1：不回退）；
      * 权重/库**不可用** → **照常启动**（`/healthz` 报可读原因、`/embed` 503），
        因为「起不来」比「起得来但没就绪」更难诊断（可观测优先）。
    """
    parser = argparse.ArgumentParser(prog="ib-embed", description="MOD-IB-26 bge-m3 常驻推理服务")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        cfg = load_config()
    except ConfigError as exc:
        # 只报键名，不回显值（IFC-IB-263）
        print(f"[ib-embed] 配置错误：{exc}", flush=True)
        return 2

    runtime = load_runtime(cfg)
    try:
        runtime.load()
    except InferenceUnavailable as exc:
        # 不可用也要起得来：/healthz 会持续报出该原因
        logger.warning("模型尚未就绪 code=model_not_ready reason=%s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("模型加载异常 code=internal_error exc=%s", type(exc).__name__)
    else:
        try:
            actual = int(runtime.descriptor().dim)
        except Exception:  # noqa: BLE001
            actual = cfg.dim
        if actual != cfg.dim:
            # 契约 §4.1：服务端 dim 不得由配置覆盖为与权重不符的值 → 启动失败，不回退
            print(
                f"[ib-embed] 维度不一致：IB_EMBED_DIM={cfg.dim} 与权重实测 {actual} 不符（拒启动）",
                flush=True,
            )
            return 3

    serve(cfg, runtime, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":  # pragma: no cover - 进程入口
    raise SystemExit(main())
