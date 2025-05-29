from typing import Optional, Protocol, TypeVar
from starlette.requests import Request


T_co = TypeVar("T_co", covariant=True)


class TokenExtractorStrategy(Protocol[T_co]):
    """
    Protocol for token extraction strategies.
    This protocol defines a method for extracting tokens from requests.
    """

    async def __call__(self, request: Request) -> Optional[T_co]: ...


class NullExtractorStrategy(TokenExtractorStrategy[None]):
    """
    A null extractor strategy that always returns None.
    This is used when no token extraction is needed.
    """

    async def __call__(self, request: Request) -> None:
        """Always return None regardless of the request."""
        return None

    def __str__(self) -> str:
        """Return a string representation of the null extractor."""
        return "NullExtractorStrategy()"
