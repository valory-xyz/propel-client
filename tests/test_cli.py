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

"""Tests cli."""

import json
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from propel_client.cli import cli
from propel_client.propel import LoginError


class TestCli:
    def setup(self):
        self.runner = CliRunner()
        self.client_mock = MagicMock()
        self.credentials = {"some": "creads"}
        self.client_mock.login = Mock(return_value=self.credentials)
        self.username = "user"
        self.password = "password"
        self.storage_mock = MagicMock()
        self.storage_mock.store = MagicMock()
        self.storage_mock.load = MagicMock()

    def run_cli(self, *args, **kwargs):
        with patch(
            "propel_client.cli.PropelClient", return_value=self.client_mock
        ), patch("propel_client.cli.CredentialStorage", return_value=self.storage_mock):
            result = self.runner.invoke(cli, args, **kwargs)
        return result

    def test_login_ok(self):
        result = self.run_cli("login", "-u", self.username, "-p", self.password)
        assert result.exit_code == 0
        assert result.output == "Logged in\n"
        self.client_mock.login.assert_called_once_with(self.username, self.password)
        self.storage_mock.store.assert_called_once_with(self.credentials)

    def test_login_ok_stdin(self):
        result = self.run_cli("login", input=f"{self.username}\n{self.password}\n")
        assert result.exit_code == 0
        assert "Logged in" in result.output
        self.client_mock.login.assert_called_once_with(self.username, self.password)
        self.storage_mock.store.assert_called_once_with(self.credentials)

    def test_login_fails(self):
        self.client_mock.login = Mock(side_effect=LoginError("ooops"))
        result = self.run_cli("login", "-u", self.username, "-p", self.password)
        assert result.exit_code == 1
        assert "Login failed" in result.output
        self.client_mock.login.assert_called_once_with(self.username, self.password)
        self.storage_mock.store.assert_not_called()

    def test_call_no_creds(self):
        self.storage_mock.load = MagicMock(return_value=None)
        with patch(
            "propel_client.cli.CredentialStorage", return_value=self.storage_mock
        ):
            result = self.runner.invoke(cli, ["call", "/some_api_endpoint"])
        assert result.exit_code == 1
        assert "No credentials found! Please, login first" in result.output

    def test_logout_no_creds(self):
        self.storage_mock.load = MagicMock(return_value=None)
        with patch(
            "propel_client.cli.CredentialStorage", return_value=self.storage_mock
        ):
            result = self.runner.invoke(cli, ["logout"])
        assert result.exit_code == 1
        assert "No credentials found! Please, login first" in result.output

    def test_logout_ok(self):
        self.storage_mock.clear = Mock()
        result = self.run_cli("logout")
        assert result.exit_code == 0
        self.storage_mock.clear.assert_called_once()

    def test_call_ok(self):
        call_resp = '{"1": "2"}'
        self.client_mock.call = MagicMock(return_value=call_resp)
        result = self.run_cli("call", "/some")
        assert result.exit_code == 0
        assert json.loads(call_resp) == json.loads(result.output)
        self.client_mock.call.assert_called_once_with("/some", None)

    def test_call_ok_str_payload(self):
        call_resp = '{"1": "2"}'
        self.client_mock.call = MagicMock(return_value=call_resp)
        result = self.run_cli("call", "/some", call_resp)
        assert result.exit_code == 0
        assert json.loads(call_resp) == json.loads(result.output)
        self.client_mock.call.assert_called_once_with("/some", json.loads(call_resp))

    def test_call_ok_stdin_payload(self):
        call_resp = '{"1": "2"}'
        self.client_mock.call = MagicMock(return_value=call_resp)
        with patch("propel_client.cli.stdin.read", return_value=call_resp):
            result = self.run_cli("call", "/some", "-")
        assert result.exit_code == 0
        assert json.loads(call_resp) == json.loads(result.output)
        self.client_mock.call.assert_called_once_with("/some", json.loads(call_resp))

    def test_call_ok_stdin_bad_payload(self):
        call_resp = '{"1": "2"}'
        self.client_mock.call = MagicMock(return_value=call_resp)
        with patch("propel_client.cli.stdin.read", return_value=""):
            result = self.run_cli("call", "/some", "-")
        assert result.exit_code == 1
        assert "payload not a valid json" in result.output
        self.client_mock.call.assert_not_called()
