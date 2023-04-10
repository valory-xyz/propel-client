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
"""Crendetials storage implementation."""
import json
import os
from pathlib import Path
from typing import Dict, Optional

from propel_client.constants import CREDENTIALS_FILE_PATH


class CredentialStorage:
    """Infile credential storage."""

    CONF_PATH: Path = CREDENTIALS_FILE_PATH

    def _ensure_dir(self) -> None:
        """Make app config dirs if needed."""
        os.makedirs(str(Path(self.CONF_PATH).parent), exist_ok=True)

    def store(self, credentials: Dict) -> None:
        """
        Store credentials.

        :param credentials: dict with credentials to store
        """
        self._ensure_dir()
        self.CONF_PATH.write_text(json.dumps(credentials), encoding="utf-8")

    def load(self) -> Optional[Dict]:
        """
        Load credentials.

        :return: None if no credentials stored or dict.
        """
        self._ensure_dir()
        if not self.CONF_PATH.exists():
            return None
        return json.loads(self.CONF_PATH.read_text(encoding="utf-8")) or None

    def clear(self) -> None:
        """Clear credentials."""
        self.store({})
