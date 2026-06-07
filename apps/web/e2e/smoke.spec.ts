import { test, expect } from "@playwright/test";

test("dashboard and sidebar render", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Venues" })).toBeVisible();
  await expect(page.getByRole("link", { name: "New Review" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Reviewer Profiles" })).toBeVisible();
});

test("venues page renders the table", async ({ page }) => {
  await page.goto("/venues");
  await expect(page.getByRole("heading", { name: /Venues/ })).toBeVisible();
  await expect(page.getByText("Import venue discovery (Perplexity)")).toBeVisible();
  await expect(page.getByText("Quartile/Rank")).toBeVisible();
});

test("reviewer profiles page lists the 5 main reviewers", async ({ page }) => {
  await page.goto("/reviewer-profiles");
  await expect(page.getByText("reviewer-methodology")).toBeVisible();
  await expect(page.getByText("integrity-ai-use-auditor")).toBeVisible();
});

test("ai engines page shows the default template engine", async ({ page }) => {
  await page.goto("/ai-engines");
  await expect(page.getByRole("heading", { name: "AI Engines" })).toBeVisible();
});
