from typing import Protocol, TypeVar
from starlette.requests import Request


T_co = TypeVar("T_co", covariant=True)


class TokenExtractorStrategy(Protocol[T_co]):
    """
    Protocol for token extraction strategies.
    This protocol defines a method for extracting tokens from requests.
    """

    def __call__(self, request: Request) -> T_co: ...
