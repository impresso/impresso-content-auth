import json
import os
from pathlib import Path
from typing import Optional

from starlette.requests import Request

from impresso_content_auth.strategy.extractor.base import (
    TokenExtractorStrategy,
)


class ManifestWithSecretExtractor(TokenExtractorStrategy[Optional[str]]):
    """
    Extract secrets from file manifests.

    This extractor looks for the manifest file corresponding to the requested
    resource, reads the manifest, and extracts the 'secret' value from it.

    The manifest file follows this pattern:
    - original file: /xxx/file.txt
    - manifest file: /xxx/file_manifest.json
    """

    def __init__(self, base_path: str = "/app/static_files"):
        """Initialize the manifest extractor with a base path.

        Args:
            base_path: Base directory path where files and manifests are stored.
        """
        self.base_path = base_path

    def __call__(self, request: Request) -> Optional[str]:
        """Extract the secret from the manifest file for the requested resource.

        Args:
            request: The incoming HTTP request.

        Returns:
            The secret value from the manifest as a string, or None if no valid
            manifest is found or it doesn't contain a secret.
        """
        # Get the original URI that was requested
        original_uri = request.headers.get("x-original-uri", "")

        if not original_uri:
            return None

        # Convert the URI to a file path
        file_path = self._uri_to_path(original_uri)
        if not file_path:
            return None

        # Determine the manifest path
        manifest_path = self._get_manifest_path(file_path)
        if not os.path.exists(manifest_path):
            return None

        # Read the manifest and extract the secret
        return self._extract_secret_from_manifest(manifest_path)

    def _uri_to_path(self, uri: str) -> Optional[str]:
        """Convert a URI to a file path.

        Args:
            uri: The URI to convert.

        Returns:
            The absolute file path or None if invalid.
        """
        # Remove any query parameters or fragments
        uri_path = uri.split("?")[0].split("#")[0]

        # Remove leading slash to make it relative to base_path
        if uri_path.startswith("/"):
            uri_path = uri_path[1:]

        return os.path.join(self.base_path, uri_path)

    def _get_manifest_path(self, file_path: str) -> str:
        """Get the manifest path for a given file path.

        Args:
            file_path: The original file path.

        Returns:
            The path to the corresponding manifest file.
        """
        # Extract path without extension
        path_obj = Path(file_path)
        file_name = path_obj.stem
        directory = path_obj.parent

        # Create manifest file path
        manifest_file = f"{file_name}_manifest.json"
        return os.path.join(directory, manifest_file)

    def _extract_secret_from_manifest(self, manifest_path: str) -> Optional[str]:
        """Extract the secret from a manifest file.

        Args:
            manifest_path: Path to the manifest file.

        Returns:
            The secret as a string, or None if not found.
        """
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            secret = manifest.get("secret")
            return str(secret) if secret is not None else None
        except (IOError, json.JSONDecodeError):
            return None
