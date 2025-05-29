from typing import Protocol, TypeVar

T = TypeVar("T", contravariant=True)


class TokenMatcherStrategy(Protocol[T]):
    """
    Protocol for token matching strategies.
    This protocol defines a method for matching two tokens.

    Returns True if the tokens match, False otherwise.
    """

    def __call__(self, a: T, b: T) -> bool: ...


class NullMatcherStrategy(TokenMatcherStrategy[T]):
    """
    A null matcher strategy that always returns False.
    This is used when no token matching is needed.
    """

    def __call__(self, a: T, b: T) -> bool:
        """Always return False regardless of the tokens."""
        return False

    def __str__(self) -> str:
        """Return a string representation of the null matcher."""
        return "NullMatcherStrategy()"
