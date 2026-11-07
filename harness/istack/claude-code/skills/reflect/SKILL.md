---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Workers run per [the workers doc](../../docs/workers.md). Read it once per session before you start one.

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript in `~/.claude/projects/<slug>/`, where the slug is the workspace path with each `/` and `.` changed to `-`. Do not glob across other project folders. That reads private chats from unrelated projects.

```bash
ls -t ~/.claude/projects/<slug>/*.jsonl | head -5
```

The newest file is usually this session. Confirm by finding the conversation's opening user prompt in it. Its `<session>/subagents/` folder holds subagent transcripts. If none matches, write a tight digest of the session to a file and pass that instead.

## 2. Run three reviewers and a synthesizer

Run a panel with three reviewers, all with `claude: true`. They read the session transcript, which stays on Claude, and they need the MCP servers to look up the tickets, chat threads, and traces the transcript references.

| Lens | Role | Prompt template |
|---|---|---|
| Judgment | `reflect judgment` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `references/tooling-reviewer.md` |
| Divergent | `reflect divergent` | `references/divergent-reviewer.md` |

Each brief is its template verbatim, with the transcript path or digest substituted where marked.

## 3. Synthesize

In the same panel, set `synthesize` to the `reflect synthesizer` role with `claude: true` and a `briefText` that points to `references/synthesizer.md`. The panel appends the reviewers' report paths. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Only the Accepted list waits for approval.

Never edit a skill under `~/.claude/plugins/cache/`. Before approval, show its destination, `.claude/skills/<skill>/` or `~/.claude/skills/<skill>/`. After approval, copy the skill folder there and edit the copy. A plugin loaded from a local checkout, as istack is, gets edited in that checkout and committed there. Never open a PR or push.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): write it per the `writing-for-agents` skill, then test it per the Eval playbook.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): run the `anthropic-skills:skill-creator` skill's description-optimization loop.
- `new skill: <kebab-name>`: create it with the `anthropic-skills:skill-creator` skill, written per `writing-for-agents`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
