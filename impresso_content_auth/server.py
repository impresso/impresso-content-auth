#!/usr/bin/env python3
"""Simple server for Impresso Content Authorization service."""

from typing import Dict, List, Any

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request


async def health(request: Request) -> JSONResponse:
    """Health check endpoint.
    
    Args:
        request: The incoming request.
        
    Returns:
        A JSON response with status "ok".
    """
    return JSONResponse({"status": "ok"})


routes: List[Route] = [
    Route("/health", endpoint=health)
]


app: Starlette = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
