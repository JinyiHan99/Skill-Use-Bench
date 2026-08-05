import { pgTable, text, boolean, primaryKey } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { timestamps, idGenerator } from "./_helpers";
import { agents } from "./agents";
import { users } from "./users";

export const knowledgeBases = pgTable(
  "knowledge_bases",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => idGenerator("knowledge_bases"))
      .notNull(),
    userId: text("user_id")
      .references(() => users.id, { onDelete: "cascade" })
      .notNull(),
    name: text("name").notNull(),
    description: text("description"),
    type: text("type").notNull().default("file"),
    ...timestamps,
  },
);

export const agentsKnowledgeBases = pgTable(
  "agents_knowledge_bases",
  {
    agentId: text("agent_id")
      .references(() => agents.id, { onDelete: "cascade" })
      .notNull(),
    knowledgeBaseId: text("knowledge_base_id")
      .references(() => knowledgeBases.id, { onDelete: "cascade" })
      .notNull(),
    userId: text("user_id")
      .references(() => users.id, { onDelete: "cascade" })
      .notNull(),
    enabled: boolean("enabled").default(true),
    ...timestamps,
  },
  (t) => [primaryKey({ columns: [t.agentId, t.knowledgeBaseId] })],
);

export const insertKnowledgeBaseSchema = createInsertSchema(knowledgeBases);
export type NewKnowledgeBase = typeof knowledgeBases.$inferInsert;
export type KnowledgeBaseItem = typeof knowledgeBases.$inferSelect;
