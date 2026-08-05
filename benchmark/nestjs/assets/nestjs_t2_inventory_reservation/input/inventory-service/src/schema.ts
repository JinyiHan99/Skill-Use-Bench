import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';

export const inventoryItems = sqliteTable('inventory_items', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  sku: text('sku').notNull().unique(),
  name: text('name').notNull(),
  stock: integer('stock').notNull(),
});

export const reservations = sqliteTable('reservations', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  sku: text('sku').notNull(),
  quantity: integer('quantity').notNull(),
  note: text('note').notNull(),
});

export const schema = {
  inventoryItems,
  reservations,
};
