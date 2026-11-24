import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import desk_steps


class EnvironmentSetupTests(unittest.TestCase):
    def test_process_environment_can_supply_private_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_env = Path(tmp) / ".env"
            supplied = {
                "SEC_USER_AGENT": "Student student@example.edu",
                "API_KEY": "test-only-key",
                "MODEL": "test-model",
            }
            with patch.dict(os.environ, supplied, clear=False):
                values = desk_steps.read_env(missing_env)
        self.assertEqual(values["SEC_USER_AGENT"], supplied["SEC_USER_AGENT"])
        self.assertEqual(values["API_KEY"], supplied["API_KEY"])
        self.assertEqual(values["MODEL"], supplied["MODEL"])

    def test_process_environment_overrides_file_without_editing_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "SEC_USER_AGENT=File User file@example.edu\nMODEL=file-model\n",
                encoding="utf-8",
            )
            supplied = {
                "SEC_USER_AGENT": "Process User process@example.edu",
                "MODEL": "process-model",
            }
            with patch.dict(os.environ, supplied, clear=False):
                values = desk_steps.read_env(env_file)
        self.assertEqual(values["SEC_USER_AGENT"], supplied["SEC_USER_AGENT"])
        self.assertEqual(values["MODEL"], supplied["MODEL"])


if __name__ == "__main__":
    unittest.main()
