import { mkdirSync, writeFileSync } from 'node:fs';

const baseUrl = process.env.JARVIS_BASE_URL || 'https://healthymeappbyankita.streamlit.app';
const suite = process.env.JARVIS_SUITE || 'all';
const environment = process.env.JARVIS_ENVIRONMENT || 'uat';
const accessMode = process.env.JARVIS_ACCESS_MODE || 'read_only';
const privacyMode = process.env.JARVIS_PRIVACY_MODE || 'strict';
const requireAuth = String(process.env.JARVIS_REQUIRE_AUTH || 'false').toLowerCase() === 'true';
const mutationEnabled = String(process.env.JARVIS_MUTATION_ENABLED || 'false').toLowerCase() === 'true';
const mutationApproved = String(process.env.JARVIS_MUTATION_APPROVED || 'false').toLowerCase() === 'true';
const productionReadOnlyApproved =
  String(process.env.JARVIS_PRODUCTION_READ_ONLY_APPROVED || 'false').toLowerCase() === 'true';
const deployIntent = String(process.env.JARVIS_DEPLOY_INTENT || 'false').toLowerCase() === 'true';
const ownerDeployApproval =
  String(process.env.JARVIS_OWNER_DEPLOY_APPROVAL || 'false').toLowerCase() === 'true';

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

if (!['all', 'public', 'member', 'admin', 'auth'].includes(suite)) {
  errors.push(`Unsupported JARVIS_SUITE: ${suite}. Use all, public, member, admin or auth.`);
}
if (!['uat', 'production'].includes(environment)) {
  errors.push(`Unsupported JARVIS_ENVIRONMENT: ${environment}. Use uat or production.`);
}
if (!['read_only', 'mutation'].includes(accessMode)) {
  errors.push(`Unsupported JARVIS_ACCESS_MODE: ${accessMode}. Use read_only or mutation.`);
}
if (!['strict', 'diagnostic'].includes(privacyMode)) {
  errors.push(`Unsupported JARVIS_PRIVACY_MODE: ${privacyMode}. Use strict or diagnostic.`);
}

if (environment === 'production' && accessMode === 'mutation') {
  errors.push('Jarvis mutation testing is prohibited in production.');
}
if (environment === 'production' && accessMode === 'read_only' && !productionReadOnlyApproved) {
  errors.push('Production read-only testing requires the explicit production approval checkbox.');
}
if (accessMode === 'mutation' && environment !== 'uat') {
  errors.push('Mutation testing is restricted to the UAT environment.');
}
if (accessMode === 'mutation' && !mutationEnabled) {
  errors.push('Mutation testing requires repository variable JARVIS_MUTATION_ENABLED=true.');
}
if (accessMode === 'mutation' && !mutationApproved) {
  errors.push('Mutation testing requires the explicit manual mutation approval checkbox.');
}
if (privacyMode === 'diagnostic') {
  warnings.push('Diagnostic media is failure-only, remains on the ephemeral runner and is deleted before job completion.');
}
if (deployIntent && !ownerDeployApproval) {
  warnings.push('Deployment eligibility will remain blocked until Vineet owner approval is recorded.');
}

if (memberEmailConfigured !== memberPasswordConfigured) {
  errors.push('Member credentials are only partially configured. Set both secrets or neither.');
}
if (adminEmailConfigured !== adminPasswordConfigured) {
  errors.push('Admin credentials are only partially configured. Set both secrets or neither.');
}

const memberRouteRequested = suite === 'all' || suite === 'member' || suite === 'auth';
const adminRouteRequested = suite === 'all' || suite === 'admin' || suite === 'auth';

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
      headers: { 'User-Agent': 'HealthyMe-Jarvis-QC/0.4' },
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
  environment,
  access_mode: accessMode,
  privacy_mode: privacyMode,
  require_authenticated_route: requireAuth,
  policy: {
    github_artifact_upload: false,
    evidence_retention: 'runner_lifetime_only',
    production_mutation: 'blocked',
    automatic_deployment: false,
  },
  approvals: {
    mutation_repository_gate: mutationEnabled,
    mutation_manual_gate: mutationApproved,
    production_read_only_gate: productionReadOnlyApproved,
    deploy_intent: deployIntent,
    owner_deploy_approval: ownerDeployApproval,
  },
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

if (errors.length > 0) process.exitCode = 1;
