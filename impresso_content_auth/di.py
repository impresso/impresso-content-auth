from typing import Literal
from dependency_injector import containers, providers

from impresso_content_auth.service.solr import SolrService
from impresso_content_auth.strategy.extractor.base import NullExtractorStrategy
from impresso_content_auth.strategy.extractor.bearer_token import BearerTokenExtractor
from impresso_content_auth.strategy.extractor.cookie_bitmap_extractor import (
    CookieBitmapExtractor,
)
from impresso_content_auth.strategy.extractor.iiif_presentation_manifest import (
    IIIFPresentationManifestExtractor,
    extract_url_from_x_original_uri,
)
from impresso_content_auth.strategy.extractor.manifest_with_secret import (
    ManifestWithSecretExtractor,
)
from impresso_content_auth.strategy.extractor.solr_document import (
    SolrDocumentExtractor,
    extract_id_from_x_original_uri_with_iiif,
)
from impresso_content_auth.strategy.extractor.static_secret import StaticSecretExtractor
from impresso_content_auth.strategy.matcher.base import NullMatcherStrategy
from impresso_content_auth.strategy.matcher.bitwise_and import BitWiseAndMatcherStrategy
from impresso_content_auth.strategy.matcher.equality import EqualityMatcher


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


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container for Impresso Content Auth."""

    config = AppConfiguration()

    null_extractor: providers.Singleton = providers.Singleton(NullExtractorStrategy)
    null_matcher: providers.Singleton = providers.Singleton(NullMatcherStrategy)

    solr_service: providers.Singleton = providers.Singleton(
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
                    id_extractor_func=extract_id_from_x_original_uri_with_iiif,
                    field="rights_bm_get_img_l",
                    solr_id_field="page_id_ss",
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
        }
    )
