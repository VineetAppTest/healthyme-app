import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const runnerTemp = process.env.RUNNER_TEMP || '.jarvis-tmp';
const safeStatusPath = join(runnerTemp, 'jarvis-safe-status.json');
const cleanupStatusPath = join(runnerTemp, 'jarvis-cleanup-status.json');
const deployIntent = String(process.env.JARVIS_DEPLOY_INTENT || 'false').toLowerCase() === 'true';
const ownerApproval =
  String(process.env.JARVIS_OWNER_DEPLOY_APPROVAL || 'false').toLowerCase() === 'true';

const blockers = [];
const safeStatus = existsSync(safeStatusPath)
  ? JSON.parse(readFileSync(safeStatusPath, 'utf8'))
  : null;
const cleanupStatus = existsSync(cleanupStatusPath)
  ? JSON.parse(readFileSync(cleanupStatusPath, 'utf8'))
  : null;

if (!safeStatus) blockers.push('privacy-safe test status is missing');
if (!cleanupStatus) blockers.push('test-data cleanup status is missing');
if (safeStatus && safeStatus.failed_test_count > 0) blockers.push('one or more Jarvis routes failed');
if (safeStatus && safeStatus.evidence_security_status !== 'pass') {
  blockers.push('evidence-security scan did not pass');
}
if (cleanupStatus && cleanupStatus.status !== 'pass') blockers.push('UAT test-data cleanup did not pass');
if (safeStatus?.environment === 'production' && safeStatus?.access_mode === 'mutation') {
  blockers.push('production mutation is prohibited');
}
if (deployIntent && !ownerApproval) blockers.push('Vineet owner approval is required');

const technicallyEligible = blockers.filter((item) => item !== 'Vineet owner approval is required').length === 0;
const decision = !deployIntent
  ? 'not_requested'
  : blockers.length === 0
    ? 'eligible_for_external_deployment_workflow'
    : 'blocked';

const report = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  evaluated_at: new Date().toISOString(),
  deploy_intent: deployIntent,
  owner_approval: ownerApproval,
  technically_eligible: technicallyEligible,
  decision,
  blockers,
  automatic_deployment_performed: false,
};

console.log(JSON.stringify(report, null, 2));

const summaryPath = process.env.GITHUB_STEP_SUMMARY;
if (summaryPath) {
  const markdown = [
    '### Jarvis deployment gate',
    '',
    `- Deployment requested: ${deployIntent ? 'yes' : 'no'}`,
    `- Technical eligibility: ${technicallyEligible ? 'yes' : 'no'}`,
    `- Vineet approval recorded: ${ownerApproval ? 'yes' : 'no'}`,
    `- Decision: ${decision}`,
    `- Jarvis deployed application code: no`,
    blockers.length ? `- Blockers: ${blockers.join('; ')}` : '- Blockers: none',
    '',
  ].join('\n');
  writeFileSync(summaryPath, markdown, { flag: 'a' });
}

const outputPath = process.env.GITHUB_OUTPUT;
if (outputPath) {
  writeFileSync(outputPath, `eligible=${decision === 'eligible_for_external_deployment_workflow'}\n`, {
    flag: 'a',
  });
}

if (deployIntent && blockers.length > 0) process.exitCode = 1;
