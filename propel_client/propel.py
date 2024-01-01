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
import time
from typing import Any, Dict, Generator, Iterable, List, Optional, Union

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

    def __init__(
        self,
        message: str,
        *args: Any,
        code: Optional[int] = None,
        content: Optional[bytes] = None,
    ) -> None:
        """Init exception."""
        self.code = code
        self.content = content
        super().__init__(message, *args)


class PropelClient:
    """Propel client."""

    # TODO: use nested constants for api2 endpoints  # pylint: disable=fixme
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
        """
        url = self._get_url(self.LOGIN_ENDPOINT)
        response = requests.post(
            url,
            data={
                "username": username,
                "password": password,
            },
            allow_redirects=False,
        )

        self._check_response(response)

        credentials = self._get_credentials_from_response(response)
        self.credentials_storage.store(credentials)
        return credentials

    @staticmethod
    def _get_credentials_from_response(response: requests.Response) -> Dict[str, str]:
        """
        Make credentials record(headers) from server response.

        :param response: reqeusts.Response

        :return: dict
        """
        return {"Authorization": f"Token {response.json()['token']}"}

    def _get_credentials_params(self) -> Dict:
        """
        Get credentials options for requests method.

        :return: dict
        """
        credentials = self.credentials_storage.load()
        if not credentials:
            raise NoCredentials("Credentials not specified. please login first")
        return {"headers": credentials}

    def logout(self) -> None:
        """Logout user."""
        url = self._get_url(self.LOGOUT_ENDPOINT)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        self.credentials_storage.clear()

    @staticmethod
    def _check_response(
        response: requests.Response, codes: Iterable[int] = (200,)
    ) -> None:
        """Check response has status code from the list."""
        if response.status_code not in codes:
            msg = (
                f"Bad status code: {response.status_code}."
                f"Content: {str(response.content)}"
            )
            raise HttpRequestError(
                msg,
                code=response.status_code,
                content=response.content,
            )

    def openai(self, path: str, payload: Optional[Dict] = None) -> str:
        """
        Make openai call.

        :param path: openai endpoint path to call
        :param payload: optional dict to pass as post body

        :return: json string
        """
        url = self._get_url(self.OPENAI_ENDPOINT)
        json_data = {"endpoint_path": path, "payload": payload}
        response = requests.post(url, json=json_data, **self._get_credentials_params())
        self._check_response(response)

        return response.content.decode()

    def keys_list(self) -> Dict:
        """
        List all keys.

        :return: dict
        """
        url = self._get_url(self.API_KEYS_LIST)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def keys_create(self) -> Dict:
        """
        Create key.

        :return: dict
        """
        url = self._get_url(self.API_KEYS_LIST) + "/"
        response = requests.post(url, **self._get_credentials_params())
        self._check_response(response, codes=[201])
        return response.json()

    def get_seats(self) -> Dict:
        """
        Get seats.

        :return: dict
        """
        url = self._get_url(self.API_SEATS_LIST)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_list(self) -> Dict:
        """
        List agents.

        :return: dict
        """
        url = self._get_url(self.API_AGENTS_LIST)
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_get(self, agent_name_or_id: Union[int, str]) -> Dict:
        """
        Get agent by name or id.

        :param agent_name_or_id: str or int

        :return: dict
        """
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_restart(self, agent_name_or_id: Union[int, str]) -> Dict:
        """
        Restart agent by name or id.

        :param agent_name_or_id: str or int

        :return: dict
        """
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/restart/"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_stop(self, agent_name_or_id: Union[int, str]) -> Dict:
        """
        Stop agent by name or id.

        :param agent_name_or_id: str or int

        :return: dict
        """
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/stop/"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def agents_variables_add(
        self, agent_name_or_id: Union[int, str], variables: List[str]
    ) -> Dict:
        """
        Add variables to agent.

        :param agent_name_or_id: str or int
        :param variables: list of str

        :return: dict
        """
        url = (
            self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/variables_add/"
        )
        response = requests.post(
            url,
            json={"variables": variables},
            **self._get_credentials_params(),
            allow_redirects=False,
        )
        self._check_response(response)
        return response.json()

    def agents_variables_remove(
        self, agent_name_or_id: Union[int, str], variables: List[str]
    ) -> Dict:
        """
        Remove variables from agent.

        :param agent_name_or_id: str or int
        :param variables: list of str

        :return: dict
        """
        url = (
            self._get_url(self.API_AGENTS_LIST)
            + f"/{agent_name_or_id}/variables_remove/"
        )

        response = requests.post(
            url, **self._get_credentials_params(), json={"variables": variables}
        )
        self._check_response(response)
        return response.json()

    def agents_delete(self, agent_name_or_id: Union[int, str]) -> Dict:
        """
        Delete agent by name or id.

        :param agent_name_or_id: str or int

        :return: dict
        """
        url = self._get_url(self.API_AGENTS_LIST) + f"/{agent_name_or_id}/delete"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response)
        return response.json()

    def _agents_create_from_data(self, agent_data: Dict[str, Any]) -> Dict:
        """
        Create agent by agent data.

        :param agent_data: agent data dict
        :return: respose dict
        """
        url = self._get_url(self.API_AGENTS_LIST) + "/"
        response = requests.post(url, json=agent_data, **self._get_credentials_params())
        self._check_response(response, codes=[201])
        return response.json()

    def agents_create(  # pylint: disable=too-many-arguments
        self,
        key: Union[int, str],
        name: Optional[str] = None,
        service_ipfs_hash: Optional[str] = None,
        chain_id: Optional[int] = None,
        token_id: Optional[int] = None,
        ingress_enabled: bool = False,
        variables: Optional[List[str]] = None,
        tendermint_ingress_enabled: bool = False,
    ) -> Dict:
        """
        Create agent by agent options.

        :param key: key id
        :param name: optional agent name
        :param service_ipfs_hash: optional service ipfs hash id
        :param chain_id: optional chain id
        :param token_id: optional token id
        :param ingress_enabled: option bool
        :param variables: optional list of strings of varible names or ids
        :param tendermint_ingress_enabled: optional bool
        :return: dict
        """
        agent_data: Dict[str, Union[List, int, str]] = {"key": int(key)}

        if name is not None:
            agent_data["name"] = name

        if service_ipfs_hash is not None:
            agent_data["service_ipfs_hash"] = service_ipfs_hash

        if chain_id is not None:
            agent_data["chain_id"] = chain_id

        if token_id is not None:
            agent_data["token_id"] = token_id

        if variables:
            agent_data["variables"] = variables

        agent_data["ingress_enabled"] = ingress_enabled
        agent_data["tendermint_ingress_enabled"] = tendermint_ingress_enabled

        return self._agents_create_from_data(agent_data)

    def variables_list(self) -> Dict:
        """
        List user variables.

        :return: dict
        """
        url = self._get_url(self.API_VARIABLES_LIST) + "/"
        response = requests.get(url, **self._get_credentials_params())
        self._check_response(response, codes=[200])
        return response.json()

    def variables_create(
        self, name: str, key: str, value: str, type_: str = "str"
    ) -> Dict:
        """
        Create variable.

        :param name: variable name
        :param key: agent config variable key name
        :param value: value
        :param type_: variable type, defaults to "str"
        :return: dict
        """
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
        agent_name_or_id: Union[int, str],
        state: str,
        timeout: int = 120,
        period: int = 3,
    ) -> bool:
        """
        Wait agent reaches state.

        :param agent_name_or_id: str or int
        :param state: state to wait for
        :param timeout: wait timeout, defaults to 120
        :param period: state poll period, defaults to 3
        :raises TimeoutError: on timeout reached
        :return: True
        """
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
        agent_name_or_id: Union[int, str],
        state: str,
        timeout: int = 120,
        period: int = 3,
    ) -> Generator:
        """
        Wait agent reaches state.

        :param agent_name_or_id: str or int
        :param state: state to wait for
        :param timeout: wait timeout, defaults to 120
        :param period: state poll period, defaults to 3

        :raises TimeoutError: on timeout reached
        :return: Generator
        :yield: current state str
        """
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
