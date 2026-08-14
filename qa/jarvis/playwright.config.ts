import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.JARVIS_BASE_URL || 'https://healthymeappbyankita.streamlit.app';
const privacyMode = process.env.JARVIS_PRIVACY_MODE || 'strict';
const diagnosticMediaEnabled = privacyMode === 'diagnostic';
const appleContrastSpec = /apple-control-contrast\.spec\.ts/;

export default defineConfig({
  testDir: './tests',
  outputDir: 'artifacts/test-results',
  timeout: 150_000,
  expect: {
    timeout: 45_000,
  },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['./reporters/safe-reporter.ts']],
  use: {
    baseURL,
    actionTimeout: 30_000,
    navigationTimeout: 90_000,
    screenshot: diagnosticMediaEnabled ? 'only-on-failure' : 'off',
    trace: 'off',
    video: diagnosticMediaEnabled ? 'retain-on-failure' : 'off',
    viewport: { width: 1440, height: 1000 },
  },
  projects: [
    {
      name: 'jarvis-chromium',
      testIgnore: appleContrastSpec,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'apple-macos-safari-light',
      testMatch: appleContrastSpec,
      use: {
        ...devices['Desktop Safari'],
        colorScheme: 'light',
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: 'apple-macos-safari-dark',
      testMatch: appleContrastSpec,
      use: {
        ...devices['Desktop Safari'],
        colorScheme: 'dark',
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: 'apple-iphone-safari-light',
      testMatch: appleContrastSpec,
      use: {
        ...devices['iPhone 15'],
        colorScheme: 'light',
      },
    },
    {
      name: 'apple-iphone-safari-dark',
      testMatch: appleContrastSpec,
      use: {
        ...devices['iPhone 15'],
        colorScheme: 'dark',
      },
    },
  ],
});
