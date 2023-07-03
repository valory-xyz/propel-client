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
from typing import Any, Callable, Dict, Optional

import click  # type: ignore

from propel_client.constants import PROPEL_SERVICE_BASE_URL
from propel_client.cred_storage import CredentialStorage
from propel_client.propel import LoginError, NoCredentials, PropelClient

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
def call(obj: ClickAPPObject, path: str, payload: Optional[str] = None) -> None:
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
cli.add_command(call)
