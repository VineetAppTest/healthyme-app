import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const fixture = JSON.parse(readFileSync('fixtures/uat-test-data.json', 'utf8'));
const runnerTemp = process.env.RUNNER_TEMP || '.jarvis-tmp';
const runId = process.env.JARVIS_RUN_ID || 'jarvis-local';
const environment = process.env.JARVIS_ENVIRONMENT || 'uat';
const accessMode = process.env.JARVIS_ACCESS_MODE || 'read_only';
const privacyMode = process.env.JARVIS_PRIVACY_MODE || 'strict';

mkdirSync(runnerTemp, { recursive: true });

const context = {
  jarvis_run_id: runId,
  prepared_at: new Date().toISOString(),
  environment,
  access_mode: accessMode,
  privacy_mode: privacyMode,
  suite: process.env.JARVIS_SUITE || 'all',
  test_data_classification: fixture.classification,
  mutation_namespace: fixture.mutation_namespace,
  approved_subject_aliases: (fixture.subjects || []).map((subject) => subject.alias),
  cleanup_required: accessMode === 'mutation',
};

writeFileSync(join(runnerTemp, 'jarvis-run-context.json'), `${JSON.stringify(context, null, 2)}\n`);

if (accessMode === 'mutation') {
  const ledger = {
    jarvis_run_id: runId,
    route_completed: false,
    records: [],
  };
  writeFileSync(join(runnerTemp, 'jarvis-mutation-ledger.json'), `${JSON.stringify(ledger, null, 2)}\n`);
}

console.log(
  JSON.stringify(
    {
      jarvis_run_id: runId,
      environment,
      access_mode: accessMode,
      privacy_mode: privacyMode,
      test_data_classification: fixture.classification,
      cleanup_required: accessMode === 'mutation',
      status: 'prepared',
    },
    null,
    2,
  ),
);
