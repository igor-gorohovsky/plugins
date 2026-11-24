# istack harness tree

This folder is generated from `harness/pstack/claude-code` by `node scripts/generate-istack-tree.mjs`. Do not edit it by hand.

The script runs the upstream generator, then copies the tree here and renames `pstack` to `istack` and `poteto` to `igoroh` in paths and text. URLs and the author credit keep their upstream spelling. Then it applies istack's own changes from `harness/istack-patches`:

- `patches/<path>.patch` changes or deletes the upstream file `<path>`.
- `files/<path>` is a file with no upstream source, such as `claude-code/scripts/istack-worker`.

Paths are relative to `harness/istack/`. To change istack, edit this folder, then run `node scripts/generate-istack-tree.mjs --record`. It rewrites `harness/istack-patches` from this folder, and `node scripts/generate-istack-tree.mjs --check` then passes.

After `git merge upstream/main` or an edit under `pstack/`, run `node scripts/generate-istack-tree.mjs` from the repository root. When a patch no longer applies, the script merges the upstream change into istack's version of the file. A clean merge rewrites the patch. A conflict leaves markers in the file here and stops the script: resolve them, run `node scripts/generate-istack-tree.mjs --record`, and commit the result.
