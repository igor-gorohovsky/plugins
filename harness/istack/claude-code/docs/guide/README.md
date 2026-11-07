# The istack guide

istack works best when you stop micromanaging the agent. You describe what you want and how you'll know it's done. `/istack:igoroh-mode` picks the playbook, runs the other skills as the steps need them, and shows you the evidence. When a step fans out, it starts workers in Herdr terminals, so you can watch and steer them from the sidebar. This guide teaches that habit with realistic prompts.

Here's what you'll learn:

1. [Set up istack](./01-setup.md). Install the plugin in Claude Code inside Herdr, and pick the harness and model for each role.
2. [Route work through `/istack:igoroh-mode`](./02-igoroh-mode.md). Give it a goal and watch it pick a playbook.
3. [Understand the code](./03-understand.md). A read-only investigation, then `/istack:how`, `/istack:why`, `/istack:teach`, and `/istack:recall` before you edit anything.
4. [Design the change](./04-design.md). `/istack:architect`, `/istack:arena`, `/istack:swarm`, `/istack:interrogate`, prototypes, and plans before code locks in a shape.
5. [Build and clean the change](./05-build-and-clean.md). The build playbooks, `/istack:tdd`, `/istack:unslop`, and `/istack:no-comments`.
6. [Verify and ship](./06-verify-and-ship.md). Prove behavior on the real app, formally verify what tests rarely reach, vet numbers with `/istack:benchmark-checklist`, then open a focused PR and drive it to merged.
7. [Run work while you sleep](./07-overnight.md). Trust before loops, an overnight contract, a decision log you can audit, and the Orchestrate playbook for a program that spans days and many PRs.
8. [Steer with principle names](./08-principles.md). The 24 names that redirect an agent mid-task.
9. [Make it yours](./09-make-it-yours.md). Your own mode, `/istack:correct` for repeated mistakes, and how to test a skill change.
10. [Recipes and pitfalls](./10-recipes-and-pitfalls.md). Prompts to copy and mistakes to skip.

Read the pages in order the first time. After that, each page stands alone.

Every istack skill takes the plugin prefix, so you type `/istack:igoroh-mode` and not `/igoroh-mode`. Claude Code built-ins, such as `/loop`, `/simplify`, and `/workflows`, keep their own names.

When you're stuck, or can't tell which skill fits, type [`/istack:igoroh-help`](../../skills/igoroh-help/SKILL.md) with your question:

```text
/istack:igoroh-help which skill should i use to review this branch?
```

It answers, hands you a prompt to send, and links the skill or guide page the answer came from. It doesn't start the work, because a istack run spends real tokens, so you send the prompt when you're ready. It runs only when you type it.

## If you only remember one thing

Give the agent a goal and a way to check it, in your own words:

```text
/istack:igoroh-mode the export writes duplicate rows when a retry lands mid-run. repro first, then fix and verify.
```

You don't need to name a playbook or list skills. "repro first" and a checkable outcome are all the routing signal `/istack:igoroh-mode` needs. It matches the Bug fix playbook, copies the steps into a todo list, and calls the right skills as each step fires.

Next: [Set up istack](./01-setup.md).
