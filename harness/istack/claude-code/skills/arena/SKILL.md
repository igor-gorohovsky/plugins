---
name: arena
description: "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
disable-model-invocation: true
---

# Arena

Workers run per [the workers doc](../../docs/workers.md). Read it once per session before you start one.

Open a todolist with one entry per phase (Frame, Fan out and cross-judge, Pick, Graft, Verify) before launching anything.

## Phase A: Frame

Every candidate gets the same prompt, so the prompt is the contract.

1. State the artifact each candidate is producing.
2. Derive the rubric, 3-6 concrete gradeable criteria for what success looks like on *this* task. It is the picker's tool in Phase C. Candidates only see the task.
3. Pick the runners. Run one worker per seat of the `arena runners` role. Add workers on a seat when the arena covers more design directions, or the same seat N times when the work is generation-bound rather than judgment-sensitive.
4. Give each candidate its own output location (a git worktree for code, otherwise `<dir>/candidate-<n>/`), per the **separate-before-serializing-shared-state** principle skill.

## Phase B: Fan out and cross-judge

Run a panel with one worker per candidate. Each brief carries the task, the path to the shared grounding, the candidate's own output path, and instructions to produce the artifact and a short rationale naming the alternatives it considered and what it rejected. Write the rubric to `<dir>/rubric.md`.

Then start a judge on the `arena cross-judge pool` role with this brief: score each candidate against the rubric at `<dir>/rubric.md` criterion by criterion, and recommend a base with a rationale. The judge runs at the first seat whose family differs from yours, so it never shares the picker's bias. When every seat is your family, skip the judge. Pick the base alone in Phase C and say so.

A candidate still without a report after its retry is a dropout. Proceed with N-1 and note it.

## Phase C: Pick a base

Read every candidate end to end before picking. Score each against the rubric criterion by criterion, not on holistic feel, and compare with the judge's report when Phase B ran one. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API, per the Laziness Protocol.

## Phase D: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per the **redesign-from-first-principles** principle skill, so the result stays coherent under one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase E: Verify

Verify the synthesized artifact like any other output, per the **prove-it-works** principle skill. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase D). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, the judge's verdict or that Phase B skipped the judge, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result.
