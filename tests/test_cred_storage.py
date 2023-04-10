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

"""Tests credential storage."""

import json
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from unittest.mock import patch

from propel_client.cred_storage import CredentialStorage


@contextmanager
def conf_tmp_file() -> Generator[Path, None, None]:
    """Mock credentials storage conf file path."""
    with TemporaryDirectory() as tmp_dir:
        conf_path = Path(tmp_dir) / ".pcli/conf.json"
        with patch.object(CredentialStorage, "CONF_PATH", conf_path):
            yield conf_path


def test_cred_storage_works() -> None:
    """Test credentials storage works."""
    data = {"some": "data"}
    with conf_tmp_file() as conf_file:
        assert CredentialStorage().load() is None
        assert not conf_file.exists()
        CredentialStorage().store(data)
        assert conf_file.exists()
        assert CredentialStorage().load() == data
        assert json.loads(conf_file.read_text()) == data
        CredentialStorage().clear()
        assert CredentialStorage().load() is None
        assert json.loads(conf_file.read_text()) == {}
