import { Injectable } from '@nestjs/common';
import {
  LedgerRepository,
  type LedgerEntry,
} from './ledger.repository';

@Injectable()
export class LedgerService {
  constructor(private readonly ledgerRepository: LedgerRepository) {}

  list(): Promise<LedgerEntry[]> {
    return this.ledgerRepository.list();
  }

  record(input: {
    fromAccountId: number;
    toAccountId: number;
    amountCents: number;
    requestId: string;
    note: string;
  }): Promise<LedgerEntry> {
    return this.ledgerRepository.record(input);
  }
}
