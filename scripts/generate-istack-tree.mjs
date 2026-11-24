#!/usr/bin/env node

// Builds harness/istack/claude-code: the Claude Code tree of pstack, renamed to istack and igoroh-*.
// pstack/ and harness/pstack/ stay identical to upstream, so `git merge upstream/main` touches only them.
// istack's own changes live in harness/istack-patches: one patch per changed upstream file under patches/,
// and the files with no upstream source under files/. --record derives both from harness/istack.
// After a merge or an edit under pstack/, run this script from the repository root and commit the result.

import { execFileSync, spawnSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, posix, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const UPSTREAM_GENERATOR = join(ROOT, "scripts", "generate-pstack-harness-trees.mjs");
const SOURCE = join(ROOT, "harness", "pstack", "claude-code");
const OUT = join(ROOT, "harness", "istack");
const PATCHES = join(ROOT, "harness", "istack-patches", "patches");
const FILES = join(ROOT, "harness", "istack-patches", "files");
const TREE = "claude-code";
const COMMAND = "node scripts/generate-istack-tree.mjs";
// Edits made in harness/istack before an upstream change can be recorded only once harness/istack has that change.
const SET_EDITS_ASIDE = `set them aside with \`git stash push -- harness/istack\`, run \`${COMMAND}\` and commit, then run \`git stash pop\` and \`${COMMAND} --record\`.`;

// Order matters: each pair runs on the text left by the pairs before it.
const RENAMES = [
  [/pstack/g, "istack"],
  [/Pstack/g, "Istack"],
  [/poteto/g, "igoroh"],
  [/Poteto/g, "Igoroh"],
];
// Text that keeps its original spelling: URLs (links to upstream files) and the author credit.
const PROTECTED = /https?:\/\/[^\s)>`"'\]]+|\[poteto\]\(/g;

const README = `# istack harness tree

This folder is generated from \`harness/pstack/claude-code\` by \`${COMMAND}\`. An edit made here is kept only once \`${COMMAND} --record\` saves it to \`harness/istack-patches\`.

The script runs the upstream generator, then copies the tree here and renames \`pstack\` to \`istack\` and \`poteto\` to \`igoroh\` in paths and text. URLs and the author credit keep their upstream spelling. Then it applies istack's own changes from \`harness/istack-patches\`:

- \`patches/<path>.patch\` changes or deletes the upstream file \`<path>\`.
- \`files/<path>\` is a file with no upstream source, such as \`claude-code/scripts/istack-worker\`.

Paths are relative to \`harness/istack/\`. To change istack, edit this folder, then run \`${COMMAND} --record\`. It rewrites \`harness/istack-patches\` from this folder, and \`${COMMAND} --check\` then passes.

After \`git merge upstream/main\` or an edit under \`pstack/\`, run \`${COMMAND}\` from the repository root. When a patch no longer applies, the script merges the upstream change into istack's version of the file. A clean merge rewrites the patch. A conflict leaves markers in the file here and stops the script: resolve them, run \`${COMMAND} --record\`, and commit the result.
`;

function listFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    if (name === ".DS_Store" || name === "node_modules" || name === "__pycache__") return [];
    const path = join(dir, name);
    return statSync(path).isDirectory() ? listFiles(path) : [path];
  });
}

function renameText(text) {
  let result = "";
  let start = 0;
  for (const match of text.matchAll(PROTECTED)) {
    result += RENAMES.reduce((part, [re, to]) => part.replace(re, to), text.slice(start, match.index));
    result += match[0];
    start = match.index + match[0].length;
  }
  return result + RENAMES.reduce((part, [re, to]) => part.replace(re, to), text.slice(start));
}

function renameBytes(bytes) {
  return bytes.includes(0) ? bytes : Buffer.from(renameText(bytes.toString("utf8")));
}

function buildBaseTree() {
  const tree = new Map([["README.md", { bytes: Buffer.from(README), executable: false }]]);
  for (const path of listFiles(SOURCE)) {
    const target = `${TREE}/${renameText(relative(SOURCE, path))}`;
    if (tree.has(target)) throw new Error(`two files rename to ${target}`);
    tree.set(target, { bytes: renameBytes(readFileSync(path)), executable: (statSync(path).mode & 0o111) !== 0 });
  }
  return tree;
}

function readTree(dir) {
  return new Map(
    existsSync(dir)
      ? listFiles(dir).map((path) => [relative(dir, path), { bytes: readFileSync(path), executable: (statSync(path).mode & 0o111) !== 0 }])
      : [],
  );
}

function writeTree(dir, tree) {
  for (const [path, { bytes, executable }] of tree) {
    mkdirSync(dirname(join(dir, path)), { recursive: true });
    writeFileSync(join(dir, path), bytes);
    chmodSync(join(dir, path), executable ? 0o755 : 0o644);
  }
}

function runInTempDir(tree, action) {
  const dir = mkdtempSync(join(tmpdir(), "istack-"));
  try {
    writeTree(dir, tree);
    return action(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function applyPatch(dir, patch, reverse = false) {
  const args = ["apply", "--whitespace=nowarn", ...(reverse ? ["-R"] : []), patch];
  const result = spawnSync("git", args, { cwd: dir, encoding: "utf8" });
  return { ok: result.status === 0, reason: (result.stderr || String(result.error ?? "")).trim() };
}

function listPatches() {
  return existsSync(PATCHES) ? listFiles(PATCHES).filter((path) => path.endsWith(".patch")).sort() : [];
}

function locatePatchedFile(patch) {
  return relative(PATCHES, patch).replace(/\.patch$/, "");
}

function listGitPaths(args) {
  const listing = execFileSync("git", [...args, "-z", "--", OUT], { cwd: ROOT, encoding: "utf8" });
  return listing.split("\0").filter(Boolean);
}

// Paths under harness/istack that differ from the last commit: edits, resolved merges, and files an earlier run wrote.
function listUncommittedPaths() {
  return new Set(listGitPaths(["status", "--porcelain", "--untracked-files=all", "--no-renames"]).map((entry) => relative(OUT, join(ROOT, entry.slice(3)))));
}

// Untracked files that git ignores under harness/istack, such as a .venv or a log: junk, not istack's own files.
function listIgnoredPaths() {
  return listGitPaths(["ls-files", "--others", "--ignored", "--exclude-standard"]).map((path) => relative(OUT, join(ROOT, path)));
}

// Reversing the patch on istack's version of the file gives the old upstream file, the base of a three-way merge.
function mergeUpstreamChange(path, patch, base, ours) {
  return runInTempDir(new Map([[path, ours], ["ours", ours]]), (dir) => {
    const reversed = applyPatch(dir, patch, true);
    if (!reversed.ok) throw new Error(`harness/istack-patches/patches/${path}.patch does not apply to upstream, and harness/istack/${path} has edits that the patch lacks. To keep them, ${SET_EDITS_ASIDE}\n${reversed.reason}`);
    if (!base.has(path)) return { entry: ours, message: "upstream removed this file. istack's version is kept", conflict: true };
    writeTree(dir, new Map([["upstream", base.get(path)]]));
    const merged = spawnSync("git", ["merge-file", "-p", "-L", "istack", "-L", "old upstream", "-L", "new upstream", "ours", path, "upstream"], { cwd: dir });
    if (merged.status === null || merged.status > 127) throw new Error(`git merge-file failed on ${path}`);
    const conflict = merged.status > 0;
    const message = conflict ? `${merged.status} conflicts with the upstream change` : "merged the upstream change";
    return { entry: { bytes: merged.stdout, executable: ours.executable }, message, conflict };
  });
}

// Without onDisk, a patch that does not apply stops the run. With it, the upstream change is merged into the file on disk.
function applyPatches(base, onDisk) {
  const merges = new Map();
  const tree = runInTempDir(base, (dir) => {
    for (const patch of listPatches()) {
      const applied = applyPatch(dir, patch);
      if (applied.ok) continue;
      const path = locatePatchedFile(patch);
      if (!onDisk) throw new Error(`harness/istack-patches/patches/${path}.patch does not apply. Run \`${COMMAND}\` to merge the upstream change.\n${applied.reason}`);
      if (!onDisk.has(path)) {
        merges.set(path, { message: "upstream changed a file that istack deletes. istack still deletes it", conflict: false });
        rmSync(join(dir, path), { force: true });
        continue;
      }
      const merge = mergeUpstreamChange(path, patch, base, onDisk.get(path));
      merges.set(path, merge);
      writeTree(dir, new Map([[path, merge.entry]]));
    }
    return readTree(dir);
  });
  return { tree, merges };
}

function addOwnFiles(tree) {
  for (const [path, entry] of readTree(FILES)) {
    if (tree.has(path)) throw new Error(`upstream now has harness/istack/${path}, which harness/istack-patches/files/ also has. Run --record to turn it into a patch.`);
    tree.set(path, entry);
  }
  return tree;
}

function buildTree(onDisk) {
  const base = buildBaseTree();
  const { tree, merges } = applyPatches(base, onDisk);
  return { base, tree: addOwnFiles(tree), merges };
}

function isSame(a, b) {
  return Boolean(a && b && a.bytes.equals(b.bytes) && a.executable === b.executable);
}

function findDrift(tree, onDisk) {
  return [...new Set([...tree.keys(), ...onDisk.keys()])].sort().filter((path) => !isSame(tree.get(path), onDisk.get(path)));
}

// Rewrites harness/istack-patches from the tree: a patch for each upstream file it changes or deletes, and a copy of each file upstream lacks.
function recordTree(base, tree) {
  const changed = [...base.keys()].filter((path) => !isSame(base.get(path), tree.get(path)));
  const own = new Map([...tree].filter(([path]) => !base.has(path)));
  const patches = runInTempDir(new Map(changed.map((path) => [path, base.get(path)])), (dir) => {
    execFileSync("git", ["init", "-q"], { cwd: dir });
    // --force and the diff options keep the user's ignore rules and diff settings out of the patches.
    execFileSync("git", ["add", "-A", "--force"], { cwd: dir });
    for (const path of changed) {
      if (tree.has(path)) writeTree(dir, new Map([[path, tree.get(path)]]));
      else rmSync(join(dir, path));
    }
    return changed.map((path) => [path, execFileSync("git", ["diff", "--binary", "--no-renames", "--no-color", "--no-ext-diff", "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/", "--", path], { cwd: dir, maxBuffer: 1 << 30 })]);
  });
  rmSync(PATCHES, { recursive: true, force: true });
  rmSync(FILES, { recursive: true, force: true });
  writeTree(FILES, own);
  for (const [path, patch] of patches) {
    mkdirSync(dirname(join(PATCHES, path)), { recursive: true });
    writeFileSync(join(PATCHES, `${path}.patch`), patch);
  }
  const drifted = findDrift(addOwnFiles(applyPatches(base).tree), tree);
  if (drifted.length > 0) throw new Error(`harness/istack-patches does not reproduce harness/istack: ${drifted.join(", ")}`);
  console.log(`harness/istack-patches: ${changed.length} patches, ${own.size} files`);
}

// Files with no uncommitted edit that the patch layer builds differently on the current upstream: harness/istack lacks an
// upstream change, and --record would write patches that undo it.
function findStalePaths(base, onDisk, uncommitted) {
  const unapplied = new Set();
  const tree = runInTempDir(base, (dir) => {
    for (const patch of listPatches()) if (!applyPatch(dir, patch).ok) unapplied.add(locatePatchedFile(patch));
    return readTree(dir);
  });
  for (const [path, entry] of readTree(FILES)) tree.set(path, entry);
  // A file whose patch no longer applies went through the merge path, where a conflict resolved in istack's favour
  // looks just like a stale file, so the check leaves it out.
  return findDrift(tree, onDisk).filter((path) => !uncommitted.has(path) && !unapplied.has(path));
}

function describePaths(paths) {
  return paths.length > 20 ? `${paths.slice(0, 20).join(", ")} and ${paths.length - 20} more` : paths.join(", ");
}

// Claude Code installs only this tree, so a relative link must resolve inside it. A patch that deletes a file can leave one dangling.
function findDanglingLinks(tree) {
  const dirs = new Set([...tree.keys()].flatMap((path) => path.split("/").slice(0, -1).map((_, index, parts) => parts.slice(0, index + 1).join("/"))));
  const has = (path) => tree.has(path) || dirs.has(path);
  return [...tree].filter(([path]) => path.endsWith(".md")).flatMap(([path, { bytes }]) =>
    [...bytes.toString("utf8").matchAll(/\]\(([^)\s]+)\)/g)]
      .map(([, href]) => href)
      .filter((href) => {
        const target = href.replace(/[#?].*/, "");
        return target && !/^[a-z][a-z0-9+.-]*:/i.test(target) && !has(posix.join(posix.dirname(path), target).replace(/\/$/, ""));
      })
      .map((href) => `harness/istack/${path} links to ${href}, which is not in the tree`),
  );
}

function reportDanglingLinks(tree) {
  const dangling = findDanglingLinks(tree);
  for (const line of dangling) console.log(`FAIL ${line}`);
  if (dangling.length > 0) process.exit(1);
}

const check = process.argv.includes("--check");
execFileSync(process.execPath, [UPSTREAM_GENERATOR, ...(check ? ["--check"] : [])], { cwd: ROOT, stdio: "inherit" });
if (process.argv.includes("--record")) {
  // --record rewrites the patch layer from harness/istack, so an edit made in the layer and not yet generated would be lost.
  const pending = execFileSync("git", ["status", "--porcelain", "--", dirname(PATCHES)], { cwd: ROOT, encoding: "utf8" });
  if (pending) throw new Error(`harness/istack-patches has uncommitted changes that --record would overwrite:\n${pending}If an earlier --record or run of this script made them, commit them and run --record again. If you edited harness/istack-patches by hand, run \`${COMMAND}\` to apply them, then commit.`);
  const base = buildBaseTree();
  const onDisk = readTree(OUT);
  for (const path of listIgnoredPaths()) if (!base.has(path)) onDisk.delete(path);
  const stale = findStalePaths(base, onDisk, listUncommittedPaths());
  if (stale.length > 0) throw new Error(`harness/istack lacks the upstream change to ${describePaths(stale)}, and --record would write patches that undo it. Run \`${COMMAND}\` first, then --record. If harness/istack also has edits of yours, ${SET_EDITS_ASIDE}`);
  recordTree(base, onDisk);
  reportDanglingLinks(onDisk);
} else if (check) {
  const { tree } = buildTree();
  reportDanglingLinks(tree);
  const drifted = findDrift(tree, readTree(OUT));
  for (const path of drifted.slice(0, 20)) console.log(`harness/istack/${path}`);
  if (drifted.length > 0) {
    console.log(`harness/istack is out of date. Run \`${COMMAND}\` and commit the result, or \`${COMMAND} --record\` to keep edits made there.`);
    process.exit(1);
  }
  console.log("harness/istack is up to date.");
} else {
  const onDisk = readTree(OUT);
  const { base, tree, merges } = buildTree(onDisk);
  // A merged file carries its edits into the result. Any other edit that the patch layer lacks would be lost.
  const uncommitted = listUncommittedPaths();
  const dropped = findDrift(tree, onDisk).filter((path) => uncommitted.has(path) && !merges.has(path));
  if (dropped.length > 0) throw new Error(`harness/istack has edits that harness/istack-patches lacks, and this run would drop them: ${describePaths(dropped)}. Keep them with \`${COMMAND} --record\`. If an earlier run of this script wrote them, discard them with \`git checkout -- harness/istack\` and \`git clean -fd -- harness/istack\`, then run it again.`);
  rmSync(OUT, { recursive: true, force: true });
  writeTree(OUT, tree);
  console.log(`harness/istack: ${tree.size} files`);
  for (const [path, { message }] of merges) console.log(`harness/istack/${path}: ${message}`);
  if ([...merges.values()].some(({ conflict }) => conflict)) {
    console.log(`Resolve the files above in harness/istack, then run \`${COMMAND} --record\`.`);
    process.exit(1);
  }
  if (merges.size > 0) recordTree(base, tree);
  reportDanglingLinks(tree);
}
