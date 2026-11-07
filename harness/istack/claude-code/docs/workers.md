# Workers

istack runs every subagent as a **worker**: an interactive agent (Claude Code, pi, or Codex) in its own Herdr terminal, started by `istack-worker`. The user watches and steers workers from Herdr's sidebar, so istack never uses the Agent tool. When `HC_TERMINAL_ID` is unset or `istack-worker` cannot start a worker, stop and tell the user.

## Roles

`~/.claude/rules/istack-models.md` maps each role to one or more seats, written `<opus|sonnet|haiku|fable> <effort>`, `pi <provider/model> <effort>`, `codex <model> <effort>`, or `inherit-parent`. `istack-worker roles` prints every role with the command each seat runs. A panel role (`arena runners`, `architect runners`, `interrogate reviewers`) runs one worker per seat, picked with `--seat N` from 0. `/istack:setup-istack` writes the file.

Pick the effort for the job with `--effort`. Raise it one step for the hardest or subtlest work, and lower it for routine work. Keep the seat's harness and model, so a mixed panel stays mixed.

## One worker

1. Write the brief to a file. It is the worker's whole context. It opens with the user's goal in your words, then the scope, the done condition, how to verify, and what the report contains.
   - A code delegate's brief starts with: `Read <absolute path of igoroh-mode's SKILL.md> in full before any work.`
   - A worker that edits code gets its own git worktree as `--cwd`.
2. Start it:
   `istack-worker start --role <role> [--seat N] --name <name> --cwd <dir> --brief <file> --report <file>`
   - Add `--claude` when the worker reads MCP data (Slack, Notion, Sembly, Sentry) or a session transcript or memory. pi has no such MCP servers, and that data stays on Claude.
3. Keep working. hc notes you when the worker's turn ends (`<hc from="t7 name">`). `istack-worker wait --name <name> --report <file>` blocks for up to 9 minutes and returns `done`, `no-report`, `blocked`, `error`, `exited`, or `working`.
   - `blocked` means a person is needed: read the screen with `hc read <name>` and ask the user.
4. Read the report file, not the screen. You own the result. Check the claims and the diff before you relay them.
5. Steer a running worker with `hc send <name> "<text>"`. Once you accept the report, run `istack-worker stop <name>`.

A follow-up or retry goes to a fresh worker whose brief carries the original brief, every later directive, and the prior report. Message an existing worker only when the work needs state that lives in it: its uncommitted changes, or a process it still runs.

## Panels

A fan-out with a fixed shape runs through the `istack:panel` workflow. A skill that says "run a panel" authorizes the Workflow tool call. Call it with `name: "istack:panel"` and these `args`:

| Arg | Value |
| --- | --- |
| `dir` | `~/.cache/istack/runs/<skill>-<slug>`. Create it. Each worker's report lands at `<dir>/<name>.md`. |
| `cwd` | The default working directory for workers. |
| `roles` | The JSON object that `istack-worker roles --json` prints. |
| `workers` | `[{name, role, seat?, cwd?, brief? or briefText?, effort?, claude?}]`. Names are unique, lowercase, and 32 characters at most. |
| `verify` | Optional. `{instructions}`. Each report's findings are rerun in its worker's `cwd`, and only reproduced ones are kept. |
| `judge` | Optional. `{role, briefText}`. One judge from the first seat of another family than `parentFamily` (default `claude`). |
| `synthesize` | Optional. `{role, briefText, claude?}`. One synthesizer over every report. |

The judge and the synthesizer get the report paths appended to their `briefText`. A Claude seat runs them as workflow agents, and any other seat runs them as workers. The workflow retries each worker once when it ends without a report. It returns `{workers, gaps, findings, judge, synthesis}` with report paths. Read the files you need.

When the Workflow tool is missing, or `istack:panel` is not found, do the same steps yourself: start each worker, wait for all of them, then start the judge or synthesizer as one more worker. Say so in your reply.
