import { Injectable, OnModuleInit } from '@nestjs/common';
import { TransactionHost } from '@nestjs-cls/transactional';
import { Transactional } from '@nest-native/drizzle';
import { InventoryRepository } from './inventory.repository';
import type { DrizzleTransactionalAdapter } from '../transaction.types';

@Injectable()
export class InventoryService implements OnModuleInit {
  constructor(
    private readonly inventoryRepository: InventoryRepository,
    private readonly txHost: TransactionHost<DrizzleTransactionalAdapter>,
  ) {}

  async onModuleInit(): Promise<void> {
    await this.inventoryRepository.migrate();
  }

  listItems() {
    return this.inventoryRepository.listItems();
  }

  listReservations() {
    return this.inventoryRepository.listReservations();
  }

  @Transactional()
  async commitReservation(input: {
    sku: string;
    quantity: number;
  }): Promise<{
    transactionActive: boolean;
    reservationCountForSku: number;
  }> {
    const reservationCountForSku =
      await this.inventoryRepository.reserveWithInjectedTransaction({
        ...input,
        note: 'committed manual transaction',
      });

    return {
      transactionActive: this.txHost.isTransactionActive(),
      reservationCountForSku,
    };
  }

  @Transactional()
  async rollbackReservation(input: {
    sku: string;
    quantity: number;
  }): Promise<void> {
    await this.inventoryRepository.reserveWithInjectedTransaction({
      ...input,
      note: 'rolled back manual transaction',
    });

    throw new Error('manual rollback requested');
  }
}
