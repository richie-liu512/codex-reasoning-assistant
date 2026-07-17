# Codex Reasoning Assistant

[简体中文](README.zh-CN.md)

Show the active Codex model and reasoning effort at the beginning of every task, then recommend whether to continue, raise or lower the effort, or change models for the work ahead.

## What it does

- Reads the model and reasoning effort used by the current task;
- Shows where that effort sits within the selected model's supported range;
- Checks whether the current configuration can protect the quality of the next phase;
- Recommends a configuration again at natural phase boundaries in long-running work;
- States clearly when the active effort cannot be confirmed instead of presenting a configuration default as the current value.

At the beginning of a task, you see a compact check such as:

```text
Reasoning check: GPT-5.6 Sol · Extra High (actual, 4/6) | recommended: Sol · High | proceed
```

If the current effort is too low, the assistant pauses before the difficult phase and reports what is complete, what remains, the recommended configuration, and where to resume. If the effort is clearly higher than the remaining work needs, it first completes the part that benefits from stronger reasoning and recommends a lower setting at an appropriate checkpoint. When the configuration fits, the task continues.

## How it decides

The assistant first chooses a model capable of the task, then selects the lowest reasoning effort that meets the quality bar. It considers:

- ambiguity in the goal and evidence;
- the depth and fragility of dependent reasoning;
- how easily an incorrect result can be detected through tests or review;
- the impact and reversibility of failure;
- the complexity of tools, state, concurrency, and recovery.

File count, task length, and expected token usage are not treated as reasoning difficulty by themselves. The same effort name also does not imply the same capability across different models.

Model roles and effort guidance come from a dated policy with a review deadline. See [Reasoning Policy](docs/reasoning-policy.md) for the current basis and official sources.

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

If you already have a `UserPromptSubmit` hook that checks reasoning effort, disable one of them to avoid duplicate checks.

## Usage

After installation, every submitted task is checked automatically. No extra prompt is required.

You can also ask directly:

```text
Check whether my current model and reasoning effort fit this task.
```

At a phase boundary in longer work, ask:

```text
Which model and reasoning effort should I use for the next phase?
```

The assistant gives a recommendation, and you decide whether to switch. It helps change configuration or start another task only when you explicitly request that action.

## Confidence in the detected value

- `actual`: the model comes from the current hook event and the effort is confirmed from current task state;
- `default_only`: only a Codex configuration default is available, and the running task has not been confirmed to use it;
- `unavailable`: the current environment cannot reliably confirm the active effort.

The model catalog's default effort is reported separately and is never presented as the active task value.

## Data and permissions

Detection reads only the Codex metadata needed to identify the model and reasoning effort. It does not output, save, log, or transmit prompt content, and it does not write to Codex task state.

See [Privacy](PRIVACY.md) and [Security](SECURITY.md) for details.

## Verify a checkout

After cloning the repository, run:

```bash
python plugins/codex-reasoning-assistant/scripts/verify.py
```

Verification covers plugin structure, hook wrappers, privacy scanning, Python syntax, and unit tests.

## Compatibility

Codex plugin formats and internal state structures can evolve. If detection fails, the task continues and the assistant marks the active effort as unavailable.

## License

Licensed under the [MIT License](LICENSE). [LICENSE.zh-CN](LICENSE.zh-CN) is an unofficial Chinese translation.
