from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Any, Dict

from flask import Flask, Response, jsonify, request

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "orders-api",
            "trace_id": record.__dict__.get("trace_id"),
        }
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload)


handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

app = Flask(__name__)


def _log(level: str, message: str, **fields: Any) -> None:
    extra = {"trace_id": fields.pop("trace_id", os.urandom(4).hex()), "extra_fields": fields}
    getattr(logger, level)(message, extra=extra)


@app.before_request
def before_request() -> None:  # pragma: no cover - flask hook
    request._start_time = time.time()  # type: ignore[attr-defined]


@app.after_request
def after_request(response: Response) -> Response:  # pragma: no cover - flask hook
    duration = time.time() - getattr(request, "_start_time", time.time())  # type: ignore[attr-defined]
    _log(
        "info",
        "request completed",
        path=request.path,
        status=response.status_code,
        duration_ms=int(duration * 1000),
    )
    return response


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/orders")
def create_order():
    payload = request.get_json(force=True) or {}
    customer = payload.get("customer")
    total = float(payload.get("total", 0))

    if not customer:
        _log("error", "missing customer")
        return jsonify({"error": "customer is required"}), 400

    if total <= 0:
        _log("error", "invalid order total", total=total)
        return jsonify({"error": "total must be > 0"}), 400

    if random.random() < 0.15:
        _log("warning", "inventory downstream latency", latency_ms=random.randint(500, 800))

    order_id = random.randint(1000, 9999)
    _log("info", "order accepted", customer=customer, total=total, order_id=order_id)
    return jsonify({"status": "accepted", "id": order_id})


@app.get("/chaos")
def chaos():
    _log("error", "forced chaos", component="chaos")
    return jsonify({"error": "boom"}), 500
