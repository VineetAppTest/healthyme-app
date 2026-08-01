import type { Page, Request, TestInfo } from '@playwright/test';

type TimelineEvent = {
  checkpoint: string;
  elapsed_ms: number;
  iso_time: string;
  detail?: Record<string, unknown>;
};

type BrowserDiagnostic = {
  type: 'console' | 'page_error' | 'request_failed' | 'http_error' | 'network_timing';
  at: string;
  detail: Record<string, unknown>;
};

const SENSITIVE_QUERY_KEYS = new Set([
  'access_token',
  'authorization_id',
  'code',
  'code_challenge',
  'email',
  'id_token',
  'nonce',
  'password',
  'payload',
  'provider',
  'refresh_token',
  'state',
  'token',
]);

function isSensitiveKey(raw: string): boolean {
  const key = raw.toLowerCase();
  return (
    SENSITIVE_QUERY_KEYS.has(key) ||
    key.includes('password') ||
    key.includes('secret') ||
    key.endsWith('token')
  );
}

export function redactUrl(raw: string): string {
  try {
    const value = new URL(raw);
    const authenticationPath = /\/(auth|login|logout|oauth|callback)(\/|$)/i.test(value.pathname);
    for (const [key] of value.searchParams.entries()) {
      if (authenticationPath || isSensitiveKey(key)) {
        value.searchParams.set(key, '<redacted>');
      }
    }
    value.hash = value.hash ? '#<redacted>' : '';
    return value.toString();
  } catch {
    return raw.replace(
      /(access_token|authorization_id|code|code_challenge|id_token|nonce|password|payload|provider|refresh_token|state|token)=([^&\s]+)/gi,
      '$1=<redacted>',
    );
  }
}

export function redactText(raw: string): string {
  return raw
    .replace(/https?:\/\/[^\s"'<>]+/gi, (match) => redactUrl(match))
    .replace(/(Bearer\s+)[A-Za-z0-9._~-]+/gi, '$1<redacted>')
    .replace(/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g, '<redacted-jwt>')
    .replace(
      /(access_token|authorization_id|code|code_challenge|id_token|nonce|password|payload|provider|refresh_token|state|token)=([^&\s]+)/gi,
      '$1=<redacted>',
    );
}

export function sanitizeValue(value: unknown): unknown {
  if (typeof value === 'string') {
    return redactText(value);
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item));
  }
  if (value && typeof value === 'object') {
    const output: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) {
      output[key] = isSensitiveKey(key) ? '<redacted>' : sanitizeValue(item);
    }
    return output;
  }
  return value;
}

export class JarvisDiagnostics {
  private readonly startedAt = Date.now();
  private readonly timeline: TimelineEvent[] = [];
  private readonly browserEvents: BrowserDiagnostic[] = [];
  private readonly requestStartedAt = new WeakMap<Request, number>();
  private readonly runId =
    process.env.JARVIS_RUN_ID || `jarvis-local-${new Date().toISOString().replace(/[^0-9]/g, '')}`;

  constructor(
    private readonly page: Page,
    private readonly routeId: string,
  ) {
    page.on('console', (message) => {
      if (!['warning', 'error'].includes(message.type())) return;
      this.browserEvents.push({
        type: 'console',
        at: new Date().toISOString(),
        detail: {
          level: message.type(),
          text: redactText(message.text()),
          location: {
            ...message.location(),
            url: redactUrl(message.location().url || ''),
          },
        },
      });
    });

    page.on('pageerror', (error) => {
      this.browserEvents.push({
        type: 'page_error',
        at: new Date().toISOString(),
        detail: {
          name: error.name,
          message: redactText(error.message),
          stack: redactText(error.stack || ''),
        },
      });
    });

    page.on('request', (request) => {
      this.requestStartedAt.set(request, Date.now());
    });

    page.on('requestfailed', (request) => {
      this.browserEvents.push({
        type: 'request_failed',
        at: new Date().toISOString(),
        detail: {
          method: request.method(),
          resource_type: request.resourceType(),
          url: redactUrl(request.url()),
          failure: sanitizeValue(request.failure()) as Record<string, unknown> | null,
          elapsed_ms: Date.now() - (this.requestStartedAt.get(request) || Date.now()),
        },
      });
    });

    page.on('response', (response) => {
      const request = response.request();
      const elapsedMs = Date.now() - (this.requestStartedAt.get(request) || Date.now());
      const common = {
        method: request.method(),
        resource_type: request.resourceType(),
        status: response.status(),
        url: redactUrl(response.url()),
        elapsed_ms: elapsedMs,
      };

      if (response.status() >= 400) {
        this.browserEvents.push({
          type: 'http_error',
          at: new Date().toISOString(),
          detail: {
            ...common,
            status_text: response.statusText(),
          },
        });
      } else if (['document', 'fetch', 'xhr'].includes(request.resourceType())) {
        this.browserEvents.push({
          type: 'network_timing',
          at: new Date().toISOString(),
          detail: common,
        });
      }
    });
  }

  mark(checkpoint: string, detail?: Record<string, unknown>): void {
    this.timeline.push({
      checkpoint,
      elapsed_ms: Date.now() - this.startedAt,
      iso_time: new Date().toISOString(),
      detail: detail ? (sanitizeValue(detail) as Record<string, unknown>) : undefined,
    });
  }

  async attach(testInfo: TestInfo): Promise<void> {
    const frameNavigationEntries = [];
    for (const [index, frame] of this.page.frames().entries()) {
      const entries = await frame
        .evaluate(() =>
          performance.getEntriesByType('navigation').map((entry) => {
            const navigation = entry as PerformanceNavigationTiming;
            return {
              name: navigation.name,
              duration: navigation.duration,
              dom_content_loaded: navigation.domContentLoadedEventEnd,
              load_event_end: navigation.loadEventEnd,
              request_start: navigation.requestStart,
              response_start: navigation.responseStart,
              response_end: navigation.responseEnd,
              type: navigation.type,
            };
          }),
        )
        .catch(() => []);

      frameNavigationEntries.push({
        frame_index: index,
        frame_name: frame.name(),
        frame_url: redactUrl(frame.url()),
        navigation_entries: entries.map((entry) => ({
          ...entry,
          name: redactUrl(entry.name),
        })),
      });
    }

    const runMetadata = {
      jarvis_run_id: this.runId,
      route_id: this.routeId,
      git_sha: process.env.JARVIS_GIT_SHA || '',
      github_event: process.env.JARVIS_GITHUB_EVENT || '',
      base_url: redactUrl(process.env.JARVIS_BASE_URL || ''),
      project: testInfo.project.name,
      retry: testInfo.retry,
      worker_index: testInfo.workerIndex,
      status: testInfo.status,
      expected_status: testInfo.expectedStatus,
    };

    await testInfo.attach('jarvis-run-metadata.json', {
      body: Buffer.from(JSON.stringify(runMetadata, null, 2)),
      contentType: 'application/json',
    });

    await testInfo.attach('jarvis-timeline.json', {
      body: Buffer.from(
        JSON.stringify(
          {
            ...runMetadata,
            final_host_url: redactUrl(this.page.url()),
            total_elapsed_ms: Date.now() - this.startedAt,
            checkpoints: this.timeline,
            frame_navigation: frameNavigationEntries,
          },
          null,
          2,
        ),
      ),
      contentType: 'application/json',
    });

    await testInfo.attach('jarvis-browser-diagnostics.json', {
      body: Buffer.from(JSON.stringify(sanitizeValue(this.browserEvents), null, 2)),
      contentType: 'application/json',
    });
  }
}
