from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any


CONTEXT_TAG = "codex-reasoning-assistant"
TAIL_WINDOW_BYTES = 16 * 1024 * 1024
POLICY_RELATIVE_PATH = Path(
    "skills/codex-reasoning-assistant/references/reasoning-policy.json"
)


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured) if configured else Path.home() / ".codex"


def plugin_root() -> Path:
    configured = os.environ.get("PLUGIN_ROOT")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent.parent


def policy_path() -> Path:
    configured = os.environ.get("REASONING_ASSISTANT_POLICY")
    return Path(configured) if configured else plugin_root() / POLICY_RELATIVE_PATH


def read_json_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        return {}
    allowed = {
        "session_id",
        "turn_id",
        "transcript_path",
        "cwd",
        "hook_event_name",
        "model",
        "permission_mode",
    }
    return {key: value.get(key) for key in allowed if key in value}


def parse_turn_context_line(line: str) -> dict[str, Any] | None:
    if '"type":"turn_context"' not in line and '"type": "turn_context"' not in line:
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    if event.get("type") != "turn_context":
        return None
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else None


def read_latest_turn_context(
    transcript_path: str | None, turn_id: str | None
) -> dict[str, Any] | None:
    if not transcript_path or not turn_id:
        return None
    path = Path(transcript_path)
    if not path.is_file():
        return None

    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            start = max(0, size - TAIL_WINDOW_BYTES)
            handle.seek(start)
            text = handle.read().decode("utf-8", errors="ignore")
        lines = text.splitlines()
        if start > 0 and lines:
            lines = lines[1:]
        for line in reversed(lines):
            payload = parse_turn_context_line(line)
            if payload is not None and payload.get("turn_id") == turn_id:
                return payload
    except OSError:
        return None
    return None


def read_thread_state(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None

    databases = list(codex_home().glob("state_*.sqlite"))
    try:
        databases.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    except OSError:
        pass

    for database in databases:
        try:
            uri = database.resolve().as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True, timeout=1)
            try:
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(threads)").fetchall()
                }
                if not {"id", "model", "reasoning_effort"}.issubset(columns):
                    continue
                row = connection.execute(
                    "SELECT model, reasoning_effort FROM threads WHERE id = ?",
                    (session_id,),
                ).fetchone()
                if row:
                    return {"model": row[0], "effort": row[1]}
            finally:
                connection.close()
        except (OSError, sqlite3.Error):
            continue
    return None


def parse_simple_toml_defaults(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            break
        if "=" not in line:
            continue
        key, raw_value = (part.strip() for part in line.split("=", 1))
        if key not in {"model", "model_reasoning_effort"}:
            continue
        if (
            len(raw_value) >= 2
            and raw_value[0] == raw_value[-1]
            and raw_value[0] in {'"', "'"}
        ):
            result[key] = raw_value[1:-1]
    return result


def read_config_default() -> dict[str, Any] | None:
    path = codex_home() / "config.toml"
    if not path.is_file():
        return None
    try:
        try:
            import tomllib

            with path.open("rb") as handle:
                config = tomllib.load(handle)
        except ModuleNotFoundError:
            config = parse_simple_toml_defaults(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return {
        "model": config.get("model"),
        "effort": config.get("model_reasoning_effort"),
    }


def read_model_catalog(model: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "supported_efforts": [],
        "catalog_default_effort": None,
        "catalog_description": None,
        "catalog_models": [],
    }
    path = codex_home() / "models_cache.json"
    if not path.is_file():
        return result
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return result

    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list):
        return result

    identifiers: list[str] = []
    for entry in models:
        if not isinstance(entry, dict):
            continue
        identifier = entry.get("slug") or entry.get("id") or entry.get("model")
        if isinstance(identifier, str):
            identifiers.append(identifier)
        if identifier != model:
            continue
        result["catalog_default_effort"] = entry.get("default_reasoning_level")
        result["catalog_description"] = entry.get("description")
        levels = entry.get("supported_reasoning_levels")
        if isinstance(levels, list):
            result["supported_efforts"] = [
                level["effort"]
                for level in levels
                if isinstance(level, dict) and isinstance(level.get("effort"), str)
            ]
    result["catalog_models"] = identifiers
    return result


def empty_policy(model: str, effort: str, status: str) -> dict[str, Any]:
    return {
        "policy_status": status,
        "policy_version": "unknown",
        "policy_updated_at": "unknown",
        "policy_review_after": "unknown",
        "model_profile_key": model,
        "model_role": "unknown",
        "recommended_baseline": "unknown",
        "baseline_rule": "unknown",
        "escalation_rule": "unknown",
        "switch_review_at": "none",
        "switch_model_guidance": "unknown",
        "calibration_status": "unavailable",
        "current_effort_guidance": "unknown",
        "current_effort_label": effort,
        "assessment_factors": [],
        "available_policy_models": [],
    }


def read_reasoning_policy(
    model: str, effort: str, catalog_models: list[str]
) -> dict[str, Any]:
    path = policy_path()
    if not path.is_file():
        return empty_policy(model, effort, "missing")
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_policy(model, effort, "invalid")
    if not isinstance(policy, dict):
        return empty_policy(model, effort, "invalid")

    aliases = policy.get("model_aliases")
    profile_key = model
    if isinstance(aliases, dict) and isinstance(aliases.get(model), str):
        profile_key = aliases[model]

    profiles = policy.get("model_profiles")
    profile = profiles.get(profile_key) if isinstance(profiles, dict) else None
    effort_levels = policy.get("effort_levels")
    effort_definition = (
        effort_levels.get(effort) if isinstance(effort_levels, dict) else None
    )

    status = "loaded"
    review_after = policy.get("review_after")
    if isinstance(review_after, str):
        try:
            if date.today() > date.fromisoformat(review_after):
                status = "stale"
        except ValueError:
            status = "invalid_review_date"
    if not isinstance(profile, dict):
        status = "model_unlisted" if status == "loaded" else status
        profile = {}

    factor_map = policy.get("decision_factors")
    factors = list(factor_map.keys()) if isinstance(factor_map, dict) else []
    profile_keys = set(profiles.keys()) if isinstance(profiles, dict) else set()
    alias_keys = set(aliases.keys()) if isinstance(aliases, dict) else set()
    available_models = [
        item for item in catalog_models if item in profile_keys or item in alias_keys
    ]

    return {
        "policy_status": status,
        "policy_version": policy.get("policy_version") or "unknown",
        "policy_updated_at": policy.get("updated_at") or "unknown",
        "policy_review_after": review_after or "unknown",
        "model_profile_key": profile_key,
        "model_role": profile.get("role") or "unknown",
        "recommended_baseline": profile.get("recommended_baseline") or "unknown",
        "baseline_rule": profile.get("baseline_rule") or "unknown",
        "escalation_rule": profile.get("escalation_rule") or "unknown",
        "switch_review_at": profile.get("switch_review_at") or "none",
        "switch_model_guidance": profile.get("switch_model_guidance") or "unknown",
        "calibration_status": profile.get("calibration_status") or "unavailable",
        "current_effort_guidance": (
            effort_definition.get("use_when")
            if isinstance(effort_definition, dict)
            else "unknown"
        ),
        "current_effort_label": (
            effort_definition.get("label")
            if isinstance(effort_definition, dict)
            else effort
        ),
        "assessment_factors": factors,
        "available_policy_models": available_models,
    }


def resolve_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = payload.get("session_id") or os.environ.get("CODEX_THREAD_ID")
    turn_id = payload.get("turn_id")
    transcript_path = payload.get("transcript_path")
    hook_model = payload.get("model")
    model = hook_model
    model_status = "actual" if isinstance(hook_model, str) and hook_model else "unavailable"
    model_source = "hook_input" if model_status == "actual" else "unavailable"
    effort = None
    source = "unavailable"
    status = "unavailable"

    state = read_thread_state(session_id if isinstance(session_id, str) else None)
    if state:
        state_model = state.get("model")
        if model_status != "actual" and isinstance(state_model, str):
            model = state_model
            model_status = "actual"
            model_source = "thread_state"
        state_matches_model = (
            isinstance(state_model, str)
            and isinstance(model, str)
            and state_model == model
        )
        effort = state.get("effort") if state_matches_model else None
        if isinstance(effort, str) and effort and state_matches_model:
            source = "thread_state"
            status = "actual"

    if status != "actual":
        turn_context = read_latest_turn_context(
            transcript_path if isinstance(transcript_path, str) else None,
            turn_id if isinstance(turn_id, str) else None,
        )
        if turn_context:
            turn_model = turn_context.get("model")
            if model_status != "actual" and isinstance(turn_model, str):
                model = turn_model
                model_status = "actual"
                model_source = "turn_context"
            turn_matches_model = (
                isinstance(turn_model, str)
                and isinstance(model, str)
                and turn_model == model
            )
            effort = turn_context.get("effort") if turn_matches_model else None
            if isinstance(effort, str) and effort and turn_matches_model:
                source = "turn_context"
                status = "actual"

    if status != "actual":
        default = read_config_default()
        if default:
            if model_status != "actual" and isinstance(default.get("model"), str):
                model = default.get("model")
                model_status = "default_only"
                model_source = "config_default"
            effort = default.get("effort")
            if isinstance(effort, str) and effort:
                source = "config_default"
                status = "default_only"

    model_value = model if isinstance(model, str) and model else "unknown"
    effort_value = effort if isinstance(effort, str) and effort else "unknown"
    catalog = read_model_catalog(model_value)
    order = catalog["supported_efforts"]
    rank = order.index(effort_value) + 1 if effort_value in order else None
    policy = read_reasoning_policy(
        model_value, effort_value, catalog.get("catalog_models", [])
    )

    return {
        "status": status,
        "source": source,
        "model_status": model_status,
        "model_source": model_source,
        "model": model_value,
        "current_effort": effort_value,
        "supported_efforts": order,
        "current_rank": rank,
        "rank_count": len(order) if order else None,
        "catalog_default_effort": catalog["catalog_default_effort"] or "unknown",
        "catalog_description": catalog["catalog_description"] or "unknown",
        **policy,
    }


def single_line(value: Any) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def render_context(metadata: dict[str, Any]) -> str:
    supported = ",".join(metadata["supported_efforts"]) or "unknown"
    rank = metadata["current_rank"] or "unknown"
    rank_count = metadata["rank_count"] or "unknown"
    factors = ",".join(metadata["assessment_factors"]) or "unknown"
    model_options = ",".join(metadata["available_policy_models"]) or "unknown"
    return "\n".join(
        [
            f"<{CONTEXT_TAG}>",
            f"status={metadata['status']}",
            f"source={metadata['source']}",
            f"model_status={metadata['model_status']}",
            f"model_source={metadata['model_source']}",
            f"model={metadata['model']}",
            f"current_effort={metadata['current_effort']}",
            f"current_effort_label={single_line(metadata['current_effort_label'])}",
            f"supported_efforts={supported}",
            f"current_rank={rank}",
            f"rank_count={rank_count}",
            f"catalog_default_effort={metadata['catalog_default_effort']}",
            f"catalog_description={single_line(metadata['catalog_description'])}",
            f"available_policy_models={model_options}",
            f"policy_status={metadata['policy_status']}",
            f"policy_version={metadata['policy_version']}",
            f"policy_updated_at={metadata['policy_updated_at']}",
            f"policy_review_after={metadata['policy_review_after']}",
            f"model_profile_key={metadata['model_profile_key']}",
            f"model_role={single_line(metadata['model_role'])}",
            f"recommended_baseline={metadata['recommended_baseline']}",
            f"baseline_rule={single_line(metadata['baseline_rule'])}",
            f"escalation_rule={single_line(metadata['escalation_rule'])}",
            f"switch_review_at={metadata['switch_review_at']}",
            f"switch_model_guidance={single_line(metadata['switch_model_guidance'])}",
            f"calibration_status={metadata['calibration_status']}",
            f"current_effort_guidance={single_line(metadata['current_effort_guidance'])}",
            f"assessment_factors={factors}",
            "instruction=Before substantive work, provide one compact reasoning recommendation in the user's language. "
            "State the detected model and effort, whether it is actual/default-only/unavailable, "
            "the recommended model and effort for the next phase, and whether to proceed, pause, "
            "or stop at a checkpoint. Choose the model before effort and use the lowest effort that "
            "meets the quality bar. Do not treat file count, token volume, or duration alone as reasoning "
            "complexity. If the active setting is too weak, pause before the risky phase. If it is materially "
            "too strong, finish the difficult portion and recommend lowering only at a recoverable checkpoint. "
            "For long work, recommend the next phase's setting at each natural boundary. Never change settings "
            "or launch another run without explicit user authorization. If status is not actual, do not claim "
            "the active effort is confirmed. If policy_status is stale, invalid, missing, or model_unlisted, "
            "treat model-specific calibration as unavailable or only a weak prior.",
            "privacy=Do not quote, store, transmit, or log prompt content for this check.",
            f"</{CONTEXT_TAG}>",
        ]
    )


def fallback_output(source: str, error_type: str | None = None) -> dict[str, Any]:
    lines = [
        f"<{CONTEXT_TAG}>",
        "status=unavailable",
        f"source={source}",
        "model=unknown",
        "current_effort=unknown",
        "instruction=Runtime detection is unavailable. Do not infer or claim the active level. Still assess the next phase and recommend a model and effort, preserving quality first.",
    ]
    if error_type:
        lines.append(f"error_type={error_type}")
    lines.append(f"</{CONTEXT_TAG}>")
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(lines),
        },
    }


def main() -> int:
    try:
        if "--probe" in sys.argv:
            print(json.dumps(resolve_metadata({}), ensure_ascii=False))
            return 0

        payload = read_json_stdin()
        metadata = resolve_metadata(payload)
        response = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": render_context(metadata),
            },
        }
        print(json.dumps(response, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps(fallback_output("hook_error", type(error).__name__)))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
