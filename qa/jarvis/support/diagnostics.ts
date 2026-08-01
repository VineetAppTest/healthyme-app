import type { Page, TestInfo } from '@playwright/test';

type TimelineEvent = {
  checkpoint: string;
  elapsed_ms: number;
  iso_time: string;
  detail?: Record<string, unknown>;
};

type BrowserDiagnostic = {
  type: 'console' | 'request_failed' | 'http_error';
  at: string;
  detail: Record<string, unknown>;
};

export class JarvisDiagnostics {
  private readonly startedAt = Date.now();
  private readonly timeline: TimelineEvent[] = [];
  private readonly browserEvents: BrowserDiagnostic[] = [];

  constructor(private readonly page: Page) {
    page.on('console', (message) => {
      if (!['warning', 'error'].includes(message.type())) return;
      this.browserEvents.push({
        type: 'console',
        at: new Date().toISOString(),
        detail: {
          level: message.type(),
          text: message.text(),
          location: message.location(),
        },
      });
    });

    page.on('requestfailed', (request) => {
      this.browserEvents.push({
        type: 'request_failed',
        at: new Date().toISOString(),
        detail: {
          method: request.method(),
          url: request.url(),
          failure: request.failure(),
        },
      });
    });

    page.on('response', (response) => {
      if (response.status() < 400) return;
      this.browserEvents.push({
        type: 'http_error',
        at: new Date().toISOString(),
        detail: {
          status: response.status(),
          status_text: response.statusText(),
          url: response.url(),
        },
      });
    });
  }

  mark(checkpoint: string, detail?: Record<string, unknown>): void {
    this.timeline.push({
      checkpoint,
      elapsed_ms: Date.now() - this.startedAt,
      iso_time: new Date().toISOString(),
      detail,
    });
  }

  async attach(testInfo: TestInfo): Promise<void> {
    const navigationEntries = await this.page
      .evaluate(() =>
        performance.getEntriesByType('navigation').map((entry) => {
          const navigation = entry as PerformanceNavigationTiming;
          return {
            name: navigation.name,
            duration: navigation.duration,
            dom_content_loaded: navigation.domContentLoadedEventEnd,
            load_event_end: navigation.loadEventEnd,
            response_end: navigation.responseEnd,
            type: navigation.type,
          };
        }),
      )
      .catch(() => []);

    await testInfo.attach('jarvis-timeline.json', {
      body: Buffer.from(
        JSON.stringify(
          {
            final_url: this.page.url(),
            total_elapsed_ms: Date.now() - this.startedAt,
            checkpoints: this.timeline,
            navigation_entries: navigationEntries,
          },
          null,
          2,
        ),
      ),
      contentType: 'application/json',
    });

    await testInfo.attach('jarvis-browser-diagnostics.json', {
      body: Buffer.from(JSON.stringify(this.browserEvents, null, 2)),
      contentType: 'application/json',
    });
  }
}
