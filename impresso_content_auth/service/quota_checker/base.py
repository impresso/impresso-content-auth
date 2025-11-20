"""Base class for quota checker implementations."""

from abc import ABC, abstractmethod
from typing import Literal


class QuotaChecker(ABC):
    """
    Abstract base class for quota checker implementations.

    Quota checkers track unique document accesses per user within a rolling time window.
    """

    @abstractmethod
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
        pass
