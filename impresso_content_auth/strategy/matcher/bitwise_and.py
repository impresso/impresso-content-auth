from typing import TypeVar
import logging

from impresso_content_auth.strategy.matcher.base import TokenMatcherStrategy

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BitWiseAndMatcherStrategy(TokenMatcherStrategy[int]):
    """
    A matcher strategy that performs a bitwise AND operation.

    This strategy converts two integers to bitmaps and returns True
    if their bitwise AND operation results in a non-zero value.
    """

    def __call__(self, a: int, b: int) -> bool:
        """
        Perform a bitwise AND operation on two integers.

        Args:
            a: First integer
            b: Second integer

        Returns:
            True if the bitwise AND operation results in a value
            greater than or equal to the threshold (or any non-zero
            value if threshold is None), False otherwise.
        """
        try:
            result = a & b
            return result > 0
        except (TypeError, ValueError) as e:
            logger.warning("BitWiseAnd match failed: %s", str(e))
            return False

    def __str__(self) -> str:
        """Return a string representation of the bitwise AND matcher."""
        return "BitWiseAndMatcherStrategy()"
