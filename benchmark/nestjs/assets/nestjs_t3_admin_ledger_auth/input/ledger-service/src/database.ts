import { createClient, type Client } from '@libsql/client';
import { drizzle, type LibSQLDatabase } from 'drizzle-orm/libsql';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { schema } from './schema';

export type AppDatabase = LibSQLDatabase<typeof schema> & {
  $client: Client;
};

export function createDatabase(): AppDatabase {
  const client = createClient({
    url: `file:${join(
      tmpdir(),
      `nest-native-drizzle-showcase-${process.pid}-${Date.now()}.db`,
    )}`,
  });

  return drizzle(client, { schema });
}
