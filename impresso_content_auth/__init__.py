"""Impresso Content Authorization package."""

from typing import cast
import logging
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version() -> str:
    """Get the version from pyproject.toml."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        logger.warning("pyproject.toml not found at %s", pyproject_path)
        return "0.1.0"  # Fallback version

    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    return cast(str, pyproject_data.get("project", {}).get("version", "0.1.0"))


__version__: str = get_version()
