"""YAML loading helpers that preserve PolicyEngine period keys as text."""

from __future__ import annotations

from typing import Any

import yaml


class PolicyEngineSafeLoader(yaml.SafeLoader):
    """Safe loader that does not coerce period keys to Python dates."""


PolicyEngineSafeLoader.yaml_implicit_resolvers = {
    key: [
        (tag, expression)
        for tag, expression in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(text: str) -> Any:
    """Safely parse YAML while retaining dates such as ``0000-01-01``."""

    return yaml.load(text, Loader=PolicyEngineSafeLoader)
