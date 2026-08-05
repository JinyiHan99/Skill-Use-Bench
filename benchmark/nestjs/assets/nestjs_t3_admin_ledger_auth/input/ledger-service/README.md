# Sample 00 - Full Showcase

This is the full integration baseline for `@nest-native/drizzle`. It keeps
Drizzle explicit while showing the Nest-native structure users expect in a real
application.

## What It Demonstrates

- `DrizzleModule.forRoot()` with a real libSQL Drizzle client
- Feature modules with repositories, services, and controllers
- `@DrizzleRepository()` and constructor injection with `@InjectDrizzle()`
- CLS-backed `@Transactional()` across multiple injected services
- `@InjectTransaction()` inside a repository participating in the active
  transaction
- Request-scoped providers with `REQUEST` injection
- Nest enhancers: guards, interceptors, pipes, and filters
- Mixed validation: `drizzle-zod` for transfer input and `class-validator` DTOs
  for account/project creation
- Swagger/OpenAPI document generation
- Express smoke coverage and a Fastify bootstrap file using the same application
  module
- Database seeding and a smoke test that verifies commit and rollback behavior

## Commands

```bash
npm run test --workspace nest-native-drizzle-showcase
npm run start --workspace nest-native-drizzle-showcase
npm run start:fastify --workspace nest-native-drizzle-showcase
```

`start:fastify` expects `@nestjs/platform-fastify` to be installed by the
application. The sample keeps it out of the workspace dependency graph while the
current Nest Fastify adapter line depends on a Fastify version with a published
high-severity advisory.

## Main Files

- `src/app.module.ts`: root Drizzle, CLS transaction, validation, and feature
  module setup
- `src/accounts`: class-validator DTO flow and guarded controller
- `src/transfers`: `drizzle-zod` validation plus transaction orchestration
- `src/ledger`: repository-level `@InjectTransaction()` usage
- `src/projects`: Swagger/OpenAPI DTO flow
- `scripts/smoke.ts`: Express verification for the full workflow

## Post-Sample Review

The focused samples already shaped the current public API, and this showcase did
not require a package change. The main ergonomics signal is documentation:
applications benefit from seeing `@Transactional()` and `@InjectTransaction()`
used together, because it clarifies when to orchestrate transactions in services
and when a repository needs the active transaction escape hatch.
