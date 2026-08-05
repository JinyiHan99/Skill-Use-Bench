import { TransactionalAdapterDrizzleOrm } from '@nestjs-cls/transactional-adapter-drizzle-orm';
import type { AppDatabase } from './database';

export type DrizzleTransactionalAdapter =
  TransactionalAdapterDrizzleOrm<AppDatabase>;
