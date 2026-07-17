# Architecture / 架构

## English

The repository is a one-plugin marketplace:

```text
.agents/plugins/marketplace.json
plugins/codex-reasoning-assistant/
├── .codex-plugin/plugin.json
├── hooks/
│   ├── hooks.json
│   ├── run_hook.sh
│   ├── run_hook.ps1
│   └── reasoning_effort_context.py
├── skills/codex-reasoning-assistant/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/reasoning-policy.json
└── scripts/verify.py
```

The `UserPromptSubmit` hook runs before each user turn. Its detection order is:

1. take the active model from the current hook event, which has priority over every fallback;
2. query the current session in Codex's local state database using read-only SQLite for reasoning effort, accepting it only when the row's model matches the hook model;
3. if effort is unavailable, scan a bounded local transcript tail for a `turn_context` metadata event whose `turn_id` and model both match the current hook event;
4. if still unavailable, read top-level defaults from the local Codex configuration and mark them `default_only`;
5. read the local model catalog for supported effort order and model availability;
6. load the bundled, dated policy for model-specific guidance;
7. inject compact developer context and let the active Codex model assess the actual task.

State database and transcript formats are not stable public APIs. Every reader is best-effort, read-only, bounded, and fail-open. Unknown values stay unknown.

## 中文

本仓库本身是一个只包含单个插件的市场，目录结构见上方代码块。

`UserPromptSubmit` Hook 会在每次用户提交任务前运行，读取顺序如下：

1. 直接采用当前 Hook 事件提供的活动模型，并使它高于所有后备来源；
2. 使用只读 SQLite 查询 Codex 本地状态数据库中的当前任务；只有记录中的模型与 Hook 模型一致时，才采用其中的推理等级；
3. 如果等级不可用，则在有限大小的本地转录尾部寻找 `turn_id` 和模型都与当前 Hook 一致的 `turn_context` 元数据事件；
4. 如果仍不可用，则读取本地 Codex 配置中的顶层默认值，并标记为 `default_only`；
5. 读取本地模型目录，获得等级顺序和可用模型；
6. 加载插件自带、带日期的模型化策略；
7. 注入紧凑的开发者上下文，由当前 Codex 模型结合真实任务进行判断。

状态数据库和转录格式不是稳定的公开接口。因此所有读取都采用尽力而为、只读、有限范围和开放失败原则；无法确认的值会保持未知。
