import logging
from typing import Optional

from starlette.requests import Request

from impresso_content_auth.strategy.extractor.base import TokenExtractorStrategy
from impresso_content_auth.utils.jwt_utils import validate_jwt, get_bitmap

logger = logging.getLogger(__name__)


class CookieBitmapExtractor(TokenExtractorStrategy[Optional[int]]):
    """
    A strategy to extract a bitmap from a JWT token stored in a cookie.

    This extractor:
    1. Retrieves the cookie value from the request
    2. Validates the JWT token
    3. Extracts and returns the bitmap from the validated token
    """

    def __init__(
        self,
        cookie_name: str,
        jwt_secret: str,
        jwt_algorithms: Optional[list[str]] = None,
        bitmap_key: str = "bitmap",
    ):
        """
        Initialize the cookie bitmap extractor.

        Args:
            cookie_name: The name of the cookie containing the JWT token
            jwt_secret: The secret key used to validate the JWT token
            jwt_algorithms: List of allowed algorithms for decoding, defaults to ['HS256']
            bitmap_key: The key in the JWT payload that contains the bitmap
        """
        self.cookie_name = cookie_name
        self.jwt_secret = jwt_secret
        self.jwt_algorithms = jwt_algorithms
        self.bitmap_key = bitmap_key

    async def __call__(self, request: Request) -> Optional[int]:
        """
        Extract bitmap from JWT token in cookie.

        Args:
            request: The incoming HTTP request

        Returns:
            The extracted bitmap as an integer if successful, None otherwise
        """
        # Get the cookie from the request
        cookie_value = request.cookies.get(self.cookie_name)
        if not cookie_value:
            logger.warning("Cookie '%s' not found in request", self.cookie_name)
            return None

        # Get audience from the request
        fwd_host = request.headers.get("x-forwarded-host")
        fwd_proto = request.headers.get("x-forwarded-proto")
        fwd_port = request.headers.get("x-forwarded-port")

        if fwd_host and fwd_proto:
            port_part = (
                f":{fwd_port}" if fwd_port and fwd_port not in ["80", "443"] else ""
            )
            audience = f"{fwd_proto}://{fwd_host}{port_part}"
        else:
            audience = None

        # Validate the JWT token
        token_content = validate_jwt(
            token=cookie_value,
            secret=self.jwt_secret,
            audience=audience,
            algorithms=self.jwt_algorithms,
        )
        if not token_content:
            logger.warning(
                "Failed to validate JWT token from cookie '%s'", self.cookie_name
            )
            return None

        # Extract the bitmap from the token content
        bitmap = get_bitmap(token_content, key=self.bitmap_key)
        if bitmap is None:
            logger.warning(
                "Bitmap with key '%s' not found in validated token", self.bitmap_key
            )
            return None

        logger.debug("Successfully extracted bitmap from cookie '%s'", self.cookie_name)
        return bitmap

    def __str__(self) -> str:
        """Return a string representation of the cookie bitmap extractor."""
        return f"CookieBitmapExtractor(cookie_name='{self.cookie_name}')"
