import { expect, test, type Page } from '@playwright/test';

import {
  loginSubmitAction,
  resolveAppSurface,
  surfaceUrl,
  type AppSurface,
} from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';

const email = process.env.JARVIS_MEMBER_EMAIL || '';
const password = process.env.JARVIS_MEMBER_PASSWORD || '';

function checkpoint(code: string): void {
  console.log(`JARVIS_CHECKPOINT ${code}`);
}

async function signInMember(page: Page): Promise<void> {
  checkpoint('MEMBER_LOGIN_OPEN');
  await page.goto('/Login', { waitUntil: 'domcontentloaded' });
  const loginApp = await resolveAppSurface(page, /HealthyMe|Secure Login/i);
  await expect(loginApp.getByRole('heading', { name: 'Secure Login' })).toBeVisible();
  await loginApp.getByLabel('Email', { exact: true }).fill(email);
  await loginApp.getByLabel('Password', { exact: true }).fill(password);
  await loginSubmitAction(loginApp).click();

  const memberApp = await resolveAppSurface(
    page,
    /Member Home|Upcoming Schedule|Messages from Nutritionist/i,
    120_000,
  );
  await expect(memberApp.getByText('Member Home', { exact: true }).first()).toBeVisible({
    timeout: 120_000,
  });
  checkpoint('MEMBER_HOME_READY');
}

async function clickExerciseJournalSelector(surface: AppSurface): Promise<string> {
  const button = surface.getByRole('button', { name: 'Exercise Journal', exact: true }).first();
  if (await button.isVisible().catch(() => false)) {
    await button.click();
    return 'button';
  }

  const tab = surface.getByRole('tab', { name: 'Exercise Journal', exact: true }).first();
  if (await tab.isVisible().catch(() => false)) {
    await tab.click();
    return 'tab';
  }

  const text = surface.getByText('Exercise Journal', { exact: true }).first();
  await expect(text).toBeVisible({ timeout: 30_000 });
  await text.click();
  return 'text';
}

test('HM-MEMBER-EXERCISE-JOURNAL-001: dropdown rerun stays on Exercise Journal', async ({ page }, testInfo) => {
  test.skip(!email || !password, 'Dedicated Jarvis member credentials are required.');

  const diagnostics = new JarvisDiagnostics(page, 'HM-MEMBER-EXERCISE-JOURNAL-001');
  diagnostics.mark('T0_TEST_STARTED');

  try {
    await signInMember(page);
    diagnostics.mark('T1_MEMBER_AUTHENTICATED');

    checkpoint('DAILY_LOG_OPEN');
    await page.goto('/Daily_Log', { waitUntil: 'domcontentloaded' });
    let dailyLog = await resolveAppSurface(
      page,
      /Food Journal|Exercise Journal|Daily Log/i,
      120_000,
    );
    checkpoint('DAILY_LOG_SURFACE_READY');

    const selectorKind = await clickExerciseJournalSelector(dailyLog);
    checkpoint(`EXERCISE_SELECTOR_CLICKED_${selectorKind.toUpperCase()}`);

    dailyLog = await resolveAppSurface(
      page,
      /Exercise Journal Date|Select the date for this exercise journal entry/i,
      120_000,
    );
    await expect(dailyLog.getByText('Exercise Journal Date', { exact: true }).first()).toBeVisible({
      timeout: 90_000,
    });
    checkpoint('EXERCISE_JOURNAL_READY');
    diagnostics.mark('T2_EXERCISE_JOURNAL_SELECTED', {
      host_url: page.url(),
      app_url: surfaceUrl(dailyLog),
      selector_kind: selectorKind,
    });

    const statusDropdown = dailyLog.getByRole('combobox', {
      name: 'Status',
      exact: true,
    }).first();
    await expect(statusDropdown).toBeVisible({ timeout: 60_000 });
    checkpoint('STATUS_DROPDOWN_READY');
    await statusDropdown.click();
    await dailyLog.getByRole('option', { name: 'Completed', exact: true }).click();
    checkpoint('STATUS_DROPDOWN_CHANGED');
    diagnostics.mark('T3_EXERCISE_DROPDOWN_CHANGED_WITHOUT_SAVE');

    dailyLog = await resolveAppSurface(
      page,
      /Exercise Journal Date|Food Journal Date|Food Journal|Exercise Journal/i,
      120_000,
    );
    const exerciseDateVisible = await dailyLog
      .getByText('Exercise Journal Date', { exact: true })
      .first()
      .isVisible()
      .catch(() => false);
    const foodDateVisible = await dailyLog
      .getByText('Food Journal Date', { exact: true })
      .first()
      .isVisible()
      .catch(() => false);

    checkpoint(
      exerciseDateVisible
        ? 'POST_DROPDOWN_EXERCISE_VISIBLE'
        : 'POST_DROPDOWN_EXERCISE_NOT_VISIBLE',
    );
    checkpoint(
      foodDateVisible ? 'POST_DROPDOWN_FOOD_VISIBLE' : 'POST_DROPDOWN_FOOD_NOT_VISIBLE',
    );
    diagnostics.mark('T4_POST_DROPDOWN_JOURNAL_STATE', {
      exercise_journal_visible: exerciseDateVisible,
      food_journal_visible: foodDateVisible,
    });

    expect(
      exerciseDateVisible,
      'Exercise Journal disappeared after a dropdown-triggered Streamlit rerun.',
    ).toBe(true);
    expect(
      foodDateVisible,
      'Food Journal became active after changing an Exercise Journal dropdown.',
    ).toBe(false);
  } finally {
    await diagnostics.attach(testInfo);
  }
});
