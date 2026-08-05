import { Injectable } from '@nestjs/common';
import { AccountsRepository, type Account } from './accounts.repository';

@Injectable()
export class AccountsService {
  constructor(private readonly accountsRepository: AccountsRepository) {}

  list(): Promise<Account[]> {
    return this.accountsRepository.list();
  }

  create(input: {
    ownerName: string;
    balanceCents: number;
  }): Promise<Account> {
    return this.accountsRepository.create(input);
  }

  debit(id: number, amountCents: number): Promise<Account> {
    return this.accountsRepository.adjustBalance(id, -amountCents);
  }

  credit(id: number, amountCents: number): Promise<Account> {
    return this.accountsRepository.adjustBalance(id, amountCents);
  }
}
