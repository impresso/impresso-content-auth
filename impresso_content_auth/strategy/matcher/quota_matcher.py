"""Quota matcher that checks if a user is within their quota for a document."""

import logging
from typing import Optional

from starlette.requests import Request

from impresso_content_auth.service.quota_checker.base import QuotaChecker
from impresso_content_auth.strategy.extractor.base import TokenExtractorStrategy

logger = logging.getLogger(__name__)


class QuotaMatcher:
    """
    A matcher strategy that checks if a user can access a document based on quota.

    This matcher:
    1. Extracts user ID and document ID from the request using configured extractors
    2. Calls the quota checker service to verify if the user is within their quota
    3. Returns True if access is allowed (below quota), False if quota is reached
    """

    def __init__(
        self,
        quota_checker: QuotaChecker,
        user_id_extractor: TokenExtractorStrategy[Optional[str]],
        doc_id_extractor: TokenExtractorStrategy[Optional[str]],
    ):
        """
        Initialize the quota matcher.

        Args:
            quota_checker: The quota checker service implementation
            user_id_extractor: Extractor strategy for extracting user ID from request
            doc_id_extractor: Extractor strategy for extracting document ID from request
        """
        self.quota_checker = quota_checker
        self.user_id_extractor = user_id_extractor
        self.doc_id_extractor = doc_id_extractor

    async def __call__(self, request: Request) -> bool:
        """
        Check if a user is within their quota for a document.

        Extracts user ID and document ID from the request and checks quota status.

        Args:
            request: The incoming HTTP request

        Returns:
            True if the user is below quota (access allowed)
            False if the user has reached their quota (access denied)
        """
        try:
            # Extract user ID and document ID from request
            user_id = await self.user_id_extractor(request)
            doc_id = await self.doc_id_extractor(request)

            # Check if both were extracted
            if not user_id or not doc_id:
                logger.warning(
                    "Failed to extract user ID or document ID from request (user_id=%s, doc_id=%s)",
                    user_id,
                    doc_id,
                )
                # Fail open: allow access if extraction fails
                return True

            result = await self.quota_checker(user_id, doc_id)

            if result == "below_quota":
                logger.debug(
                    "User %s is within quota for document %s", user_id, doc_id
                )
                return True
            else:  # quota_reached
                logger.debug(
                    "User %s has reached quota for document %s", user_id, doc_id
                )
                return False

        except Exception as e:
            logger.error("Error checking quota: %s", str(e))
            # Fail open: allow access if quota check fails
            return True

    def __str__(self) -> str:
        """Return a string representation of the quota matcher."""
        return (
            f"QuotaMatcher(quota_checker={self.quota_checker}, "
            f"user_id_extractor={self.user_id_extractor}, "
            f"doc_id_extractor={self.doc_id_extractor})"
        )
