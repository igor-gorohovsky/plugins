# Route work through `/istack:igoroh-mode`

`/istack:igoroh-mode` is the front door. You give it a goal, it matches one of twenty-three playbooks, copies that playbook's steps into the todo list, and calls the other skills as the steps need them. In this page you learn what a good prompt looks like, and how little of one you actually need.

![A dispatcher pulls a switch lever to route robots on rail handcars toward lit gates, under a /igoroh-mode departure board listing BUG FIX, FEATURE, and INVESTIGATION.](./images/router.jpg)

## What happens to your prompt

```mermaid
flowchart TD
    A[Your prompt] --> B[igoroh-mode]
    B --> C[Read the Principles section]
    C --> D{Match the task}
    D -->|Read-only question| E[Investigation]
    D -->|Defect| F[Bug fix]
    D -->|New behavior| G[Feature]
    D -->|Structure only| H[Refactoring]
    D -->|Measured slowness| I[Perf issue]
    D -->|Large work or no match| J[figure-it-out]
    E --> K[Verify and report]
    F --> K
    G --> K
    H --> K
    I --> K
    J --> K
```

The diagram shows the common routes. There are also playbooks for hillclimbing a metric, diagnosing runtime symptoms and captured traces, prototypes, visual parity, authoring and evaluating skills, autonomous runs, opening a PR, babysitting a PR or stack to merge-ready, shipping a verified stack, running a PR queue or a stack on autopilot, orchestrating project-scale programs, session pickup, pausing safely, multi-phase plans, and worktree cleanup. The [playbook directory](../../skills/igoroh-mode/playbooks/) has the full set.

## Say the goal, not the ceremony

You don't write a spec. You say what's wrong or what you want, plus anything you already know that saves the agent time:

```text
/istack:igoroh-mode users get two notifications after a retry. repro first, then fix and verify.
```

That's a Bug fix prompt. "repro first" is a real constraint, not politeness, and the playbook honors it. Watch the todo list fill with the Bug fix steps. A skipped step stays visible with `skip: <reason>`.

## What goes in a prompt

A useful prompt carries up to five things, and each one fits in a sentence:

- **The goal.** Say what's wrong, or what you want.
- **The done check.** It must be able to pass or fail. "Make it better" and "work on it for an hour" aren't checks.
- **The proof you want to see.** Ask for the real command output, a video of the flow, the stored value, or a before-and-after number.
- **What you already know.** A symptom, a repro step, a log line, or a link saves the agent a search.
- **The real constraints.** "repro first", "don't change any code yet", "zero behavior change", and "let me review before proceeding" each change what the agent does.

Here's one prompt with all five:

```text
/istack:igoroh-mode the csv export drops its last row since yesterday's deploy. failing job id is 4812. repro first, then fix. done means the 60k-row fixture exports every row. show me the row counts before and after.
```

Two things are worth leaving out:

- **The how.** Say what to achieve, and leave the agent room to find a better path than the one you'd pick. The same goes for a list of skills, covered in the pitfall below.
- **Your theory of the cause, at first.** A stated guess narrows the search to wherever you pointed. Let the agent restate the problem before you share your hunch.

For a noisy report, such as a long thread or a vague bug, make the restatement the first step:

```text
/istack:igoroh-mode read this thread. restate the underlying issue in your own words, in plain english. don't change any code yet.
```

A misreading shows up in the restatement, before any code exists. Correct it there, and it costs you one message instead of one wrong fix. For the restatement alone, with no playbook, run [`/istack:in-your-own-words`](../../skills/in-your-own-words/SKILL.md). It restates what the agent thinks your goals are and what problem you're trying to solve.

When you're unsure whether a prompt is aimed right, run [`/istack:sharpen`](../../skills/sharpen/SKILL.md) on it before you send it:

```text
/istack:sharpen write a migration guide for the v2 config format.
```

The agent says what a top professional would do that you didn't ask for, the rawest material they would start from, the methods and tools they would use, and what other than you or the agent would show the result is right. Then it rewrites your prompt to ask for exactly that, deeper but not bigger, and leaves your choices open. It doesn't do the task. Read the rewrite, then send it, for example with `/istack:igoroh-mode`.

## Follow up short

When the conversation already carries the context, the prompt shrinks to almost nothing. All of these are enough:

```text
/istack:igoroh-mode do it
```

```text
continue
```

```text
keep going until done
```

Short works because the playbook holds the structure and the mode is still in context. It loads once and stays there, so you don't retype it on every turn. Start each new task with it anyway, because its pull fades over a long chat. [Set up istack](./01-setup.md#run-your-first-task) shows how to start a task.

## Switch tasks with "new task"

A long chat accumulates context from the last task. When you change subjects, say so:

```text
/istack:igoroh-mode new task. figure out why the cache entry survives logout. don't change any code yet.
```

"new task" tells `/istack:igoroh-mode` to re-match rather than continue the prior playbook. "don't change any code yet" pins this one to Investigation. Without those two phrases, a mode mid-Feature tends to treat your question as the next feature step.

## Give parallel work its own tree

If you run several workers against one repository on one computer, they will fight over the working tree, the ports, and the build output. istack handles most of that for you. Every worker that edits code gets its own git worktree, with its own branch, so it can install dependencies, run your app, and prove the change without touching your checkout.

Each worker runs as its own terminal in Herdr. Watch the sidebar for the one that needs you, read a worker's screen with `hc read <name>`, and steer it with `hc send <name> "<text>"`. istack stops the worker once it accepts the report.

A fan-out with a fixed shape runs through the `istack:panel` workflow. `/istack:swarm`, `/istack:arena`, `/istack:interrogate`, `/istack:how`, `/istack:why`, and `/istack:reflect` each fan out that way, one worker per seat in its role. `/workflows` shows the panel live while it runs.

When a specific base or location matters, say so up front:

```text
/istack:igoroh-mode new task. branch off <base> in a fresh worktree, then port the parser change there.
```

Each task in its own branch and worktree means no worker stomps another's files. The [Opening a PR playbook](../../skills/igoroh-mode/playbooks/opening-a-pr.md) already works from a worktree for code changes, so mostly you only say this when a specific base or location matters.

Worktrees accumulate, and each one costs disk. When disk gets tight, ask:

```text
/istack:igoroh-mode what's eating my disk? prune the worktrees that are safe to prune.
```

The [Worktree cleanup playbook](../../skills/igoroh-mode/playbooks/worktree-cleanup.md) classifies every worktree by merge state, uncommitted work, and which chats still touch it. It deletes only what that evidence clears and pauses for your call on anything holding uncommitted work.

## Leave it running

When you step away, say what done means and go:

```text
/istack:igoroh-mode im stepping away. keep going until the migration check reports zero old callers. log your decisions.
```

Work you'll review later routes through [`/istack:figure-it-out`](../../skills/figure-it-out/SKILL.md), which designs the run's phases and keeps a [`/istack:show-me-your-work`](../../skills/show-me-your-work/SKILL.md) decision log. [Run work while you sleep](./07-overnight.md) covers the full overnight contract.

**Pitfall:** don't enumerate skills in your prompt ("use /istack:how, then /istack:architect, then /istack:arena..."). The playbook already sequences them, and a hand-written sequence usually reorders or drops steps the playbook would have kept. Name a skill only when you want to override a specific choice.

Read [`igoroh-mode`](../../skills/igoroh-mode/SKILL.md) itself for the full routing rules.

Next: [Understand the code](./03-understand.md).
