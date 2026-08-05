import { expect, test } from '@playwright/test';

import {
  loginSubmitAction,
  resolveAppSurface,
} from '../support/app-surface';
import type { AppSurface } from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';

const email = process.env.JARVIS_ADMIN_EMAIL || '';
const password = process.env.JARVIS_ADMIN_PASSWORD || '';
const isPullRequest = process.env.JARVIS_GITHUB_EVENT === 'pull_request';

async function selectOptionCount(surface: AppSurface, label: string): Promise<number> {
  const control = surface.getByLabel(label, { exact: true }).first();
  await expect(control).toBeVisible();
  await control.click();
  const options = surface.getByRole('option');
  await expect(options.first()).toBeVisible();
  const count = await options.count();
  await control.press('Escape');
  return count;
}

test('HM-ADMIN-002: Member Plan Builder read-only regression', async ({ page }, testInfo) => {
  test.skip(isPullRequest, 'Live branch assertions run only after the deployment exists.');
  test.skip(!email || !password, 'JARVIS_ADMIN_EMAIL and JARVIS_ADMIN_PASSWORD are required.');

  const diagnostics = new JarvisDiagnostics(page, 'HM-ADMIN-002');
  diagnostics.mark('P0_TEST_STARTED');

  try {
    await page.goto('/Login', { waitUntil: 'domcontentloaded' });
    const loginApp = await resolveAppSurface(page, /HealthyMe|Secure Login/i);
    await loginApp.getByLabel('Email', { exact: true }).fill(email);
    await loginApp.getByLabel('Password', { exact: true }).fill(password);
    await loginSubmitAction(loginApp).click();

    const adminApp = await resolveAppSurface(
      page,
      /Admin Dashboard|Main Workflows/i,
      120_000,
    );
    await expect(adminApp.getByText('Admin Dashboard', { exact: true }).first()).toBeVisible({
      timeout: 120_000,
    });
    diagnostics.mark('P1_ADMIN_READY');

    const builderAction = adminApp
      .getByRole('button', { name: 'Recommendation Profile Builder', exact: true })
      .first();
    await expect(builderAction).toBeVisible({ timeout: 60_000 });
    await builderAction.click();

    const builderApp = await resolveAppSurface(page, /Member Plan Builder/i, 120_000);
    await expect(builderApp.getByText('Member Plan Builder', { exact: true }).first()).toBeVisible({
      timeout: 120_000,
    });
    diagnostics.mark('P2_PLAN_BUILDER_READY');

    await builderApp.getByRole('button', { name: 'Setup', exact: true }).click();
    await expect(builderApp.getByText('More setup details', { exact: true })).toHaveCount(0);
    const setupProfileCount = await selectOptionCount(builderApp, 'Select Meal Plan');
    expect(setupProfileCount).toBeGreaterThanOrEqual(2);
    diagnostics.mark('P3_SETUP_REPOSITORY_VISIBLE', {
      profile_option_count: setupProfileCount,
    });

    await builderApp.getByRole('button', { name: 'View Member Plan', exact: true }).click();
    const filterLabels = ['Meal Profile', 'Member', 'Health Concerns'];
    for (const label of filterLabels) {
      await expect(builderApp.getByLabel(label, { exact: true }).first()).toBeVisible({
        timeout: 60_000,
      });
    }
    const mealProfileCount = await selectOptionCount(builderApp, 'Meal Profile');
    expect(mealProfileCount).toBe(setupProfileCount);
    diagnostics.mark('P4_FILTERS_AND_PROFILE_RETENTION_CONFIRMED', {
      filter_count: filterLabels.length,
      profile_option_count: mealProfileCount,
    });

    await builderApp.getByRole('button', { name: 'Exercise', exact: true }).click();
    await expect(builderApp.getByLabel('Member', { exact: true }).first()).toBeVisible({
      timeout: 60_000,
    });
    await expect(builderApp.getByText('Member Plan', { exact: true })).toHaveCount(0);

    const disclosure = builderApp
      .locator('[data-testid="stExpander"]')
      .filter({ hasText: 'More details' })
      .first();
    await expect(disclosure).toBeVisible({ timeout: 60_000 });
    await disclosure.locator('summary').click();
    const detailBody = disclosure.locator('[data-testid="stExpanderDetails"]');
    await expect(detailBody).toBeVisible();
    const disclosureBox = await disclosure.locator('details').boundingBox();
    const detailBox = await detailBody.boundingBox();
    if (!disclosureBox || !detailBox) {
      throw new Error('Exercise disclosure bounds were unavailable.');
    }
    expect(detailBox.y + detailBox.height).toBeLessThanOrEqual(
      disclosureBox.y + disclosureBox.height + 1,
    );
    diagnostics.mark('P5_EXERCISE_LABEL_AND_DISCLOSURE_CONFIRMED', {
      disclosure_height: Math.round(disclosureBox.height),
      detail_height: Math.round(detailBox.height),
    });

    await builderApp.getByRole('button', { name: 'Supplement', exact: true }).click();
    await expect(builderApp.getByLabel('Member', { exact: true }).first()).toBeVisible({
      timeout: 60_000,
    });
    await expect(builderApp.getByText('Member Plan', { exact: true })).toHaveCount(0);
    diagnostics.mark('P6_SUPPLEMENT_MEMBER_LABEL_CONFIRMED');
  } finally {
    await diagnostics.attach(testInfo);
  }
});
