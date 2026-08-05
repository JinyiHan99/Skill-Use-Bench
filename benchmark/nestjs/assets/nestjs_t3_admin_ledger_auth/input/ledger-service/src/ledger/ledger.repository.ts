import { sql } from 'drizzle-orm';
import {
  DrizzleRepository,
  InjectDrizzle,
  InjectTransaction,
} from '@nest-native/drizzle';
import type { AppDatabase } from '../database';
import { ledgerEntries } from '../schema';

export type LedgerEntry = typeof ledgerEntries.$inferSelect;

@DrizzleRepository()
export class LedgerRepository {
  constructor(
    @InjectDrizzle() private readonly db: AppDatabase,
    @InjectTransaction() private readonly tx: AppDatabase,
  ) {}

  async migrate(): Promise<void> {
    await this.db.run(sql`
      CREATE TABLE IF NOT EXISTS ledger_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_account_id INTEGER NOT NULL,
        to_account_id INTEGER NOT NULL,
        amount_cents INTEGER NOT NULL,
        request_id TEXT NOT NULL,
        note TEXT NOT NULL
      )
    `);
    await this.db.delete(ledgerEntries);
  }

  async list(): Promise<LedgerEntry[]> {
    return this.db.select().from(ledgerEntries).orderBy(ledgerEntries.id);
  }

  async record(input: {
    fromAccountId: number;
    toAccountId: number;
    amountCents: number;
    requestId: string;
    note: string;
  }): Promise<LedgerEntry> {
    const [entry] = await this.tx.insert(ledgerEntries).values(input).returning();
    return entry;
  }
}
