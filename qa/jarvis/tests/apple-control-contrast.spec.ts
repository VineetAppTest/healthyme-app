import { expect, test } from '@playwright/test';
import type { Locator } from '@playwright/test';


const fixtureUrl =
  process.env.JARVIS_APPLE_FIXTURE_URL || 'http://127.0.0.1:8502';

type Rgba = [number, number, number, number];

function parseCssColor(value: string): Rgba {
  const match = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/i);
  if (!match) throw new Error(`Unsupported computed colour: ${value}`);
  return [
    Number(match[1]),
    Number(match[2]),
    Number(match[3]),
    match[4] === undefined ? 1 : Number(match[4]),
  ];
}

function linearise(channel: number): number {
  const normalised = channel / 255;
  return normalised <= 0.04045
    ? normalised / 12.92
    : Math.pow((normalised + 0.055) / 1.055, 2.4);
}

function luminance(colour: Rgba): number {
  return (
    0.2126 * linearise(colour[0]) +
    0.7152 * linearise(colour[1]) +
    0.0722 * linearise(colour[2])
  );
}

function contrastRatio(foreground: Rgba, background: Rgba): number {
  const foregroundLuminance = luminance(foreground);
  const backgroundLuminance = luminance(background);
  const lighter = Math.max(foregroundLuminance, backgroundLuminance);
  const darker = Math.min(foregroundLuminance, backgroundLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

async function expectReadableSurface(control: Locator): Promise<void> {
  const colours = await control.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      background: style.backgroundColor,
      colour: style.color,
      textFill: style.getPropertyValue('-webkit-text-fill-color'),
      colorScheme: style.colorScheme,
    };
  });

  const background = parseCssColor(colours.background);
  const foreground = parseCssColor(colours.textFill || colours.colour);
  expect(background[3]).toBe(1);
  expect(background[0]).toBeGreaterThanOrEqual(248);
  expect(background[1]).toBeGreaterThanOrEqual(245);
  expect(background[2]).toBeGreaterThanOrEqual(239);
  expect(contrastRatio(foreground, background)).toBeGreaterThanOrEqual(4.5);
  expect(colours.colorScheme).toContain('light');
}

test('HM-APPLE-001: controls remain readable in Apple light and dark modes', async ({ page }) => {
  await page.goto(fixtureUrl, { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'HealthyMe Apple contrast fixture' }),
  ).toBeVisible({ timeout: 90_000 });

  await page.getByLabel('Text input', { exact: true }).fill('Readable Apple text');
  await page.getByLabel('Password input', { exact: true }).fill('Synthetic password');
  await page.getByLabel('Text area', { exact: true }).fill('Readable Body-Mind response');

  const controls = page.locator(
    [
      '[data-testid="stTextInput"] input',
      '[data-testid="stTextArea"] textarea',
      '[data-testid="stNumberInput"] input',
      '[data-testid="stDateInput"] input',
      '[data-testid="stTimeInput"] input',
      '[data-testid="stSelectbox"] [data-baseweb="select"]>div',
      '[data-testid="stMultiSelect"] [data-baseweb="select"]>div',
    ].join(','),
  );

  const controlCount = await controls.count();
  expect(controlCount).toBeGreaterThanOrEqual(9);
  for (let index = 0; index < controlCount; index += 1) {
    const control = controls.nth(index);
    if (await control.isVisible()) await expectReadableSurface(control);
  }

  await expect(page.getByLabel('Checkbox input', { exact: true })).toBeChecked();
  await expect(page.getByLabel('Toggle input', { exact: true })).toBeChecked();
  await expect(page.getByTestId('stFileUploaderDropzone')).toBeVisible();
  await expect(page.getByTestId('stDataFrame')).toBeVisible();
});
