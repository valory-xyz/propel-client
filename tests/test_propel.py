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
"""Propel api client tests."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from propel_client.propel import HttpRequestError, LoginError, PropelClient

base_url = "http://some/base"
USERNAME = "user1"
PASSWORD = "password1"
mock_credentials = {"sessionid": "12", "csrftoken": "123"}


def _get_client():
    return PropelClient(
        base_url=base_url,
        credentials_storage=MagicMock(load=Mock(return_value=mock_credentials)),
    )


def test_get_url():
    propel = _get_client()
    assert propel._get_url("/handler1") == f"{base_url}/handler1"


def test_login() -> None:
    """Test PropelClient.login."""
    propel = _get_client()
    with patch("requests.get", return_value=MagicMock(content=b"")), pytest.raises(
        LoginError, match="Can not get csrf token."
    ):
        propel.login(USERNAME, PASSWORD)

    with patch(
        "requests.get",
        return_value=MagicMock(
            content=b'name="csrfmiddlewaretoken" value="aaaazzzzz0009">'
        ),
    ):
        # bad respose on login post
        with patch(
            "requests.post", return_value=MagicMock(status_code=500)
        ), pytest.raises(LoginError, match="Bad service response code"):
            propel.login(USERNAME, PASSWORD)

        # no session id in cookies
        with patch(
            "requests.post", return_value=MagicMock(status_code=200)
        ), pytest.raises(LoginError, match="Bad username or password?"):
            propel.login(USERNAME, PASSWORD)

        with patch(
            "requests.post",
            return_value=MagicMock(
                status_code=200,
                cookies=requests.utils.cookiejar_from_dict(mock_credentials),
            ),
        ) as post_mock:
            assert propel.login(USERNAME, PASSWORD) == mock_credentials
            assert post_mock.call_args_list[-1][0][0] == f"{base_url}/accounts/login/"


def test_logout() -> None:
    """Test PropelClient.logout."""
    propel = _get_client()

    with patch("requests.get", return_value=MagicMock(status_code=500)), pytest.raises(
        HttpRequestError, match="Bad status code: 500"
    ):
        propel.logout()

    with patch("requests.get", return_value=MagicMock(status_code=200)) as get_mock:
        propel.logout()
        assert get_mock.call_args_list[-1][0][0] == f"{base_url}/accounts/logout"


def test_call() -> None:
    """Test PropelClient.call."""
    propel = _get_client()

    with patch("requests.post", return_value=MagicMock(status_code=500)), pytest.raises(
        HttpRequestError, match="Bad status code: 500"
    ):
        propel.call(path="/test", payload={"1": 2})

    some_resp = {1: 2}

    with patch(
        "requests.post",
        return_value=MagicMock(status_code=200, content=json.dumps(some_resp).encode()),
    ) as post_mock:
        resp = propel.call(path="/test", payload={"1": 2})
        post_mock.assert_called_once()

        assert resp == json.dumps(some_resp)
