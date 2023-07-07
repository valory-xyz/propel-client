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
"""Propel client implementation."""
import abc
import re
import time
from typing import Dict, List, Optional

import requests

from propel_client import constants
from propel_client.cred_storage import CredentialStorage


class BaseClientError(Exception):
    """Base client exception class."""


class NoCredentials(BaseClientError):
    """No crednetials specified exception."""


class LoginError(BaseClientError):
    """Login error. bad username/password."""


class HttpRequestError(BaseClientError):
    """Bad http request response."""

    def __init__(self, message, code=None, content=None, *args: object) -> None:
        self.code = code
        self.content = content
        super().__init__(message, *args)


class PropelClient:
    """Propel client."""

    # TODO: use nested constants for api2 endpoints
    LOGIN_ENDPOINT = constants.LOGIN_ENDPOINT
    LOGOUT_ENDPOINT = constants.LOGOUT_ENDPOINT
    OPENAI_ENDPOINT = constants.OPENAI_ENDPOINT
    API_KEYS_LIST = constants.KEYS_LIST
    API_SEATS_LIST = constants.SEATS_LIST
    API_AGENTS_LIST = constants.AGENTS_LIST
    API_VARIABLES_LIST = constants.VARIABLES_LIST

    def __init__(
        self,
        base_url: str,
        credentials_storage: CredentialStorage,
    ) -> None:
        """
        Init client.

        :param base_url: base propel http server url
        :param credentials_storage: credential storage instance.
        """
        self.base_url = base_url
        self.credentials_storage = credentials_storage

    def _get_url(self, path: str) -> str:
        """
        Return full url for path specified.

        :param path: path of propel endpoint

        :return: full url string for propel server
        """
        return f"{self.base_url}{path}"

    def login(self, username: str, password: str) -> Dict:
        """
        Login and return credentials.

        :param username: username string
        :param password: password string

        :return: dict  with credentials

        :raises LoginError: if something goes wrong during login process
        """
        url = self._get_url(self.LOGIN_ENDPOINT)
        response = requests.post(
            url,
            data={
                "username": username,
                "password": password,
            },
            allow_redirects=False,
            verify=False,
        )

        self._check_response(response)

        credentials = self._get_credentials_from_response(response)
        self.credentials_storage.store(credentials)
        return credentials

    def _get_credentials_from_response(self, response):
        return {"Authorization": f"Token {response.json()['token']}"}

    def _get_credentials_params(self):
        credentials = self.credentials_storage.load()
        if not credentials:
            raise NoCredentials("Credentials not specified. please login first")
        return {"headers": credentials, "verify": False}

    def logout(self) -> None:
        """
        Logout user.

        :raises HttpRequestError: on request errors
        """
        url = self._get_url(self.LOGOUT_ENDPOINT)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        self.credentials_storage.clear()

    def _check_response(self, response, codes=[200]):
        if response.status_code not in codes:
            raise HttpRequestError(
                f"Bad status code: {response.status_code}. Content: {response.content}",
                code=response.status_code,
                content=response.content,
            )

    def openai(self, path: str, payload: Optional[Dict] = None) -> str:
        """
        Make openai call.

        :param path: openai endpoint path to call
        :param payload: optional dict to pass as post body

        :return: json string

        :raises HttpRequestError: on request errors
        """
        url = self._get_url(self.OPENAI_ENDPOINT)
        json_data = {"endpoint_path": path, "payload": payload}
        response = requests.post(url, json=json_data, **self._get_credentials_params())
        self._check_response(response)

        return response.content.decode()

    def keys_list(self):
        url = self._get_url(self.API_KEYS_LIST)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def keys_create(self):
        url = self._get_url(self.API_KEYS_LIST) + "/"
        response = requests.post(url, **self._get_credentials_params())
        self._check_response(response, codes=[201])
        return response.json()

    def get_seats(self):
        url = self._get_url(self.API_SEATS_LIST)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_list(self):
        url = self._get_url(self.API_AGENTS_LIST)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_get(self, agent_name_or_id):
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_restart(self, agent_name_or_id):
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/restart"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_stop(self, agent_name_or_id):
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/stop"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_delete(self, agent_name_or_id):
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/delete"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_create(self, agent_data):
        url = self._get_url(self.API_AGENTS_LIST) + "/"
        response = requests.post(url, json=agent_data, **self._get_credentials_params())
        self._check_response(response, codes=[201])
        return response.json()

    def agents_create2(
        self,
        key: str,
        name: Optional[str] = None,
        service_ipfs_hash: Optional[str] = None,
        chain_id: Optional[int] = None,
        token_id: Optional[int] = None,
        ingress_enabled: bool = False,
        variables: Optional[List[str]] = None,
        tendermint_ingress_enabled: bool = False,
    ):
        agent_data = {"key": key}

        vars = [
            "name",
            "service_ipfs_hash",
            "chain_id",
            "token_id",
            "ingress_enabled",
            "variables",
            "tendermint_ingress_enabled",
        ]

        for var in vars:
            if locals()[var]:
                agent_data[var] = locals()[var]

        return self.agents_create(agent_data)

    def variables_list(self):
        url = self._get_url(self.API_VARIABLES_LIST) + "/"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response, codes=[200])
        return response.json()

    def variables_create(self, name: str, key: str, value: str, type_: str = "str"):
        url = self._get_url(self.API_VARIABLES_LIST) + "/"
        variable_data = {
            "name": name,
            "key": key,
            "masked_value": value,
            "var_type": type_,
        }
        response = requests.post(
            url, json=variable_data, **self._get_credentials_params()
        )
        self._check_response(response, codes=[201])
        return response.json()

    def agents_wait_for_state(
        self,
        agent_name_or_id: int | str,
        state: str,
        timeout: int = 120,
        period: int = 3,
    ):
        start = time.time()
        while time.time() - start < timeout:
            try:
                agent_data = self.agents_get(agent_name_or_id=agent_name_or_id)
                if agent_data["agent_state"] == state:
                    return True
                time.sleep(period)
            except requests.exceptions.ConnectionError:
                pass

        raise TimeoutError()

    def agents_wait_for_state_iter(
        self,
        agent_name_or_id: int | str,
        state: str,
        timeout: int = 120,
        period: int = 3,
    ):
        start = time.time()
        while time.time() - start < timeout:
            try:
                agent_data = self.agents_get(agent_name_or_id=agent_name_or_id)
                yield agent_data["agent_state"]
                if agent_data["agent_state"] == state:
                    return True
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(period)

        raise TimeoutError()
