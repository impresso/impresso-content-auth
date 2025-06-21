from typing import TypeVar
import logging

from impresso_content_auth.strategy.matcher.base import TokenMatcherStrategy
from impresso_content_auth.utils.bitmap import BitMask64, is_access_allowed

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BitWiseAndMatcherStrategy(TokenMatcherStrategy[BitMask64]):
    """
    A matcher strategy that performs a bitwise AND operation.

    This strategy converts two integers to bitmaps and returns True
    if their bitwise AND operation results in a non-zero value.
    """

    def __call__(self, a: BitMask64, b: BitMask64) -> bool:
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
            access_is_allowed = is_access_allowed(a, b)
            if access_is_allowed:
                logger.debug(
                    "BitWiseAnd match succeeded: %s & %s = %s", a, b, access_is_allowed
                )
            else:
                logger.debug(
                    "BitWiseAnd match failed: %s & %s = %s", a, b, access_is_allowed
                )
            return access_is_allowed
        except (TypeError, ValueError) as e:
            logger.warning("BitWiseAnd match failed: %s", str(e))
            return False

    def __str__(self) -> str:
        """Return a string representation of the bitwise AND matcher."""
        return "BitWiseAndMatcherStrategy()"
