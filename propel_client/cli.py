# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
"""CLI implementation."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from sys import stdin
from typing import Any, Callable, Dict, Optional

import click  # type: ignore

from propel_client.constants import PROPEL_SERVICE_BASE_URL, VAR_TYPES
from propel_client.cred_storage import CredentialStorage
from propel_client.propel import (
    HttpRequestError,
    LoginError,
    NoCredentials,
    PropelClient,
)
from propel_client.utils import get_env_vars_for_service


url_option = click.option(
    "--url",
    "-U",
    type=str,
    required=False,
    default=PROPEL_SERVICE_BASE_URL,
    help="Base url for propel service",
)


@dataclass()
class ClickAPPObject:
    """Click app context object."""

    storage: CredentialStorage
    propel_client: PropelClient

    def logout(self) -> None:
        """Perform logout."""
        self.propel_client.logout()

    def login(self, username: str, password: str) -> None:
        """
        Perform login.

        :param username: username string
        :param password: password string
        """
        self.propel_client.login(username, password)

    def openai(self, path: str, payload: Optional[Dict] = None) -> str:
        """
        Make openai call.

        :param path: openai endpoint path to call
        :param payload: optional dict to pass as post body

        :return: json string
        """
        return self.propel_client.openai(path, payload)


@click.group()
@click.pass_context
@url_option
def cli(ctx: click.Context, url: str) -> None:
    """
    Group commands.

    :param ctx: click context
    :param url: base propel api url
    """
    ctx.url = url
    storage = CredentialStorage()
    propel_client = PropelClient(url, storage)
    ctx.obj = ClickAPPObject(storage=storage, propel_client=propel_client)


def no_credentials_error(func: Callable) -> Callable:
    """
    Decorate with no credetials error converted to click error message.

    :param func: function to wrap

    :return: wrapper for func
    """

    @wraps(func)
    def wrap(*args, **kwargs) -> Any:  # type: ignore
        try:
            return func(*args, **kwargs)
        except NoCredentials as exc:
            raise click.ClickException(
                "No credentials found! Please, login first!"
            ) from exc

    return wrap


@click.command()
@click.option("--username", "-u", type=str, required=False, help="Optional username")
@click.option("--password", "-p", type=str, required=False, help="Optional password")
@click.pass_obj
def login(obj: ClickAPPObject, username: str, password: str) -> None:
    """
    Perform login cli command.

    :param obj: ClickAPPObject
    :param username: username string
    :param password: password string

    :raises ClickException: if login failed
    """
    while not username:
        username = click.prompt("Username")

    while not password:
        password = click.prompt("Password", hide_input=True)

    try:
        obj.login(username=username, password=password)
        click.echo("Logged in")
    except LoginError as exc:
        raise click.ClickException(f"Login failed: {exc}") from exc


@click.command()
@click.pass_obj
@no_credentials_error
def logout(obj: ClickAPPObject) -> None:
    """
    Perform logut cli command.

    :param obj: ClickAPPObject
    """
    obj.logout()
    click.echo("Logged out!")


@click.command()
@click.pass_obj
@click.argument("path", type=str, required=True)
@click.argument("payload", type=str, required=False, default=None)
@no_credentials_error
def openai(obj: ClickAPPObject, path: str, payload: Optional[str] = None) -> None:
    """
    Perform openai call cli command and print out result.

    :param obj: ClickAPPObject
    :param path: openai endpoint path to call
    :param payload: optional dict to pass as post body

    :raises ClickException: if json is not valid
    """
    payload_data = None
    if payload is not None:
        if payload == "-":
            payload = stdin.read()
        try:
            payload_data = json.loads(payload)
        except Exception as exc:  # pylint: disable=broad-except
            raise click.ClickException("payload not a valid json!") from exc
    result = obj.openai(path, payload_data)
    result = json.dumps(json.loads(result), indent=4)
    click.echo(result)


cli.add_command(login)
cli.add_command(logout)
cli.add_command(openai)


@click.group(name="keys")
@click.pass_obj
def keys_group(obj: ClickAPPObject) -> None:
    """
    Group keys commands.

    :param obj: ClickAPPObject
    """
    del obj


@click.command(name="list")
@click.pass_obj
def keys_list(obj: ClickAPPObject) -> None:
    """
    List keys command.

    :param obj: ClickAPPObject
    """
    keys = obj.propel_client.keys_list()
    print_json(keys)


@click.command(name="create")
@click.pass_obj
def keys_create(obj: ClickAPPObject) -> None:
    """
    Create keys command.

    :param obj: ClickAPPObject
    """
    keys = obj.propel_client.keys_create()
    print_json(keys)


keys_group.add_command(keys_list)
keys_group.add_command(keys_create)
cli.add_command(keys_group)


@click.group(name="seats")
@click.pass_obj
def seats_group(obj: ClickAPPObject) -> None:
    """
    Group seat commands.

    :param obj: ClickAPPObject
    """
    del obj


@click.command(name="ensure")
@click.pass_obj
def seats_ensure(obj: ClickAPPObject) -> None:
    """
    Ensure seats command.

    :param obj: ClickAPPObject
    """
    seats = obj.propel_client.get_seats()
    if seats["n_available"] < 1:
        raise click.ClickException("No seats")

    click.echo(f"Seats are ok: {seats['n_available']}")


seats_group.add_command(seats_ensure)
cli.add_command(seats_group)


@click.group(name="agents")
@click.pass_obj
def agents_group(obj: ClickAPPObject) -> None:
    """
    Group agents commands.

    :param obj: ClickAPPObject
    """
    del obj


@click.command(name="list")
@click.pass_obj
def agents_list(obj: ClickAPPObject) -> None:
    """
    List agents command.

    :param obj: ClickAPPObject
    """
    agents = obj.propel_client.agents_list()
    print_json(agents)


@click.command(name="create")
@click.pass_obj
@click.option("--key", type=int, required=True)
@click.option("--name", type=str, required=False)
@click.option("--service-ipfs-hash", type=str, required=False)
@click.option("--variables", type=str, required=False)
@click.option("--chain-id", type=int, required=False)
@click.option("--token-id", type=int, required=False)
@click.option("--ingress-enabled", type=bool, required=False, default=False)
@click.option("--tendermint-ingress-enabled", type=bool, required=False, default=False)
def agents_create(  # pylint: disable=too-many-arguments
    obj: ClickAPPObject,
    key: int,
    name: str,
    variables: str,
    chain_id: int,
    token_id: int,
    ingress_enabled: bool,
    service_ipfs_hash: str,
    tendermint_ingress_enabled: bool,
) -> None:
    """
    Create agent command.

    :param obj: ClickAPPObject
    :param key: key id
    :param name: optional agent name
    :param service_ipfs_hash: optional service ipfs hash id
    :param chain_id: optional chain id
    :param token_id: optional token id
    :param ingress_enabled: option bool
    :param variables: optional str
    :param tendermint_ingress_enabled: optional bool
    """
    variables_list = variables.split(",") or None if variables else []
    agent = obj.propel_client.agents_create(
        key=key,
        name=name,
        service_ipfs_hash=service_ipfs_hash,
        chain_id=chain_id,
        token_id=token_id,
        ingress_enabled=ingress_enabled,
        variables=variables_list,
        tendermint_ingress_enabled=tendermint_ingress_enabled,
    )
    print_json(agent)


@click.command(name="deploy")
@click.pass_context
@click.option("--key", type=int, required=True)
@click.option("--name", type=str, required=False)
@click.option("--service-ipfs-hash", type=str, required=False)
@click.option("--variables", type=str, required=False)
@click.option("--chain-id", type=int, required=False)
@click.option("--token-id", type=int, required=False)
@click.option("--ingress-enabled", type=bool, required=False, default=False)
@click.option("--tendermint-ingress-enabled", type=bool, required=False, default=False)
@click.option("--timeout", type=int, required=False, default=120)
def agents_deploy(  # pylint: disable=too-many-arguments
    ctx: click.Context,
    key: int,
    name: str,
    variables: str,
    chain_id: int,
    token_id: int,
    ingress_enabled: bool,
    service_ipfs_hash: str,
    tendermint_ingress_enabled: bool,
    timeout: int,
) -> None:
    """
    Deploy agent command.

    :param ctx: click context
    :param key: key id
    :param name: optional agent name
    :param service_ipfs_hash: optional service ipfs hash id
    :param chain_id: optional chain id
    :param token_id: optional token id
    :param ingress_enabled: option bool
    :param variables: optional str
    :param tendermint_ingress_enabled: optional bool
    :param timeout: int
    """
    ctx.invoke(seats_ensure)
    click.echo(f"[Agent: {name}] ensure agent deleted")
    ctx.invoke(agents_ensure_deleted, name_or_id=name)
    click.echo(f"[Agent: {name}] agent deleted")
    click.echo(f"[Agent: {name}] create agent")
    ctx.invoke(
        agents_create,
        key=key,
        name=name,
        variables=variables,
        chain_id=chain_id,
        token_id=token_id,
        ingress_enabled=ingress_enabled,
        service_ipfs_hash=service_ipfs_hash,
        tendermint_ingress_enabled=tendermint_ingress_enabled,
    )
    ctx.invoke(agents_wait, name_or_id=name, state="DEPLOYED", timeout=timeout)
    click.echo(f"[Agent: {name}] agent deployed")
    ctx.invoke(agents_restart, name_or_id=name)
    ctx.invoke(agents_wait, name_or_id=name, state="STARTED", timeout=timeout)
    click.echo(f"[Agent: {name}] agent started")


agents_group.add_command(agents_deploy)


@click.command(name="get")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_get(obj: ClickAPPObject, name_or_id: str) -> None:
    """
    Get agent command.

    :param name_or_id: str

    :param obj: ClickAPPObject
    """
    agent = obj.propel_client.agents_get(name_or_id)
    print_json(agent)


@click.command(name="wait")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
@click.argument("state", type=str, required=True)
@click.option("--timeout", type=int, required=False, default=120)
@click.option("--period", type=int, required=False, default=10)
def agents_wait(
    obj: ClickAPPObject, name_or_id: str, state: str, timeout: int, period: int
) -> None:
    """
    Wait agent command.

    :param obj: ClickAPPObject
    :param name_or_id: str
    :param state: str
    :param timeout: int
    :param period: int in seconds
    """
    try:
        for cur_state in obj.propel_client.agents_wait_for_state_iter(
            agent_name_or_id=name_or_id, state=state, timeout=timeout, period=period
        ):
            click.echo(
                f"[Agent: {name_or_id}] state: {cur_state}, waiting for {state} for next {period} seconds"
            )
    except TimeoutError as e:
        raise click.ClickException(
            f"[Agent: {name_or_id}] Timeout during wait for state: {state}"
        ) from e


@click.command(name="ensure-deleted")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
@click.option("--timeout", type=int, required=False, default=120)
def agents_ensure_deleted(obj: ClickAPPObject, name_or_id: str, timeout: int) -> None:
    """
    Ensure agfent deleted command.

    :param name_or_id: str
    :param timeout: int

    :param obj: ClickAPPObject
    """
    if _is_deleted(obj.propel_client, name_or_id):
        click.echo(f"[Agent: {name_or_id}] already deleted")
        return

    obj.propel_client.agents_stop(name_or_id)
    # TODO: add state constants! # pylint: disable=fixme
    started = time.time()
    obj.propel_client.agents_wait_for_state(name_or_id, "DEPLOYED", timeout=timeout)

    obj.propel_client.agents_delete(name_or_id)
    while 1:
        if _is_deleted(obj.propel_client, name_or_id):
            break

        if (time.time() - started) < timeout:
            raise click.ClickException(
                f"[Agent: {name_or_id}] timeout waiting for deleted!"
            )
        time.sleep(3)

    click.echo(f"[Agent: {name_or_id}] Agent was deleted")


def _is_deleted(client: PropelClient, name_or_id: str) -> bool:
    """
    Check if agent deleted helper.

    :param client: PropelClient instance
    :param name_or_id: str

    :return: bool
    """
    try:
        client.agents_get(name_or_id)
        return False
    except HttpRequestError as e:
        if e.code == 404 and e.content == b'{"detail":"Not found."}':
            return True
        raise ValueError(f"Bad response from server: {e}") from e


@click.command(name="restart")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_restart(obj: ClickAPPObject, name_or_id: str) -> None:
    """
    Restart agent command.

    :param name_or_id: str
    :param obj: ClickAPPObject
    """
    agent = obj.propel_client.agents_restart(name_or_id)
    click.echo(f"[Agent: {name_or_id}] restart triggered.")
    print_json(agent)


@click.command(name="stop")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_stop(obj: ClickAPPObject, name_or_id: str) -> None:
    """
    Stop agent command.

    :param name_or_id: str
    :param obj: ClickAPPObject
    """
    agent = obj.propel_client.agents_stop(name_or_id)
    click.echo(f"[Agent: {name_or_id}] stop triggered.")
    print_json(agent)


@click.command(name="variables-add")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
@click.argument("variables", type=str, required=False)
def agents_variables_add(obj: ClickAPPObject, name_or_id: str, variables: str) -> None:
    """
    Add variables to agent.

    :param name_or_id: str
    :param variables: str
    :param obj: ClickAPPObject
    """
    variables_list = variables.split(",") or [] if variables else []
    agent = obj.propel_client.agents_variables_add(name_or_id, variables_list)
    click.echo(f"[Agent: {name_or_id}] variables added {variables_list}.")
    print_json(agent)


@click.command(name="variables-remove")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
@click.argument("variables", type=str, required=False)
def agents_variables_remove(
    obj: ClickAPPObject, name_or_id: str, variables: str
) -> None:
    """
    Remove variables from agent.

    :param name_or_id: str
    :param variables: str
    :param obj: ClickAPPObject
    """
    variables_list = variables.split(",") or [] if variables else []
    agent = obj.propel_client.agents_variables_remove(name_or_id, variables_list)
    click.echo(f"[Agent: {name_or_id}] variables removed {variables_list}.")
    print_json(agent)


@click.command(name="delete")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_delete(obj: ClickAPPObject, name_or_id: str) -> None:
    """
    Delete agent command.

    :param name_or_id: str
    :param obj: ClickAPPObject
    """
    agent = obj.propel_client.agents_delete(name_or_id)
    click.echo(f"[Agent: {name_or_id}] delete triggered.")
    print_json(agent)


agents_group.add_command(agents_list)
agents_group.add_command(agents_create)
agents_group.add_command(agents_get)
agents_group.add_command(agents_wait)
agents_group.add_command(agents_restart)
agents_group.add_command(agents_stop)
agents_group.add_command(agents_delete)
agents_group.add_command(agents_ensure_deleted)
cli.add_command(agents_group)


@click.group(name="variables")
@click.pass_obj
def variables_group(obj: ClickAPPObject) -> None:
    """
    Group variables commands.

    :param obj: ClickAPPObject
    """
    del obj


@click.command(name="list")
@click.pass_obj
def variables_list_command(obj: ClickAPPObject) -> None:
    """
    List variables command.

    :param obj: ClickAPPObject
    """
    variables = obj.propel_client.variables_list()
    print_json(variables)


@click.command(name="create")
@click.pass_obj
@click.argument("name", type=str, required=True)
@click.argument("key", type=str, required=True)
@click.argument("value", type=str, required=True)
@click.argument("var_type", type=click.Choice(VAR_TYPES), required=False, default="str")
def variables_create(
    obj: ClickAPPObject, name: str, key: str, value: str, var_type: str = "str"
) -> None:
    """
    Create variables command.

    :param obj: ClickAPPObject
    :param name: variable name
    :param key: agent config variable key name
    :param value: value
    :param var_type: variable type
    """
    variable = obj.propel_client.variables_create(name, key, value, var_type)
    print_json(variable)


variables_group.add_command(variables_create)
variables_group.add_command(variables_list_command)
cli.add_command(variables_group)


def print_json(data: Dict) -> None:
    """
    Print json helper.

    :param data: dict to print
    """
    click.echo(make_json(data))


def make_json(data: Dict) -> str:
    """
    Make json.

    :param data: dict to print
    :return: str
    """
    return json.dumps(data, indent=4)


@click.group(name="service")
@click.pass_obj
def service_group(obj: ClickAPPObject) -> None:
    """
    Group agents commands.

    :param obj: ClickAPPObject
    """
    del obj


@click.command(name="deploy")
@click.pass_context
@click.option("--keys", type=str, required=True)
@click.option("--service-dir", type=click.Path(file_okay=True), required=True)
@click.option("--name", type=str, required=True)
@click.option("--service-ipfs-hash", type=str, required=False)
@click.option("--chain-id", type=int, required=False)
@click.option("--token-id", type=int, required=False)
@click.option("--ingress-enabled", type=bool, required=False, default=False)
@click.option("--tendermint-ingress-enabled", type=bool, required=False, default=False)
@click.option("--timeout", type=int, required=False, default=120)
def service_deploy(  # pylint: disable=too-many-arguments
    ctx: click.Context,
    keys: str,
    name: str,
    chain_id: int,
    token_id: int,
    ingress_enabled: bool,
    service_ipfs_hash: str,
    tendermint_ingress_enabled: bool,
    timeout: int,
    service_dir: str,
) -> None:
    """Deploy service with keys ids and variables from service file and env variables."""
    keys_list = list(map(int, keys.split(",")))
    service_vars = dict(get_env_vars_for_service(Path(service_dir)))
    environ_vars_set = set(service_vars.keys()).intersection(set(os.environ.keys()))
    variable_names = []
    for env_name in sorted(environ_vars_set):
        env_value = os.environ.get(env_name)
        variable_name = f"{name.upper()}_{env_name}"
        variable_names.append(variable_name)
        click.echo(f"Create/update variable: {variable_name}: {env_name}={env_value}")
        ctx.invoke(variables_create, name=variable_name, key=env_name, value=env_value)

    click.echo(
        f"Deploy {len(keys_list)} agents for service with variables {','.join(variable_names)}"
    )
    with ThreadPoolExecutor(max_workers=len(keys_list)) as executor:
        for idx, key_id in enumerate(keys_list):
            agent_name = f"{name}_agent_{idx}"
            click.echo(
                f"[Agent: {agent_name}] Deploying agent {agent_name} with key {key_id}"
            )
            executor.submit(
                ctx.invoke,
                agents_deploy,
                key=key_id,
                name=agent_name,
                variables=",".join(variable_names) if variable_names else None,
                chain_id=chain_id,
                token_id=token_id,
                ingress_enabled=ingress_enabled,
                service_ipfs_hash=service_ipfs_hash,
                tendermint_ingress_enabled=tendermint_ingress_enabled,
                timeout=timeout,
            )


service_group.add_command(service_deploy)

cli.add_command(service_group)
