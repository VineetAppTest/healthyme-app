import { mkdirSync, writeFileSync } from 'node:fs';
import type {
  FullConfig,
  FullResult,
  Reporter,
  Suite,
  TestCase,
  TestResult,
} from '@playwright/test/reporter';

type SafeTestResult = {
  route_id: string;
  title: string;
  status: string;
  duration_ms: number;
  retry_count: number;
};

function routeId(title: string): string {
  return title.match(/^(HM-[A-Z0-9-]+)/)?.[1] || 'JARVIS-CONTRACT';
}

class SafeReporter implements Reporter {
  private readonly results: SafeTestResult[] = [];

  onBegin(_config: FullConfig, suite: Suite): void {
    console.log(`Jarvis is executing ${suite.allTests().length} approved test(s).`);
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    const safe = {
      route_id: routeId(test.title),
      title: test.title,
      status: result.status,
      duration_ms: result.duration,
      retry_count: result.retry,
    };
    this.results.push(safe);
    console.log(`${safe.status.toUpperCase()} ${safe.route_id} ${safe.duration_ms}ms retry=${safe.retry_count}`);
  }

  onError(): void {
    console.log('Jarvis runner error recorded; raw error details are withheld by privacy policy.');
  }

  onEnd(result: FullResult): void {
    mkdirSync('artifacts', { recursive: true });
    const output = {
      jarvis_run_id: process.env.JARVIS_RUN_ID || 'local',
      completed_at: new Date().toISOString(),
      overall_status: result.status,
      tests: this.results,
    };
    writeFileSync('artifacts/jarvis-safe-results.json', `${JSON.stringify(output, null, 2)}\n`);
    console.log(`Jarvis completed with status ${result.status}.`);
  }
}

export default SafeReporter;
