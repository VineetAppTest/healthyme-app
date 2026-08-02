import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const root = 'artifacts';
const findings = [];
const checkedFiles = [];

const sensitiveAssignment =
  /(access_token|authorization_id|code|code_challenge|id_token|nonce|password|payload|provider|refresh_token|state|token)=([^&\s"'<>]+)/gi;
const jwtPattern = /\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g;
const bearerPattern = /Bearer\s+(?!<redacted>)[A-Za-z0-9._~-]+/gi;

function acceptableValue(value) {
  const decoded = decodeURIComponent(value).toLowerCase();
  return decoded.includes('<redacted>') || decoded.includes('redacted-jwt');
}

function inspectText(path, text) {
  checkedFiles.push(relative(root, path));

  for (const match of text.matchAll(sensitiveAssignment)) {
    if (!acceptableValue(match[2])) {
      findings.push({
        file: relative(root, path),
        type: 'unredacted_sensitive_query_value',
        key: match[1],
      });
    }
  }

  if (jwtPattern.test(text)) {
    findings.push({ file: relative(root, path), type: 'jwt_like_value' });
  }
  jwtPattern.lastIndex = 0;

  if (bearerPattern.test(text)) {
    findings.push({ file: relative(root, path), type: 'bearer_value' });
  }
  bearerPattern.lastIndex = 0;
}

function inspectJsonReport(path) {
  const report = JSON.parse(readFileSync(path, 'utf8'));
  for (const suite of report.suites || []) {
    for (const spec of suite.specs || []) {
      for (const test of spec.tests || []) {
        for (const result of test.results || []) {
          for (const attachment of result.attachments || []) {
            if (!attachment.body) continue;
            if (!String(attachment.contentType || '').match(/json|text/)) continue;
            const decoded = Buffer.from(attachment.body, 'base64').toString('utf8');
            inspectText(`${path}#${spec.title}#${attachment.name}`, decoded);
          }
        }
      }
    }
  }
}

function walk(path) {
  for (const entry of readdirSync(path)) {
    const full = join(path, entry);
    const stats = statSync(full);
    if (stats.isDirectory()) {
      if (entry === 'html-report') continue;
      walk(full);
      continue;
    }

    if (full.endsWith('jarvis-results.json')) {
      inspectJsonReport(full);
    } else if (/\.(json|md|txt)$/i.test(full)) {
      inspectText(full, readFileSync(full, 'utf8'));
    } else if (/\.(zip|trace)$/i.test(full)) {
      findings.push({ file: relative(root, full), type: 'unsanitized_trace_archive' });
    }
  }
}

mkdirSync(root, { recursive: true });
if (existsSync(root)) walk(root);

const report = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  checked_at: new Date().toISOString(),
  checked_file_count: checkedFiles.length,
  findings,
  status: findings.length === 0 ? 'pass' : 'fail',
};

writeFileSync(join(root, 'jarvis-evidence-security.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

if (findings.length > 0) process.exitCode = 1;
