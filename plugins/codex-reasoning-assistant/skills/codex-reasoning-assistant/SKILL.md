---
name: codex-reasoning-assistant
description: Show the active Codex model and reasoning effort at the start of each task, assess whether they fit the next phase, and recommend continuing, raising or lowering effort, or changing models. Use when the injected reasoning-assistant context is present, when the user asks whether the current configuration fits a task, or when a long-running task reaches a phase boundary.
---

# Codex Reasoning Assistant

Use the injected `<codex-reasoning-assistant>` context as the runtime source.

## Show the check

Before substantive work, show one compact line in the user's language with:

- the detected model and reasoning effort;
- whether the effort is actual, default-only, or unavailable;
- the recommended model and effort for the next phase;
- the action: proceed, pause before a difficult phase, or stop at a checkpoint.

Keep the check brief and continue immediately when the configuration fits.

## Choose the recommendation

Assess the next phase rather than the whole conversation. Choose a model capable of the work, then choose the lowest effort that protects correctness, completeness, safety, and required evidence.

Consider goal ambiguity, dependency depth, verification difficulty, failure impact, and tool or state complexity. Do not use file count, task duration, or expected token volume as a direct measure of reasoning difficulty.

## Handle a mismatch

If the current configuration is too weak, pause before the phase whose quality is at risk. Report completed work, remaining work, the recommended configuration, and the exact resume point.

If the current configuration is materially stronger than the remaining work needs, finish the portion that benefits from it and recommend lowering at the next recoverable checkpoint. Complete short tasks instead of interrupting them for a marginal saving.

Present the recommendation and let the user decide whether to switch. Change configuration or start another task only when the user explicitly requests it.

## Reassess long-running work

At each natural phase boundary, recommend the model and effort for the next phase. Base the recommendation on that phase's uncertainty and validation burden.

## Interpret runtime status

Treat `status=actual` as the active effort. Treat `default_only` as an unconfirmed configuration default. If detection or model calibration is unavailable or stale, state the uncertainty.

Do not expose prompt content, session identifiers, or local paths in the visible check. Read `references/reasoning-policy.json` when detailed model guidance is needed.
