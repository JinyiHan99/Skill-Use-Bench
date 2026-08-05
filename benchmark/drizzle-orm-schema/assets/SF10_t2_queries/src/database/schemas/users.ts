import { pgTable, text, uniqueIndex } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { timestamps, idGenerator } from "./_helpers";

export const users = pgTable(
  "users",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => idGenerator("users"))
      .notNull(),
    email: text("email").notNull(),
    name: text("name").notNull(),
    avatarUrl: text("avatar_url"),
    ...timestamps,
  },
  (t) => [uniqueIndex("users_email_unique").on(t.email)],
);

export const insertUserSchema = createInsertSchema(users);
export type NewUser = typeof users.$inferInsert;
export type UserItem = typeof users.$inferSelect;
