#!/usr/bin/env node

// Builds harness/istack/claude-code: the Claude Code tree of pstack, renamed to istack and igoroh-*.
// pstack/ and harness/pstack/ stay identical to upstream, so `git merge upstream/main` touches only them.
// Then it applies harness/istack-patches/*.patch in name order, so local changes survive a regeneration.
// After a merge or an edit under pstack/, run this script from the repository root and commit the result.

import { execFileSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const UPSTREAM_GENERATOR = join(ROOT, "scripts", "generate-pstack-harness-trees.mjs");
const SOURCE = join(ROOT, "harness", "pstack", "claude-code");
const OUT = join(ROOT, "harness", "istack");
const PATCHES = join(ROOT, "harness", "istack-patches");
const TREE = "claude-code";
const COMMAND = "node scripts/generate-istack-tree.mjs";

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

This folder is generated from \`harness/pstack/claude-code\` by \`${COMMAND}\`. Do not edit it by hand.

The script runs the upstream generator, then copies the tree here and renames \`pstack\` to \`istack\` and \`poteto\` to \`igoroh\` in paths and text. URLs and the author credit keep their upstream spelling. Then it applies each \`harness/istack-patches/*.patch\` in name order.

To change a file here, edit it, then write the change as a patch against the generated tree in \`harness/istack-patches/\`. Patch paths are relative to \`harness/istack/\`. When an upstream change makes a patch fail, the script stops and names the patch.

After \`git merge upstream/main\` or an edit under \`pstack/\`, run \`${COMMAND}\` from the repository root and commit the result.
`;

function listFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    if (name === ".DS_Store" || name === "node_modules") return [];
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

function buildTree() {
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

function applyPatches(tree) {
  const patches = existsSync(PATCHES) ? readdirSync(PATCHES).filter((name) => name.endsWith(".patch")).sort() : [];
  if (patches.length === 0) return tree;
  const dir = mkdtempSync(join(tmpdir(), "istack-"));
  try {
    writeTree(dir, tree);
    for (const name of patches) {
      try {
        execFileSync("git", ["apply", "--whitespace=nowarn", join(PATCHES, name)], { cwd: dir, stdio: "pipe" });
      } catch (error) {
        throw new Error(`harness/istack-patches/${name} does not apply to the generated tree. Update it.\n${error.stderr}`);
      }
    }
    return readTree(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function findDrift(tree) {
  const onDisk = readTree(OUT);
  return [...new Set([...tree.keys(), ...onDisk.keys()])].sort().filter((path) => {
    const [want, have] = [tree.get(path), onDisk.get(path)];
    return !want || !have || !want.bytes.equals(have.bytes) || want.executable !== have.executable;
  });
}


const check = process.argv.includes("--check");
execFileSync(process.execPath, [UPSTREAM_GENERATOR, ...(check ? ["--check"] : [])], { cwd: ROOT, stdio: "inherit" });
const tree = applyPatches(buildTree());
if (check) {
  const drifted = findDrift(tree);
  for (const path of drifted.slice(0, 20)) console.log(`harness/istack/${path}`);
  if (drifted.length > 0) {
    console.log(`harness/istack is out of date. Run \`${COMMAND}\` and commit the result.`);
    process.exit(1);
  }
  console.log("harness/istack is up to date.");
} else {
  rmSync(OUT, { recursive: true, force: true });
  writeTree(OUT, tree);
  console.log(`harness/istack: ${tree.size} files`);
}
