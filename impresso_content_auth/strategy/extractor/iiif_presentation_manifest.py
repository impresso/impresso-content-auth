"""
Strategy module for extracting tokens from IIIF Presentation API manifests.
"""

import logging
from typing import Callable, Generic, Optional, TypeVar, cast
from urllib.parse import urljoin, urlparse

import httpx
from dacite import from_dict
from starlette.requests import Request

from impresso_content_auth.models.generated.iiifPresentationContext import (
    IiifPresentationApiV3ManifestSchema,
)
from impresso_content_auth.strategy.extractor.base import TokenExtractorStrategy
from impresso_content_auth.utils.bitmap import BitMask64

T = TypeVar("T")
logger = logging.getLogger(__name__)


class IIIFPresentationManifestExtractor(Generic[T], TokenExtractorStrategy[BitMask64]):
    """
    A strategy that extracts tokens from IIIF Presentation API manifests.

    This extractor:
    1. Extracts a file URL from the request
    2. Transforms the URL to locate the manifest file
    3. Downloads and parses the manifest
    4. Extracts bitmap tokens from the manifest's metadata
    """

    def __init__(
        self,
        url_extractor_func: Callable[[Request], Optional[str]],
        metadata_field: str = "explore_bitmaps",
        manifest_path: str = "manifest.json",
        timeout: int = 10,
    ):
        """
        Initialize the IIIF Presentation Manifest extractor.

        Args:
            url_extractor_func: Function to extract file URL from the request
            metadata_field: The metadata field to extract from the manifest
            manifest_path: The path to the manifest file relative to the resource
            timeout: HTTP request timeout in seconds
        """
        self.url_extractor_func = url_extractor_func
        self.metadata_field = metadata_field
        self.manifest_path = manifest_path
        self.timeout = timeout
        # Create a httpx client with timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __call__(self, request: Request) -> Optional[BitMask64]:
        """
        Extract a token from a IIIF Presentation Manifest based on the request.

        Args:
            request: The HTTP request

        Returns:
            The extracted token or None if not found
        """
        # Extract file URL from the request
        file_url = self.url_extractor_func(request)
        if not file_url:
            logger.debug("No file URL extracted from request")
            return None

        # Get manifest URL by replacing the file path with manifest path
        manifest_url = self._get_manifest_url(file_url)
        logger.debug("Fetching manifest from: %s", manifest_url)

        try:
            # Download and parse the manifest
            manifest = await self._fetch_manifest(manifest_url)
            if not manifest:
                logger.debug("No manifest found at '%s'", manifest_url)
                return None

            # Extract bitmap from manifest metadata
            bitmap = self._extract_bitmap_from_manifest(manifest)
            if bitmap:
                logger.debug("Extracted bitmap: %s", bitmap)
                return BitMask64(bitmap)
            else:
                logger.debug("No bitmap found in manifest metadata")
                return None

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error("Network error while fetching manifest: %s", str(e))
            raise
        except ValueError as e:
            logger.error("Error processing manifest: %s", str(e))
            raise

    def _get_manifest_url(self, file_url: str) -> str:
        """
        Transform a file URL into a manifest URL.

        Args:
            file_url: The URL of the resource file

        Returns:
            The URL of the manifest file
        """
        parsed_url = urlparse(file_url)
        path_parts = parsed_url.path.rsplit("/", 1)

        if len(path_parts) > 1:
            # Replace the file name with manifest path
            base_path = path_parts[0]
            manifest_url = urljoin(
                f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}/",
                self.manifest_path,
            )
        else:
            # If there's no path separator, just append manifest path
            manifest_url = urljoin(file_url, self.manifest_path)

        return manifest_url

    async def _fetch_manifest(
        self, url: str
    ) -> Optional[IiifPresentationApiV3ManifestSchema]:
        """
        Fetch and parse a IIIF Presentation manifest from a URL using httpx.

        Args:
            url: The URL of the manifest file

        Returns:
            The parsed manifest as a dictionary, or None if not found
        """
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                logger.debug(
                    "Failed to fetch manifest: %s (status %d)",
                    url,
                    response.status_code,
                )
                return None

            return cast(
                IiifPresentationApiV3ManifestSchema,
                from_dict(
                    data_class=IiifPresentationApiV3ManifestSchema, data=response.json()
                ),
            )
        except httpx.RequestError as e:
            logger.error("Error fetching manifest (%s): %s", url, str(e))
            raise

    def _extract_bitmap_from_manifest(
        self, manifest: IiifPresentationApiV3ManifestSchema
    ) -> Optional[str]:
        """
        Extract the bitmap value from a manifest's metadata.

        Args:
            manifest: The parsed manifest dictionary

        Returns:
            The bitmap value as a string, or None if not found
        """
        try:
            # Navigate through manifest structure to find items
            if not manifest.items:
                return None

            # Look for metadata in the first canvas
            canvas = manifest.items[0]
            if not canvas.metadata:
                return None

            # Find metadata item matching the target field
            for item in canvas.metadata:
                if not item.label:
                    continue

                # Check if the label matches our target field in any language
                for lang_values in item.label.values():
                    if not isinstance(lang_values, list):
                        continue

                    if self.metadata_field in lang_values:
                        # Get the value from the first language we find
                        for lang_bitmap_values in item.value.values():
                            if (
                                isinstance(lang_bitmap_values, list)
                                and lang_bitmap_values
                            ):
                                return cast(str, lang_bitmap_values[0])

            return None

        except (KeyError, IndexError) as e:
            logger.error("Error extracting bitmap from manifest: %s", str(e))
            return None

    async def close(self) -> None:
        """Close the httpx client explicitly."""
        await self.client.aclose()

    def __str__(self) -> str:
        """Return a string representation of the extractor."""
        return (
            "IIIFPresentationManifestExtractor("
            f"metadata_field={self.metadata_field}, "
            f"manifest_path={self.manifest_path}, "
            f"timeout={self.timeout})"
        )


def extract_url_from_x_original_uri(request: Request) -> Optional[str]:
    """
    Extract full URL from the `X-Original-URI` header of the request.

    Args:
        request: The HTTP request

    Returns:
        The extracted URL or None if not found
    """
    path = request.headers.get("x-original-uri", "")
    if not path:
        logger.debug("No 'x-original-uri' header found in request")
        return None

    # Extract the host from headers
    host = request.headers.get("x-forwarded-host", "")
    if not host:
        logger.debug("No 'host' header found in request")
        return None

    # Determine scheme (http or https)
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"

    # Construct full URL
    full_url = f"{scheme}://{host}{path}"
    logger.debug("Extracted full URL: %s", full_url)

    return full_url
