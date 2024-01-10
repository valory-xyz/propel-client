"""Various utils."""
from itertools import chain
from pathlib import Path

from aea.helpers.env_vars import ENV_VARIABLE_RE, is_env_variable
from autonomy.configurations.loader import load_service_config


def get_all_env_vars(d):
    """Get env vars from dict."""
    for value in d.values():
        if is_env_variable(value):
            result = ENV_VARIABLE_RE.match(value)
            _, var_name, _, _, default = result.groups()
            yield var_name, default
        if isinstance(value, dict):
            yield from get_all_env_vars(value)


def get_env_vars_for_service(service_path: Path):
    """Get env vars for service path."""
    service = load_service_config(service_path)
    return set(chain(*(get_all_env_vars(i) for i in service.overrides)))
