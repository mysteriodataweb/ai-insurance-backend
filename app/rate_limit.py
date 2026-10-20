import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    """In-memory sliding-window limiter. Per process: fine for a single instance, not for a fleet."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self.hits[key]
        while bucket and bucket[0] <= now - self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        if len(self.hits) > 10_000:
            self._prune(now)
        return True

    def _prune(self, now: float) -> None:
        for key in [k for k, b in self.hits.items() if not b or b[-1] <= now - self.window]:
            del self.hits[key]

    def reset(self) -> None:
        self.hits.clear()


def client_key(request: Request) -> str:
    # Authenticated callers are limited per token; anonymous callers per client IP.
    auth = request.headers.get("authorization")
    if auth:
        return f"auth:{auth}"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


limiters: list[RateLimiter] = []


def rate_limit(limit: int, window_seconds: int):
    limiter = RateLimiter(limit, window_seconds)
    limiters.append(limiter)

    async def dependency(request: Request) -> None:
        if not limiter.allow(client_key(request)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please try again later.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
