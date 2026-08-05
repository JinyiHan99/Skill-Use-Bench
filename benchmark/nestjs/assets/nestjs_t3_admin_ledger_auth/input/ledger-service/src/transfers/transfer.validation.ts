import { createInsertSchema } from 'drizzle-zod';
import { z } from 'zod';
import { ledgerEntries } from '../schema';

export const transferSchema = createInsertSchema(ledgerEntries)
  .pick({
    fromAccountId: true,
    toAccountId: true,
    amountCents: true,
  })
  .extend({
    fail: z.boolean().optional(),
  });

export type TransferInput = z.infer<typeof transferSchema>;
