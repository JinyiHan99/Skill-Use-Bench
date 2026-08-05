import { Injectable } from '@nestjs/common';
import { count, eq, sql } from 'drizzle-orm';
import { InjectDrizzle, InjectTransaction } from '@nest-native/drizzle';
import type { AppDatabase } from '../database';
import { inventoryItems, reservations } from '../schema';

@Injectable()
export class InventoryRepository {
  constructor(
    @InjectDrizzle() private readonly db: AppDatabase,
    @InjectTransaction() private readonly tx: AppDatabase,
  ) {}

  async migrate(): Promise<void> {
    await this.db.run(sql`
      CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        stock INTEGER NOT NULL
      )
    `);
    await this.db.run(sql`
      CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        note TEXT NOT NULL
      )
    `);
    await this.db.delete(reservations);
    await this.db.delete(inventoryItems);
    await this.db.insert(inventoryItems).values([
      {
        sku: 'book-001',
        name: 'Nest Native Patterns',
        stock: 10,
      },
      {
        sku: 'kit-001',
        name: 'Drizzle Starter Kit',
        stock: 5,
      },
    ]);
  }

  async listItems(): Promise<Array<{
    id: number;
    sku: string;
    name: string;
    stock: number;
  }>> {
    return this.db
      .select({
        id: inventoryItems.id,
        sku: inventoryItems.sku,
        name: inventoryItems.name,
        stock: inventoryItems.stock,
      })
      .from(inventoryItems)
      .orderBy(inventoryItems.id);
  }

  async listReservations(): Promise<Array<{
    id: number;
    sku: string;
    quantity: number;
    note: string;
  }>> {
    return this.db
      .select({
        id: reservations.id,
        sku: reservations.sku,
        quantity: reservations.quantity,
        note: reservations.note,
      })
      .from(reservations)
      .orderBy(reservations.id);
  }

  async reserveWithInjectedTransaction(input: {
    sku: string;
    quantity: number;
    note: string;
  }): Promise<number> {
    const item = await this.findItemForReservation(input.sku);

    if (!item || item.stock < input.quantity) {
      throw new Error('not enough stock');
    }

    await this.tx
      .update(inventoryItems)
      .set({ stock: item.stock - input.quantity })
      .where(eq(inventoryItems.sku, input.sku));
    await this.tx.insert(reservations).values(input);

    const [summary] = await this.tx
      .select({ reservationCount: count() })
      .from(reservations)
      .where(eq(reservations.sku, input.sku));

    return summary?.reservationCount ?? 0;
  }

  private async findItemForReservation(sku: string): Promise<{
    sku: string;
    stock: number;
  } | undefined> {
    const [item] = await this.tx
      .select({
        sku: inventoryItems.sku,
        stock: inventoryItems.stock,
      })
      .from(inventoryItems)
      .where(eq(inventoryItems.sku, sku));

    return item;
  }
}
