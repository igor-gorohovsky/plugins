# istack harness tree

This folder is generated from `harness/pstack/claude-code` by `node scripts/generate-istack-tree.mjs`. Do not edit it by hand.

The script runs the upstream generator, then copies the tree here and renames `pstack` to `istack` and `poteto` to `igoroh` in paths and text. URLs and the author credit keep their upstream spelling. Then it applies each `harness/istack-patches/*.patch` in name order.

To change a file here, edit it, then write the change as a patch against the generated tree in `harness/istack-patches/`. Patch paths are relative to `harness/istack/`. When an upstream change makes a patch fail, the script stops and names the patch.

After `git merge upstream/main` or an edit under `pstack/`, run `node scripts/generate-istack-tree.mjs` from the repository root and commit the result.
