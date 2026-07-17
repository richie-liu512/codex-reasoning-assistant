# Privacy Policy

## English

Codex Reasoning Assistant reads Codex metadata only to identify the active model and reasoning effort.

It keeps only the minimum local metadata needed to identify the current model and reasoning effort:

- the active model supplied by the current Codex hook event;
- the current Codex thread row in local read-only state databases for reasoning effort, only when its model matches the hook model;
- a bounded tail of the local transcript only when thread state is unavailable, accepting only a `turn_context` metadata event with the current `turn_id` and model;
- top-level model defaults from the local Codex configuration as an explicitly unconfirmed fallback;
- the local model catalog and the policy bundled with this plugin.

Codex sends the hook a JSON event envelope that can contain a `prompt` field. The hook deserializes that envelope, immediately returns an allowlisted metadata-only dictionary, and never accesses the prompt value during detection. It does not output, save, log, quote, summarize, transmit, or otherwise reuse prompt content.

It does not transmit data, call an API, invoke another model, create telemetry, or write an audit log.

The hook output contains model and effort metadata, policy labels, and instructions. It excludes session identifiers, transcript paths, database paths, configuration paths, user names, and prompt text.

Uninstalling the plugin removes its code. The plugin does not create a separate data store that needs cleanup.

## 中文

Codex 智能推理助手只读取确认当前模型和推理等级所需的 Codex 元数据。

它只保留确认当前模型和推理等级所必需的最少本地元数据：

- 当前 Codex Hook 事件直接提供的活动模型；
- 本地只读状态数据库中用于确认推理等级的当前任务记录，并且只有记录模型与 Hook 模型一致时才采用；
- 只有在任务状态不可用时，才读取有限大小的本地转录尾部，并且只接受 `turn_id` 和模型都与当前轮一致的 `turn_context` 元数据事件；
- 作为明确未确认的后备信息，读取本地 Codex 配置中的顶层模型默认值；
- 本地模型目录和插件自带的策略文件。

Codex 交给 Hook 的 JSON 事件信封可能包含 `prompt` 字段。Hook 会反序列化这个信封，随后立刻只返回白名单中的元数据字典，并且在探测过程中不访问提示词的值。它不会输出、保存、记录、引用、总结、传输或以其他方式复用提示词正文。

它不会传输数据、调用接口、启动另一个模型、创建遥测或写入审计日志。

Hook 输出只包含模型和等级元数据、策略标签和行为指令，不包含任务标识、转录路径、数据库路径、配置路径、用户名或提示词正文。

卸载插件即可移除其代码。本插件不会创建需要另外清理的数据存储。
