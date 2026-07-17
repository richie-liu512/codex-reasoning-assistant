---
name: codex-reasoning-assistant
description: Read the active Codex model and reasoning effort at the start of each task, assess whether they fit the next phase, and recommend continuing, raising or lowering effort, or changing models. Use when the injected reasoning-assistant context is present, when the user asks whether the current configuration fits a task, or when long-running work reaches a phase boundary.
---

# Codex Reasoning Assistant

Use the injected `<codex-reasoning-assistant>` context as the runtime source. Do not infer the active model or effort from the visible interface or a configuration default when the injected context does not confirm it.

## Assess the next phase

Identify the next substantive phase, its success criteria, and how its result will be verified. Assess that phase rather than assigning one setting to the entire conversation.

Choose a model capable of the work before choosing reasoning effort. Then select the lowest effort that protects correctness, completeness, safety, and required evidence. Use the injected `model_role`, `recommended_baseline`, `baseline_rule`, `escalation_rule`, `switch_review_at`, and `switch_model_guidance` fields for model-specific calibration.

Read `references/reasoning-policy.json` when comparing multiple models, resolving an exact effort boundary, or checking whether the injected policy is current. If the policy is stale, missing, invalid, or does not list the model, present model-specific guidance only as a weak prior.

## Calibrate reasoning effort

Base the recommendation on the amount of independent judgment required and how difficult an error would be to detect and repair. Do not reduce the decision to a mechanical score.

- Use None or Minimal only for mechanical work that requires almost no interpretation and when the model supports those levels.
- Use Low for a clear, local, low-impact path with direct verification.
- Use Medium for several dependent steps and limited judgment when the goal, success criteria, and verification are clear.
- Use High for complex logic tracing, debugging, testing key assumptions, or handling meaningful edge cases.
- Use Extra High for highly ambiguous, cross-source, high-impact, or difficult-to-verify work.
- Use Max only when representative evaluation or prior failure shows a real benefit over Extra High on the hardest quality-first work.
- Use Ultra only when the work divides cleanly and proactive subagent delegation is appropriate and available; treat it as orchestration, not merely a larger scalar effort.

Before raising effort, check whether the real blocker is unclear success criteria, missing context, unknown dependencies, incorrect tool routing, or a missing verification loop. Higher effort cannot repair those gaps. Do not treat file count, task duration, or expected token volume as reasoning difficulty by themselves.

## Report the decision

Before substantive work, give one compact line in the user's language containing:

- the detected model and effort, with actual, default-only, or unavailable status;
- the recommended model and effort for the next phase;
- the action: proceed, pause before the difficult phase, or lower at a checkpoint.

Treat the runtime rank as diagnostic metadata, not the product's purpose. Omit it unless the user asks for it or it materially clarifies the recommendation.

Apply switching cost before choosing the action. If a short or nearly complete task is clear and directly verifiable, proceed with the active configuration even when it is stronger than necessary; optionally recommend a lower setting for the next similar task. Recommend switching down during the current task only when enough lower-effort work remains for the saving to be meaningful.

Keep the report brief and continue immediately when the configuration fits or switching would not be worthwhile.

## Handle a mismatch

If the current configuration is too weak, pause before the phase whose quality is at risk. Report completed work, remaining work, the recommended configuration, and the exact resume point.

If the current configuration is materially stronger than the remaining work needs, finish the portion that benefits from it and recommend lowering at the next recoverable checkpoint. Complete short tasks instead of interrupting them for a marginal saving.

Present the recommendation and let the user decide whether to switch. Change configuration or start another task only when the user explicitly requests it.

## Reassess long-running work

At each natural phase boundary, recommend the model and effort for the next phase. Base the new recommendation on that phase's uncertainty, impact, and validation burden rather than carrying forward the previous phase's setting.

## Respect runtime truth and privacy

Treat `status=actual` as confirmed. Treat `default_only` as an unconfirmed configuration default. Treat `unavailable` as unknown and never claim the active effort is known.

Do not expose prompt content, session identifiers, local paths, or other private runtime data in the visible recommendation.
