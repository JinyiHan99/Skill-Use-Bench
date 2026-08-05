---
name: rust-mcp-server-generator
description: 'Use this skill when creating an MCP (Model Context Protocol) server in Rust using the rmcp crate. Ensures correct project structure, macro usage, async handlers, and testing patterns.'
---

# Rust MCP Server Generator

## Overview

This skill defines the standard structure and implementation patterns for building MCP (Model Context Protocol) servers in Rust using the `rmcp` crate. Every MCP server created must follow this exact project layout, use the prescribed macros, implement async handlers, include integration tests, and use `tracing` for logging.

## When to Use

- When asked to create a new MCP server
- When implementing MCP tools in Rust
- When adding new tools to an existing Rust MCP server
- When scaffolding a Rust project that exposes capabilities via MCP

## Project Structure

Every MCP server project must follow this exact directory layout:

```
my-mcp-server/
├── Cargo.toml
├── src/
│   ├── main.rs
│   ├── handler.rs
│   └── tools/
│       ├── mod.rs
│       └── <tool_name>.rs
├── tests/
│   └── integration_test.rs
└── README.md
```

Do not place tool implementations in `main.rs` or `handler.rs`. Each tool gets its own file under `src/tools/`.

## Cargo.toml Requirements

The `Cargo.toml` must include `rmcp` as a dependency. The following dependencies are mandatory:

```toml
[package]
name = "my-mcp-server"
version = "0.1.0"
edition = "2021"

[dependencies]
rmcp = { version = "0.1", features = ["server", "transport-stdio"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
anyhow = "1"
```

Do not use alternative MCP libraries. Do not omit the `server` and `transport-stdio` features from `rmcp`. Do not use `log` or `println!` for logging — use `tracing` exclusively.

## Handler Implementation

The main handler struct must use the `#[tool_router]` macro on its `impl` block. This is the entry point that routes incoming MCP tool calls to the correct handler functions.

```rust
use rmcp::{tool_router, ServerHandler, ToolCallResult};

pub struct MyHandler {
    // handler state
}

#[tool_router]
impl MyHandler {
    // Tool methods go here
}

impl ServerHandler for MyHandler {
    // Required trait implementation
}
```

Never implement tool routing manually with match statements or if/else chains. The `#[tool_router]` macro handles dispatch.

## Tool Implementation

Each tool function must:
1. Use the `#[tool]` attribute macro with name and description
2. Be an `async fn`
3. Accept typed parameters (using serde-deserializable structs)
4. Return `Result<ToolCallResult, anyhow::Error>`

```rust
use rmcp::{tool, ToolCallResult};
use serde::Deserialize;

#[derive(Deserialize)]
pub struct ReadFileParams {
    pub path: String,
}

#[tool(name = "read_file", description = "Read contents of a file at the given path")]
pub async fn read_file(params: ReadFileParams) -> Result<ToolCallResult, anyhow::Error> {
    let content = tokio::fs::read_to_string(&params.path).await?;
    Ok(ToolCallResult::text(content))
}
```

Critical rules for tool functions:
- Every tool function must be `async fn` — synchronous tool handlers are forbidden
- Parameter structs must derive `Deserialize`
- Return type must be `Result<ToolCallResult, anyhow::Error>` — do not use custom error types at the tool boundary
- Tool names in the `#[tool]` attribute must be snake_case
- Tool descriptions must be a single sentence starting with an action verb

## Main Entry Point

The `main.rs` must initialize tracing, create the handler, and start the server with stdio transport:

```rust
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .init();

    tracing::info!("Starting MCP server");

    let handler = MyHandler::new();
    rmcp::serve_stdio(handler).await?;

    Ok(())
}
```

Do not use `println!` for server startup messages — use `tracing::info!`. Do not use `std::io` directly for transport — use `rmcp::serve_stdio`.

## Error Handling

Tool functions must use `anyhow::Result` for error propagation. Use the `?` operator for fallible operations. Include context in errors using `.context()`:

```rust
use anyhow::Context;

#[tool(name = "parse_json", description = "Parse a JSON string into structured data")]
pub async fn parse_json(params: ParseParams) -> Result<ToolCallResult, anyhow::Error> {
    let value: serde_json::Value = serde_json::from_str(&params.input)
        .context("Failed to parse input as valid JSON")?;
    Ok(ToolCallResult::text(value.to_string()))
}
```

Never use `unwrap()` or `expect()` in tool handlers. Never return raw strings as errors — always use typed errors with context.

## Integration Tests

Every MCP server must have integration tests in `tests/integration_test.rs` that verify tool invocation works end-to-end:

```rust
use my_mcp_server::MyHandler;
use rmcp::test_utils::invoke_tool;

#[tokio::test]
async fn test_read_file_returns_content() {
    let handler = MyHandler::new();
    let result = invoke_tool(&handler, "read_file", json!({"path": "test.txt"})).await;
    assert!(result.is_ok());
}

#[tokio::test]
async fn test_read_file_missing_returns_error() {
    let handler = MyHandler::new();
    let result = invoke_tool(&handler, "read_file", json!({"path": "/nonexistent"})).await;
    assert!(result.is_err());
}
```

Tests must cover both success and error paths for each tool.

## Logging

All logging must use `tracing` macros. Use appropriate levels:
- `tracing::info!` — server lifecycle events (start, stop, client connect)
- `tracing::debug!` — tool invocation details (tool name, parameter summary)
- `tracing::warn!` — recoverable issues (retries, fallbacks)
- `tracing::error!` — unrecoverable failures

```rust
tracing::debug!(tool_name = %name, "Invoking tool");
tracing::error!(error = %e, "Tool execution failed");
```

Never use `println!`, `eprintln!`, or the `log` crate. Structured fields (key = %value) are preferred over format strings.

## Verification Checklist

Before marking an MCP server complete:

- [ ] `Cargo.toml` includes `rmcp` with `server` and `transport-stdio` features
- [ ] Project structure matches: `src/main.rs`, `src/handler.rs`, `src/tools/mod.rs`, `src/tools/<name>.rs`
- [ ] Handler impl block has `#[tool_router]` macro
- [ ] Every tool function has `#[tool(name = "...", description = "...")]` attribute
- [ ] Every tool function is `async fn`
- [ ] All tool functions return `Result<ToolCallResult, anyhow::Error>`
- [ ] `tracing` used for all logging (no `println!` or `log` crate)
- [ ] `tests/integration_test.rs` exists with tests for each tool
- [ ] No `unwrap()` or `expect()` in tool handler code
- [ ] `main.rs` uses `rmcp::serve_stdio` with tracing initialization
