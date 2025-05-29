import asyncio
import contextlib
import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from impresso_content_auth.di import Container
from impresso_content_auth.strategy.extractor.base import NullExtractorStrategy
from impresso_content_auth.strategy.matcher.base import NullMatcherStrategy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def health(_request: Request) -> JSONResponse:
    """Health check endpoint.
    Args:
        _request: The incoming request (unused).
    Returns:
        A JSON response with status "ok".
    """
    return JSONResponse({"status": "ok"})


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):  # type: ignore
    """Initialize the application and its components."""

    uvicorn_logger = logging.getLogger("uvicorn")
    for handler in uvicorn_logger.handlers:
        logger.addHandler(handler)

    load_dotenv()
    app.state.container = Container()
    app.state.container.config.from_yaml(Path(__file__).parent / "config.yml")

    for name, extractor_provider in app.state.container.extractors.providers.items():
        extractor = extractor_provider()
        if not isinstance(extractor, NullExtractorStrategy):
            logger.info(
                "Configured extractor: %s: %s",
                name,
                extractor,
            )

    for name, matcher_provider in app.state.container.matchers.providers.items():
        matcher = matcher_provider()
        if not isinstance(matcher, NullMatcherStrategy):
            logger.info(
                "Configured matcher: %s: %s",
                name,
                matcher,
            )

    yield
    # Cleanup logic if needed
    logger.info("Shutting down Impresso Content Auth server...")


async def auth_check(request: Request) -> Response:
    """Authorization check endpoint."""
    container = request.app.state.container

    client_token_extractor_name = request.path_params.get("client_token_extractor")
    resource_token_extractor_name = request.path_params.get("resource_token_extractor")

    # Get the token extractor strategy based on the request
    client_token_extractor = container.extractors.providers.get(
        client_token_extractor_name or ""
    )
    resource_token_extractor = container.extractors.providers.get(
        resource_token_extractor_name or ""
    )
    if not client_token_extractor or not resource_token_extractor:
        if not client_token_extractor:
            logger.warning(
                "No extractor found for client token: %s",
                client_token_extractor_name,
            )
        if not resource_token_extractor:
            logger.warning(
                "No extractor found for resource token: %s",
                resource_token_extractor_name,
            )
        return Response(status_code=HTTP_403_FORBIDDEN)

    client_token_extractor = client_token_extractor()
    resource_token_extractor = resource_token_extractor()

    matcher_name = request.path_params.get("matcher")
    matcher = container.matchers.providers.get(matcher_name or "")
    if not matcher:
        logger.warning("No matcher found for: %s", matcher_name)
        return Response(status_code=HTTP_403_FORBIDDEN)

    matcher = matcher()

    client_token, resource_token = await asyncio.gather(
        client_token_extractor(request),
        resource_token_extractor(request),
    )

    if client_token is None or resource_token is None:
        # If either token is None, we can't proceed with the comparison
        return Response(status_code=HTTP_403_FORBIDDEN)

    return Response(
        status_code=(
            HTTP_200_OK if matcher(client_token, resource_token) else HTTP_403_FORBIDDEN
        )
    )


routes: List[Route] = [
    Route("/health", endpoint=health),
    Route(
        "/{matcher:str}/{client_token_extractor:str}/{resource_token_extractor:str}",
        endpoint=auth_check,
    ),
]

app: Starlette = Starlette(debug=True, routes=routes, lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
