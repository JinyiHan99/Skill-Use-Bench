import 'reflect-metadata';
import assert from 'node:assert/strict';
import { NestFactory } from '@nestjs/core';
import { ExpressAdapter } from '@nestjs/platform-express';
import { AppModule } from '../src/app.module';

interface ItemResponse {
  id: number;
  sku: string;
  name: string;
  stock: number;
}

interface ReservationResponse {
  id: number;
  sku: string;
  quantity: number;
  note: string;
}

async function smoke(): Promise<void> {
  // The HTTP driver is supplied explicitly via `ExpressAdapter` instead of
  // `NestFactory`'s default-driver auto-discovery. Auto-discovery resolves
  // `@nestjs/platform-express` relative to `@nestjs/core`, so it only succeeds
  // when both are hoisted together; constructing the adapter here resolves it
  // from this sample's own declared dependency, independent of workspace
  // hoisting.
  const app = await NestFactory.create(AppModule, new ExpressAdapter(), {
    abortOnError: false,
    logger: false,
  });
  await app.listen(0, '127.0.0.1');

  try {
    const baseUrl = await app.getUrl();

    assert.equal(await stockFor(baseUrl, 'book-001'), 10);
    assert.deepEqual(await listReservations(baseUrl), []);

    const rollback = await postReservation(
      baseUrl,
      '/inventory/reservations/rollback',
      {
        sku: 'book-001',
        quantity: 3,
      },
    );

    assert.equal(rollback.status, 500);
    assert.equal(await stockFor(baseUrl, 'book-001'), 10);
    assert.deepEqual(await listReservations(baseUrl), []);

    const commit = await postReservation(
      baseUrl,
      '/inventory/reservations/commit',
      {
        sku: 'book-001',
        quantity: 4,
      },
    );
    const commitBody = await commit.json() as {
      transactionActive: boolean;
      reservationCountForSku: number;
    };

    assert.equal(commit.status, 201);
    assert.deepEqual(commitBody, {
      transactionActive: true,
      reservationCountForSku: 1,
    });
    assert.equal(await stockFor(baseUrl, 'book-001'), 6);

    const reservations = await listReservations(baseUrl);
    assert.equal(reservations.length, 1);
    assert.equal(reservations[0]?.sku, 'book-001');
    assert.equal(reservations[0]?.note, 'committed manual transaction');
  } finally {
    await app.close();
  }
}

async function stockFor(baseUrl: string, sku: string): Promise<number> {
  const items = await listItems(baseUrl);
  const item = items.find(candidate => candidate.sku === sku);

  assert.ok(item);
  return item.stock;
}

async function listItems(baseUrl: string): Promise<ItemResponse[]> {
  const response = await fetch(`${baseUrl}/inventory`);
  assert.equal(response.status, 200);
  return response.json() as Promise<ItemResponse[]>;
}

async function listReservations(
  baseUrl: string,
): Promise<ReservationResponse[]> {
  const response = await fetch(`${baseUrl}/inventory/reservations`);
  assert.equal(response.status, 200);
  return response.json() as Promise<ReservationResponse[]>;
}

async function postReservation(
  baseUrl: string,
  path: string,
  body: { sku: string; quantity: number },
): Promise<Response> {
  return fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify(body),
  });
}

void smoke().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
