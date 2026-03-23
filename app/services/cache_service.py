import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover - optional dependency
    Redis = None  # type: ignore[assignment]


class CacheService:
    _memory_store: dict[str, tuple[float, str]] = {}
    _memory_lock = asyncio.Lock()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        self._redis: Redis | None = None

    async def get_json(self, key: str) -> Any | None:
        payload = await self._get_raw(key)
        if payload is None:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            await self.delete(key)
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        payload = json.dumps(value, separators=(",", ":"), default=str)
        await self._set_raw(key, payload, ttl_seconds)

    async def get_or_set_json(
        self,
        key: str,
        ttl_seconds: int,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        cached = await self.get_json(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set_json(key, value, ttl_seconds)
        return value

    async def increment(self, key: str, ttl_seconds: int) -> tuple[int, int]:
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                count = await redis_client.incr(key)
                if count == 1:
                    await redis_client.expire(key, ttl_seconds)
                ttl = await redis_client.ttl(key)
                return int(count), max(int(ttl or ttl_seconds), 0)
            except Exception as exc:
                self.logger.warning("Redis increment failed: %s", exc)

        async with self._memory_lock:
            expires_at, raw = self._memory_store.get(key, (0.0, "0"))
            now = time.monotonic()
            if expires_at <= now:
                count = 1
                expires_at = now + ttl_seconds
            else:
                count = int(raw) + 1
            self._memory_store[key] = (expires_at, str(count))
            return count, max(int(expires_at - now), 0)

    async def get_counter(self, key: str) -> tuple[int, int]:
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                current = await redis_client.get(key)
                if current is None:
                    return 0, 0
                ttl = await redis_client.ttl(key)
                return int(current), max(int(ttl or 0), 0)
            except Exception as exc:
                self.logger.warning("Redis counter lookup failed: %s", exc)

        async with self._memory_lock:
            expires_at, raw = self._memory_store.get(key, (0.0, "0"))
            now = time.monotonic()
            if expires_at <= now:
                self._memory_store.pop(key, None)
                return 0, 0
            return int(raw), max(int(expires_at - now), 0)

    async def delete(self, key: str) -> None:
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                await redis_client.delete(key)
                return
            except Exception as exc:
                self.logger.warning("Redis delete failed: %s", exc)

        async with self._memory_lock:
            self._memory_store.pop(key, None)

    async def _get_raw(self, key: str) -> str | None:
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                payload = await redis_client.get(key)
                return payload.decode("utf-8") if isinstance(payload, bytes) else payload
            except Exception as exc:
                self.logger.warning("Redis cache get failed: %s", exc)

        async with self._memory_lock:
            expires_at, payload = self._memory_store.get(key, (0.0, ""))
            if expires_at <= time.monotonic():
                self._memory_store.pop(key, None)
                return None
            return payload

    async def _set_raw(self, key: str, payload: str, ttl_seconds: int) -> None:
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                await redis_client.set(key, payload, ex=ttl_seconds)
                return
            except Exception as exc:
                self.logger.warning("Redis cache set failed: %s", exc)

        async with self._memory_lock:
            self._memory_store[key] = (time.monotonic() + ttl_seconds, payload)

    def _get_redis_client(self) -> Redis | None:
        if Redis is None or not self.settings.redis_url:
            return None
        if self._redis is None:
            self._redis = Redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=False,
            )
        return self._redis
