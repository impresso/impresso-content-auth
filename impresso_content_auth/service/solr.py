"""
Service module for interacting with Solr using httpx.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, cast
from cachetools import TTLCache

import httpx
from httpx import Limits, Timeout

logger = logging.getLogger(__name__)

def _get_post_key(url: str, json_data: Dict[str, Any]) -> str:
    """Generates a unique, hashable key from the URL and sorted JSON data."""
    # 1. Sort the JSON data to ensure consistent key generation 
    #    (order of keys shouldn't matter for the cache)
    sorted_json_str = json.dumps(json_data, sort_keys=True)
    
    # 2. Combine the URL and the sorted JSON string
    return f"{url}:{sorted_json_str}"

class SolrService:
    """
    Service for interacting with Solr using httpx with connection pooling.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        username: Optional[str] = None,
        password: Optional[str] = None,
        proxy_url: Optional[str] = None,
    ):
        """
        Initialize the Solr service with connection pooling.

        Args:
            base_url: Base URL of the Solr service (e.g., 'http://localhost:8983/solr')
            timeout: Request timeout in seconds
            max_connections: Maximum number of connections in the pool
            max_keepalive_connections: Maximum number of idle connections to keep in the pool
            username: Optional username for basic authentication
            password: Optional password for basic authentication
            proxy_url: Optional proxy URL to use for requests
        """
        self.base_url = base_url.rstrip("/")
        limits = Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        self.client = httpx.Client(
            timeout=Timeout(timeout),
            limits=limits,
            headers={"Content-Type": "application/json"},
            auth=(
                httpx.BasicAuth(username=username, password=password)
                if username and password
                else None
            ),
            proxy=proxy_url,
        )
        self._proxy_url = proxy_url
        self._auth_credentials = (username, password) if username and password else None
        self._cache = TTLCache[str, str](maxsize=10000, ttl=3600)

    @property
    def authentication_details(self) -> str | None:
        """Solr client auth details (redacted)."""
        if self._auth_credentials:
            username, password = self._auth_credentials or ("", "")
            redacted_password = "[REDACTED]" if password else "None"
            return f"Basic Auth: {username}:{redacted_password}"
        return None

    @property
    def proxy_url(self) -> Optional[str]:
        """Get the proxy URL if configured."""
        return self._proxy_url

    def __del__(self) -> None:
        """Ensure the client is closed when the service is garbage collected."""
        if hasattr(self, "client"):
            self.client.close()

    def close(self) -> None:
        """Close the httpx client explicitly."""
        self.client.close()

    def post_query(
        self,
        collection: str,
        body: Dict[str, Any],
        handler: str = "select",
    ) -> Dict[str, Any]:
        """
        Send a POST request to Solr.

        Args:
            collection: Name of the Solr collection
            body: Request body to send to Solr
            handler: Solr request handler (default: 'select')

        Returns:
            Parsed JSON response from Solr

        Raises:
            httpx.HTTPStatusError: On HTTP status errors
            httpx.RequestError: On request errors
            ValueError: On invalid responses
        """
        url = f"{self.base_url}/{collection}/{handler}"

        cached_response = self._cache.get(_get_post_key(url, body))
        if cached_response is not None:
            logger.debug(
                "Cache hit for Solr POST request to collection '%s' at %s with body: %s",
                collection,
                url,
                body,
            )
            return cast(Dict[str, Any], json.loads(cached_response))

        try:
            logger.debug(
                "Sending POST request to Solr collection '%s' at %s with body: %s",
                collection,
                url,
                body,
            )
            response = self.client.post(
                url,
                json=body,
            )
            response.raise_for_status()
            result = cast(Dict[str, Any], response.json())
            self._cache[_get_post_key(url, body)] = json.dumps(result)
            return result
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error querying Solr collection '%s': %s : %s",
                collection,
                str(e),
                response.text,
            )
            raise e
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON response from Solr: {response.text}"
            ) from exc

    def search(
        self,
        collection: str,
        q: str = "*:*",
        fq: Optional[Union[str, List[str]]] = None,
        fields: Optional[List[str]] = None,
        rows: int = 10,
        start: int = 0,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform a search query against a Solr collection.

        Args:
            collection: Name of the Solr collection
            q: Query string (default: '*:*')
            fq: Filter query string or list of filter queries
            fields: List of fields to return
            rows: Number of rows to return
            start: Start offset
            sort: Sort order

        Returns:
            Parsed JSON response from Solr
        """
        body = {"query": q, "limit": rows, "offset": start}

        params: Dict[str, Any] = {}

        if fq:
            params["fq"] = fq
        if fields:
            params["fl"] = ",".join(fields)
        if sort:
            params["sort"] = sort

        if params:
            body["params"] = params

        return self.post_query(collection, body)
