import { mkdtemp, rm, symlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { build } from "vite";
import react from "@vitejs/plugin-react";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const output = await mkdtemp(join(tmpdir(), "scorpio-ui-tests-"));
try {
  await symlink(join(root, "node_modules"), join(output, "node_modules"), "dir");
  await build({
    root,
    configFile: false,
    plugins: [react()],
    logLevel: "error",
    define: {
      "process.env.NODE_ENV": JSON.stringify("development"),
      "import.meta.env.VITE_API_URL": JSON.stringify("https://api.example.test/"),
    },
    build: {
      outDir: output,
      emptyOutDir: false,
      minify: false,
      lib: { entry: join(root, "tests/index.ts"), formats: ["es"], fileName: () => "tests.mjs" },
      rollupOptions: { external: [/^node:/, /^react(?:-dom|-test-renderer|-router-dom)?(?:\/|$)/] },
    },
  });
  const result = spawnSync(process.execPath, ["--test", join(output, "tests.mjs")], {
    stdio: "inherit",
    env: { ...process.env, NODE_ENV: "development" },
  });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
} finally {
  await rm(output, { recursive: true, force: true });
}
