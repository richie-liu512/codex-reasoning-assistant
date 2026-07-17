from __future__ import annotations

import importlib.util
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "codex-reasoning-assistant"
MODULE_PATH = PLUGIN_ROOT / "hooks" / "reasoning_effort_context.py"
POLICY_PATH = (
    PLUGIN_ROOT
    / "skills"
    / "codex-reasoning-assistant"
    / "references"
    / "reasoning-policy.json"
)

SPEC = importlib.util.spec_from_file_location("reasoning_effort_context", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_catalog(home: Path, model: str = "gpt-5.6-sol") -> None:
    catalog = {
        "models": [
            {
                "slug": model,
                "description": "Synthetic model fixture",
                "default_reasoning_level": "low",
                "supported_reasoning_levels": [
                    {"effort": "low"},
                    {"effort": "medium"},
                    {"effort": "high"},
                    {"effort": "xhigh"},
                    {"effort": "max"},
                ],
            },
            {"slug": "gpt-5.6-terra", "supported_reasoning_levels": []},
        ]
    }
    (home / "models_cache.json").write_text(json.dumps(catalog), encoding="utf-8")


class ReasoningEffortContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        write_catalog(self.home)
        self.env = patch.dict(
            os.environ,
            {
                "CODEX_HOME": str(self.home),
                "PLUGIN_ROOT": str(PLUGIN_ROOT),
                "REASONING_ASSISTANT_POLICY": str(POLICY_PATH),
            },
            clear=False,
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def test_thread_state_is_actual_and_has_catalog_rank(self) -> None:
        database = self.home / "state_test.sqlite"
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, model TEXT, reasoning_effort TEXT)"
            )
            connection.execute(
                "INSERT INTO threads VALUES (?, ?, ?)",
                ("thread-1", "gpt-5.6-sol", "xhigh"),
            )
            connection.commit()
        finally:
            connection.close()

        metadata = MODULE.resolve_metadata(
            {"session_id": "thread-1", "model": "gpt-5.6-sol"}
        )

        self.assertEqual(metadata["status"], "actual")
        self.assertEqual(metadata["source"], "thread_state")
        self.assertEqual(metadata["current_effort"], "xhigh")
        self.assertEqual(metadata["current_rank"], 4)
        self.assertEqual(metadata["rank_count"], 5)

    def test_hook_model_outranks_state_and_rejects_mismatched_effort(self) -> None:
        database = self.home / "state_test.sqlite"
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, model TEXT, reasoning_effort TEXT)"
            )
            connection.execute(
                "INSERT INTO threads VALUES (?, ?, ?)",
                ("thread-1", "gpt-5.6-terra", "high"),
            )
            connection.commit()
        finally:
            connection.close()

        metadata = MODULE.resolve_metadata(
            {"session_id": "thread-1", "model": "gpt-5.6-sol"}
        )

        self.assertEqual(metadata["model"], "gpt-5.6-sol")
        self.assertEqual(metadata["model_status"], "actual")
        self.assertEqual(metadata["model_source"], "hook_input")
        self.assertEqual(metadata["status"], "unavailable")
        self.assertEqual(metadata["current_effort"], "unknown")

    def test_transcript_fallback_ignores_prompt_content(self) -> None:
        transcript = self.home / "synthetic.jsonl"
        secret_marker = "SYNTHETIC_PRIVATE_PROMPT_MARKER"
        transcript.write_text(
            "\n".join(
                [
                    json.dumps({"type": "user", "payload": {"text": secret_marker}}),
                    json.dumps(
                        {
                            "type": "turn_context",
                            "payload": {
                                "turn_id": "previous-turn",
                                "model": "gpt-5.6-sol",
                                "effort": "low",
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "turn_context",
                            "payload": {
                                "turn_id": "current-turn",
                                "model": "gpt-5.6-sol",
                                "effort": "high",
                            },
                        }
                    ),
                ]
            ),
            encoding="utf-8",
        )

        metadata = MODULE.resolve_metadata(
            {
                "session_id": "missing-thread",
                "turn_id": "current-turn",
                "model": "gpt-5.6-sol",
                "transcript_path": str(transcript),
            }
        )
        rendered = MODULE.render_context(metadata)

        self.assertEqual(metadata["status"], "actual")
        self.assertEqual(metadata["source"], "turn_context")
        self.assertEqual(metadata["current_effort"], "high")
        self.assertNotIn(secret_marker, rendered)
        self.assertNotIn(str(transcript), rendered)

    def test_transcript_without_current_turn_match_is_not_actual(self) -> None:
        transcript = self.home / "synthetic.jsonl"
        transcript.write_text(
            json.dumps(
                {
                    "type": "turn_context",
                    "payload": {
                        "turn_id": "previous-turn",
                        "model": "gpt-5.6-sol",
                        "effort": "xhigh",
                    },
                }
            ),
            encoding="utf-8",
        )

        metadata = MODULE.resolve_metadata(
            {
                "session_id": "missing-thread",
                "turn_id": "current-turn",
                "model": "gpt-5.6-sol",
                "transcript_path": str(transcript),
            }
        )

        self.assertEqual(metadata["status"], "unavailable")
        self.assertEqual(metadata["current_effort"], "unknown")

    def test_config_value_is_labeled_default_only(self) -> None:
        (self.home / "config.toml").write_text(
            'model = "gpt-5.6-sol"\nmodel_reasoning_effort = "medium"\n',
            encoding="utf-8",
        )

        metadata = MODULE.resolve_metadata(
            {"session_id": "missing-thread", "model": "gpt-5.6-sol"}
        )

        self.assertEqual(metadata["status"], "default_only")
        self.assertEqual(metadata["source"], "config_default")
        self.assertEqual(metadata["current_effort"], "medium")
        self.assertEqual(metadata["model"], "gpt-5.6-sol")
        self.assertEqual(metadata["model_source"], "hook_input")

    def test_catalog_default_never_becomes_active_effort(self) -> None:
        metadata = MODULE.resolve_metadata(
            {"session_id": "missing-thread", "model": "gpt-5.6-sol"}
        )

        self.assertEqual(metadata["status"], "unavailable")
        self.assertEqual(metadata["current_effort"], "unknown")
        self.assertEqual(metadata["catalog_default_effort"], "low")

    def test_hook_context_excludes_local_identifiers(self) -> None:
        metadata = MODULE.resolve_metadata(
            {"session_id": "private-session-id", "model": "gpt-5.6-sol"}
        )
        rendered = MODULE.render_context(metadata)

        self.assertNotIn("private-session-id", rendered)
        self.assertNotIn(str(self.home), rendered)
        self.assertIn("status=unavailable", rendered)

    def test_hook_envelope_drops_prompt_field_immediately(self) -> None:
        raw = json.dumps(
            {
                "session_id": "thread-1",
                "turn_id": "turn-1",
                "model": "gpt-5.6-sol",
                "prompt": "SYNTHETIC_PROMPT_THAT_MUST_NOT_BE_RETAINED",
            }
        )
        with patch("sys.stdin", io.StringIO(raw)):
            payload = MODULE.read_json_stdin()

        self.assertNotIn("prompt", payload)
        self.assertEqual(payload["turn_id"], "turn-1")


if __name__ == "__main__":
    unittest.main()
