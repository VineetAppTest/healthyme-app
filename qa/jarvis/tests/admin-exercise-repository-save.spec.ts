import { expect, test, type Page } from '@playwright/test';

import {
  loginSubmitAction,
  resolveAppSurface,
  type AppSurface,
} from '../support/app-surface';
import { JarvisDiagnostics } from '../support/diagnostics';
import {
  markMutationRouteComplete,
  markSyntheticRecordCleaned,
  registerSyntheticRecord,
} from '../support/test-data-ledger';

const email = process.env.JARVIS_ADMIN_EMAIL || '';
const password = process.env.JARVIS_ADMIN_PASSWORD || '';
const mutationRun = (process.env.JARVIS_ACCESS_MODE || 'read_only') === 'mutation';
const namespace = process.env.JARVIS_MUTATION_NAMESPACE || 'jarvis_uat';
const runSuffix = (process.env.JARVIS_RUN_ID || 'local').replace(/[^a-zA-Z0-9]+/g, '_').slice(-28);
const exerciseTitle = `${namespace}_exercise_${runSuffix}`;

async function signInAdmin(page: Page): Promise<void> {
  await page.goto('/Login', { waitUntil: 'domcontentloaded' });
  const loginApp = await resolveAppSurface(page, /HealthyMe|Secure Login/i);
  await expect(loginApp.getByRole('heading', { name: 'Secure Login' })).toBeVisible();
  await loginApp.getByLabel('Email', { exact: true }).fill(email);
  await loginApp.getByLabel('Password', { exact: true }).fill(password);
  await loginSubmitAction(loginApp).click();
  const adminApp = await resolveAppSurface(
    page,
    /Admin Dashboard|Main Workflows|Review & Assessment/i,
    120_000,
  );
  await expect(adminApp.getByText('Admin Dashboard', { exact: true }).first()).toBeVisible({
    timeout: 120_000,
  });
}

async function openExerciseManager(page: Page): Promise<AppSurface> {
  await page.goto('/Admin_Exercise_Manager', { waitUntil: 'domcontentloaded' });
  return resolveAppSurface(
    page,
    /Manage & Allocate Exercises|Current Exercise Repository|Add Exercise/i,
    120_000,
  );
}

async function chooseExerciseOption(surface: AppSurface, title: string): Promise<boolean> {
  const select = surface.getByRole('combobox', { name: 'Select exercise', exact: true }).first();
  if (!(await select.isVisible().catch(() => false))) return false;
  await select.click();
  const option = surface.getByRole('option').filter({ hasText: title }).first();
  const visible = await option.isVisible().catch(() => false);
  if (visible) await option.click();
  return visible;
}

async function openEditSection(page: Page): Promise<AppSurface> {
  let surface = await openExerciseManager(page);
  await surface.getByRole('button', { name: 'Edit / Delete', exact: true }).click();
  surface = await resolveAppSurface(page, /Edit or Delete Exercise|Select exercise/i, 120_000);
  return surface;
}

async function removeSyntheticExercise(page: Page): Promise<boolean> {
  const surface = await openEditSection(page);
  const found = await chooseExerciseOption(surface, exerciseTitle);
  if (!found) return true;
  await surface.getByRole('checkbox', { name: 'Confirm delete selected exercise', exact: true }).check();
  await surface.getByRole('button', { name: 'Delete Exercise', exact: true }).click();

  const refreshed = await resolveAppSurface(
    page,
    /Current Exercise Repository|Edit or Delete Exercise|Exercise deleted/i,
    120_000,
  );
  const deleteMessage = await refreshed.getByText('Exercise deleted.', { exact: true }).isVisible().catch(() => false);
  if (deleteMessage) return true;

  const verification = await openEditSection(page);
  return !(await chooseExerciseOption(verification, exerciseTitle));
}

test('HM-ADMIN-EXERCISE-REPOSITORY-001: save feedback, persistence and cleanup', async ({ page }, testInfo) => {
  test.skip(!email || !password, 'Dedicated Jarvis admin credentials are required.');
  test.skip(!mutationRun, 'Controlled mutation mode is required for this route.');

  const diagnostics = new JarvisDiagnostics(page, 'HM-ADMIN-EXERCISE-REPOSITORY-001');
  const findings: string[] = [];
  let registered = false;
  let cleaned = false;
  diagnostics.mark('T0_TEST_STARTED');

  try {
    await signInAdmin(page);
    diagnostics.mark('T1_ADMIN_AUTHENTICATED');

    let manager = await openExerciseManager(page);
    await manager.getByRole('button', { name: 'Add Exercise', exact: true }).click();
    manager = await resolveAppSurface(page, /Add New Exercise|Save Exercise/i, 120_000);
    await manager.getByLabel('Title', { exact: true }).fill(exerciseTitle);
    await manager.getByLabel('Category', { exact: true }).fill('Jarvis UAT');
    await manager.getByLabel('Timing / duration / reps', { exact: true }).fill('1 controlled test');

    registerSyntheticRecord({
      entityType: 'exercise_repository',
      alias: 'UAT_EXERCISE_A',
      syntheticId: exerciseTitle,
    });
    registered = true;

    await manager.getByRole('button', { name: 'Save Exercise', exact: true }).click();
    manager = await resolveAppSurface(
      page,
      /Exercise saved|Add New Exercise|Current Exercise Repository/i,
      120_000,
    );
    const successVisible = await manager
      .getByText('Exercise saved.', { exact: true })
      .isVisible()
      .catch(() => false);
    diagnostics.mark('T2_SAVE_FEEDBACK_CHECKED', { success_visible: successVisible });
    if (!successVisible) findings.push('SAVE_SUCCESS_MESSAGE_MISSING');

    let editSurface = await openEditSection(page);
    const visibleBeforeRefresh = await chooseExerciseOption(editSurface, exerciseTitle);
    diagnostics.mark('T3_IMMEDIATE_REPOSITORY_CHECK', {
      synthetic_record_visible: visibleBeforeRefresh,
    });
    if (!visibleBeforeRefresh) findings.push('SYNTHETIC_EXERCISE_NOT_VISIBLE_AFTER_SAVE');

    await page.reload({ waitUntil: 'domcontentloaded' });
    editSurface = await openEditSection(page);
    const visibleAfterRefresh = await chooseExerciseOption(editSurface, exerciseTitle);
    diagnostics.mark('T4_REFRESH_PERSISTENCE_CHECK', {
      synthetic_record_visible: visibleAfterRefresh,
    });
    if (!visibleAfterRefresh) findings.push('SYNTHETIC_EXERCISE_NOT_PERSISTENT_AFTER_REFRESH');
  } finally {
    if (registered) {
      cleaned = await removeSyntheticExercise(page).catch(() => false);
      if (cleaned) markSyntheticRecordCleaned(exerciseTitle);
    }
    markMutationRouteComplete('HM-ADMIN-EXERCISE-REPOSITORY-001');
    diagnostics.mark('T5_SYNTHETIC_CLEANUP', { cleaned });
    await diagnostics.attach(testInfo);
  }

  expect(cleaned, 'Jarvis could not confirm cleanup of the synthetic exercise record.').toBe(true);
  expect(findings, `Jarvis detected: ${findings.join(', ')}`).toEqual([]);
});
