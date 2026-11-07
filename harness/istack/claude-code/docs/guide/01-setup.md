# Set up istack

In this page you install the plugin, pick which models istack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

istack runs in Claude Code, and it runs every worker as a Herdr terminal. Start Claude Code from inside Herdr, so `HC_TERMINAL_ID` is set. Without it no worker can start, and istack tells you so. The [workers doc](../workers.md) covers how workers run.

Install from the local marketplace at `~/projects/plugins`:

```text
/plugin marketplace add ~/projects/plugins
/plugin install istack@igor-plugins
```

Claude Code prefixes plugin commands with the plugin name, so each istack skill runs as `/istack:<name>`, such as `/istack:setup-istack`.

## Pick your models

Run:

```text
/istack:setup-istack
```

[`/istack:setup-istack`](../../skills/setup-istack/SKILL.md) links `istack-worker` onto your PATH, detects the harnesses and models this machine can run, asks for a reasoning budget, shows you each role (code workers, judgment, the review panels), and asks what you want. Answer the questions. It writes `~/.claude/rules/istack-models.md`, a small rule that every istack skill and every worker reads.

A seat is one harness, one model, and one effort. The rule writes a seat as `<opus|sonnet|haiku|fable> <effort>`, `pi <provider>/<model> <effort>`, `codex <model> <effort>`, or `inherit-parent`. A worker runs in a Herdr terminal on that seat's harness, so one panel can mix Claude Code, pi, and Codex.

The budget sets the effort on each seat. `unlimited` is `max`, `large` is `xhigh`, `medium` is `high`, and `small` is `medium`. A higher budget thinks longer and spends more tokens.

Setup writes a line for every role. A role with no line keeps `istack-worker`'s own default, so deleting a line restores that default. A rerun keeps any seat you changed. When a default changes in a later version, a rule written before the change still pins the old default, so delete that role's line, or delete the file, then run setup again.

Set a role to `inherit-parent` to run it on the chat's own model. For a panel role the value is a list, and one worker runs per seat, so the list length sets the panel size. `arena runners`, `architect runners`, and `interrogate reviewers` are panel roles, and each keeps seats from at least two harness families so the panel stays a real second opinion. Run `istack-worker roles` at any time to see every role with the command each seat runs.

## Accept the verification offers, or don't

At the end of setup, `/istack:setup-istack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/istack:create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.claude/skills/verify-<app>/`, a project-local skill that teaches a worker to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/istack:create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to istack, say yes. A worker that can check its own work keeps going until the check passes. A worker that can't hands every result back to you to check by hand. Of everything in this guide, the verification skill pays off the most.

Then setup offers once to generate a formal verification skill with [`/istack:create-formal-verification-skill`](../../skills/create-formal-verification-skill/SKILL.md), unless the project already has one. Tests check the cases someone thought to write. A formal verification skill checks one key property of your code, such as "a job never runs twice at once", in every case within a stated scope. Say yes when your code has concurrency, retries, a state machine, or a parser, where a bug is costly and tests rarely reach the case that breaks. Otherwise say no, and run it later if that changes. [Verify and ship](./06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill) covers it.

After setup, start a new chat. The model rule applies to new sessions.

## Keep the cost in check

istack spends extra tokens on workers and review panels. That's the price of the rigor. To spend fewer:

- Rerun `/istack:setup-istack` and pick a smaller reasoning budget, or cheaper seats such as a pi seat on a cheap model. A strong model in the main chat with cheaper, faster workers in the code roles is a good split.
- Set a role to `inherit-parent` so it runs on the chat's own model.
- Shorten a panel list. Each seat runs one worker.
- Save `/istack:igoroh-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/istack:igoroh-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/istack:igoroh-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

A step that fans out starts workers. Each worker opens as a terminal in Herdr, so you can watch it in the sidebar, read its screen with `hc read <name>`, and steer it with `hc send <name> "<text>"`. You don't sit and wait on it. You keep working, and istack notes you when the worker's turn ends.

From here you can type normal follow-ups. `/istack:igoroh-mode` loads into the chat once and stays in context, but its pull fades over a long chat, so start each new task with it. A worker reads the mode itself, because istack puts the mode's path in its brief.

Next: [Route work through `/istack:igoroh-mode`](./02-igoroh-mode.md).
