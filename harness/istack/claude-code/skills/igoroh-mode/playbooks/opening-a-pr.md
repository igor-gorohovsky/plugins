### Opening a PR

Invoked at the end of every other playbook.

**Worktree and branch.** Work from a git worktree off main. Subagents inherit it. Multiple `Task` calls on the same branch each get their own worktree, or `git fetch && git reset --hard origin/<branch>` between them. Dirty branch with unrelated work: patch out, fresh worktree, apply. Snarled worktree: reset from main, redo minimally. Name the branch `<ticket-id>-<slug>` in lower-case kebab case, such as `ag-241-crop-card-previews`. Without a ticket, use a plain kebab-case name.

**Commits.** Commit liberally, so that the commit history makes the review easy. A mechanical refactor never shares a commit with a behavior change. Tests go in the same commit as the code they test. Subjects are imperative, sentence case, at most 72 characters, with no type prefix and no ticket ID. Add a body only when the diff does not show the why. Before the first review, rebase into small ordered commits. After review starts, add `fixup!` commits and never rewrite pushed history, unless the user tells you to.

**PRs.** Run `/deslop` from `cursor-team-kit` over the diff before commit and `/no-comments` before review. Write titles and commit bodies with `/technical-writing` (every layer except Diátaxis, and apply the STE vocabulary rules: one word per action, keep articles, a plain verb over `-ing` where one works). Write the description with the `pr` skill. Apply `/unslop` to all of them.

**Titles.** Conventional Commits `type(scope): subject`, no trailing period. Type such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`. Scope is the area, such as `artifacts` or `igoroh-mode`. When a ticket exists, its ID starts the subject, for example `feat(artifacts): AG-241 crop card previews to the page`. The subject is short and imperative. PRs are squash-merged, so the title becomes the commit on main. Update the title when the scope of the branch changes.

**Descriptions.** Follow the `pr` skill (Summary, Evidence, Merge Danger). Put these lines above the first heading:

- `Ticket: <tracker url>` when a ticket exists. If the user gave the ticket ID but no URL, look it up in the tracker.
- `Stacked on #<n>.` for a stack child.

The body is a one-minute briefing for a reviewer who has the diff, and it becomes the squash commit body. Keep it short. Full SHAs, test-run logs, swarm or arena recitals, and file-by-file checklists stay out. Link an artifact when they matter. For a UI change, put screenshots in the Evidence section per `../references/pr-screenshots.md`. After each change to the branch, update the body, the title, and the screenshots. For a stack, update every affected layer in the same pass.

**Forge.** Resolve the forge before the first PR operation and keep that choice for create, edit, view, watch, and merge. GitHub CLI (`gh`) is the default. If `command -v origin` succeeds and Origin can resolve the repository, prefer `origin pr ...`. If Origin is absent or cannot resolve the repository, stay on `gh` and record the fallback. Do not require Graphite (`gt`).

**Built-in PR tool.** When the run provides a built-in PR tool, create, edit, retarget, and mark ready through it, never through a forge CLI. A CLI-made PR misses what the tool tracks. Use the resolved forge for everything the tool does not cover, and for every PR operation when the run has no such tool.

**Size and stacks.** One concern per PR. Move a change that is out of scope into its own PR, and do not grow the current one. Propose a stack, never start one silently, when the task splits into vertical slices that you can deliver independently. Each slice goes through all layers (data model, API, UI) and gives one complete capability. Do not split by layer, except when that layer itself carries the risk, such as a difficult migration. A diff of more than about 500 non-generated lines is a secondary signal, not the trigger. Create the stack before you write files. Use GitHub native stacks through `gh stack` and the `gh-stack` skill, per `../references/gh-stack.md`. Agents must use only the non-interactive forms. Keep raw `git rebase` out of a tracked stack, and use `gh stack rebase --upstack`. A stack is strictly linear, so parallel work needs a separate stack. Without `gh stack`, a stack is a base-branch chain. Create a child with `gh pr create --base <parent-branch>` or `origin pr create --base <parent-branch>`, and retarget with `gh pr edit <pr> --base <parent-branch>` or `origin pr edit <pr> --base <parent-branch>`. As a parent merges, move its child onto trunk per `playbooks/shipping.md` step 4.

**Readiness.** Open every PR as a draft and assign it to the user, with `gh pr create --draft --assignee @me` or, for a stack, `gh stack submit --auto`, then `gh pr edit --add-assignee @me` on each layer. Only a babysit (`playbooks/babysit.md`) or a request from the user marks a PR ready. Run `origin pr view <number>` or `gh pr view <number>` before you refer to PR status.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the phase or stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A babysit for each new PR stalls the build and spends checks on commits later waves restart. Push back when feedback drifts from intent.

A subagent that opens a PR runs `/deslop` and `/no-comments`, and posts the URL. It returns to the parent without babysitting, unless it is an Autopilot-full or Autopilot-stack owner. That owner's brief assigns the babysit loop and is the ask `playbooks/babysit.md` waits for. The owner starts the loop after its code-ready report, reports merge-ready, and is exempt from the rules here and in `playbooks/babysit.md` that hold babysitting until a whole stack is built.
