import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const runnerTemp = process.env.RUNNER_TEMP || '.jarvis-tmp';
const resultsPath = 'artifacts/jarvis-safe-results.json';
const evidencePath = 'artifacts/jarvis-evidence-security.json';
const summaryPath = process.env.GITHUB_STEP_SUMMARY;
const safeStatusPath = join(runnerTemp, 'jarvis-safe-status.json');

mkdirSync(runnerTemp, { recursive: true });

const results = existsSync(resultsPath)
  ? JSON.parse(readFileSync(resultsPath, 'utf8'))
  : { overall_status: 'failed', tests: [] };
const evidence = existsSync(evidencePath)
  ? JSON.parse(readFileSync(evidencePath, 'utf8'))
  : { status: 'fail', findings: [{ type: 'missing_evidence_security_report' }] };

const tests = (results.tests || []).map((test) => ({
  route_id: test.route_id,
  status: test.status,
  duration_ms: test.duration_ms,
  retry_count: test.retry_count,
}));
const passed = tests.filter((test) => test.status === 'passed').length;
const failed = tests.filter((test) => test.status !== 'passed').length;

const safeStatus = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  environment: process.env.JARVIS_ENVIRONMENT || 'uat',
  access_mode: process.env.JARVIS_ACCESS_MODE || 'read_only',
  privacy_mode: process.env.JARVIS_PRIVACY_MODE || 'strict',
  overall_status: results.overall_status,
  evidence_security_status: evidence.status,
  evidence_security_findings: Array.isArray(evidence.findings) ? evidence.findings.length : 1,
  passed_test_count: passed,
  failed_test_count: failed,
  tests,
};

writeFileSync(safeStatusPath, `${JSON.stringify(safeStatus, null, 2)}\n`);

if (summaryPath) {
  const rows = tests.length
    ? tests
        .map(
          (test) =>
            `| ${test.route_id} | ${test.status} | ${test.duration_ms} ms | ${test.retry_count} |`,
        )
        .join('\n')
    : '| No safe test result available | failed | - | - |';

  const markdown = [
    '## Jarvis UAT privacy-safe result',
    '',
    `- Environment: ${safeStatus.environment}`,
    `- Access mode: ${safeStatus.access_mode}`,
    `- Privacy mode: ${safeStatus.privacy_mode}`,
    `- Passed tests: ${passed}`,
    `- Failed tests: ${failed}`,
    `- Evidence-security scan: ${safeStatus.evidence_security_status}`,
    `- Identifiable-data findings: ${safeStatus.evidence_security_findings}`,
    '',
    '| Route | Status | Duration | Retries |',
    '|---|---:|---:|---:|',
    rows,
    '',
    'Raw page content, member details, health data, credentials and network bodies are not included in this summary.',
    '',
  ].join('\n');
  writeFileSync(summaryPath, markdown, { flag: 'a' });
}

console.log(
  JSON.stringify(
    {
      jarvis_run_id: safeStatus.jarvis_run_id,
      passed_test_count: passed,
      failed_test_count: failed,
      evidence_security_status: safeStatus.evidence_security_status,
      status: 'safe_summary_written',
    },
    null,
    2,
  ),
);
