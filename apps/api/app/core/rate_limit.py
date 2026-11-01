"""A minimal in-process rate limiter for sensitive endpoints (spec section 18).

This is a simple fixed-window counter per key, held in process memory. It is
NOT distributed-safe — running multiple API replicas would give each its own
counter. That's an explicitly documented limitation for this stage of the
project (see CLAUDE.md); a production deployment with multiple replicas
would move this to Redis. For a single-process demo/local deployment it does
its job: it meaningfully slows down abuse of the booking-creation endpoint.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, status

_buckets: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> None:
    now = time.monotonic()
    window_start = now - window_seconds
    bucket = _buckets[key]
    while bucket and bucket[0] < window_start:
        bucket.pop(0)
    if len(bucket) >= max_requests:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests. Please slow down and try again shortly."
        )
    bucket.append(now)
