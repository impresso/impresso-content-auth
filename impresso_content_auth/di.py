from typing import Literal
from dependency_injector import containers, providers

from impresso_content_auth.strategy.extractor.base import NullExtractorStrategy
from impresso_content_auth.strategy.extractor.bearer_token import BearerTokenExtractor
from impresso_content_auth.strategy.extractor.manifest_with_secret import (
    ManifestWithSecretExtractor,
)
from impresso_content_auth.strategy.extractor.static_secret import StaticSecretExtractor
from impresso_content_auth.strategy.matcher.base import NullMatcherStrategy
from impresso_content_auth.strategy.matcher.equality import EqualityMatcher


class AppConfiguration(providers.Configuration):
    def is_manifest_with_secret_enabled(self) -> Literal["true", "false"]:
        """Check if the manifest with secret extractor is enabled."""
        return "true" if self.static_files_path() is not None else "false"

    def is_static_secret_enabled(self) -> Literal["true", "false"]:
        """Check if the static secret extractor is enabled."""
        return "true" if self.static_secret() is not None else "false"


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container for Impresso Content Auth."""

    config = AppConfiguration()

    null_extractor: providers.Singleton = providers.Singleton(NullExtractorStrategy)
    null_matcher: providers.Singleton = providers.Singleton(NullMatcherStrategy)

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
        }
    )

    matchers: providers.Aggregate = providers.Aggregate(
        {
            "equality": providers.Singleton(EqualityMatcher),
        }
    )
