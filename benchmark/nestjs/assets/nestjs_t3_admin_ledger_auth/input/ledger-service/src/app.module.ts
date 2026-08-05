import { Module, ValidationPipe } from '@nestjs/common';
import { APP_PIPE } from '@nestjs/core';
import {
  ClsPluginTransactional,
} from '@nestjs-cls/transactional';
import { TransactionalAdapterDrizzleOrm } from '@nestjs-cls/transactional-adapter-drizzle-orm';
import { ClsModule } from 'nestjs-cls';
import {
  DrizzleModule,
  getDrizzleClientToken,
} from '@nest-native/drizzle';
import { AccountsModule } from './accounts/accounts.module';
import { createDatabase, type AppDatabase } from './database';
import { DatabaseSeedService } from './database-seed.service';
import { LedgerModule } from './ledger/ledger.module';
import { ProjectsModule } from './projects/projects.module';
import { schema } from './schema';
import { TransfersModule } from './transfers/transfers.module';

@Module({
  imports: [
    DrizzleModule.forRoot<AppDatabase>({
      schema,
      connection: createDatabase(),
      shutdown: database => database.$client.close(),
    }),
    ClsModule.forRoot({
      global: true,
      plugins: [
        new ClsPluginTransactional({
          adapter: new TransactionalAdapterDrizzleOrm({
            drizzleInstanceToken: getDrizzleClientToken(),
          }),
          enableTransactionProxy: true,
        }),
      ],
    }),
    AccountsModule,
    LedgerModule,
    ProjectsModule,
    TransfersModule,
  ],
  providers: [
    DatabaseSeedService,
    {
      provide: APP_PIPE,
      useValue: new ValidationPipe({
        transform: true,
        whitelist: true,
      }),
    },
  ],
})
export class AppModule {}
