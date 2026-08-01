import type { Frame, Page } from '@playwright/test';

import { redactUrl } from './diagnostics';

export type AppSurface = Page | Frame;

const DEFAULT_APP_SIGNAL = /(HealthyMe|Secure Login|Member Home|Admin Dashboard)/i;

async function bodyText(surface: Page | Frame): Promise<string> {
  return surface
    .locator('body')
    .innerText({ timeout: 1_500 })
    .catch(() => '');
}

export function surfaceUrl(surface: AppSurface): string {
  return surface.url();
}

/**
 * Resolve the document that actually contains HealthyMe.
 *
 * Streamlit Community Cloud can host the app inside a cross-origin iframe while
 * local/staging deployments may render directly in the main document. Jarvis
 * must support both without hard-coding one hosting arrangement.
 *
 * A single host reload is allowed halfway through the wait. This handles a
 * Community Cloud shell that has created the app iframe but has not completed a
 * cold start. The recovery remains inside the same route attempt and is visible
 * in the video/network evidence.
 */
export async function resolveAppSurface(
  page: Page,
  requiredSignal: RegExp = DEFAULT_APP_SIGNAL,
  timeoutMs = 90_000,
): Promise<AppSurface> {
  const startedAt = Date.now();
  const deadline = startedAt + timeoutMs;
  const recoveryAt = startedAt + Math.min(Math.floor(timeoutMs / 2), 45_000);
  let recoveryAttempted = false;

  while (Date.now() < deadline) {
    const mainText = await bodyText(page);
    if (requiredSignal.test(mainText)) {
      return page;
    }

    for (const frame of page.frames()) {
      if (frame === page.mainFrame() || frame.isDetached() || frame.url() === 'about:blank') {
        continue;
      }
      const text = await bodyText(frame);
      if (requiredSignal.test(text)) {
        return frame;
      }
    }

    if (!recoveryAttempted && Date.now() >= recoveryAt) {
      recoveryAttempted = true;
      await page
        .reload({ waitUntil: 'domcontentloaded', timeout: 60_000 })
        .catch(() => undefined);
    }

    await page.waitForTimeout(500);
  }

  const frameUrls = page.frames().map((frame) => redactUrl(frame.url()));
  throw new Error(
    `Jarvis could not resolve the HealthyMe application surface within ${timeoutMs} ms. ` +
      `Host URL: ${redactUrl(page.url())}; frames: ${JSON.stringify(frameUrls)}; ` +
      `cold_start_recovery_attempted=${recoveryAttempted}`,
  );
}

export function loginSubmitAction(surface: AppSurface) {
  return surface
    .getByRole('button', {
      name: /Continue with Supabase|Sign in securely/i,
    })
    .first();
}
