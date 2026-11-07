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

A panel is several workers on one task shape, such as one per seat, slice, or angle, then optionally a judge or a synthesizer over their reports. Run it with the steps above:

1. Make a run folder, `~/.cache/istack/runs/<skill>-<slug>`. Each worker's brief and report go to `<dir>/<name>.brief.md` and `<dir>/<name>.md`.
2. Start every worker before you wait on any. Names are unique, lowercase, and at most 32 characters.
3. Wait on each worker in turn. Retry a worker once, as a fresh worker, when it ends `no-report` or `exited`. A worker still without a report is a gap, and your reply names it.
4. **Verify**, when the skill asks for it. For each report, rerun every finding's command in that worker's `--cwd`. Keep a finding only when the output you see shows the failure and the failure breaks the stated intent.
5. **Judge**, when the skill asks for it. Start one more worker on the judge role, at the first seat whose family differs from yours. When you run on Claude, that is the first pi or Codex seat. When every seat is your family, skip the judge and say so. Its brief lists the report paths and the gaps.
6. **Synthesize**, when the skill asks for it. Start one more worker on the synthesizer role. Its brief lists the report paths and the gaps.
7. Stop every worker once you accept its report.
