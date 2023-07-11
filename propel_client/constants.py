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
"""Various constatns.."""

import os
from pathlib import Path


# TODO: nested constants for API2  # pylint: disable=fixme

API_PREFIX = "/api2"
LOGIN_ENDPOINT = f"{API_PREFIX}/token-auth/"
LOGOUT_ENDPOINT = f"{API_PREFIX}/token-auth/logout"
KEYS_LIST = f"{API_PREFIX}/keys"
SEATS_LIST = f"{API_PREFIX}/seats"
AGENTS_LIST = f"{API_PREFIX}/agents"
VARIABLES_LIST = f"{API_PREFIX}/variables"

OPENAI_ENDPOINT = "/openai/"
PROPEL_SERVICE_BASE_URL = "https://app.propel.valory.xyz"
CREDENTIALS_FILE = ".pcli/creds.json"
CREDENTIALS_FILE_PATH = Path(os.path.expanduser(f"~/{CREDENTIALS_FILE}"))


VAR_TYPES = ["str", "int", "bool", "float", "dict", "list", "none"]
