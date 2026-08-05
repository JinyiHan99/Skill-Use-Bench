import 'reflect-metadata';
import assert from 'node:assert/strict';
import { INestApplication } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { ExpressAdapter } from '@nestjs/platform-express';
import { SwaggerModule } from '@nestjs/swagger';
import { AppModule } from '../src/app.module';
import { createOpenApiDocument } from '../src/openapi';

interface AccountResponse {
  id: number;
  ownerName: string;
  balanceCents: number;
}

interface LedgerEntryResponse {
  id: number;
  requestId: string;
}

async function smoke(): Promise<void> {
  // The HTTP driver is supplied explicitly via `ExpressAdapter` instead of
  // `NestFactory`'s default-driver auto-discovery. Auto-discovery resolves
  // `@nestjs/platform-express` relative to `@nestjs/core`, so it only succeeds
  // when both are hoisted together; constructing the adapter here resolves it
  // from this sample's own declared dependency, independent of workspace
  // hoisting.
  await runScenario('express', () =>
    NestFactory.create(AppModule, new ExpressAdapter(), {
      abortOnError: false,
      logger: false,
    }),
  );
}

async function runScenario(
  adapterName: string,
  createApp: () => Promise<INestApplication>,
): Promise<void> {
  const app = await createApp();
  const document = createOpenApiDocument(app);

  SwaggerModule.setup('docs', app, document);
  assertOpenApiDocument(document);

  await app.listen(0, '127.0.0.1');

  try {
    const baseUrl = await app.getUrl();

    await assertUnauthorized(baseUrl);
    await assertClassValidator(baseUrl);
    await assertSeededAccounts(baseUrl, adapterName);
    await assertProjectCreation(baseUrl);
    await assertTransactionalTransfer(baseUrl, adapterName);
  } finally {
    await app.close();
  }
}

function assertOpenApiDocument(document: {
  openapi: string;
  paths: Record<string, unknown>;
  components?: { schemas?: Record<string, unknown> };
}): void {
  assert.equal(document.openapi, '3.0.0');
  assert.ok(document.paths['/accounts']);
  assert.ok(document.paths['/transfers']);
  assert.ok(document.paths['/projects']);
  assert.ok(document.components?.schemas?.CreateAccountDto);
  assert.ok(document.components?.schemas?.TransferDto);
  assert.ok(document.components?.schemas?.CreateProjectDto);
}

async function assertUnauthorized(baseUrl: string): Promise<void> {
  const response = await fetch(`${baseUrl}/accounts`);

  assert.equal(response.status, 401);
}

async function assertClassValidator(baseUrl: string): Promise<void> {
  const response = await apiFetch(baseUrl, '/accounts', {
    method: 'POST',
    body: {
      ownerName: 'A',
      balanceCents: -1,
    },
  });

  assert.equal(response.status, 400);
}

async function assertSeededAccounts(
  baseUrl: string,
  adapterName: string,
): Promise<void> {
  const response = await apiFetch(baseUrl, '/accounts');
  const accounts = await response.json() as AccountResponse[];

  assert.equal(response.status, 200);
  assert.equal(response.headers.get('x-showcase-enhancer'), 'interceptor');
  assert.equal(accounts.length, 2, adapterName);
  assert.equal(accounts[0]?.ownerName, 'Ada Lovelace');
}

async function assertProjectCreation(baseUrl: string): Promise<void> {
  const created = await apiFetch(baseUrl, '/projects', {
    method: 'POST',
    body: {
      name: 'Verify the full showcase',
      status: 'done',
    },
  });

  assert.equal(created.status, 201);

  const list = await apiFetch(baseUrl, '/projects');
  const projects = await list.json() as Array<{ name: string }>;

  assert.equal(projects.length, 2);
  assert.equal(projects[0]?.name, 'Verify the full showcase');
}

async function assertTransactionalTransfer(
  baseUrl: string,
  adapterName: string,
): Promise<void> {
  const committed = await apiFetch(baseUrl, '/transfers', {
    method: 'POST',
    requestId: `${adapterName}-commit`,
    body: {
      fromAccountId: 1,
      toAccountId: 2,
      amountCents: 1250,
    },
  });

  await assertStatus(committed, 201);
  assert.deepEqual(await committed.json(), {
    transactionActive: true,
    requestId: `${adapterName}-commit`,
  });

  const rolledBack = await apiFetch(baseUrl, '/transfers', {
    method: 'POST',
    requestId: `${adapterName}-rollback`,
    body: {
      fromAccountId: 1,
      toAccountId: 2,
      amountCents: 500,
      fail: true,
    },
  });

  await assertStatus(rolledBack, 409);

  const ledger = await apiFetch(baseUrl, '/ledger');
  const entries = await ledger.json() as LedgerEntryResponse[];
  assert.equal(entries.length, 1);
  assert.equal(entries[0]?.requestId, `${adapterName}-commit`);

  const accounts = await (await apiFetch(baseUrl, '/accounts')).json() as
    AccountResponse[];
  assert.equal(accounts[0]?.balanceCents, 8750);
  assert.equal(accounts[1]?.balanceCents, 8750);
}

async function apiFetch(
  baseUrl: string,
  path: string,
  options: {
    method?: string;
    body?: unknown;
    requestId?: string;
  } = {},
): Promise<Response> {
  return fetch(`${baseUrl}${path}`, {
    method: options.method ?? 'GET',
    headers: {
      'content-type': 'application/json',
      'x-api-key': 'showcase-secret',
      'x-request-id': options.requestId ?? 'showcase-smoke',
    },
    body: options.body === undefined
      ? undefined
      : JSON.stringify(options.body),
  });
}

async function assertStatus(
  response: Response,
  expectedStatus: number,
): Promise<void> {
  if (response.status === expectedStatus) {
    return;
  }

  throw new Error(
    `Expected ${expectedStatus}, received ${response.status}: ${
      await response.text()
    }`,
  );
}

void smoke().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
