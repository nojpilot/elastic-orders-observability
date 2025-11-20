#!/usr/bin/env python3
"""Simple alert hook querying Elasticsearch for error spikes."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import requests

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX = os.getenv("INDEX_PATTERN", "orders-*")
LEVEL = os.getenv("ALERT_LEVEL", "ERROR")
WINDOW_MINUTES = int(os.getenv("WINDOW_MINUTES", "5"))
THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "5"))
WEBHOOK = os.getenv("ALERT_WEBHOOK")


def build_search_body() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "query": {
            "bool": {
                "filter": [
                    {"query_string": {"default_field": "event.level", "query": LEVEL}},
                    {
                        "range": {
                            "@timestamp": {
                                "gte": (now - timedelta(minutes=WINDOW_MINUTES)).isoformat(),
                                "lte": now.isoformat(),
                            }
                        }
                    },
                ]
            }
        }
    }


def main() -> None:
    url = f"{ES_URL}/{INDEX}/_count"
    response = requests.get(url, json=build_search_body(), timeout=10)
    response.raise_for_status()
    count = response.json().get("count", 0)

    message = f"{count} {LEVEL} events in last {WINDOW_MINUTES}m"

    if count >= THRESHOLD and WEBHOOK:
        payload = {"text": f"[orders-api] {message} exceeds threshold ({THRESHOLD})"}
        requests.post(WEBHOOK, json=payload, timeout=10).raise_for_status()
        print(f"Alert posted: {message}")
    else:
        print(message)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"alert script failed: {exc}", file=sys.stderr)
        sys.exit(1)
