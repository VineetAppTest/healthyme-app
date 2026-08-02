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
  last_checkpoint?: string;
};

function routeId(title: string): string {
  return title.match(/^(HM-[A-Z0-9-]+)/)?.[1] || 'JARVIS-CONTRACT';
}

class SafeReporter implements Reporter {
  private readonly results: SafeTestResult[] = [];
  private readonly lastCheckpoint = new Map<string, string>();

  onBegin(_config: FullConfig, suite: Suite): void {
    console.log(`Jarvis is executing ${suite.allTests().length} approved test(s).`);
  }

  onStdOut(chunk: string | Buffer, test?: TestCase): void {
    if (!test) return;
    const text = chunk.toString();
    for (const match of text.matchAll(/JARVIS_CHECKPOINT\s+([A-Z0-9_]+)/g)) {
      const checkpoint = match[1];
      this.lastCheckpoint.set(test.id, checkpoint);
      console.log(`CHECKPOINT ${routeId(test.title)} ${checkpoint}`);
    }
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    const safe = {
      route_id: routeId(test.title),
      title: test.title,
      status: result.status,
      duration_ms: result.duration,
      retry_count: result.retry,
      last_checkpoint: this.lastCheckpoint.get(test.id),
    };
    this.results.push(safe);
    const checkpoint = safe.last_checkpoint ? ` checkpoint=${safe.last_checkpoint}` : '';
    console.log(
      `${safe.status.toUpperCase()} ${safe.route_id} ${safe.duration_ms}ms retry=${safe.retry_count}${checkpoint}`,
    );
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
