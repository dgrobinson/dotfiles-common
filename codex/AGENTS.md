# Global Codex instructions (symlinked to ~/.codex/AGENTS.md).

## Spend tracking

Use the `openai-usage` wrapper for any task expected to cost more than $1.

Workflow:
- Before starting: `openai-usage --delta --label "<repo>:<task>"`
- After finishing: run the same command with the same label.
- Report the delta in the final response.

Label guidance:
- Use `<repo>:<task>` as the base label.
- If you rerun the same task, append a short run id (e.g. `<repo>:<task>:2025-02-01a`) and reuse it for both before/after calls.
