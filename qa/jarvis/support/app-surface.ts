import type { Frame, Page } from '@playwright/test';

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
 */
export async function resolveAppSurface(
  page: Page,
  requiredSignal: RegExp = DEFAULT_APP_SIGNAL,
  timeoutMs = 90_000,
): Promise<AppSurface> {
  const deadline = Date.now() + timeoutMs;

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

    await page.waitForTimeout(500);
  }

  const frameUrls = page.frames().map((frame) => frame.url());
  throw new Error(
    `Jarvis could not resolve the HealthyMe application surface within ${timeoutMs} ms. ` +
      `Host URL: ${page.url()}; frames: ${JSON.stringify(frameUrls)}`,
  );
}

export function loginSubmitAction(surface: AppSurface) {
  return surface
    .getByRole('button', {
      name: /Continue with Supabase|Sign in securely/i,
    })
    .first();
}
