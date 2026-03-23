from dataclasses import dataclass

from app.core.config import Settings
from app.services.cache_service import CacheService


@dataclass(slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimitService:
    def __init__(self, cache_service: CacheService, settings: Settings) -> None:
        self.cache_service = cache_service
        self.settings = settings

    async def check_login(self, client_ip: str, username: str) -> RateLimitDecision:
        count, ttl = await self.cache_service.get_counter(self._login_key(client_ip, username))
        if count >= self.settings.auth_login_rate_limit_attempts:
            return RateLimitDecision(allowed=False, retry_after_seconds=max(ttl, 1))
        return RateLimitDecision(allowed=True)

    async def record_failed_login(self, client_ip: str, username: str) -> RateLimitDecision:
        count, ttl = await self.cache_service.increment(
            self._login_key(client_ip, username),
            self.settings.auth_login_rate_limit_window_seconds,
        )
        if count >= self.settings.auth_login_rate_limit_attempts:
            return RateLimitDecision(allowed=False, retry_after_seconds=max(ttl, 1))
        return RateLimitDecision(allowed=True)

    async def reset_login(self, client_ip: str, username: str) -> None:
        await self.cache_service.delete(self._login_key(client_ip, username))

    def _login_key(self, client_ip: str, username: str) -> str:
        normalized_user = username.strip().lower() or "anonymous"
        normalized_ip = client_ip.strip() or "unknown"
        return f"auth:login:{normalized_ip}:{normalized_user}"
