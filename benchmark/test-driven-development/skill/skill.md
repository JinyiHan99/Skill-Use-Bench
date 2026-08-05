---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass. Then refactor.

The core discipline is the **red-green-refactor cycle**: every change to production code must be preceded by a failing test that motivates it. If you didn't watch the test fail, you don't know if it tests the right thing.

## When to Use

Use this workflow for:
- New features
- Bug fixes
- Refactoring that changes behavior
- Any modification to production logic

Exceptions (only with explicit user permission):
- Throwaway prototypes
- Generated boilerplate
- Pure configuration changes

## The Red-Green-Refactor Cycle

Every code change follows three phases in strict order. Skipping or reordering phases defeats the purpose of the methodology.

### Phase RED — Write a Failing Test

Before touching any production code, write exactly one test that captures the next desired behavior. Run it immediately to confirm it fails.

The test function name must follow the pattern `test_<behavior>_<condition>_<expected>` so that the test name alone communicates what is being verified. For example, `test_parse_empty_input_returns_none` or `test_retry_timeout_raises_error`. Avoid vague names like `test_it_works` or `test_basic`.

Each test function should verify a single behavior — one logical assertion per test. If you find yourself writing "and" in the test name, split it into separate tests. This keeps failure messages unambiguous: when a test fails, you know exactly which behavior broke.

Always test real behavior by exercising the actual code path. Mocks should only be introduced when there is a genuine external dependency (network, database, filesystem) that cannot be provided in the test environment. When you must mock, mock at the boundary — never mock the unit under test itself, and never assert on mock internals (call counts, argument lists) as the primary verification. The test should assert on the observable outcome of the function, not on how it called its collaborators.

After writing the test, run `pytest` targeting just the new test file to confirm the test fails with an assertion error (not an import error or syntax error). The failure message should clearly indicate the missing behavior.

### Phase GREEN — Minimal Implementation

Write the simplest production code that makes the failing test pass. Do not add features, handle edge cases, or optimize — those are separate cycles. Run `pytest` again to confirm the new test passes and all previously passing tests remain green.

If any existing test breaks, fix it immediately before moving on. A broken test suite is never acceptable, even temporarily.

### Phase REFACTOR — Clean Up Under Green

Only after reaching green, improve the code structure: extract helpers, rename variables, reduce duplication. After each refactoring step, run `pytest` to confirm all tests still pass. Never introduce new behavior during refactor — if you realize you need new behavior, start a new RED phase.

### Cycle Discipline

The three phases must execute in strict RED → GREEN → REFACTOR order. Each transition requires running `pytest`:

1. After writing the test (RED): run `pytest` — must see the new test fail
2. After writing implementation (GREEN): run `pytest` — must see all tests pass
3. After each refactor step: run `pytest` — must see all tests still pass

This means for a single feature, the minimum number of `pytest` invocations is three. Each `pytest` run serves as a checkpoint that proves the cycle is being followed correctly.

## Bug Fix Protocol

When fixing a bug, the first step is always to write a failing test that reproduces the bug. This test must fail before the fix and pass after. Never apply a fix without first having a test that demonstrates the problem — otherwise you cannot prove the fix actually addresses the issue, and the bug may silently regress later.

The workflow for a bug fix is:
1. Write a test that triggers the buggy behavior (RED)
2. Run `pytest` — confirm it fails, proving the bug exists
3. Apply the minimal fix (GREEN)
4. Run `pytest` — confirm the bug test now passes along with all others
5. Refactor if needed, keeping all tests green

## Test Quality Standards

Each test should be self-contained and independent. Do not rely on test execution order or shared mutable state between tests. Use fresh fixtures or setup for each test.

Keep test files organized alongside the code they test. For a module `src/calculator.py`, the corresponding tests should be in `tests/test_calculator.py`.

Avoid testing private methods directly. Private methods are implementation details — test them through the public interface that uses them. If you find a private method that seems to need its own tests, consider whether it should be extracted into its own module with a public interface.

## Handling Pre-Existing Code Without Tests

When working on a codebase that has existing code without tests, do not attempt to add tests for all existing code at once. Instead, apply the "boy scout rule": whenever you touch existing code (to fix a bug or add a feature), first write tests for the specific behavior you are about to change. This ensures that your changes are covered by the TDD cycle without requiring a massive upfront testing effort.

## Verification Checklist

Before marking work complete:

- Every new or modified function has a corresponding test
- Each test was observed to fail before its implementation was written
- Each test failure was an assertion failure (not a syntax or import error)
- Minimal code was written to pass each test
- All tests pass after implementation
- Tests use real code paths (mocks only for genuine external dependencies)
- Test names follow `test_<behavior>_<condition>_<expected>` format
- Each test verifies a single behavior
- No direct testing of private methods
- `pytest` was run at each phase transition (RED, GREEN, REFACTOR)
