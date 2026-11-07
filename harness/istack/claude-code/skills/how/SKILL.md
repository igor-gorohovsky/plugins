---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
disable-model-invocation: true
---

# How

Workers run per [the workers doc](../../docs/workers.md). Read it once per session before you start one.

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Explorers run on the `how explorer` role and the explainer on the `how explainer` role. Every brief says the worker reads and runs code but edits no file. The prompt templates are in this skill's `references/`. Give workers their absolute paths.

## 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. Start one explainer worker that explores and explains in one pass, briefed with `references/explainer-prompt.md` without the explorer-findings section. Go to step 4.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): go to step 2.

When in doubt, take the simple path.

## 2. Explore (complex only)

Decompose the question into 2 to 4 angles, each a distinct slice of the subsystem. Run a panel with one explorer per angle, each briefed with `references/explorer-prompt.md` and its angle filled in.

## 3. Synthesize (complex only)

Once every explorer has reported, start one worker on the `how explainer` role. Its brief points to `references/explainer-prompt.md` and carries the question and the explorers' report paths.

## 4. Present

Read the explainer's report and present it. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## Output format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
