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
import re
from typing import Dict, Optional

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


class PropelClient:
    """Propel client."""

    LOGIN_ENDPOINT = constants.LOGIN_ENDPOINT
    LOGOUT_ENDPOINT = constants.LOGOUT_ENDPOINT
    OPENAI_ENDPOINT = constants.OPENAI_ENDPOINT

    def __init__(self, base_url: str, credentials_storage: CredentialStorage) -> None:
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
        resp = requests.get(url)
        match = re.search(
            r'name="csrfmiddlewaretoken" value="([a-zA-Z0-9]+)">', resp.content.decode()
        )
        if not match:
            raise LoginError("Can not get csrf token.")
        csrftoken = match.groups()[0]

        response = requests.post(
            url,
            data={
                "username": username,
                "password": password,
                "csrfmiddlewaretoken": csrftoken,
            },
            cookies=resp.cookies,
            allow_redirects=False,
        )

        if response.status_code not in [200, 302]:
            raise LoginError("Bad service response code")

        credentials = requests.utils.dict_from_cookiejar(response.cookies)

        if "sessionid" not in credentials:
            raise LoginError("Bad username or password?")

        return credentials

    def _get_cookies(self) -> requests.cookies.RequestsCookieJar:
        """
        Get cookie jar for requests from credentials dict.

        :return: RequestsCookieJar
        :raises NoCredentials: if no crendetials stored in storage
        """
        credentials = self.credentials_storage.load()
        if not credentials:
            raise NoCredentials()
        jar = requests.utils.cookiejar_from_dict(credentials)
        return jar

    def logout(self) -> None:
        """
        Logout user.

        :raises HttpRequestError: on request errors
        """
        cookies = self._get_cookies()
        url = self._get_url(self.LOGOUT_ENDPOINT)
        response = requests.get(url, cookies=cookies)
        if response.status_code not in [200, 302]:
            raise HttpRequestError(f"Bad status code: {response.status_code}")

    def call(self, path: str, payload: Optional[Dict] = None) -> str:
        """
        Make openai call.

        :param path: openai endpoint path to call
        :param payload: optional dict to pass as post body

        :return: json string

        :raises HttpRequestError: on request errors
        """
        cookies = self._get_cookies()
        url = self._get_url(self.OPENAI_ENDPOINT)
        json_data = {"endpoint_path": path, "payload": payload}
        response = requests.post(url, json=json_data, cookies=cookies)

        if response.status_code != 200:
            raise HttpRequestError(f"Bad status code: {response.status_code}")

        return response.content.decode()
