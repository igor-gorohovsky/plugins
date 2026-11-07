# Design before you write code

One attempt at a hard design locks in the first shape the model thought of. `/istack:architect` settles types and boundaries before implementation. `/istack:arena` runs several attempts at the same brief and merges the best parts. `/istack:interrogate` has other models try to break the result. When the job is coverage rather than design synthesis, `/istack:swarm` fans out slices or races and aggregates their results.

The two most common design mistakes are taking the agent's first design and polishing a plan that no code has tested. This page fixes both. You plan through code. Prototypes answer the open questions, a README or tutorial sets the target, and the written plan comes last.

Every fan-out on this page runs the same way. Each worker is an agent in its own Herdr terminal, started through the `istack:panel` workflow and shown live in `/workflows`. One worker per seat of the role, so a mixed panel means mixed model families. You watch them in Herdr's sidebar and steer one with `hc send <name> "<text>"`. The [workers doc](../../docs/workers.md) has the mechanics.

![Three robots draft competing bridge models at their own tables under /architect, /arena, and /interrogate panels, while a judge robot with a clipboard inspects skeptically.](./images/design.jpg)

## Settle the shape with `/istack:architect`

```text
/istack:architect design the import pipeline before writing any code. i care most about how callers use it.
```

[`/istack:architect`](../../skills/architect/SKILL.md) grounds itself first, running `/istack:how` over the code the design touches and `/istack:why` when it moves ownership or layers. Then it runs `/istack:arena` to produce competing design sketches, with the caller's usage written first in each, followed by types, signatures, and a module map.

By default it proceeds straight from the synthesized design into implementation. If you want to see the design first, say so:

```text
/istack:architect with checkpoint. stop and show me before implementing.
```

The design isn't sacred once code starts. If implementation shows the same workaround in unrelated places, or types that only compile with `any` or forced casts, `/istack:architect` treats that as proof the design is wrong. It scraps the sketch and starts over instead of patching around it.

## Fan out attempts with `/istack:arena`

```text
/istack:arena take my prompt to the arena verbatim. i want to compare their proposals with yours.
```

[`/istack:arena`](../../skills/arena/SKILL.md) is the general tool underneath. N workers attempt the same design or code brief in parallel, each in its own git worktree, so no two of them edit the same files. A read-only judge from a different model family scores every candidate against a rubric. When no seat from another family can run, the panel skips the judge and you pick the base yourself. You read each candidate end to end, pick a base, graft in the best ideas from the losers, and verify the result.

```mermaid
flowchart LR
    A[One task] --> B[istack:panel fan-out]
    B --> C[Candidate 1]
    B --> D[Candidate 2]
    B --> E[Candidate N]
    C --> F[Cross-judge]
    D --> F
    E --> F
    F --> G[Pick a base]
    G --> H[Graft the best parts]
    H --> I[Verify]
```

The panel comes from your [`/istack:setup-istack`](../../skills/setup-istack/SKILL.md) configuration, which runs one worker per seat of the `arena runners` role. `istack-worker roles` prints the seats, and you can adjust them per task. Ask for more candidates when the decision matters, fewer when it doesn't:

```text
/istack:arena this, 5 candidates. the cache key format is expensive to change later.
```

## Cover slices and races with `/istack:swarm`

```text
/istack:swarm check every package under packages/ against its check.sh. one worker per package. one report.
```

[`/istack:swarm`](../../skills/swarm/SKILL.md) fans N workers across independent slices, coverage matrices, gauntlet lanes, exploration partitions, or declared race arms. Each worker gets its own scope, its own git worktree when it writes, and its own check, then reports `PASS`, `ISSUES`, or `BLOCKED`. The panel waits for every worker and returns one compact report with any gaps or dropouts.

Reach for it when parallelism buys coverage or lets independent checks race. `/istack:arena` gives every worker the same design or code brief, then picks a base and grafts the best parts. `/istack:swarm` covers slices or runs a race with a selection rule declared up front. It does not use the base-selection and grafting ceremony.

## Break it with `/istack:interrogate`

```text
/istack:interrogate the whole branch, but skeptically. no nitpicks unless it's an actual bug or regression.
```

[`/istack:interrogate`](../../skills/interrogate/SKILL.md) gives the change and its intent to adversaries on the configured models, one worker per seat in its own worktree at the scope's head, and each tries to break it with a run against the real code. Adversaries find different failures. A finding survives only when the panel reruns its command and sees a failure that breaks the intent. The report lists every verified finding with the adversaries that found it, then what each adversary dropped and why, and applies nothing.

Read the Dropped list too. You can override the verdict.

## Prototype instead of debating

Never take the first design. Ask for a few, and pick from evidence you can see:

```text
/istack:igoroh-mode prototype a few options for the new dropdown menu. take screenshots or videos for me to compare.
```

The [Prototype playbook](../../skills/igoroh-mode/playbooks/prototype.md) builds throwaway sketches in a scratch directory, puts the variants behind one switcher, drives each one, and captures screenshots or timings. It also works for behavior and algorithms, not just UI. Prototypes are planning with code. They let the agent answer its own open questions by running something instead of asking you, and they leave room for an option you wouldn't have thought of.

The same idea scales up to a real design. Pair `/istack:architect` with prototypes and keep a review gate:

```text
/istack:igoroh-mode we need rate limiting for external webhooks. /istack:architect it first, and answer open questions with prototypes. let me review before proceeding.
```

Don't spend adversaries on an abstract plan. `/istack:interrogate` drops every finding a run does not prove, so a plan with no code behind it gives them little to break. Let prototypes settle the questions, then review what got built.

## Write the README first for shared code

For a package or API that other code will use, start with the doc a user would read:

```text
/istack:igoroh-mode write a tutorial for how i would use the new config package first. then /istack:teach me why it beats the current one.
```

Writing the tutorial first forces the caller's view. You describe the API to a hypothetical user and work back to the implementation. The doc also becomes a concrete target the agent checks its own work against. Name [`/istack:technical-writing`](../../skills/technical-writing/SKILL.md) when the doc itself matters, so a tutorial stays a tutorial instead of drifting into reference and explanation at once.

## Plan after the design settles

istack has no planning skill, on purpose. When you do want a written plan, ask for it once the design is settled:

```text
/istack:igoroh-mode turn this design into a plan. small verifiable PRs, each with its own verification steps.
```

The [Multi-phase plan playbook](../../skills/igoroh-mode/playbooks/multi-phase-plan.md) settles any remaining open questions by prototype, then writes one section per PR, each ending in proof that the change works. A passing test suite alone doesn't count as that proof. The plan is the deliverable. The playbook doesn't implement it, and it names which execution playbook should run it next.

For a migration, state the bar in the prompt:

```text
/istack:igoroh-mode plan the migration of our ui library to the new styling system. small verifiable PRs, each with visual regression checks. the result must match the original exactly, bugs included.
```

"bugs included" keeps the migration from quietly fixing things on the way, which would make the old and new output impossible to compare. For a project that spans many days, you can commit the plan to the repo for a while so other agents see the work in progress. Delete it when the work lands.

## How much design work does a task deserve?

You might be wondering whether every change needs this. No. Most changes need none of it. A rough ladder:

- A small, finished change you're unsure about needs `/istack:interrogate` alone.
- A change that crosses function boundaries or moves ownership earns `/istack:architect`, which brings `/istack:arena` with it.
- A standalone decision where independent attempts would help, like naming, formats, or an algorithm, is `/istack:arena` directly.
- A coverage matrix, set of parallel checks, or race with declared arms is `/istack:swarm`.
- An open question you could answer by running something, like a layout, a timing, or an approach, gets a prototype, not a debate.
- A contested design that's expensive to reverse gets `/istack:architect`, then `/istack:interrogate` before shipping.
- Work that spans several PRs gets a plan, written after the design settles.

`/istack:igoroh-mode` already applies this ladder. Boundary-crossing work triggers `/istack:architect` on its own, so you reach for these directly mainly when you want more or less scrutiny than the default.

Next: [Build and clean the change](./05-build-and-clean.md).
