# gh stack cheat sheet

GitHub native stacked PRs. CLI is `gh stack`, a `gh` extension.

The official `gh-stack` skill (shipped by GitHub in `github/gh-stack` under `skills/`) is the
authoritative reference and carries far more detail. This page is the minimum needed to work a
stack without it.

## Setup

```sh
gh extension install github/gh-stack
git config rerere.enabled true         # remember conflict resolutions
git config remote.pushDefault origin   # required when the repo has more than one remote
```

## Reading a stack

`gh stack` prints trunk-first, left to right — left is the bottom, right is the top:

```
(main) <- auth <- api <- frontend
```

`auth` is based on `main` and merges first. `up` moves away from trunk, `down` moves toward it.

## Creating a stack

```sh
gh stack init auth              # create the stack, check out its first branch
git add ... && git commit -m "Add auth middleware"
gh stack add api                # next layer, branched from the current one
git add ... && git commit -m "Add API routes"
gh stack submit --auto          # push every branch and open draft PRs
```

Branch names are taken verbatim. Add `--open` to `submit` for review-ready PRs instead of drafts.

## Changing a lower layer

```sh
gh stack down                   # or: gh stack checkout api
git add ... && git commit -m "Fix the thing"
gh stack rebase --upstack       # replay every branch above onto the change
gh stack top
gh stack push
```

## Staying in sync, merging

```sh
gh stack sync [--prune]         # fetch, reconcile, rebase, push, refresh PR state
gh stack merge <pr> --yes       # that PR plus every unmerged PR below it
```

`merge` is all-or-nothing: if any PR in the scoped set cannot merge, none do.

## Driving it from an agent

These are the rules that make the difference between working and hanging:

| Always | Never | Why |
| --- | --- | --- |
| `gh stack view --json` | `gh stack view` | opens a TUI under a PTY |
| `gh stack submit --auto` | `gh stack submit` | prompts per new PR |
| `gh stack merge <t> --yes` | `gh pr merge` | `gh pr merge` cannot merge a stack |
| `gh stack init <branch>` | `gh stack init` | prompts for names |
| `gh stack add <branch>` | `gh stack add` | prompts, and fails even when piped |
| `gh stack up` / `down` / `top` / `bottom` | `gh stack switch` | `switch` is menu-only |
| — | `gh stack modify` | TUI-only; restructure with `unstack` then `init` |

`view --json` writes JSON to stdout and status text to stderr — parse stdout, branch on exit codes.

Exit codes: `0` success, `2` not in a stack, `3` rebase conflict (resolve, `git add`, then
`gh stack rebase --continue`), `4` GitHub API failure, `7` rebase already in progress, `8` stack
file locked (retry after ~5s), `9` stacked PRs not enabled on the repository.

## PR bodies

`gh stack submit` auto-generates titles and bodies. They will not match `playbooks/opening-a-pr.md`.
Rewrite each one with `gh pr edit` after you submit.
