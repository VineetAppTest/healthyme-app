import { expect, test } from '@playwright/test';

import { JarvisDiagnostics } from '../support/diagnostics';

const email = process.env.JARVIS_MEMBER_EMAIL || '';
const password = process.env.JARVIS_MEMBER_PASSWORD || '';


test('HM-MEMBER-001: member login, landing and refresh persistence', async ({ page }, testInfo) => {
  test.skip(!email || !password, 'JARVIS_MEMBER_EMAIL and JARVIS_MEMBER_PASSWORD are required.');

  const diagnostics = new JarvisDiagnostics(page);
  diagnostics.mark('T0_TEST_STARTED', { route: 'HM-MEMBER-001' });

  try {
    await page.goto('/Login', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Secure Login' })).toBeVisible();
    diagnostics.mark('T1_LOGIN_UI_READY', { url: page.url() });

    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    diagnostics.mark('T2_CREDENTIALS_ENTERED');

    await page.getByRole('button', { name: 'Continue with Supabase' }).click();
    diagnostics.mark('T3_LOGIN_SUBMITTED');

    await expect(page.getByText('Member Home', { exact: true }).first()).toBeVisible({
      timeout: 120_000,
    });
    diagnostics.mark('T4_MEMBER_HOME_VISIBLE', { url: page.url() });

    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible({
      timeout: 60_000,
    });
    diagnostics.mark('T5_MEMBER_HOME_USABLE');

    await page.reload({ waitUntil: 'domcontentloaded' });
    diagnostics.mark('T6_REFRESH_REQUESTED', { url: page.url() });

    await expect(page.getByText('Member Home', { exact: true }).first()).toBeVisible({
      timeout: 90_000,
    });
    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible({
      timeout: 60_000,
    });
    diagnostics.mark('T7_REFRESH_PERSISTENCE_CONFIRMED', { url: page.url() });
  } finally {
    await diagnostics.attach(testInfo);
  }
});
