from typing import Optional

from starlette.requests import Request

from impresso_content_auth.strategy.extractor.base import (
    TokenExtractorStrategy,
)


class BearerTokenExtractor(TokenExtractorStrategy[Optional[str]]):
    """
    Extract bearer tokens from the Authorization header.

    This extractor looks for the standard Authorization header with the
    'Bearer' prefix and returns the token part. If no valid bearer token
    is found, returns None.
    """

    def __call__(self, request: Request) -> Optional[str]:
        """Extract bearer token from the request's Authorization header.

        Args:
            request: The incoming HTTP request.

        Returns:
            The bearer token as a string, or None if no valid bearer token
            is found.
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]
