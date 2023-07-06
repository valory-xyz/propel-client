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
from dataclasses import dataclass
from functools import wraps
from sys import stdin
import time
from typing import Any, Callable, Dict, Optional

import click  # type: ignore

from propel_client.constants import PROPEL_SERVICE_BASE_URL, VAR_TYPES
from propel_client.cred_storage import CredentialStorage
from propel_client.propel import HttpRequestError, LoginError, NoCredentials, PropelClient

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
        creds = self.propel_client.login(username, password)

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


@click.group()
@click.pass_obj
def keys(obj: ClickAPPObject):
    pass


@click.command(name="list")
@click.pass_obj
def keys_list(obj: ClickAPPObject):
    keys = obj.propel_client.keys_list()
    print_json(keys)


keys.add_command(keys_list)
cli.add_command(keys)


@click.group()
@click.pass_obj
def seats(obj: ClickAPPObject):
    pass


@click.command(name="ensure")
@click.pass_obj
def seats_ensure(obj: ClickAPPObject):
    seats = obj.propel_client.get_seats()
    if seats["n_available"] < 1:
        raise click.ClickException("No seats")

    click.echo(f"Seats are ok: {seats['n_available']}")


seats.add_command(seats_ensure)
cli.add_command(seats)


@click.group()
@click.pass_obj
def agents(obj: ClickAPPObject):
    pass


@click.command(name="list")
@click.pass_obj
def agents_list(obj: ClickAPPObject):
    agents = obj.propel_client.agents_list()
    print_json(agents)


@click.command(name="create")
@click.pass_obj
@click.option("--key", type=str, required=True)
@click.option("--name", type=str, required=False)
@click.option("--service-ipfs-hash", type=str, required=False)
@click.option("--variables", type=str, required=False)
@click.option("--chain-id", type=int, required=False)
@click.option("--token-id", type=int, required=False)
@click.option("--ingress-enabled", type=bool, required=False, default=False)
@click.option("--tendermint-ingress-enabled", type=bool, required=False, default=False)
def agents_create(
    obj: ClickAPPObject,
    key,
    name,
    variables,
    chain_id,
    token_id,
    ingress_enabled,
    service_ipfs_hash,
    tendermint_ingress_enabled,
):
    if variables:
        variables = variables.split(",") or None
    agent = obj.propel_client.agents_create2(
        key=key,
        name=name,
        service_ipfs_hash=service_ipfs_hash,
        chain_id=chain_id,
        token_id=token_id,
        ingress_enabled=ingress_enabled,
        variables=variables,
        tendermint_ingress_enabled=tendermint_ingress_enabled,
    )
    print_json(agent)


@click.command(name="get")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_get(obj: ClickAPPObject, name_or_id: str):
    agent = obj.propel_client.agents_get(name_or_id)
    print_json(agent)


@click.command(name="wait")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
@click.argument("state", type=str, required=True)
@click.option("--timeout", type=int, required=False, default=120)
def agents_wait(obj: ClickAPPObject, name_or_id: str, state: str, timeout: int):
    try:
        for state in obj.propel_client.agents_wait_for_state_iter(
            agent_name_or_id=name_or_id, state=state, timeout=timeout
        ):
            print("STATE:", state)
    except TimeoutError:
        raise click.ClickException(f"Timeout during wait for state: {state}")


@click.command(name="ensure-deleted")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
@click.option("--timeout", type=int, required=False, default=120)
def agents_ensure_deleted(obj: ClickAPPObject, name_or_id: str, timeout: int):
    if _is_deleted(obj.propel_client, name_or_id):
        print("already deleted")
        return
    
    obj.propel_client.agents_stop(name_or_id)
    # TODO: add state constants!
    started = time.time()
    obj.propel_client.agents_wait_for_state(name_or_id, 'DEPLOYED', timeout=timeout)
    
    obj.propel_client.agents_delete(name_or_id)
    while 1:
        if _is_deleted(obj.propel_client, name_or_id):
            break
        
        if (time.time() - started ) < timeout:
            raise click.ClickException("timeout!")
        time.sleep(3)

    click.echo("Agent was deleted")


def _is_deleted(client: PropelClient, name_or_id: str):
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
def agents_restart(obj: ClickAPPObject, name_or_id: str):
    agent = obj.propel_client.agents_restart(name_or_id)
    print_json(agent)


@click.command(name="stop")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_stop(obj: ClickAPPObject, name_or_id: str):
    agent = obj.propel_client.agents_stop(name_or_id)
    print_json(agent)


@click.command(name="delete")
@click.pass_obj
@click.argument("name_or_id", type=str, required=True)
def agents_delete(obj: ClickAPPObject, name_or_id: str):
    agent = obj.propel_client.agents_delete(name_or_id)
    print_json(agent)


agents.add_command(agents_list)
agents.add_command(agents_create)
agents.add_command(agents_get)
agents.add_command(agents_wait)
agents.add_command(agents_restart)
agents.add_command(agents_stop)
agents.add_command(agents_delete)
agents.add_command(agents_ensure_deleted)
cli.add_command(agents)


@click.group()
@click.pass_obj
def variables(obj: ClickAPPObject):
    pass


@click.command(name="list")
@click.pass_obj
def variables_list(obj: ClickAPPObject):
    variables = obj.propel_client.variables_list()
    print_json(variables)


@click.command(name="create")
@click.pass_obj
@click.argument("name", type=str, required=True)
@click.argument("key", type=str, required=True)
@click.argument("value", type=str, required=True)
@click.argument("var_type", type=click.Choice(VAR_TYPES), required=False, default="str")
def variables_create(obj: ClickAPPObject, name, key, value, var_type):
    variable = obj.propel_client.variables_create(name, key, value, var_type)
    print_json(variable)


variables.add_command(variables_create)
variables.add_command(variables_list)
cli.add_command(variables)


def print_json(data):
    result = json.dumps(data, indent=4)
    print(result)
