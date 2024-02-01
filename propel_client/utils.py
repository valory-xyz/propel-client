"""Various utils."""
from itertools import chain
from pathlib import Path
from typing import Any, Generator

from aea.helpers.env_vars import ENV_VARIABLE_RE, is_env_variable
from autonomy.configurations.loader import load_service_config


RESOURCE_ENV_VARS = [
    ("AUTONOMY_AGENT_MEMORY_LIMIT", 1024),
    ("AUTONOMY_AGENT_CPU_LIMIT", 1.0),
    ("AUTONOMY_AGENT_MEMORY_REQUEST", 256),
    ("AUTONOMY_AGENT_CPU_REQUEST", 1.0),
]


def get_all_env_vars(d: Any) -> Generator[tuple[str | Any, str | Any] | Any, Any, None]:
    """Get env vars from dict."""
    for value in d.values():
        if is_env_variable(value):
            result = ENV_VARIABLE_RE.match(value)  # type: ignore
            _, var_name, _, _, default = result.groups()  # type: ignore
            yield var_name, default
        if isinstance(value, dict):
            yield from get_all_env_vars(value)


def get_env_vars_for_service(
    service_path: Path,
) -> set[tuple[str | Any, str | Any] | Any]:
    """Get env vars for service path."""
    service = load_service_config(service_path)
    return set(
        chain(RESOURCE_ENV_VARS, *(get_all_env_vars(i) for i in service.overrides))
    )
