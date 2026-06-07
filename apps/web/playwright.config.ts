import { defineConfig, devices } from "@playwright/test";

/**
 * E2E config. Assumes the stack is already running (e.g. `docker compose up`
 * or `npm run dev` + the API on :8000). Override the target with E2E_BASE_URL.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
