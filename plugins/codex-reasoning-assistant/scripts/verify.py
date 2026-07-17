from __future__ import annotations

import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "reasoning_effort_context.py"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
POLICY = (
    PLUGIN_ROOT
    / "skills"
    / "codex-reasoning-assistant"
    / "references"
    / "reasoning-policy.json"
)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def check_structure() -> None:
    manifest = load_json(PLUGIN_MANIFEST)
    marketplace = load_json(MARKETPLACE)
    load_json(PLUGIN_ROOT / "hooks" / "hooks.json")
    load_json(POLICY)

    name = manifest.get("name")
    if name != "codex-reasoning-assistant":
        raise ValueError("Plugin manifest name is inconsistent")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        raise ValueError("Marketplace must expose exactly one plugin")
    entry = entries[0]
    if entry.get("name") != name:
        raise ValueError("Marketplace and manifest plugin names differ")
    source = entry.get("source")
    if not isinstance(source, dict) or source.get("path") != "./plugins/codex-reasoning-assistant":
        raise ValueError("Marketplace source path is incorrect")


def check_text_hygiene() -> None:
    forbidden = [
        "C:" + "\\Users\\1",
        "G:" + "\\Users\\1",
        "F:" + "\\python",
        "019f7178" + "-a1ea-7143-a7a8-84b88c3f0508",
        "[" + "TODO:",
    ]
    text_suffixes = {
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".py",
        ".ps1",
        ".sh",
        ".txt",
        ".toml",
    }
    private_patterns = [
        ("Windows user path", re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s\"']+")),
        (
            "macOS user path",
            re.compile(r"(?<!https:)/" + r"Users/[^/\s\"']+"),
        ),
        (
            "Linux user path",
            re.compile(r"(?<!https:)/" + r"home/[^/\s\"']+"),
        ),
        (
            "Codex-like session UUID",
            re.compile(
                r"\b019[0-9a-f]{5}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                re.IGNORECASE,
            ),
        ),
    ]
    violations: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            if marker in text:
                violations.append(f"{path.relative_to(REPO_ROOT)} contains {marker!r}")
        for label, pattern in private_patterns:
            if pattern.search(text):
                violations.append(f"{path.relative_to(REPO_ROOT)} contains a {label}")
        if re.search(r"(?i)(api[_-]?key|token)\s*[:=]\s*['\"][A-Za-z0-9_-]{16,}", text):
            violations.append(f"{path.relative_to(REPO_ROOT)} may contain a secret")
    if violations:
        raise ValueError("\n".join(violations))


def run_wrapper(command: list[str], env: dict[str, str]) -> dict:
    result = subprocess.run(
        command,
        input=json.dumps(
            {
                "session_id": "synthetic-session",
                "turn_id": "synthetic-turn",
                "model": "gpt-5.6-sol",
                "prompt": "SYNTHETIC_PROMPT_NOT_FOR_OUTPUT",
            }
        ),
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError("Hook wrapper did not return a JSON object")
    return value


def check_hook_integration() -> None:
    hooks = load_json(PLUGIN_ROOT / "hooks" / "hooks.json")
    handlers = hooks.get("hooks", {}).get("UserPromptSubmit")
    if not isinstance(handlers, list) or not handlers:
        raise ValueError("UserPromptSubmit hook is missing")
    command_hook = handlers[0].get("hooks", [{}])[0]
    if "run_hook.sh" not in command_hook.get("command", ""):
        raise ValueError("Unix hook command does not use the wrapper")
    if "run_hook.ps1" not in command_hook.get("commandWindows", ""):
        raise ValueError("Windows hook command does not use the wrapper")

    with tempfile.TemporaryDirectory() as temp_home:
        env = os.environ.copy()
        env["CODEX_HOME"] = temp_home
        env["PLUGIN_ROOT"] = str(PLUGIN_ROOT)

        if os.name == "nt":
            shell = shutil.which("powershell") or shutil.which("pwsh")
            if not shell:
                raise ValueError("PowerShell is required to verify the Windows wrapper")
            command = [
                shell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PLUGIN_ROOT / "hooks" / "run_hook.ps1"),
            ]
        else:
            shell = shutil.which("sh") or "/bin/sh"
            command = [shell, str(PLUGIN_ROOT / "hooks" / "run_hook.sh")]

        normal = run_wrapper(command, env)
        context = normal.get("hookSpecificOutput", {}).get("additionalContext", "")
        if f"<{ 'codex-reasoning-assistant' }>" not in context:
            raise ValueError("Hook wrapper did not inject assistant context")
        if "SYNTHETIC_PROMPT_NOT_FOR_OUTPUT" in context:
            raise ValueError("Hook wrapper exposed prompt content")

        no_python_env = env.copy()
        no_python_env["PATH"] = ""
        fallback = run_wrapper(command, no_python_env)
        fallback_context = fallback.get("hookSpecificOutput", {}).get(
            "additionalContext", ""
        )
        if "status=unavailable" not in fallback_context:
            raise ValueError("Missing-interpreter path did not fail open")
        if "source=python_unavailable" not in fallback_context:
            raise ValueError("Missing-interpreter path has the wrong source")


def run_tests() -> None:
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(REPO_ROOT / "tests"), "-v"],
        cwd=REPO_ROOT,
        check=True,
    )


def main() -> int:
    check_structure()
    check_text_hygiene()
    py_compile.compile(str(HOOK_SCRIPT), doraise=True)
    check_hook_integration()
    run_tests()
    print(
        "Verification passed: structure, privacy scan, syntax, hook wrappers, and tests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
