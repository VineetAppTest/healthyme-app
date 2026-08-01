import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.JARVIS_BASE_URL || 'https://healthymeappbyankita.streamlit.app';
const localTraceEnabled =
  !process.env.CI && String(process.env.JARVIS_ENABLE_LOCAL_TRACE || 'false').toLowerCase() === 'true';

export default defineConfig({
  testDir: './tests',
  outputDir: 'artifacts/test-results',
  timeout: 150_000,
  expect: {
    timeout: 45_000,
  },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'artifacts/html-report', open: 'never' }],
    ['json', { outputFile: 'artifacts/jarvis-results.json' }],
  ],
  use: {
    baseURL,
    actionTimeout: 30_000,
    navigationTimeout: 90_000,
    screenshot: 'only-on-failure',
    trace: localTraceEnabled ? 'retain-on-failure' : 'off',
    video: 'on',
    viewport: { width: 1440, height: 1000 },
  },
  projects: [
    {
      name: 'jarvis-chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
