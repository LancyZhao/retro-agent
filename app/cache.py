"""Caching with a Redis backend and a transparent in-memory fallback.

Ops reality: if Redis is down or the `redis` package isn't installed, the app
should degrade, not crash. `backend` reports which path is active (handy for
/health and troubleshooting).
"""
from __future__ import annotations

import json
import time
from typing import Any


class Cache:
    def __init__(self, redis_url: str = "") -> None:
        self._mem: dict[str, tuple[float, str]] = {}
        self._redis = None
        self.backend = "memory"
        if redis_url:
            try:
                import redis  # type: ignore

                client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5)
                client.ping()
                self._redis = client
                self.backend = "redis"
            except Exception:  # noqa: BLE001  (any failure -> in-memory)
                self._redis = None
                self.backend = "memory"

    def get(self, key: str) -> Any | None:
        if self._redis is not None:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None
        hit = self._mem.get(key)
        if not hit:
            return None
        expires_at, raw = hit
        if expires_at and expires_at < time.monotonic():
            self._mem.pop(key, None)
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        raw = json.dumps(value, ensure_ascii=False)
        if self._redis is not None:
            self._redis.set(key, raw, ex=ttl)
            return
        self._mem[key] = (time.monotonic() + ttl if ttl else 0.0, raw)
