import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

/**
 * Paper-by-paper walkthrough. Drop your manuscripts (PDF/DOCX/MD/TeX/ZIP) into
 * apps/web/e2e/papers/ and they each get their own test: create review → upload →
 * extract → classify → open venues. Run it slowly + visibly so you can watch:
 *
 *   $env:PW_SLOWMO="800"; npm run test:e2e:headed -- paper-runs.spec.ts
 *
 * Ships with a bundled sample so there is always at least one run.
 */
const PAPERS_DIR = path.join(__dirname, "papers");

function listPapers(): string[] {
  try {
    return fs
      .readdirSync(PAPERS_DIR)
      .filter((f) => /\.(pdf|docx|md|markdown|tex|zip)$/i.test(f) && !/^readme/i.test(f))
      .map((f) => path.join(PAPERS_DIR, f));
  } catch {
    return [];
  }
}

const papers = listPapers();

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    try { localStorage.setItem("jrs_help_seen_v1", "1"); } catch {}
  });
});

test.describe.configure({ mode: "serial" });

if (papers.length === 0) {
  test("no papers found", async () => {
    test.info().annotations.push({
      type: "note",
      description: "Drop manuscripts into apps/web/e2e/papers/ to run them paper by paper.",
    });
  });
}

for (const paperPath of papers) {
  const name = path.basename(paperPath);
  test(`paper: ${name}`, async ({ page }) => {
    // Create the review.
    await page.goto("/reviews/new");
    await page.getByPlaceholder(/Lightweight FAS/).fill(`E2E ${name}`);
    await page.getByRole("button", { name: "Create review" }).click();
    await expect(page).toHaveURL(/\/reviews\/REV-/);

    // Step 1 — upload the manuscript.
    await page.getByRole("button", { name: "1. Upload" }).click();
    await page.locator('input[type="file"]').setInputFiles(paperPath);
    await expect(page.getByText("Upload OK")).toBeVisible({ timeout: 15000 });

    // Step 2 — extraction.
    await page.getByRole("button", { name: "2. Extraction" }).click();
    await page.getByRole("button", { name: /Run extract/ }).click();
    await expect(page.getByText(/Paper extraction/).first()).toBeVisible({ timeout: 20000 });

    // Step 3 — area & paper type.
    await page.getByRole("button", { name: "3. Area & Paper Type" }).click();
    await page.getByRole("button", { name: /Run classify/ }).click();
    await expect(page.getByText(/Paper type/).first()).toBeVisible({ timeout: 20000 });

    // Step 4 — venues (just confirm the catalog renders).
    await page.getByRole("button", { name: "4. Venues" }).click();
    await expect(page.getByRole("button", { name: /Save selection/ })).toBeVisible();
  });
}
