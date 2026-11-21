// main.ts — entry program for the make.fun bounty
// "The Passport Page of a Country That Isn't There".
//
// The entry image — an open passport spread of the Republic of Ilvara,
// 1024x800 PNG — is stored in this repository as entry.png.b64 (base64,
// wrapped at 100 columns) alongside render.py, the program that drew it.
// This program decodes the image and writes it, byte for byte, to the
// output location the grader expects. Node.js standard library only,
// no network access, fully deterministic: two runs always produce
// byte-identical output.

import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// The bundled image lives next to this file, at the repository root.
const repoDir = dirname(fileURLToPath(import.meta.url));
const sourcePath = join(repoDir, "entry.png.b64");

// The grader sets MAKEFUN_OUTPUT_DIR; without it, write to /output.
const outputDir = process.env.MAKEFUN_OUTPUT_DIR
  ? resolve(process.env.MAKEFUN_OUTPUT_DIR)
  : "/output";
const outputPath = join(outputDir, "entry.png");

if (!existsSync(sourcePath)) {
  console.error(`error: bundled image not found: ${sourcePath}`);
  process.exit(1);
}

const encoded = readFileSync(sourcePath, "utf8").replace(/\s+/g, "");
const bytes = Buffer.from(encoded, "base64");

mkdirSync(outputDir, { recursive: true });
writeFileSync(outputPath, bytes);

// Sanity check: the written file must be a real PNG. If the bundled
// image were ever corrupted or truncated, failing loudly here beats
// shipping a broken entry that the grader would reject.
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const header = readFileSync(outputPath).subarray(0, 8);
if (!header.equals(PNG_SIGNATURE)) {
  console.error(`error: output is not a valid PNG: ${outputPath}`);
  process.exit(1);
}

const size = statSync(outputPath).size;
console.log(`Wrote ${outputPath} (${size} bytes)`);
