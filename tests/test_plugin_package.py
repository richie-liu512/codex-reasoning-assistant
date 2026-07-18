from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "codex-reasoning-assistant"


class PluginPackageTests(unittest.TestCase):
    def test_hooks_file_uses_codex_supported_top_level_shape(self) -> None:
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))

        self.assertEqual(set(hooks), {"hooks"})
        self.assertIn("UserPromptSubmit", hooks["hooks"])


if __name__ == "__main__":
    unittest.main()
