import { Module } from '@nestjs/common';
import { AccountsModule } from '../accounts/accounts.module';
import { LedgerModule } from '../ledger/ledger.module';
import { RequestContextService } from '../common/request-context.service';
import { TransfersController } from './transfers.controller';
import { TransfersService } from './transfers.service';

@Module({
  imports: [AccountsModule, LedgerModule],
  controllers: [TransfersController],
  providers: [RequestContextService, TransfersService],
})
export class TransfersModule {}
