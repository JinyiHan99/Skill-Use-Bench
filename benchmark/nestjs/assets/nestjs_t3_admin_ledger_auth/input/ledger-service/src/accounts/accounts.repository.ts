import { eq, sql } from 'drizzle-orm';
import {
  DrizzleRepository,
  InjectDrizzle,
  InjectTransaction,
} from '@nest-native/drizzle';
import type { AppDatabase } from '../database';
import { accounts } from '../schema';

export type Account = typeof accounts.$inferSelect;

@DrizzleRepository()
export class AccountsRepository {
  constructor(
    @InjectDrizzle() private readonly db: AppDatabase,
    @InjectTransaction() private readonly tx: AppDatabase,
  ) {}

  async migrate(): Promise<void> {
    await this.db.run(sql`
      CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_name TEXT NOT NULL,
        balance_cents INTEGER NOT NULL
      )
    `);
    await this.db.delete(accounts);
  }

  async seed(): Promise<void> {
    await this.create({ ownerName: 'Ada Lovelace', balanceCents: 10000 });
    await this.create({ ownerName: 'Grace Hopper', balanceCents: 7500 });
  }

  async list(): Promise<Account[]> {
    return this.db.select().from(accounts).orderBy(accounts.id);
  }

  async create(input: {
    ownerName: string;
    balanceCents: number;
  }): Promise<Account> {
    const [account] = await this.db.insert(accounts).values(input).returning();
    return account;
  }

  async adjustBalance(id: number, deltaCents: number): Promise<Account> {
    const [account] = await this.tx
      .update(accounts)
      .set({ balanceCents: sql`${accounts.balanceCents} + ${deltaCents}` })
      .where(eq(accounts.id, id))
      .returning();

    return account;
  }
}
