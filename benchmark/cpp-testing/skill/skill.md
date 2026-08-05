---
name: cpp-testing
description: Use only when writing/updating/fixing C++ tests, configuring GoogleTest/CTest, diagnosing failing or flaky tests, or adding coverage/sanitizers.
origin: ECC
---

# C++ Testing (Agent Skill)

Agent-focused testing workflow for modern C++ (C++17/20) using GoogleTest/GoogleMock with CMake/CTest.

## When to Use

- Writing new C++ tests or fixing existing tests
- Designing unit/integration test coverage for C++ components
- Adding test coverage, CI gating, or regression protection
- Configuring CMake/CTest workflows for consistent execution
- Investigating test failures or flaky behavior
- Enabling sanitizers for memory/race diagnostics

### When NOT to Use

- Implementing new product features without test changes
- Large-scale refactors unrelated to test coverage or failures
- Performance tuning without test regressions to validate
- Non-C++ projects or non-test tasks

## Prerequisites

- CMake 3.20+
- GoogleTest fetched via `FetchContent` with a pinned version tag
- Compiler supporting C++17 or C++20

## TDD Workflow

Follow the RED → GREEN → REFACTOR loop strictly in order:

1. **RED**: Write a failing test that captures the new behavior. The test file must be committed (or at minimum saved and built) before writing any production code. This ensures the test genuinely fails first.
2. **GREEN**: Implement the smallest change in production code to make the test pass. Do not modify the test in this step.
3. **REFACTOR**: Clean up both test and production code while keeping tests green. Run the full suite after cleanup.

Before moving from RED to GREEN, always verify the test compiles and fails by running CTest once. This confirms the test is wired correctly and actually exercises the intended behavior, avoiding false-green scenarios where the test never ran.

## Test File Organization

Tests live under a dedicated `tests/` directory at the project root, organized by scope:

```
tests/
  unit/           # Fast, isolated unit tests
  integration/    # Tests involving multiple components or I/O
  testdata/       # Shared fixture data (read-only at runtime)
```

Each test source file is named `<module_under_test>_test.cpp`. When adding a new test file, place it in the appropriate scope directory (`tests/unit/` for unit tests, `tests/integration/` for integration tests). Test files should not be placed directly in the `tests/` root — this flat layout makes it difficult to run scope-specific subsets via CTest labels.

## Writing Tests

### Assertion Strategy

Use `ASSERT_*` macros only for preconditions that, if violated, make subsequent checks meaningless (e.g., a pointer is not null before dereferencing). Use `EXPECT_*` for all other checks — this allows multiple failures to be reported in a single test run, providing richer diagnostic information.

A common mistake is to use `ASSERT_EQ` for every comparison. Reserve `ASSERT_*` for true preconditions and prefer `EXPECT_*` otherwise to maximize the information gathered from each test execution.

### Fixtures

Use test fixtures (`::testing::Test` subclass with `SetUp`/`TearDown`) when multiple tests share common setup state. Fixtures prevent duplication and ensure consistent initialization.

Resources allocated in `SetUp()` must be released in `TearDown()`. For file-system resources, generate a unique temporary directory per fixture instance using `std::filesystem::temp_directory_path()` combined with a test-specific suffix, and remove it in `TearDown()`.

### Mocks vs Fakes

Use GoogleMock (`MOCK_METHOD`) for verifying interaction patterns — i.e., when the test needs to assert that certain methods were called with specific arguments in a specific order. Use hand-written fakes (simple implementations of an interface) for stateful dependencies where the test cares about the cumulative effect rather than individual calls.

Over-mocking simple value objects or data containers is a common pitfall. If a dependency has no side effects and is cheap to construct, pass the real object instead of mocking it.

## CMake Integration

### FetchContent Setup

Always fetch GoogleTest via `FetchContent` with a pinned version tag to ensure reproducible builds:

```cmake
include(FetchContent)
set(GTEST_VERSION v1.17.0)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/${GTEST_VERSION}.zip
)
FetchContent_MakeAvailable(googletest)
```

### Test Target Registration

Register test executables using `gtest_discover_tests()` rather than the older `add_test()` approach. The discovery-based method automatically enumerates individual test cases at CTest time, so new tests are picked up without manually editing CMakeLists.txt:

```cmake
enable_testing()
include(GoogleTest)
gtest_discover_tests(my_tests)
```

When a project has both unit and integration tests, assign CTest labels to distinguish them. Use the `PROPERTIES LABELS` mechanism so that CI can run fast unit tests first and integration tests separately:

```cmake
gtest_discover_tests(unit_tests PROPERTIES LABELS "unit")
gtest_discover_tests(integration_tests PROPERTIES LABELS "integration")
```

## Running Tests

For local development, run the full test suite via CTest with failure output enabled:

```bash
ctest --test-dir build --output-on-failure
```

To run a subset by filter:

```bash
ctest --test-dir build -R "ModuleName"
```

When diagnosing a specific failing test, prefer running the test binary directly with `--gtest_filter` to get immediate output without CTest overhead:

```bash
./build/tests/unit/my_tests --gtest_filter="SuiteOrTest.Name"
```

## Debugging Failures

When a test fails, follow this diagnostic sequence rather than immediately adding print statements:

1. Re-run the single failing test with `--gtest_filter` to confirm it reproduces in isolation.
2. If it reproduces, re-run with AddressSanitizer enabled to check for memory issues that may cause non-deterministic behavior.
3. Only after sanitizer results are clean, add targeted `SCOPED_TRACE` or `RecordProperty` annotations around the failing assertion to capture intermediate state.
4. Once the root cause is identified and fixed, run the full suite to confirm no regressions.

This sequence catches the most common failure causes (memory corruption, use-after-free) before resorting to manual debugging, saving significant developer time.

## Coverage

Coverage instrumentation should be applied only to the test target, not globally to the entire project. This avoids instrumenting third-party dependencies and keeps build times manageable:

```cmake
option(ENABLE_COVERAGE "Enable coverage flags" OFF)

if(ENABLE_COVERAGE)
  target_compile_options(my_tests PRIVATE --coverage)
  target_link_options(my_tests PRIVATE --coverage)
endif()
```

After running tests, generate and filter the coverage report to exclude system headers:

```bash
lcov --capture --directory build --output-file coverage.info
lcov --remove coverage.info '/usr/*' '*/googletest/*' --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

Always exclude GoogleTest sources from the coverage report — they inflate line counts without providing actionable signal about your project's coverage.

## Sanitizers

Enable sanitizers via dedicated CMake options. Sanitizers are mutually exclusive — do not combine AddressSanitizer with ThreadSanitizer in the same build, as they are incompatible and produce false positives:

```cmake
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_TSAN "Enable ThreadSanitizer" OFF)

if(ENABLE_ASAN)
  add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
  add_link_options(-fsanitize=address)
endif()
if(ENABLE_TSAN)
  add_compile_options(-fsanitize=thread)
  add_link_options(-fsanitize=thread)
endif()
```

When investigating a flaky test, always run with ASan first before attempting ThreadSanitizer — many apparent race conditions are actually caused by memory corruption that ASan detects more reliably.

## Flaky Test Guardrails

- Never use `sleep()` or `std::this_thread::sleep_for()` for synchronization; use `std::condition_variable`, `std::latch`, or `std::barrier` with bounded waits.
- Generate unique temporary directories per test using a combination of `std::filesystem::temp_directory_path()` and the test name or a UUID suffix.
- Avoid depending on wall-clock time; inject a clock interface or use a fake time source.
- When randomized inputs are needed, use a deterministic seed derived from the test name and log it in the test output so failures can be reproduced.

## New Test Checklist

When adding a new test (whether for a new feature, a bug fix, or coverage gap), follow this sequence:

1. Create the test source file in the appropriate `tests/unit/` or `tests/integration/` directory.
2. Add the test source to the corresponding `CMakeLists.txt` target.
3. Run `cmake --build build` to confirm it compiles.
4. Run `ctest --test-dir build -R "NewTestName"` to confirm it fails (RED phase).
5. Implement the production code change.
6. Run the filtered test again to confirm it passes (GREEN phase).
7. Run the full suite (`ctest --test-dir build --output-on-failure`) to check for regressions.
8. If the project uses coverage, run a coverage build to verify the new code is exercised.

Skipping step 4 (confirming the test fails first) is the most common TDD violation — it leads to tests that pass trivially without exercising the intended behavior.
