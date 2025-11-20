"""Redis-based quota checker service using Bloom filter."""

import logging
from pathlib import Path
from time import time
from typing import Literal

import redis.asyncio as redis

from impresso_content_auth.service.quota_checker.base import QuotaChecker

logger = logging.getLogger(__name__)


class RedisQuotaChecker(QuotaChecker):
    """
    Quota checker service using Redis Bloom filter and counters.

    Tracks unique document accesses per user within a rolling time window.
    Uses a probabilistic bloom filter for memory-efficient "seen document" checking.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        quota_limit: int = 200000,
        window_seconds: int = 2592000,  # 30 days
    ):
        """
        Initialize the quota checker.

        Args:
            redis_client: Async Redis client instance
            quota_limit: Maximum unique documents per user per time window
            window_seconds: Time window duration in seconds (default: 30 days)
        """
        self.redis_client: redis.Redis = redis_client
        self.quota_limit = quota_limit
        self.window_seconds = window_seconds
        self._lua_script: str | None = None

    def _load_lua_script(self) -> str:
        """Load the Lua script for quota checking."""
        if self._lua_script is not None:
            return self._lua_script

        script_path = Path(__file__).parent / "resources" / "quotaCheck.lua"
        with open(script_path, "r") as f:
            self._lua_script = f.read()

        return self._lua_script

    async def __call__(
        self, user_id: str, doc_id: str
    ) -> Literal["below_quota", "quota_reached"]:
        """
        Check if user can access a document within their quota.

        Args:
            user_id: Unique user identifier
            doc_id: Unique document identifier

        Returns:
            "below_quota" if access is allowed
            "quota_reached" if quota limit has been hit for new documents
        """
        # Prepare Redis keys
        bloom_key = f"user:{user_id}:bloom"
        count_key = f"user:{user_id}:count"
        first_access_key = f"user:{user_id}:first_access"

        # Load the Lua script
        script_content = self._load_lua_script()

        try:
            # Execute Lua script
            # Keys: bloom_key, count_key, first_access_key
            # Args: doc_id, quota_limit, current_timestamp, window_seconds
            current_timestamp = int(time())
            keys = [bloom_key, count_key, first_access_key]
            args = [doc_id, str(self.quota_limit), str(current_timestamp), str(self.window_seconds)]

            result: list = await self.redis_client.eval(script_content, len(keys), *keys, *args)  # type: ignore

            # result[0] is allowed flag: 1 = allowed, 0 = denied
            allowed = int(result[0]) == 1

            if allowed:
                return "below_quota"
            else:
                return "quota_reached"

        except redis.ResponseError as e:
            # Handle Redis errors (e.g., Bloom filter module not installed)
            logger.error(
                "Redis quota check failed for user %s, doc %s: %s",
                user_id,
                doc_id,
                str(e),
            )
            # Fail open: allow access if Redis fails
            return "below_quota"
