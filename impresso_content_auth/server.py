import os
from typing import List

from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from impresso_content_auth.strategy.extractor.bearer_token import BearerTokenExtractor
from impresso_content_auth.strategy.extractor.manifest_with_secret import (
    ManifestWithSecretExtractor,
)
from impresso_content_auth.strategy.matcher.equality import EqualityMatcher


async def health(_request: Request) -> JSONResponse:
    """Health check endpoint.
    Args:
        _request: The incoming request (unused).
    Returns:
        A JSON response with status "ok".
    """
    return JSONResponse({"status": "ok"})


TOKEN_EXTRACTORS = {
    "bearer-token": BearerTokenExtractor(),
    "manifest-with-secret": ManifestWithSecretExtractor(
        base_path=os.environ.get("STATIC_FILES_PATH", "/app/static_files")
    ),
}

MATCHERS = {
    "equality": EqualityMatcher(),
}


async def auth_check(request: Request) -> Response:
    """Authorization check endpoint."""

    client_token_extractor_name = request.path_params.get("client_token_extractor")
    resource_token_extractor_name = request.path_params.get("resource_token_extractor")

    # Get the token extractor strategy based on the request
    client_token_extractor = TOKEN_EXTRACTORS.get(client_token_extractor_name or "")
    resource_token_extractor = TOKEN_EXTRACTORS.get(resource_token_extractor_name or "")
    if not client_token_extractor or not resource_token_extractor:
        return Response(status_code=HTTP_403_FORBIDDEN)

    matcher_name = request.path_params.get("matcher")
    matcher = MATCHERS.get(matcher_name or "")
    if not matcher:
        return Response(status_code=HTTP_403_FORBIDDEN)

    client_token = client_token_extractor(request)
    resource_token = resource_token_extractor(request)
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

app: Starlette = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
