import { test, expect } from "@playwright/test";

test("create a review and open the wizard", async ({ page }) => {
  await page.goto("/reviews/new");
  await page.getByPlaceholder(/Lightweight FAS/).fill("E2E test paper");
  await page.getByRole("button", { name: "Create review" }).click();

  await expect(page).toHaveURL(/\/reviews\/REV-/);
  await expect(page.getByRole("button", { name: "Run full review" })).toBeVisible();
  await expect(page.getByRole("button", { name: "1. Upload" })).toBeVisible();
  await expect(page.getByRole("button", { name: "13. Export" })).toBeVisible();
});

test("external prompts step exposes the Execute-query controls", async ({ page }) => {
  await page.goto("/reviews/new");
  await page.getByPlaceholder(/Lightweight FAS/).fill("E2E execute-query");
  await page.getByRole("button", { name: "Create review" }).click();
  await expect(page).toHaveURL(/\/reviews\/REV-/);

  await page.getByRole("button", { name: "7. External Prompts" }).click();
  await expect(page.getByText("Execute query (engine CLI)")).toBeVisible();
  await expect(page.getByRole("button", { name: "Execute query" })).toBeVisible();
});
