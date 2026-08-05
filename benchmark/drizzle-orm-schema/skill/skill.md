---
name: drizzle-orm-schema
description: 'Skill for writing Drizzle ORM schemas and queries in a PostgreSQL strict-mode project. Use when defining pgTable columns, indexes, relationships, or writing database queries. Enforces the builder API pattern and project-specific conventions for naming, types, and helper usage.'
---

# Drizzle ORM Schema & Query Guide

This skill defines the patterns for writing database schemas and queries using Drizzle ORM with PostgreSQL in strict mode. When this skill is active, all database code must follow the conventions below — do not use alternative patterns even if they appear in Drizzle's official documentation or examples online, as the project has specific requirements that override general best practices.

## When to Use This Skill

- Creating or editing files in `src/database/schemas/`
- Defining `pgTable` tables with columns, indexes, and relationships
- Writing database queries anywhere in the codebase
- Creating insert/update/delete operations
- Defining TypeScript types derived from schema
- Adding or modifying database migrations

## Prerequisites

| Item | Location |
|------|----------|
| Drizzle config | `drizzle.config.ts` |
| Schema files | `src/database/schemas/` |
| Migrations | `src/database/migrations/` |
| Helper functions | `src/database/schemas/_helpers.ts` |

Database dialect: `postgresql` with `strict: true` enabled in drizzle config.

## Naming Conventions

### Table Names

Table names must be **plural** and use **snake_case**:

```typescript
// Correct
export const users = pgTable("users", { ... });
export const sessionGroups = pgTable("session_groups", { ... });
export const agentsKnowledgeBases = pgTable("agents_knowledge_bases", { ... });

// Incorrect — singular or camelCase
export const user = pgTable("user", { ... });
export const sessionGroup = pgTable("sessionGroup", { ... });
```

The TypeScript variable name uses camelCase, but the SQL table name (first string argument) must always be plural snake_case.

### Column Names

Column names use **snake_case** in SQL, with camelCase TypeScript property names:

```typescript
// Correct
userId: text("user_id").notNull(),
createdAt: timestamp("created_at", { withTimezone: true }),

// Incorrect — camelCase in SQL name
userId: text("userId").notNull(),
```

## Primary Key Pattern

All entity tables use text IDs with a prefixed generator. Internal/junction tables may use UUID:

```typescript
// Entity tables — text ID with prefix
id: text("id")
    .primaryKey()
    .$defaultFn(() => idGenerator("agents"))
    .notNull(),

// Internal/junction tables — UUID
id: uuid("id").defaultRandom().primaryKey(),
```

The ID prefix (e.g., "agents") makes entity types distinguishable in logs and debugging. Always use the entity name (plural) as the prefix argument.

## Timestamps

Every table must include the standard timestamp columns by spreading the `timestamps` helper from `_helpers.ts`:

```typescript
import { timestamps } from "./_helpers";

export const agents = pgTable("agents", {
    id: text("id").primaryKey().$defaultFn(() => idGenerator("agents")).notNull(),
    name: text("name").notNull(),
    description: text("description"),
    // ... other columns ...
    ...timestamps,  // Spreads createdAt, updatedAt, accessedAt
});
```

Do not define timestamp columns manually — always use the spread helper. This ensures consistent column names, types (timestamptz), and default values across all tables. The helper provides three columns: `createdAt`, `updatedAt`, and `accessedAt`.

## Foreign Keys

Foreign keys reference the related table's `id` column and must specify `onDelete` behavior:

```typescript
userId: text("user_id")
    .references(() => users.id, { onDelete: "cascade" })
    .notNull(),
```

Cascade rules:
- `cascade` — for ownership relationships (user deletes → user's agents deleted)
- `set null` — for reference relationships (category deleted → items keep existing, category becomes null)
- `restrict` — for critical references that should prevent parent deletion

Always add `.notNull()` unless the foreign key is genuinely optional (set null on delete scenarios).

## Index Definitions

Indexes must be defined using the **array return format**. The object format is deprecated and will be removed in future Drizzle versions:

```typescript
// Correct — array format
export const agents = pgTable(
    "agents",
    {
        id: text("id").primaryKey().$defaultFn(() => idGenerator("agents")).notNull(),
        userId: text("user_id").references(() => users.id, { onDelete: "cascade" }).notNull(),
        slug: text("slug").notNull(),
        ...timestamps,
    },
    (t) => [
        uniqueIndex("agents_user_id_slug_unique").on(t.userId, t.slug),
        index("agents_user_id_idx").on(t.userId),
    ],
);

// Incorrect — deprecated object format (do NOT use)
export const agents = pgTable(
    "agents",
    { /* columns */ },
    (t) => ({
        userSlugUnique: uniqueIndex("agents_user_id_slug_unique").on(t.userId, t.slug),
    }),
);
```

Index naming convention: `<table_name>_<column_names>_<type>` where type is `idx` for regular indexes and `unique` for unique indexes.

## Type Inference

Export inferred types for each table using the standard pattern:

```typescript
import { createInsertSchema } from "drizzle-zod";

// Zod validation schema for inserts
export const insertAgentSchema = createInsertSchema(agents);

// TypeScript types
export type NewAgent = typeof agents.$inferInsert;
export type AgentItem = typeof agents.$inferSelect;
```

Always generate the Zod schema using `createInsertSchema` — do not write manual Zod schemas for database models. The inferred schema stays in sync with the table definition automatically.

## Query Style — Builder API Only

### Critical Rule: Never Use the Relational Query API

Always use `db.select()` builder API. The `db.query.*` relational API is **prohibited** in this project because it generates complex lateral joins and `json_build_array` SQL that is fragile, hard to debug, and produces unexpected performance characteristics:

```typescript
// ✅ CORRECT — builder API
const result = await db
    .select({
        id: agents.id,
        name: agents.name,
        userId: agents.userId,
    })
    .from(agents)
    .where(eq(agents.userId, userId))
    .limit(10);

// ❌ PROHIBITED — relational API
const result = await db.query.agents.findMany({
    where: eq(agents.userId, userId),
    limit: 10,
});

// ❌ PROHIBITED — relational API with relations
const result = await db.query.agents.findFirst({
    where: eq(agents.id, agentId),
    with: { knowledgeBases: true },
});
```

### JOIN Queries

Use explicit `leftJoin` / `innerJoin` with selected fields:

```typescript
const agentsWithGroups = await db
    .select({
        id: agents.id,
        name: agents.name,
        groupName: sessionGroups.name,
    })
    .from(agents)
    .leftJoin(sessionGroups, eq(agents.groupId, sessionGroups.id))
    .where(eq(agents.userId, userId));
```

### One-to-Many Relationships

For one-to-many data (e.g., agent with its knowledge bases), use **two separate queries** instead of a JOIN. JOINs for one-to-many produce duplicate parent rows that require deduplication logic:

```typescript
// Correct: two queries, then assemble
const agent = await db
    .select()
    .from(agents)
    .where(eq(agents.id, agentId))
    .limit(1)
    .then(rows => rows[0]);

const knowledgeBases = await db
    .select()
    .from(agentsKnowledgeBases)
    .innerJoin(knowledgeBases, eq(agentsKnowledgeBases.knowledgeBaseId, knowledgeBases.id))
    .where(eq(agentsKnowledgeBases.agentId, agentId));

return { ...agent, knowledgeBases };
```

### Aggregation Queries

```typescript
const counts = await db
    .select({
        userId: agents.userId,
        agentCount: count(agents.id),
    })
    .from(agents)
    .groupBy(agents.userId)
    .having(gt(count(agents.id), 5));
```

## Junction Tables (Many-to-Many)

Junction tables use composite primary keys and reference both related tables:

```typescript
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
    (t) => [
        primaryKey({ columns: [t.agentId, t.knowledgeBaseId] }),
    ],
);
```

Junction tables always include the `userId` column for access control queries, even though it's technically derivable from the parent entities.

## Column Type Rules

| Use This | Not This | Reason |
|----------|----------|--------|
| `text("col")` | `varchar("col", { length: N })` | PostgreSQL treats them identically; varchar adds pointless constraint |
| `timestamp("col", { withTimezone: true })` | `timestamp("col")` | Timezone-naive timestamps cause bugs in multi-region deployments |
| `boolean("col")` | `integer("col")` for flags | Semantic clarity and type safety |
| `jsonb("col")` | `json("col")` | jsonb is indexable and more efficient for queries |
| `text("col")` for IDs | `serial("col")` | Serial is deprecated in this project; use text with generators |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "relation does not exist" | Run `drizzle-kit push` or generate migration |
| Type error on select | Ensure selected fields match the `select({})` shape |
| Index name conflict | Use the `<table>_<columns>_<type>` naming convention |
| Timestamps not updating | Verify `...timestamps` spread is included |
| Query returns unexpected nulls | Check `leftJoin` vs `innerJoin` semantics |

## References

- Drizzle ORM documentation (orm.drizzle.team)
- Project schema helpers: `src/database/schemas/_helpers.ts`
- Migration skill: `db-migrations` (separate skill)
