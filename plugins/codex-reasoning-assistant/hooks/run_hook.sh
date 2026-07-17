#!/usr/bin/env sh
set -u

SCRIPT="$PLUGIN_ROOT/hooks/reasoning_effort_context.py"

run_candidate() {
  candidate="$1"
  if ! command -v "$candidate" >/dev/null 2>&1; then
    return 1
  fi
  if ! "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    return 1
  fi
  "$candidate" "$SCRIPT" && exit 0
  return 2
}

run_candidate python3 || status=$?
if [ "${status:-1}" -eq 2 ]; then
  status=2
else
  run_candidate python || status=$?
fi

printf '%s\n' '{"continue":true,"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"<codex-reasoning-assistant>\nstatus=unavailable\nsource=python_unavailable\ninstruction=Runtime reasoning-effort detection is unavailable because a working Python 3.10+ interpreter was not found. Do not claim the active level is confirmed. Still assess the task and recommend a model and effort.\n</codex-reasoning-assistant>"}}'
