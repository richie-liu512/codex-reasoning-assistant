# Reasoning Policy / 推理策略

## English

The bundled policy turns current official guidance into a dated workflow for choosing a model and reasoning effort.

Its decision order is:

1. choose a model that can meet the quality bar;
2. choose the lowest reasoning effort that preserves the required result;
3. increase effort only when the task's ambiguity, dependency depth, validation burden, failure impact, or tool/state complexity justifies it;
4. reassess the next phase at natural boundaries;
5. use representative tasks and verification evidence before making a highest-effort setting a default.

Current model interpretation:

- GPT-5.6 Sol: frontier, ambiguous, multi-step, quality-first work;
- GPT-5.6 Terra: strong everyday work balancing intelligence and efficiency;
- GPT-5.6 Luna: clear, repeatable, high-volume work;
- GPT-5.4 mini and Spark: simple or latency-first work with clear boundaries;
- older pinned models: preserve validated settings, but compare newer models before stacking high effort when migration is allowed.

`Ultra` is treated as a special orchestration mode, not merely a larger scalar effort. It is appropriate only when the work divides cleanly and proactive subagent delegation is available and authorized.

The policy has a `review_after` date. Once stale, the hook still reports runtime facts but tells the agent to treat model-specific calibration as a weak prior until the policy is refreshed.

Official sources:

- [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- [Prompting guidance for GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)
- [Codex Manual](https://developers.openai.com/codex/codex-manual.md)

## 中文

插件自带的策略把当前官方建议整理成带日期的模型和推理等级选择流程。

它的判断顺序是：

1. 先选择能够满足质量要求的模型；
2. 再选择能够保持结果质量的最低推理等级；
3. 只有当目标歧义、依赖深度、验证负担、失败影响或工具/状态复杂度确有需要时才提高等级；
4. 在自然阶段边界重新判断下一阶段；
5. 在把最高等级设为默认值之前，先用代表性任务和验证证据证明收益。

当前模型定位：

- GPT-5.6 Sol：复杂、开放、多步骤、质量优先的前沿任务；
- GPT-5.6 Terra：兼顾智能和效率的日常工作；
- GPT-5.6 Luna：明确、重复和高容量工作；
- GPT-5.4 mini 与 Spark：边界清楚的简单任务或延迟优先工作；
- 被旧流程固定的模型：保留已经验证的等级，但在允许迁移时，不要直接堆叠高等级而忽略新模型。

`Ultra（极限）` 被视为特殊编排模式，而不是单纯更大的数值。只有当工作能够清晰拆分、系统支持主动委派，并且任务授权允许时才适合使用。

策略包含 `review_after` 日期。过期后，Hook 仍会报告实际运行信息，但会要求代理把模型化校准视为弱先验，直到策略更新。

官方来源见上方三个链接，分别对应 GPT-5.6 模型说明、GPT-5.6 Sol 提示指南和 Codex Manual（Codex 手册）。
