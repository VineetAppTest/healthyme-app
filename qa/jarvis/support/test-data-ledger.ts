import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

type LedgerRecord = {
  entity_type: string;
  alias: string;
  synthetic_id: string;
  status: 'created' | 'cleaned';
};

type MutationLedger = {
  jarvis_run_id: string;
  route_completed: boolean;
  route_id?: string;
  records: LedgerRecord[];
};

const runnerTemp = process.env.RUNNER_TEMP || '.jarvis-tmp';
const ledgerPath = join(runnerTemp, 'jarvis-mutation-ledger.json');
const namespace = process.env.JARVIS_MUTATION_NAMESPACE || 'jarvis_uat';

function readLedger(): MutationLedger {
  if (!existsSync(ledgerPath)) {
    throw new Error('Jarvis mutation ledger is missing. Mutation routes require prepared UAT state.');
  }
  return JSON.parse(readFileSync(ledgerPath, 'utf8')) as MutationLedger;
}

function writeLedger(ledger: MutationLedger): void {
  mkdirSync(runnerTemp, { recursive: true });
  writeFileSync(ledgerPath, `${JSON.stringify(ledger, null, 2)}\n`);
}

function validateSyntheticId(syntheticId: string): void {
  const allowedIdentity = ['jarvis_member', 'jarvis_admin'].includes(syntheticId);
  if (!allowedIdentity && !syntheticId.startsWith(`${namespace}_`)) {
    throw new Error(`Synthetic test record IDs must use the ${namespace}_ namespace.`);
  }
}

export function registerSyntheticRecord(input: {
  entityType: string;
  alias: string;
  syntheticId: string;
}): void {
  validateSyntheticId(input.syntheticId);
  const ledger = readLedger();
  if (ledger.records.some((record) => record.synthetic_id === input.syntheticId)) {
    throw new Error(`Synthetic record is already registered: ${input.syntheticId}.`);
  }
  ledger.records.push({
    entity_type: input.entityType,
    alias: input.alias,
    synthetic_id: input.syntheticId,
    status: 'created',
  });
  writeLedger(ledger);
}

export function markSyntheticRecordCleaned(syntheticId: string): void {
  const ledger = readLedger();
  const record = ledger.records.find((item) => item.synthetic_id === syntheticId);
  if (!record) throw new Error(`Synthetic record is not registered: ${syntheticId}.`);
  record.status = 'cleaned';
  writeLedger(ledger);
}

export function markMutationRouteComplete(routeId: string): void {
  const ledger = readLedger();
  ledger.route_completed = true;
  ledger.route_id = routeId;
  writeLedger(ledger);
}
