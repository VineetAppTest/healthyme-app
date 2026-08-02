import { expect, test } from '@playwright/test';

import { redactText, redactUrl, sanitizeValue } from '../support/diagnostics';

const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature';


test('Jarvis redacts authentication material from URLs', () => {
  const raw =
    `https://example.com/auth/login?provider=${jwt}` +
    '&state=secret-state&payload=opaque-payload&authorization_id=opaque-id';
  const safe = redactUrl(raw);

  for (const secret of [jwt, 'secret-state', 'opaque-payload', 'opaque-id']) {
    expect(safe).not.toContain(secret);
  }
  expect(safe).toContain('redacted');
});


test('Jarvis redacts nested diagnostic values and console text', () => {
  const sanitized = JSON.stringify(
    sanitizeValue({
      app_url: 'https://app.example.com/?authorization_id=opaque-id',
      provider: 'secret-provider',
      nested: {
        access_token: 'secret-access-token',
        message: `Bearer token-value ${jwt}`,
      },
    }),
  );

  for (const secret of [
    'opaque-id',
    'secret-provider',
    'secret-access-token',
    'token-value',
    jwt,
  ]) {
    expect(sanitized).not.toContain(secret);
  }
  expect(sanitized).toContain('redacted');

  const consoleText = redactText(
    `Navigation failed for https://example.com/oauth/callback?code=secret-code&state=secret-state ${jwt}`,
  );
  expect(consoleText).not.toContain('secret-code');
  expect(consoleText).not.toContain('secret-state');
  expect(consoleText).not.toContain(jwt);
});
