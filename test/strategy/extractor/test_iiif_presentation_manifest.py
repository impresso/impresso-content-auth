"""
Tests for the IIIF Presentation Manifest extractor.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, cast
from unittest.mock import MagicMock

import pytest
from dacite import from_dict
from httpx import AsyncClient, Response
from starlette.datastructures import Headers
from starlette.requests import Request

from impresso_content_auth.models.generated.iiifPresentationContext import (
    IiifPresentationApiV3ManifestSchema,
)
from impresso_content_auth.strategy.extractor.iiif_presentation_manifest import (
    IIIFPresentationManifestExtractor,
    extract_url_from_x_original_uri,
)
from impresso_content_auth.utils.bitmap import BitMask64

# Path to the test resources directory
RESOURCES_PATH = Path("test/resources")


def load_manifest(filename: str) -> Dict[str, Any]:
    """Load a JSON manifest from the resources directory."""
    with open(RESOURCES_PATH / filename, "r", encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))


def url_extractor_func(request: Request) -> Optional[str]:
    """A mock URL extractor function for testing."""
    return extract_url_from_x_original_uri(request)


@pytest.fixture
def manifest_data_fixture() -> IiifPresentationApiV3ManifestSchema:
    """Fixture to load the example manifest data."""
    json_data = load_manifest("iiif_manifest.json")
    return from_dict(data_class=IiifPresentationApiV3ManifestSchema, data=json_data)


@pytest.fixture
def manifest_dict_fixture() -> Dict[str, Any]:
    """Fixture to load the example manifest data as a dictionary."""
    return load_manifest("iiif_manifest.json")


async def test_extract_bitmap_from_manifest_success(
    manifest_dict_fixture: Dict[str, Any],
) -> None:
    """Test successful extraction of bitmap from a manifest."""
    # Arrange
    request = Request(
        {
            "type": "http",
            "headers": Headers(
                {
                    "host": "example.com",
                    "x-original-uri": "/foo/bar.mp3",
                }
            ).raw,
        }
    )

    # Mock the HTTP client
    mock_client = MagicMock(spec=AsyncClient)
    mock_client.get.return_value = Response(200, json=manifest_dict_fixture)

    extractor: IIIFPresentationManifestExtractor[BitMask64] = (
        IIIFPresentationManifestExtractor(
            url_extractor_func=url_extractor_func,
        )
    )
    extractor.client = mock_client

    # Act
    result = await extractor(request)

    # Assert
    assert isinstance(result, BitMask64)
    assert (
        str(result)
        == "0001000000000000100000000000000000000000000000000000000000000000"
    )
    mock_client.get.assert_called_once_with("http://example.com/foo/manifest.json")


async def test_manifest_not_found() -> None:
    """Test the case where the manifest is not found (404)."""
    # Arrange
    request = Request(
        {
            "type": "http",
            "headers": Headers(
                {"host": "example.com", "x-original-uri": "/foo/bar.mp3"}
            ).raw,
        }
    )

    # Mock the HTTP client to return a 404
    mock_client = MagicMock(spec=AsyncClient)
    mock_client.get.return_value = Response(404)

    extractor: IIIFPresentationManifestExtractor[BitMask64] = (
        IIIFPresentationManifestExtractor(
            url_extractor_func=url_extractor_func,
        )
    )
    extractor.client = mock_client

    # Act
    result = await extractor(request)

    # Assert
    assert result is None


async def test_no_bitmap_in_manifest(manifest_dict_fixture: Dict[str, Any]) -> None:
    """Test the case where the manifest is valid but contains no bitmap."""
    # Arrange
    request = Request(
        {
            "type": "http",
            "headers": Headers(
                {"host": "example.com", "x-original-uri": "/foo/bar.mp3"}
            ).raw,
        }
    )

    # Create a manifest without the 'explore_bitmaps'
    manifest_dict_fixture["items"][0]["metadata"] = [
        item
        for item in manifest_dict_fixture["items"][0]["metadata"]
        if "explore_bitmaps" not in item.get("label", {}).get("en", [])
    ]

    # Mock the HTTP client
    mock_client = MagicMock(spec=AsyncClient)
    mock_client.get.return_value = Response(200, json=manifest_dict_fixture)

    extractor: IIIFPresentationManifestExtractor[BitMask64] = (
        IIIFPresentationManifestExtractor(
            url_extractor_func=url_extractor_func,
        )
    )
    extractor.client = mock_client

    # Act
    result = await extractor(request)

    # Assert
    assert result is None


async def test_no_url_extracted_from_request() -> None:
    """Test when no URL can be extracted from the request."""
    # Arrange
    request = Request({"type": "http", "headers": Headers().raw})  # No headers

    extractor: IIIFPresentationManifestExtractor[BitMask64] = (
        IIIFPresentationManifestExtractor(
            url_extractor_func=lambda r: None,
        )
    )

    # Act
    result = await extractor(request)

    # Assert
    assert result is None


def test_extract_url_from_x_original_uri() -> None:
    """Test the helper function to extract URL from headers."""
    # Arrange
    request = Request(
        {
            "type": "http",
            "headers": Headers(
                {
                    "host": "impresso-project.ch",
                    "x-forwarded-proto": "https",
                    "x-original-uri": "/api/proxy/iiif-audio/CFCE-1996-09-08-a-r0001/CFCE-1996-09-08-a-r0001.mp3",
                }
            ).raw,
        }
    )

    # Act
    url = extract_url_from_x_original_uri(request)

    # Assert
    assert (
        url
        == "https://impresso-project.ch/api/proxy/iiif-audio/CFCE-1996-09-08-a-r0001/CFCE-1996-09-08-a-r0001.mp3"
    )
