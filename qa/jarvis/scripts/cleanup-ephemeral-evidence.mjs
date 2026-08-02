import { existsSync, rmSync, writeFileSync } from 'node:fs';

const artifactRoot = 'artifacts';
const summaryPath = process.env.GITHUB_STEP_SUMMARY;

if (existsSync(artifactRoot)) {
  rmSync(artifactRoot, { recursive: true, force: true });
}

const removed = !existsSync(artifactRoot);

if (summaryPath) {
  const markdown = [
    '### Jarvis evidence disposal',
    '',
    `- GitHub artifact uploaded: no`,
    `- Temporary runner evidence deleted: ${removed ? 'yes' : 'no'}`,
    `- Retention: runner lifetime only`,
    '',
  ].join('\n');
  writeFileSync(summaryPath, markdown, { flag: 'a' });
}

console.log(
  JSON.stringify(
    {
      github_artifact_uploaded: false,
      temporary_evidence_deleted: removed,
      retention: 'runner_lifetime_only',
      status: removed ? 'pass' : 'fail',
    },
    null,
    2,
  ),
);

if (!removed) process.exitCode = 1;
