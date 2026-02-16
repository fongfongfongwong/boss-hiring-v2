"""Load and expose the global YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """Return the parsed config.yaml as a dict (cached after first load)."""
    global _config
    if _config is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
    return _config


def get_scoring_weights() -> dict[str, float]:
    return get_config().get("scoring", {}).get("weights", {})


def get_qualified_threshold() -> float:
    return get_config().get("scoring", {}).get("qualified_threshold", 70)


def get_throttle_config() -> dict[str, Any]:
    return get_config().get("throttle", {})


def get_communication_config() -> dict[str, Any]:
    return get_config().get("communication", {})
