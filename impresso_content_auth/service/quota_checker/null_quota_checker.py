"""Null quota checker that always allows access."""

from typing import Literal

from impresso_content_auth.service.quota_checker.base import QuotaChecker


class NullQuotaChecker(QuotaChecker):
    """
    Null quota checker implementation that always allows access.

    Used when quota checking is disabled or not configured.
    """

    async def __call__(
        self, user_id: str, doc_id: str
    ) -> Literal["below_quota", "quota_reached"]:
        """
        Always allow access without any quota checks.

        Args:
            user_id: Unique user identifier (ignored)
            doc_id: Unique document identifier (ignored)

        Returns:
            Always returns "below_quota"
        """
        return "below_quota"
