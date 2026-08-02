import { expect, test } from '@playwright/test';

import {
  loginSubmitAction,
  resolveAppSurface,
  surfaceUrl,
} from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';

const email = process.env.JARVIS_ADMIN_EMAIL || '';
const password = process.env.JARVIS_ADMIN_PASSWORD || '';

test('HM-ADMIN-001: admin login, landing and refresh persistence', async ({ page }, testInfo) => {
  test.skip(!email || !password, 'JARVIS_ADMIN_EMAIL and JARVIS_ADMIN_PASSWORD are required.');

  const diagnostics = new JarvisDiagnostics(page, 'HM-ADMIN-001');
  diagnostics.mark('T0_TEST_STARTED');

  try {
    await page.goto('/Login', { waitUntil: 'domcontentloaded' });
    const loginApp = await resolveAppSurface(page, /HealthyMe|Secure Login/i);
    await expect(loginApp.getByRole('heading', { name: 'Secure Login' })).toBeVisible();
    diagnostics.mark('T1_LOGIN_UI_READY', {
      host_url: page.url(),
      app_url: surfaceUrl(loginApp),
      embedded: loginApp !== page,
    });

    await loginApp.getByLabel('Email', { exact: true }).fill(email);
    await loginApp.getByLabel('Password', { exact: true }).fill(password);
    diagnostics.mark('T2_CREDENTIALS_ENTERED');

    const submitAction = loginSubmitAction(loginApp);
    await expect(submitAction).toBeVisible();
    await submitAction.click();
    diagnostics.mark('T3_LOGIN_SUBMITTED', {
      action_label: await submitAction.innerText().catch(() => 'submitted'),
    });

    const adminApp = await resolveAppSurface(
      page,
      /Admin Dashboard|Main Workflows|Review & Assessment/i,
      120_000,
    );
    await expect(adminApp.getByText('Admin Dashboard', { exact: true }).first()).toBeVisible({
      timeout: 120_000,
    });
    await expect(adminApp.getByText('Main Workflows', { exact: true }).first()).toBeVisible({
      timeout: 60_000,
    });
    diagnostics.mark('T4_ADMIN_DASHBOARD_VISIBLE', {
      host_url: page.url(),
      app_url: surfaceUrl(adminApp),
    });

    await expect(adminApp.getByRole('button', { name: /logout/i })).toBeVisible({
      timeout: 60_000,
    });
    await expect(adminApp.getByText('Member Home', { exact: true })).toHaveCount(0);
    diagnostics.mark('T5_ADMIN_DASHBOARD_USABLE_AND_ROLE_CONFIRMED');

    await page.reload({ waitUntil: 'domcontentloaded' });
    diagnostics.mark('T6_REFRESH_REQUESTED', { host_url: page.url() });

    const refreshedApp = await resolveAppSurface(
      page,
      /Admin Dashboard|Main Workflows|Review & Assessment/i,
      120_000,
    );
    await expect(refreshedApp.getByText('Admin Dashboard', { exact: true }).first()).toBeVisible({
      timeout: 90_000,
    });
    await expect(refreshedApp.getByRole('button', { name: /logout/i })).toBeVisible({
      timeout: 60_000,
    });
    await expect(refreshedApp.getByText('Member Home', { exact: true })).toHaveCount(0);
    diagnostics.mark('T7_REFRESH_PERSISTENCE_CONFIRMED', {
      host_url: page.url(),
      app_url: surfaceUrl(refreshedApp),
    });
  } finally {
    await diagnostics.attach(testInfo);
  }
});
