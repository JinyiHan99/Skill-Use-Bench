import { pgTable, text, boolean, uniqueIndex, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { timestamps, idGenerator } from "./_helpers";
import { users } from "./users";

export const agents = pgTable(
  "agents",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => idGenerator("agents"))
      .notNull(),
    userId: text("user_id")
      .references(() => users.id, { onDelete: "cascade" })
      .notNull(),
    name: text("name").notNull(),
    slug: text("slug").notNull(),
    description: text("description"),
    systemPrompt: text("system_prompt"),
    isPublic: boolean("is_public").default(false),
    ...timestamps,
  },
  (t) => [
    uniqueIndex("agents_user_id_slug_unique").on(t.userId, t.slug),
    index("agents_user_id_idx").on(t.userId),
  ],
);

export const insertAgentSchema = createInsertSchema(agents);
export type NewAgent = typeof agents.$inferInsert;
export type AgentItem = typeof agents.$inferSelect;
