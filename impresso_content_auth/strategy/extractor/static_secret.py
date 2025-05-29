from starlette.requests import Request

from impresso_content_auth.strategy.extractor.base import (
    TokenExtractorStrategy,
)


class StaticSecretExtractor(TokenExtractorStrategy[str]):
    """
    Extract a predefined static secret.

    This extractor always returns the same secret value that was provided
    during initialization, regardless of the request details.
    """

    def __init__(self, secret: str):
        """Initialize the static secret extractor with a predefined secret.

        Args:
            secret: The static secret to return for all requests.
        """
        self.secret = secret

    async def __call__(self, request: Request) -> str:
        """Return the static secret value.

        Args:
            request: The incoming HTTP request (not used).

        Returns:
            The static secret value provided during initialization.
        """
        return self.secret

    def __str__(self) -> str:
        """Return a string representation of the extractor."""
        return f"StaticSecretExtractor(secret={self.secret})"
