# 参与贡献

修改项目时，请保持以下核心行为：

- 每次任务开始时确认当前模型和推理等级；
- 区分实际值、配置默认值和无法确认的状态；
- 根据下一阶段的真实难度给出建议；
- 以完成质量为第一约束；
- 在长线任务的自然阶段边界重新判断。

更新模型策略时，只使用当前公开来源，设置新的复查日期，并说明具体变化。测试必须使用合成数据，不得提交真实 Codex 转录、状态数据库、用户配置、私人路径、令牌或账户标识。

修改 README 时，先完成 `README.zh-CN.md` 的中文原稿，再根据中文内容同步根目录的英文 `README.md`；不要先写英文再倒译中文。

提交前运行：

```bash
python plugins/codex-reasoning-assistant/scripts/verify.py
```

# Contributing

Preserve these core behaviors when changing the project:

- confirm the active model and reasoning effort at the beginning of each task;
- distinguish actual values, configuration defaults, and unavailable state;
- recommend a configuration for the real next phase;
- keep task quality as the primary constraint;
- reassess at natural phase boundaries in long-running work.

When updating model policy, use current public sources, set a new review date, and explain the specific change. Tests must use synthetic data. Do not commit real Codex transcripts, state databases, user configuration, private paths, tokens, or account identifiers.

For README changes, update the Chinese source in `README.zh-CN.md` first, then translate it into the root English `README.md`.

Run the verification command above before submitting changes.
