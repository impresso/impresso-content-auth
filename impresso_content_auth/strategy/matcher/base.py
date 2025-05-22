from typing import Protocol, TypeVar

T = TypeVar("T", contravariant=True)


class TokenMatcherStrategy(Protocol[T]):
    """
    Protocol for token matching strategies.
    This protocol defines a method for matching two tokens.

    Returns True if the tokens match, False otherwise.
    """

    def __call__(self, a: T, b: T) -> bool: ...
