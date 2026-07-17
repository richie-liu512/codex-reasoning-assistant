# Security Policy

## English

This plugin executes a local command hook before each user turn. Codex requires users to review and trust non-managed hooks; do not bypass that review for an unverified checkout.

The hook is fail-open. Detection errors never block the user's task and never authorize a model switch or configuration write.

Supported security reports include unintended data collection, command injection, unsafe path handling, incorrect trust-status reporting, or a detection path that writes to Codex state. Report vulnerabilities privately through GitHub Security Advisories for this repository. Do not include real prompts, tokens, credentials, or private transcripts in a report.

## 中文

本插件会在每次用户提交任务前执行一个本地命令 Hook。Codex 会要求用户检查并信任非托管 Hook；对于未经核验的副本，不要绕过这一步。

Hook 采用开放失败。读取错误不会阻止用户任务，也不会因此获得切换模型或写入配置的权限。

可报告的问题包括意外收集数据、命令注入、不安全的路径处理、错误标注真实性，或者任何会写入 Codex 状态的探测路径。请通过本仓库的 GitHub Security Advisories 私下报告漏洞。报告中不要附带真实提示词、令牌、凭据或私人转录。
