import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const runnerTemp = process.env.RUNNER_TEMP || '.jarvis-tmp';
const accessMode = process.env.JARVIS_ACCESS_MODE || 'read_only';
const ledgerPath = join(runnerTemp, 'jarvis-mutation-ledger.json');
const statusPath = join(runnerTemp, 'jarvis-cleanup-status.json');
const errors = [];
let recordCount = 0;
let cleanedCount = 0;
let routeCompleted = accessMode !== 'mutation';

if (accessMode === 'mutation') {
  if (!existsSync(ledgerPath)) {
    errors.push('Mutation cleanup ledger is missing.');
  } else {
    const ledger = JSON.parse(readFileSync(ledgerPath, 'utf8'));
    routeCompleted = ledger.route_completed === true;
    if (!routeCompleted) errors.push('Mutation route did not mark its controlled operation complete.');
    recordCount = Array.isArray(ledger.records) ? ledger.records.length : 0;
    cleanedCount = (ledger.records || []).filter((record) => record.status === 'cleaned').length;
    const uncleared = (ledger.records || []).filter((record) => record.status !== 'cleaned');
    if (uncleared.length > 0) {
      errors.push(`${uncleared.length} synthetic UAT record(s) were not cleaned.`);
    }
  }
}

const report = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  checked_at: new Date().toISOString(),
  access_mode: accessMode,
  route_completed: routeCompleted,
  registered_record_count: recordCount,
  cleaned_record_count: cleanedCount,
  errors,
  status: errors.length === 0 ? 'pass' : 'fail',
};

writeFileSync(statusPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

const summaryPath = process.env.GITHUB_STEP_SUMMARY;
if (summaryPath) {
  const text = [
    '### Jarvis UAT data cleanup',
    '',
    `- Access mode: ${accessMode}`,
    `- Cleanup status: ${report.status}`,
    `- Registered synthetic records: ${recordCount}`,
    `- Cleaned synthetic records: ${cleanedCount}`,
    '',
  ].join('\n');
  writeFileSync(summaryPath, text, { flag: 'a' });
}

if (errors.length > 0) process.exitCode = 1;
