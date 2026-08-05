import { Module } from '@nestjs/common';
import { DrizzleModule } from '@nest-native/drizzle';
import { AccountsController } from './accounts.controller';
import { AccountsRepository } from './accounts.repository';
import { AccountsService } from './accounts.service';

@Module({
  imports: [DrizzleModule.forFeature([AccountsRepository])],
  controllers: [AccountsController],
  providers: [AccountsService],
  exports: [DrizzleModule, AccountsService],
})
export class AccountsModule {}
