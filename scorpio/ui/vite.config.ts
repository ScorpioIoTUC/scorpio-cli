import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = "http://localhost:8000";

export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/ssh": backend,
      "/scorpio": backend,
      "/version": backend,
      "/discord": backend,
    },
  },
  preview: {
    port: 4173,
    proxy: {
      "/ssh": backend,
      "/scorpio": backend,
      "/version": backend,
      "/discord": backend,
    },
  },
});
