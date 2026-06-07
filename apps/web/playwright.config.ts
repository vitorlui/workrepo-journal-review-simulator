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
  // Run serially when watching a headed/slow demo so steps are easy to follow.
  workers: process.env.PW_SLOWMO ? 1 : undefined,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    // PW_SLOWMO=800 slows each action so you can watch the browser drive the UI.
    launchOptions: { slowMo: Number(process.env.PW_SLOWMO || 0) },
    // PW_CHANNEL=msedge|chrome uses an installed browser instead of the bundled
    // Chromium (handy on Windows where the Chromium download can be AV-blocked).
    channel: process.env.PW_CHANNEL || undefined,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
