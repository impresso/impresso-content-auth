from typing import TypeVar

T = TypeVar("T")


class EqualityMatcher:
    """
    A token matcher strategy that uses equality comparison (==) to match tokens.

    This strategy simply compares two tokens using Python's equality operator.
    Returns True if the tokens are equal, False otherwise.
    """

    def __call__(self, a: T, b: T) -> bool:
        return a == b

    def __str__(self) -> str:
        return "EqualityMatcher()"
