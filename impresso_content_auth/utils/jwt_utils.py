import base64
import jwt
import logging
from typing import Dict, Optional, Any, cast

from impresso_content_auth.utils.bitmap import BitMask64

logger = logging.getLogger(__name__)


def validate_jwt(
    token: str,
    secret: str,
    audience: str | None = None,
    algorithms: list[str] | None = None,
    verify_audience: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Validates a JWT token and returns its content as a dictionary.

    Args:
        token: The JWT token string to validate
        secret: The secret key used to sign the JWT
        algorithms: List of allowed algorithms for decoding, defaults to ['HS256']

    Returns:
        Dict containing the JWT payload if valid, None otherwise
    """
    if algorithms is None:
        algorithms = ["HS256"]

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=algorithms,
            audience=audience,
            options={"verify_exp": True, "verify_aud": verify_audience},
        )
        return cast(Dict[str, Any], payload)
    except jwt.ExpiredSignatureError:
        logger.warning("JWT validation failed: token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("JWT validation failed: %s", str(e))
        return None


def get_bitmap(
    token_content: Dict[str, Any], key: str = "bitmap"
) -> Optional[BitMask64]:
    """
    Extracts a bitmap value from the JWT content, decodes it from base64,
    and returns it as a long.

    Args:
        token_content: The decoded JWT payload
        key: The key to look for in the payload

    Returns:
        The bitmap value as a long if found, None otherwise
    """
    if key in token_content and isinstance(token_content[key], str):
        decoded = base64.b64decode(token_content[key])
        return BitMask64(decoded)
    return None
