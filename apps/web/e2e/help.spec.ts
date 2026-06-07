import { test, expect } from "@playwright/test";

test("guided tour auto-opens on first visit", async ({ page }) => {
  // Fresh context => no 'seen' flag => the tour should auto-open.
  await page.goto("/");
  await expect(page.getByText(/Guided tour ·/)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Welcome/ })).toBeVisible();
  await page.getByRole("button", { name: "Skip" }).click();
  await expect(page.getByText(/Guided tour ·/)).toHaveCount(0);
});

test("help button reopens the tour and Next advances", async ({ page }) => {
  await page.addInitScript(() => {
    try { localStorage.setItem("jrs_help_seen_v1", "1"); } catch {}
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Help — guided tour" }).click();
  await expect(page.getByRole("heading", { name: /Welcome/ })).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("heading", { name: /Create a review/ })).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
});
