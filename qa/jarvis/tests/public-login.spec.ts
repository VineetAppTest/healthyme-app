import { expect, test } from '@playwright/test';

import { resolveAppSurface, surfaceUrl } from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';


test('HM-PUBLIC-001: HealthyMe login surface is available', async ({ page }, testInfo) => {
  const diagnostics = new JarvisDiagnostics(page, 'HM-PUBLIC-001');
  diagnostics.mark('T0_TEST_STARTED');

  try {
    await page.goto('/Login', { waitUntil: 'domcontentloaded' });
    diagnostics.mark('T1_HOST_ROUTE_LOADED', { host_url: page.url() });

    const app = await resolveAppSurface(page, /HealthyMe|Secure Login/i);
    diagnostics.mark('T2_APP_SURFACE_RESOLVED', {
      host_url: page.url(),
      app_url: surfaceUrl(app),
      embedded: app !== page,
    });

    await expect(app.getByRole('heading', { name: 'Secure Login' })).toBeVisible();
    await expect(app.getByLabel('Email', { exact: true })).toBeVisible();
    await expect(app.getByLabel('Password', { exact: true })).toBeVisible();
    diagnostics.mark('T3_PRIMARY_LOGIN_UI_VISIBLE');

    const providerAction = app
      .getByRole('button', {
        name: /Continue with Supabase|Sign in securely/i,
      })
      .first();
    await expect(providerAction).toBeVisible();
    diagnostics.mark('T4_AUTH_ACTION_VISIBLE', {
      action_label: await providerAction.innerText(),
    });

    await expect(app.getByText(/No public sign-up/i).first()).toBeVisible();
    diagnostics.mark('T5_LOGIN_SURFACE_READY');
  } finally {
    await diagnostics.attach(testInfo);
  }
});
