from itertools import chain
from pathlib import Path

from aea.helpers.env_vars import is_env_variable, ENV_VARIABLE_RE
from autonomy.configurations.loader import load_service_config


def get_all_env_vars(d):
    for value in d.values():
        if is_env_variable(value):
            result = ENV_VARIABLE_RE.match(value)
            _, var_name, type_str, _, default = result.groups()
            yield var_name, default
        if isinstance(value, dict):
            yield from get_all_env_vars(value)


def get_env_vars_for_service(service_path: Path):
    service = load_service_config(service_path)
    return set(chain(*(get_all_env_vars(i) for i in service.overrides)))
