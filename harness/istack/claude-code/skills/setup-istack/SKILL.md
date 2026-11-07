---
name: setup-istack
description: Configure which harness and model each istack role runs on, and at what reasoning budget. Writes ~/.claude/rules/istack-models.md and installs istack-worker. Use for /setup-istack, "configure istack models", "istack budget", or changing istack's model choices.
---

# Setup istack

istack runs its workers in Herdr, per [the workers doc](../../docs/workers.md). This skill writes the role table those workers read, `~/.claude/rules/istack-models.md`, and puts `istack-worker` on the PATH.

## Steps

### 1. Install and check

1. Link the script: `ln -sf <istack>/scripts/istack-worker ~/.local/bin/istack-worker`, where `<istack>` is the folder that holds this skill's `skills/` folder. Check `istack-worker --help` runs.
2. Check Herdr: `HC_TERMINAL_ID` is set and `hc ls` succeeds. If not, tell the user that istack needs Claude Code running inside Herdr, and finish the remaining steps anyway.

### 2. Detect the seats

A seat is one harness, model, and effort. Collect the ones this machine can run:

- **Claude Code**: `opus`, `sonnet`, `haiku`, and `fable`, each with an effort from `low`, `medium`, `high`, `xhigh`, `max`.
- **pi**: `pi --list-models` lists `provider model` pairs. Write a seat as `pi <provider>/<model> <effort>`.
- **Codex**: when `codex` is on the PATH, ask the user which models their account has. Write a seat as `codex <model> <effort>`.
- `inherit-parent` (Claude Code on its default model) is always valid.

Never write a seat you have not confirmed this machine can run.

### 3. Load the current table

`istack-worker roles` prints every role with its current seats: lines from `~/.claude/rules/istack-models.md`, and the script's defaults for roles the file lacks. Treat the file's `# budget` line as the current budget. Drop a line whose role the script does not know, and list it in step 4.

### 4. Budget, map, and confirm

**(a) Ask for a budget** with `AskUserQuestion`. Offer these labels, and name the current budget when the file records one:

- `unlimited — max reasoning`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Set the effort, the last token of every seat, to `max`, `xhigh`, `high`, or `medium`. `inherit-parent` does not change.

**(c) Show the roles and confirm.** Show every role with its seats. Ask whether to accept as-is or change specific roles, offering the detected seats. A panel role (`arena runners`, `architect runners`, `interrogate reviewers`) runs one worker per seat, so its list length sets the fan-out. Keep at least two families in a panel role so the panel stays diverse. `arena cross-judge pool` is ordered by preference, and its judge is the first seat whose family differs from the parent chat's. Workers that read MCP data or transcripts move to Claude Code on their own (`--claude`), so a pi seat is fine for every role.

### 5. Write the file

Overwrite `~/.claude/rules/istack-models.md` whole, with no frontmatter. Claude Code loads it into every session, so keep it to these lines:

```
# istack roles: `role: seat[, seat]`. A seat is `<opus|sonnet|haiku|fable> <effort>`, `pi <provider/model> <effort>`, `codex <model> <effort>`, or `inherit-parent`. Workers start through istack-worker, per the istack workers doc.
# budget: medium (high)
feature, refactoring: pi opencode-go/deepseek-v4.1-flash high
...one line per role...
```

Then run `istack-worker roles`. It fails on any seat it cannot read. Fix the line and rerun until it prints every role.

### 6. Confirm

Tell the user the file was written, that new sessions load it, and that rerunning this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /istack:create-verification-skill." On yes, run the **create-verification-skill** skill. On no, move on without pushing.

### 8. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /istack:create-formal-verification-skill." On yes, run the **create-formal-verification-skill** skill. On no, move on without pushing.
