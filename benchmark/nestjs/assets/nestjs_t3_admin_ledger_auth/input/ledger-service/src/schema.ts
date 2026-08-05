import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';

export const accounts = sqliteTable('accounts', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  ownerName: text('owner_name').notNull(),
  balanceCents: integer('balance_cents').notNull(),
});

export const ledgerEntries = sqliteTable('ledger_entries', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  fromAccountId: integer('from_account_id').notNull(),
  toAccountId: integer('to_account_id').notNull(),
  amountCents: integer('amount_cents').notNull(),
  requestId: text('request_id').notNull(),
  note: text('note').notNull(),
});

export const projects = sqliteTable('projects', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  status: text('status').notNull(),
  createdAt: text('created_at').notNull(),
});

export const schema = {
  accounts,
  ledgerEntries,
  projects,
};
