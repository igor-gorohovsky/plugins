# PR evidence

The Evidence section lets the user trust the PR without running it. The user opens the app only when they ask to, so the evidence answers what they would have checked.

**Verified** lists each behavior the ticket promises, one line each, with its proof:

- UI: before and after screenshots at the viewports the change touches (desktop, tablet, mobile), and dark mode when colors change. A behavior that plays out over time (hover, animation, loading, layout shift, a multi-step flow) gets a short recording instead, because a still cannot show that nothing jumps.
- API or worker: the request and response of the changed call, and the DB rows or log lines that show the side effect.
- LLM, prompt or model: eval scores before and after, and the cost per run and per month.
- Bug: the repro failing before the fix and passing after.

**Not verified** lists what you could not prove and why. An empty list is a claim: write it only when it is true.

Proof comes from a run on the PR's head commit, through the repo's `verify` skill when it has one. After a push that changes behavior, run it again and replace the proof. Upload images and recordings per `pr-screenshots.md` (`--content-type video/mp4` for a recording). When the evidence outgrows the body (many screens, comparisons, an eval table), put it on one evidence page and link it from the section.

When the user asks to check a change themselves, bring up the dev stack from the branch, seed a test user with realistic data, leave it running, and give them the URL and login.
