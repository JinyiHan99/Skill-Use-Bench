# Sample 06: Manual Transaction Injection

This sample shows `@InjectTransaction()` as an advanced escape hatch for code
that needs direct access to the current transaction object.

## What It Demonstrates

| Feature | File(s) |
| --- | --- |
| CLS transaction plugin setup | `src/app.module.ts` |
| Method-level `@Transactional()` boundary | `src/inventory/inventory.service.ts` |
| Direct transaction injection | `src/inventory/inventory.repository.ts` |
| Query composition against the active transaction | `src/inventory/inventory.repository.ts` |
| Real rollback assertions | `scripts/smoke.ts` |

## Run

```bash
npm run start --workspace nest-native-drizzle-sample-06-manual-transaction
```

## Validate

```bash
npm run test --workspace nest-native-drizzle-sample-06-manual-transaction
```

## Why This Matters

The superpower here is that a repository can use the same active transaction
without accepting a database client parameter on every method. The workflow
service still owns the transaction boundary with `@Transactional()`, while the
repository uses `@InjectTransaction()` only where it needs transaction-bound
query composition.

Use this when a low-level provider truly needs the current transaction object.
Avoid it for ordinary service orchestration, where injecting `TransactionHost`
or keeping database access inside repositories is usually clearer.

## Post-Sample Review

- Library ergonomics: no package change needed. `@InjectTransaction()` bridges
  cleanly to the CLS transaction token when the plugin is configured.
- Architecture: keep this as an escape hatch. The recommended pattern remains a
  workflow service with `@Transactional()` and repositories with focused query
  methods.
- Documentation: transaction docs and the sample catalog link this beside the
  `@Transactional()` sample.
- Performance: no package performance concern found. The injected transaction
  proxy is provided by the CLS plugin and only resolves the active transaction
  during calls.
- Maintainability: repeated CLS adapter setup across transaction samples is
  acceptable for now because it keeps each sample copy-pasteable.
