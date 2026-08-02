import { mkdirSync, writeFileSync } from 'node:fs';

const baseUrl = process.env.JARVIS_BASE_URL || 'https://healthymeappbyankita.streamlit.app';
const suite = process.env.JARVIS_SUITE || 'all';
const requireAuth = String(process.env.JARVIS_REQUIRE_AUTH || 'false').toLowerCase() === 'true';

const memberEmailConfigured = Boolean(process.env.JARVIS_MEMBER_EMAIL);
const memberPasswordConfigured = Boolean(process.env.JARVIS_MEMBER_PASSWORD);
const adminEmailConfigured = Boolean(process.env.JARVIS_ADMIN_EMAIL);
const adminPasswordConfigured = Boolean(process.env.JARVIS_ADMIN_PASSWORD);

const errors = [];
const warnings = [];

let parsedUrl;
try {
  parsedUrl = new URL(baseUrl);
  if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
    errors.push('JARVIS_BASE_URL must use http or https.');
  }
  if (process.env.CI && parsedUrl.protocol !== 'https:') {
    errors.push('CI runs require an HTTPS JARVIS_BASE_URL.');
  }
} catch {
  errors.push('JARVIS_BASE_URL is not a valid URL.');
}

if (!['all', 'public', 'member', 'admin'].includes(suite)) {
  errors.push(`Unsupported JARVIS_SUITE: ${suite}. Use all, public, member or admin.`);
}

if (memberEmailConfigured !== memberPasswordConfigured) {
  errors.push('Member credentials are only partially configured. Set both secrets or neither.');
}
if (adminEmailConfigured !== adminPasswordConfigured) {
  errors.push('Admin credentials are only partially configured. Set both secrets or neither.');
}

const memberRouteRequested = suite === 'all' || suite === 'member';
const adminRouteRequested = suite === 'all' || suite === 'admin';

if (memberRouteRequested && !memberEmailConfigured) {
  const message = 'Authenticated member route is disabled until both member secrets are configured.';
  if (requireAuth) errors.push(message);
  else warnings.push(message);
}

if (adminRouteRequested && !adminEmailConfigured) {
  const message = 'Authenticated admin route is disabled until both admin secrets are configured.';
  if (requireAuth) errors.push(message);
  else warnings.push(message);
}

if (
  memberEmailConfigured &&
  adminEmailConfigured &&
  process.env.JARVIS_MEMBER_EMAIL?.trim().toLowerCase() ===
    process.env.JARVIS_ADMIN_EMAIL?.trim().toLowerCase()
) {
  errors.push('Member and admin identities must use different email addresses.');
}

let reachability = {
  attempted: false,
  reachable: false,
  status: null,
  final_url: '',
  elapsed_ms: null,
  error: '',
};

if (parsedUrl && errors.length === 0) {
  reachability.attempted = true;
  const startedAt = Date.now();
  try {
    const response = await fetch(parsedUrl, {
      redirect: 'follow',
      signal: AbortSignal.timeout(30_000),
      headers: {
        'User-Agent': 'HealthyMe-Jarvis-QC/0.3',
      },
    });
    reachability = {
      attempted: true,
      reachable: response.status < 500,
      status: response.status,
      final_url: response.url,
      elapsed_ms: Date.now() - startedAt,
      error: '',
    };
    if (!reachability.reachable) {
      warnings.push(
        `Advisory HTTP preflight returned ${response.status}; Chromium remains the authoritative availability check.`,
      );
    }
  } catch (error) {
    reachability = {
      attempted: true,
      reachable: false,
      status: null,
      final_url: '',
      elapsed_ms: Date.now() - startedAt,
      error: error instanceof Error ? error.message : String(error),
    };
    warnings.push(
      `Advisory HTTP preflight could not reach HealthyMe (${reachability.error}); Chromium will perform the authoritative check.`,
    );
  }
}

const report = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  checked_at: new Date().toISOString(),
  base_url: parsedUrl ? `${parsedUrl.origin}${parsedUrl.pathname}` : '<invalid>',
  suite,
  require_authenticated_route: requireAuth,
  credentials: {
    member_email_configured: memberEmailConfigured,
    member_password_configured: memberPasswordConfigured,
    admin_email_configured: adminEmailConfigured,
    admin_password_configured: adminPasswordConfigured,
  },
  routes: {
    public_enabled: suite === 'all' || suite === 'public',
    member_enabled: memberRouteRequested && memberEmailConfigured && memberPasswordConfigured,
    admin_enabled: adminRouteRequested && adminEmailConfigured && adminPasswordConfigured,
  },
  reachability,
  warnings,
  errors,
};

mkdirSync('artifacts', { recursive: true });
writeFileSync('artifacts/jarvis-preflight.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

if (errors.length > 0) {
  process.exitCode = 1;
}
