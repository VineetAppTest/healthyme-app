import { expect, test } from '@playwright/test';

import { JarvisDiagnostics } from '../support/diagnostics';


test('HM-PUBLIC-001: HealthyMe login surface is available', async ({ page }, testInfo) => {
  const diagnostics = new JarvisDiagnostics(page);
  diagnostics.mark('T0_TEST_STARTED', { route: 'HM-PUBLIC-001' });

  try {
    await page.goto('/Login', { waitUntil: 'domcontentloaded' });
    diagnostics.mark('T1_LOGIN_ROUTE_LOADED', { url: page.url() });

    await expect(page.getByText('HealthyMe', { exact: true }).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Secure Login' })).toBeVisible();
    diagnostics.mark('T2_PRIMARY_LOGIN_UI_VISIBLE');

    const supabaseButton = page.getByRole('button', { name: 'Continue with Supabase' });
    const auth0Button = page.getByRole('button', { name: 'Continue with Auth0' });
    const availableProviderCount =
      (await supabaseButton.count()) + (await auth0Button.count());

    expect(
      availableProviderCount,
      'At least one configured HealthyMe authentication route must be visible.',
    ).toBeGreaterThan(0);
    diagnostics.mark('T3_AUTH_PROVIDER_VISIBLE', {
      supabase_button_count: await supabaseButton.count(),
      auth0_button_count: await auth0Button.count(),
    });

    await expect(page.getByText('No public sign-up:', { exact: true })).toBeVisible();
    diagnostics.mark('T4_LOGIN_SURFACE_READY');
  } finally {
    await diagnostics.attach(testInfo);
  }
});
