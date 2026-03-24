import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from backend.core.config import (
    AUTH_RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)


class InMemoryRateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)

    def check(self, request: Request):
        client = request.client.host if request.client else "unknown"
        path = request.url.path
        bucket = f"{client}:{'auth' if '/auth/' in path else 'general'}"
        max_requests = AUTH_RATE_LIMIT_MAX_REQUESTS if "/auth/" in path else RATE_LIMIT_MAX_REQUESTS
        now = time.time()
        queue = self.requests[bucket]

        while queue and now - queue[0] > RATE_LIMIT_WINDOW_SECONDS:
            queue.popleft()

        if len(queue) >= max_requests:
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes, intenta más tarde")

        queue.append(now)


rate_limiter = InMemoryRateLimiter()
