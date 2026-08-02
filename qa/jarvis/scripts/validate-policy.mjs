import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const policyPath = 'policies/uat-access-policy.json';
const fixturePath = 'fixtures/uat-test-data.json';
const errors = [];

const policy = JSON.parse(readFileSync(policyPath, 'utf8'));
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
const fixtureText = JSON.stringify(fixture);

if (policy.evidence?.github_artifact_upload !== false) {
  errors.push('GitHub artifact upload must remain disabled.');
}
if (policy.evidence?.retention !== 'runner_lifetime_only') {
  errors.push('Evidence retention must be runner_lifetime_only.');
}
if (policy.environments?.production?.mutation !== 'blocked') {
  errors.push('Production mutation must remain blocked.');
}
if (policy.approval_gates?.deployment?.automatic_deployment !== false) {
  errors.push('Jarvis automatic deployment must remain disabled.');
}
if (fixture.classification !== 'synthetic_uat') {
  errors.push('The UAT fixture must be classified as synthetic_uat.');
}
if (!fixture.rules?.cleanup_required) {
  errors.push('The UAT fixture must require cleanup.');
}

const subjectIds = new Set((fixture.subjects || []).map((subject) => subject.healthyme_id));
for (const allowedId of policy.test_data?.allowed_healthyme_ids || []) {
  if (!subjectIds.has(allowedId)) {
    errors.push(`Allowed HealthyMe identity is missing from fixture: ${allowedId}.`);
  }
}

if (/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(fixtureText)) {
  errors.push('Email values are prohibited in the committed UAT fixture.');
}
if (/\b(?:\+?\d[\d\s().-]{7,}\d)\b/.test(fixtureText)) {
  errors.push('Phone-like values are prohibited in the committed UAT fixture.');
}

const report = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  checked_at: new Date().toISOString(),
  policy_name: policy.policy_name,
  fixture_classification: fixture.classification,
  github_artifact_upload: policy.evidence?.github_artifact_upload,
  retention: policy.evidence?.retention,
  errors,
  status: errors.length === 0 ? 'pass' : 'fail',
};

mkdirSync('artifacts', { recursive: true });
writeFileSync('artifacts/jarvis-policy-validation.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

if (errors.length > 0) process.exitCode = 1;
