import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const root = 'artifacts';
const strictPrivacy = (process.env.JARVIS_PRIVACY_MODE || 'strict') === 'strict';
const findings = [];
const checkedFiles = [];

const sensitiveAssignment =
  /(access_token|authorization_id|code|code_challenge|email|id_token|nonce|password|payload|provider|refresh_token|state|token)=([^&\s"'<>]+)/gi;
const jwtPattern = /\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g;
const bearerPattern = /Bearer\s+(?!<redacted>)[A-Za-z0-9._~-]+/gi;
const emailPattern = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi;
const uuidPattern = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/gi;
const phonePattern = /(?:\+\d{8,15}|\b\d{3}[-\s]\d{3}[-\s]\d{4}\b)/g;

function acceptableValue(value) {
  const decoded = decodeURIComponent(value).toLowerCase();
  return decoded.includes('<redacted>') || decoded.includes('redacted-jwt');
}

function addPatternFinding(path, type, pattern, text) {
  const matches = text.match(pattern) || [];
  const unredacted = matches.filter((match) => !match.toLowerCase().includes('redacted'));
  if (unredacted.length > 0) {
    findings.push({ file: relative(root, path), type, count: unredacted.length });
  }
  pattern.lastIndex = 0;
}

function inspectText(path, text) {
  checkedFiles.push(relative(root, path));

  for (const match of text.matchAll(sensitiveAssignment)) {
    if (!acceptableValue(match[2])) {
      findings.push({
        file: relative(root, path),
        type: 'unredacted_sensitive_assignment',
        key: match[1],
      });
    }
  }

  addPatternFinding(path, 'jwt_like_value', jwtPattern, text);
  addPatternFinding(path, 'bearer_value', bearerPattern, text);
  addPatternFinding(path, 'email_value', emailPattern, text);
  addPatternFinding(path, 'uuid_identifier', uuidPattern, text);
  addPatternFinding(path, 'phone_like_value', phonePattern, text);
}

function walk(path) {
  for (const entry of readdirSync(path)) {
    const full = join(path, entry);
    const stats = statSync(full);
    if (stats.isDirectory()) {
      walk(full);
      continue;
    }

    if (/\.(json|md|txt)$/i.test(full)) {
      inspectText(full, readFileSync(full, 'utf8'));
    } else if (/\.(zip|trace)$/i.test(full)) {
      findings.push({ file: relative(root, full), type: 'unsanitized_trace_archive' });
    } else if (strictPrivacy && /\.(png|jpe?g|webm|mp4)$/i.test(full)) {
      findings.push({ file: relative(root, full), type: 'media_created_in_strict_privacy_mode' });
    }
  }
}

mkdirSync(root, { recursive: true });
if (existsSync(root)) walk(root);

const report = {
  jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
  checked_at: new Date().toISOString(),
  privacy_mode: process.env.JARVIS_PRIVACY_MODE || 'strict',
  checked_file_count: checkedFiles.length,
  findings,
  status: findings.length === 0 ? 'pass' : 'fail',
};

writeFileSync(join(root, 'jarvis-evidence-security.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

if (findings.length > 0) process.exitCode = 1;
