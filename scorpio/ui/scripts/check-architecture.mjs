import { readdir, readFile } from "node:fs/promises";
import { join, relative } from "node:path";

const root = new URL("../src/", import.meta.url).pathname;
const failures = [];
let count = 0;
async function check(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await check(path);
      continue;
    }
    if (!/\.(tsx?|css)$/.test(entry.name)) continue;
    count++;
    const source = await readFile(path, "utf8");
    const name = relative(root, path);
    const lines = source.trimEnd().split("\n").length;
    if (lines > 200) failures.push(`${name}: ${lines} lines (maximum 200)`);
    if (
      /\bfetch\s*\(|new\s+EventSource\s*\(/.test(source) &&
      !["api/http.ts", "api/events.ts"].includes(name)
    ) {
      failures.push(`${name}: network transport belongs in api/http.ts or api/events.ts`);
    }
    if (name.startsWith("api/") && /from\s+["']react(?:["'/-])/.test(source)) {
      failures.push(`${name}: React hooks belong with their page, outside the API layer`);
    }
  }
}
await check(root);
if (failures.length) {
  console.error(failures.join("\n"));
  process.exitCode = 1;
} else {
  console.log(`Architecture checks passed: ${count} source files, each at most 200 lines.`);
}
