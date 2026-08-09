import logging
from typing import Optional
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: Optional[str] = None):
        self.url = redis_url or settings.REDIS_URL
        self.enabled = settings.CACHE_ENABLED
        self._client: Optional[redis.Redis] = None

    def _get_client(self) -> Optional[redis.Redis]:
        if not self.enabled:
            return None
        if self._client is None:
            try:
                self._client = redis.Redis.from_url(
                    self.url,
                    decode_responses=True,
                    socket_timeout=1.5,
                    socket_connect_timeout=1.5,
                )
            except Exception as e:
                logger.warning("Failed to initialize Redis client: %s. Redis operations will fail open.", e)
                return None
        return self._client

    def get(self, key: str) -> Optional[str]:
        client = self._get_client()
        if not client:
            return None
        try:
            return client.get(key)
        except Exception as e:
            logger.warning("Redis GET failed for key '%s': %s. Failing open to DB.", key, e)
            return None

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            ttl = ttl_seconds if ttl_seconds is not None else settings.DASHBOARD_CACHE_TTL_SECONDS
            client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.warning("Redis SET failed for key '%s': %s. Ignoring cache write error.", key, e)
            return False

    def delete(self, key: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning("Redis DELETE failed for key '%s': %s.", key, e)
            return False

    def is_connected(self) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return bool(client.ping())
        except Exception:
            return False

cache_service = CacheService()
