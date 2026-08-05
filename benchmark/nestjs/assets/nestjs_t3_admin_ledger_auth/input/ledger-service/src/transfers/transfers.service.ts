import { Injectable } from '@nestjs/common';
import { TransactionHost } from '@nestjs-cls/transactional';
import { Transactional } from '@nest-native/drizzle';
import { AccountsService } from '../accounts/accounts.service';
import { DomainError } from '../common/domain-error.filter';
import { RequestContextService } from '../common/request-context.service';
import { LedgerService } from '../ledger/ledger.service';
import type { DrizzleTransactionalAdapter } from '../transaction.types';
import type { TransferInput } from './transfer.validation';

@Injectable()
export class TransfersService {
  constructor(
    private readonly accountsService: AccountsService,
    private readonly ledgerService: LedgerService,
    private readonly requestContext: RequestContextService,
    private readonly txHost: TransactionHost<DrizzleTransactionalAdapter>,
  ) {}

  @Transactional()
  async transfer(input: TransferInput): Promise<{
    transactionActive: boolean;
    requestId: string;
  }> {
    const requestId = this.requestContext.requestId();

    await this.accountsService.debit(input.fromAccountId, input.amountCents);
    await this.accountsService.credit(input.toAccountId, input.amountCents);
    await this.ledgerService.record({
      fromAccountId: input.fromAccountId,
      toAccountId: input.toAccountId,
      amountCents: input.amountCents,
      requestId,
      note: 'committed showcase transfer',
    });

    if (input.fail) {
      throw new DomainError('showcase transfer rolled back');
    }

    return {
      transactionActive: this.txHost.isTransactionActive(),
      requestId,
    };
  }
}
