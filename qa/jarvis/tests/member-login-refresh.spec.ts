import { expect, test } from '@playwright/test';

import {
  loginSubmitAction,
  resolveAppSurface,
  surfaceUrl,
} from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';

const email = process.env.JARVIS_MEMBER_EMAIL || '';
const password = process.env.JARVIS_MEMBER_PASSWORD || '';


test('HM-MEMBER-001: member login, landing and refresh persistence', async ({ page }, testInfo) => {
  test.skip(!email || !password, 'JARVIS_MEMBER_EMAIL and JARVIS_MEMBER_PASSWORD are required.');

  const diagnostics = new JarvisDiagnostics(page, 'HM-MEMBER-001');
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

    const memberApp = await resolveAppSurface(
      page,
      /Member Home|Upcoming Schedule|Messages from Nutritionist/i,
      120_000,
    );
    await expect(memberApp.getByText('Member Home', { exact: true }).first()).toBeVisible({
      timeout: 120_000,
    });
    diagnostics.mark('T4_MEMBER_HOME_VISIBLE', {
      host_url: page.url(),
      app_url: surfaceUrl(memberApp),
    });

    await expect(memberApp.getByRole('button', { name: /logout/i })).toBeVisible({
      timeout: 60_000,
    });
    diagnostics.mark('T5_MEMBER_HOME_USABLE');

    await page.reload({ waitUntil: 'domcontentloaded' });
    diagnostics.mark('T6_REFRESH_REQUESTED', { host_url: page.url() });

    const refreshedApp = await resolveAppSurface(
      page,
      /Member Home|Upcoming Schedule|Messages from Nutritionist/i,
      120_000,
    );
    await expect(refreshedApp.getByText('Member Home', { exact: true }).first()).toBeVisible({
      timeout: 90_000,
    });
    await expect(refreshedApp.getByRole('button', { name: /logout/i })).toBeVisible({
      timeout: 60_000,
    });
    diagnostics.mark('T7_REFRESH_PERSISTENCE_CONFIRMED', {
      host_url: page.url(),
      app_url: surfaceUrl(refreshedApp),
    });
  } finally {
    await diagnostics.attach(testInfo);
  }
});
