#!/usr/bin/env python3
"""Main entry point for the impresso-content-auth tool."""

import argparse
import sys
from typing import NoReturn, Optional


def main() -> int:
    """Run the main application.
    
    Returns:
        An integer exit code.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Impresso Content Authorization Tool"
    )
    parser.add_argument("--server", action="store_true", help="Start the web server")
    
    args: argparse.Namespace = parser.parse_args()
    
    if args.server:
        from impresso_content_auth.server import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Impresso Content Authorization Tool")
        print("Use --server flag to start the web server")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
