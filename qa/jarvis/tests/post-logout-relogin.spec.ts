import { expect, test } from '@playwright/test';

import {
  loginSubmitAction,
  resolveAppSurface,
  surfaceUrl,
  type AppSurface,
} from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';

const adminEmail = process.env.JARVIS_ADMIN_EMAIL || '';
const adminPassword = process.env.JARVIS_ADMIN_PASSWORD || '';
const memberEmail = process.env.JARVIS_MEMBER_EMAIL || '';
const memberPassword = process.env.JARVIS_MEMBER_PASSWORD || '';

async function signIn(
  page: Parameters<typeof resolveAppSurface>[0],
  email: string,
  password: string,
  landingSignal: RegExp,
  landingText: string,
): Promise<AppSurface> {
  const loginApp = await resolveAppSurface(page, /Secure Login/i, 120_000);
  await expect(loginApp.getByRole('heading', { name: 'Secure Login' })).toBeVisible({
    timeout: 120_000,
  });
  await loginApp.getByLabel('Email', { exact: true }).fill(email);
  await loginApp.getByLabel('Password', { exact: true }).fill(password);
  const submitAction = loginSubmitAction(loginApp);
  await expect(submitAction).toBeEnabled({ timeout: 60_000 });
  await submitAction.click();

  const landingApp = await resolveAppSurface(page, landingSignal, 120_000);
  await expect(landingApp.getByText(landingText, { exact: true }).first()).toBeVisible({
    timeout: 120_000,
  });
  await expect(landingApp.getByRole('button', { name: /logout/i })).toBeVisible({
    timeout: 60_000,
  });
  return landingApp;
}

async function logOut(page: Parameters<typeof resolveAppSurface>[0], app: AppSurface) {
  await app.getByRole('button', { name: /logout/i }).click();
  const loginApp = await resolveAppSurface(page, /Secure Login/i, 120_000);
  await expect(loginApp.getByRole('heading', { name: 'Secure Login' })).toBeVisible({
    timeout: 120_000,
  });
  await expect(loginSubmitAction(loginApp)).toBeEnabled({ timeout: 60_000 });
  return loginApp;
}

test('HM-AUTH-001: login recovers after cross-role logout in one browser', async ({ page }, testInfo) => {
  test.skip(
    !adminEmail || !adminPassword || !memberEmail || !memberPassword,
    'Dedicated admin and member credentials are required.',
  );
  test.setTimeout(420_000);

  const diagnostics = new JarvisDiagnostics(page, 'HM-AUTH-001');
  diagnostics.mark('T0_TEST_STARTED');

  try {
    await page.goto('/Login', { waitUntil: 'domcontentloaded' });

    const firstAdminApp = await signIn(
      page,
      adminEmail,
      adminPassword,
      /Admin Dashboard|Main Workflows/i,
      'Admin Dashboard',
    );
    diagnostics.mark('T1_INITIAL_ADMIN_LOGIN_CONFIRMED', {
      host_url: page.url(),
      app_url: surfaceUrl(firstAdminApp),
    });

    const memberLoginApp = await logOut(page, firstAdminApp);
    diagnostics.mark('T2_ADMIN_LOGOUT_FRESH_LOGIN_READY', {
      host_url: page.url(),
      app_url: surfaceUrl(memberLoginApp),
    });

    const memberApp = await signIn(
      page,
      memberEmail,
      memberPassword,
      /Member Home|Upcoming Schedule/i,
      'Member Home',
    );
    diagnostics.mark('T3_MEMBER_RELOGIN_CONFIRMED', {
      host_url: page.url(),
      app_url: surfaceUrl(memberApp),
    });

    const secondAdminLoginApp = await logOut(page, memberApp);
    diagnostics.mark('T4_MEMBER_LOGOUT_FRESH_LOGIN_READY', {
      host_url: page.url(),
      app_url: surfaceUrl(secondAdminLoginApp),
    });

    const secondAdminApp = await signIn(
      page,
      adminEmail,
      adminPassword,
      /Admin Dashboard|Main Workflows/i,
      'Admin Dashboard',
    );
    diagnostics.mark('T5_SECOND_ADMIN_LOGIN_CONFIRMED', {
      host_url: page.url(),
      app_url: surfaceUrl(secondAdminApp),
    });
  } finally {
    await diagnostics.attach(testInfo);
  }
});
