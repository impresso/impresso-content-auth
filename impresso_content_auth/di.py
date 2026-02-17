from typing import Literal
from dependency_injector import containers, providers
import redis.asyncio as redis

from impresso_content_auth.service.solr import SolrService
from impresso_content_auth.service.quota_checker.base import QuotaChecker
from impresso_content_auth.service.quota_checker.redis_quota_checker import RedisQuotaChecker
from impresso_content_auth.service.quota_checker.null_quota_checker import NullQuotaChecker
from impresso_content_auth.strategy.extractor.base import NullExtractorStrategy
from impresso_content_auth.strategy.extractor.bearer_token import BearerTokenExtractor
from impresso_content_auth.strategy.extractor.cookie_bitmap_extractor import (
    CookieBitmapExtractor,
)
from impresso_content_auth.strategy.extractor.cookie_user_id_extractor import (
    CookieUserIdExtractor,
)
from impresso_content_auth.strategy.extractor.iiif_presentation_manifest import (
    IIIFPresentationManifestExtractor,
    extract_url_from_x_original_uri,
)
from impresso_content_auth.strategy.extractor.iiif_uri_doc_id_extractor import (
    IIIFUriDocIdExtractor,
)
from impresso_content_auth.strategy.extractor.manifest_with_secret import (
    ManifestWithSecretExtractor,
)
from impresso_content_auth.strategy.extractor.solr_document import (
    SolrDocumentExtractor,
    extract_id_from_x_original_uri_with_iiif, extract_id_from_x_original_uri_with_iiif_and_wildcard_page_suffix,
)
from impresso_content_auth.strategy.extractor.static_secret import StaticSecretExtractor
from impresso_content_auth.strategy.matcher.base import NullMatcherStrategy
from impresso_content_auth.strategy.matcher.bitwise_and import BitWiseAndMatcherStrategy
from impresso_content_auth.strategy.matcher.equality import EqualityMatcher
from impresso_content_auth.strategy.matcher.quota_matcher import QuotaMatcher


class AppConfiguration(providers.Configuration):
    def is_manifest_with_secret_enabled(self) -> Literal["true", "false"]:
        """Check if the manifest with secret extractor is enabled."""
        return "true" if self.static_files_path() is not None else "false"

    def is_static_secret_enabled(self) -> Literal["true", "false"]:
        """Check if the static secret extractor is enabled."""
        return "true" if self.static_secret() is not None else "false"

    def is_cookie_bitmap_enabled(self) -> Literal["true", "false"]:
        """Check if the cookie bitmap extractor is enabled."""
        return "true" if self.jwt_secret() is not None else "false"

    def is_solr_content_item_enabled(self) -> Literal["true", "false"]:
        """Check if Solr is enabled."""
        if (
            self.solr.base_url() is not None
            and self.solr.content_item_collection() is not None
            and self.solr.username() is not None
            and self.solr.password() is not None
        ):
            return "true"
        return "false"

    def is_redis_quota_checker_enabled(self) -> Literal["true", "false"]:
        """Check if Redis quota checker is enabled."""
        return "true" if self.redis.url() is not None else "false"


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container for Impresso Content Auth."""

    config = AppConfiguration()

    null_extractor: providers.Singleton = providers.Singleton(NullExtractorStrategy)
    null_matcher: providers.Singleton = providers.Singleton(NullMatcherStrategy)

    redis_client: providers.Singleton = providers.Singleton(
        redis.from_url,
        url=config.redis.url,
    )

    null_quota_checker: providers.Singleton[NullQuotaChecker] = providers.Singleton(NullQuotaChecker)

    quota_checker: providers.Selector = providers.Selector(
        config.is_redis_quota_checker_enabled,
        true=providers.Singleton(
            RedisQuotaChecker,
            redis_client=redis_client,
            quota_limit=config.redis.quota_limit.as_(int),
            window_seconds=config.redis.window_days.as_(lambda days: int(days) * 86400),
        ),
        false=null_quota_checker,
    )

    solr_service: providers.Singleton[SolrService] = providers.Singleton(
        SolrService,
        base_url=config.solr.base_url,
        username=config.solr.username,
        password=config.solr.password,
        proxy_url=config.solr.proxy_url,
    )

    extractors: providers.Aggregate = providers.Aggregate(
        {
            "bearer-token": providers.Singleton(BearerTokenExtractor),
            "manifest-with-secret": providers.Selector(
                config.is_manifest_with_secret_enabled,
                true=providers.Singleton(
                    ManifestWithSecretExtractor,
                    base_path=config.static_files_path,
                ),
                false=null_extractor,
            ),
            "static-secret": providers.Selector(
                config.is_static_secret_enabled,
                true=providers.Singleton(
                    StaticSecretExtractor,
                    secret=config.static_secret,
                ),
                false=null_extractor,
            ),
            "content-item-image-bitmap": providers.Selector(
                config.is_solr_content_item_enabled,
                true=providers.Singleton(
                    SolrDocumentExtractor,
                    solr_service=solr_service,
                    collection=config.solr.content_item_collection,
                    field="rights_bm_get_img_l",
                    # - To match by page ID:
                    # id_extractor_func=extract_id_from_x_original_uri_with_iiif,
                    # solr_id_field="page_id_ss",
                    # - To match by content item ID prefix:
                    solr_id_field="id",
                    id_extractor_func=extract_id_from_x_original_uri_with_iiif_and_wildcard_page_suffix,
                ),
                false=null_extractor,
            ),
            "content-item-explore-bitmap": providers.Selector(
                config.is_solr_content_item_enabled,
                true=providers.Singleton(
                    SolrDocumentExtractor,
                    solr_service=solr_service,
                    collection=config.solr.content_item_collection,
                    field="rights_bm_explore_l",
                    # - To match by page ID:
                    # id_extractor_func=extract_id_from_x_original_uri_with_iiif,
                    # solr_id_field="page_id_ss",
                    # - To match by content item ID prefix:
                    solr_id_field="id",
                    id_extractor_func=extract_id_from_x_original_uri_with_iiif_and_wildcard_page_suffix,
                ),
                false=null_extractor,
            ),
            "cookie-bitmap": providers.Selector(
                config.is_cookie_bitmap_enabled,
                true=providers.Singleton(
                    CookieBitmapExtractor,
                    cookie_name=config.cookie_name,
                    jwt_secret=config.jwt_secret,
                    verify_audience=config.jwt_verify_audience.as_(
                        lambda x: x.lower() == "true" if isinstance(x, str) else x
                    ),
                ),
                false=null_extractor,
            ),
            "iiif-presentation-manifest": providers.Singleton(
                IIIFPresentationManifestExtractor,
                url_extractor_func=extract_url_from_x_original_uri,
            ),
        }
    )

    matchers: providers.Aggregate = providers.Aggregate(
        {
            "equality": providers.Singleton(EqualityMatcher),
            "bitwise-and": providers.Singleton(BitWiseAndMatcherStrategy),
            "quota": providers.Singleton(
                QuotaMatcher,
                quota_checker=quota_checker,
                user_id_extractor=providers.Singleton(
                    CookieUserIdExtractor,
                    cookie_name=config.cookie_name,
                    jwt_secret=config.jwt_secret,
                    verify_audience=config.jwt_verify_audience.as_(
                        lambda x: x.lower() == "true" if isinstance(x, str) else x
                    ),
                ),
                doc_id_extractor=providers.Singleton(
                    IIIFUriDocIdExtractor,
                ),
            ),
        }
    )
