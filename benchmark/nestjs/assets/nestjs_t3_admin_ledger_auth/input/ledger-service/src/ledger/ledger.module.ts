import { Module } from '@nestjs/common';
import { DrizzleModule } from '@nest-native/drizzle';
import { LedgerController } from './ledger.controller';
import { LedgerRepository } from './ledger.repository';
import { LedgerService } from './ledger.service';

@Module({
  imports: [DrizzleModule.forFeature([LedgerRepository])],
  controllers: [LedgerController],
  providers: [LedgerService],
  exports: [DrizzleModule, LedgerService],
})
export class LedgerModule {}
