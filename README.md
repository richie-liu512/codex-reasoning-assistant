# Codex Reasoning Assistant

[简体中文](README.zh-CN.md)

## Introduction

This plugin helps you evaluate the required reasoning effort for the current task. At the start of each run, it detects the active model and reasoning configuration, analyzes the difficulty and quality requirements of the upcoming work, and recommends whether to maintain the current setup, adjust the reasoning effort, or switch models.

For multi-stage tasks, the assistant provides configuration recommendations for the next phase. It prioritizes output quality while preventing the unnecessary use of high reasoning efforts on straightforward, easily verifiable steps that offer no meaningful return.

## Core capabilities

- Read the model and reasoning effort actually used by the current task;
- Assess whether the current configuration can protect the correctness, completeness, safety, and verifiability of the next phase;
- Make model-specific recommendations instead of treating the same effort name as equally capable across different models;
- Recommend switching before a difficult phase when the current effort is too weak, or lowering at a recoverable checkpoint when it is clearly stronger than needed;
- Reassess long-running work when it enters a new phase instead of carrying one setting through the entire task mechanically;
- State clearly when the active effort cannot be confirmed instead of presenting a configuration default as the current value.

## How it works

The plugin has two parts:

1. A `UserPromptSubmit` hook reads the active model and reasoning effort in read-only mode before Codex begins processing the task;
2. A Skill uses the model's capability profile, the next phase's reasoning needs, and its validation burden to recommend a model, reasoning effort, and execution action.

The decision order is always:

1. Confirm that the model is capable of the task;
2. Select the lowest reasoning effort that still protects result quality;
3. Decide whether to proceed, pause before a difficult phase, or recommend lowering at a recoverable checkpoint.

If the model itself is not suitable for the task, increasing reasoning effort alone cannot reliably close the capability gap.

## Decision criteria

The assistant assesses the **next phase of work**. It does not choose an effort level simply from file count, task duration, or expected token usage. It considers ambiguity in the goal and evidence, the depth and fragility of dependent reasoning, how easily errors can be detected through tests, the impact and reversibility of failure, and the complexity of tools, state, concurrency, and recovery.

These factors are not a mechanical scorecard. The central questions are how much independent judgment the phase requires and how difficult an incorrect judgment would be to detect and repair.

| Reasoning effort | Work it usually fits |
| --- | --- |
| None / Minimal | Mechanical operations that require almost no interpretation or judgment, when the selected model supports these levels. |
| Low | A clear, local, low-impact path with results that can be verified directly. |
| Medium | Several dependent steps and limited judgment, with clear goals, acceptance criteria, and verification. |
| High | Complex logic tracing, debugging, testing key assumptions, or handling meaningful edge cases. |
| Extra High | Highly ambiguous goals or evidence, cross-source synthesis, high-impact work, or errors that are difficult to detect through tests and review. |
| Max | Only the hardest quality-first work, when representative evaluation or prior failure has shown a real benefit over Extra High. |
| Ultra | Work that divides cleanly and benefits from proactive delegation to multiple subagents; it is an orchestration mode, not merely a larger single-thread reasoning scalar. |

The same effort level does not imply the same capability across models. The current policy applies these model-specific boundaries:

| Model | Recommended starting point and escalation boundary |
| --- | --- |
| GPT-5.6 Sol | Medium is the balanced starting point for ordinary non-trivial work; use High for complex logic and Extra High for especially difficult or high-impact work; Max requires measured evidence of benefit. |
| GPT-5.6 Terra | Start ordinary multi-step work at Medium and use Low for clearly bounded tasks; before using Extra High or Max, compare whether Sol is the better model. |
| GPT-5.6 Luna | Use Low for clear, repeatable, high-volume work and Medium when limited judgment is required; if High appears necessary, compare Terra or Sol. |
| GPT-5.4 mini / Codex Spark | Use for sharply bounded, latency-first work; when the task becomes deep investigation, architecture, or high-impact validation, change models before repeatedly increasing effort. |
| Older models pinned by an existing workflow | Preserve settings that have already been validated; when migration is allowed, compare newer models for complex phases instead of assuming more effort removes the capability gap. |

Before recommending a higher effort, the assistant also checks whether the real problem is unclear success criteria, missing context, unknown dependencies, incorrect tool routing, or a missing verification loop. Higher reasoning effort cannot repair these foundational gaps.

See [Reasoning Policy](docs/reasoning-policy.md) for more detailed model guidance, the review mechanism, and official sources.

## Installation

Requirements:

- a Codex surface with plugin and lifecycle-hook support;
- Python 3.10 or newer, with no third-party Python packages required.

Add the plugin marketplace:

```bash
codex plugin marketplace add richie-liu512/codex-reasoning-assistant --ref main
```

Then:

1. Open `/plugins`;
2. Select the `codex-reasoning-assistant` marketplace and install **Codex Reasoning Assistant**;
3. Open `/hooks`, review the bundled hook, and trust it;
4. Start a new task.

If another `UserPromptSubmit` hook already reads reasoning effort, disable one of them to avoid checking the same task twice.

## Usage

After installation, every submitted task is assessed automatically. No extra prompt is required. A typical result is:

```text
Reasoning recommendation: current GPT-5.6 Sol · High (actual) | next phase: Sol · High | proceed
```

You can also ask directly:

```text
Check whether my current model and reasoning effort fit this task.
```

At a phase boundary in longer work, ask:

```text
Which model and reasoning effort should I use for the next phase?
```

When the recommendation matches the active setting, the task can continue. A higher recommendation means the configuration should be raised before entering the difficult phase. A lower recommendation means the current configuration can complete the task but is materially stronger than the remaining work needs. Short tasks are usually completed directly; long tasks receive a lowering recommendation at the next recoverable checkpoint. The user always decides whether to switch.

## Detection status

- `actual`: the model and reasoning effort are confirmed from current task state;
- `default_only`: only a Codex configuration default is available, and the running task has not been confirmed to use it;
- `unavailable`: the current environment cannot reliably confirm the active effort.

Detection confidence and task suitability are separate questions. The plugin first states whether the detected value is trustworthy, then independently assesses whether the configuration fits the task.

## Data and permissions

Detection reads only the Codex metadata needed to identify the model and reasoning effort. It does not output, save, log, or transmit prompt content, and it does not write to Codex task state.

See [Privacy](PRIVACY.md) and [Security](SECURITY.md) for details.

## Development and verification

After cloning the repository, run:

```bash
python plugins/codex-reasoning-assistant/scripts/verify.py
```

Verification covers plugin structure, hook wrappers, privacy scanning, Python syntax, and unit tests.

## Compatibility

Codex plugin formats and internal state structures can evolve. If detection fails, the task continues, the assistant marks the active effort as unavailable, and it recommends a configuration only from the needs of the next phase.

## License

Licensed under the [MIT License](LICENSE). [LICENSE.zh-CN](LICENSE.zh-CN) is an unofficial Chinese translation.
