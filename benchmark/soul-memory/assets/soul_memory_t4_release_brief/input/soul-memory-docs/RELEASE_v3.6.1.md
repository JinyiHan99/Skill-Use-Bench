# Soul Memory v3.6.1

## Added

1. Typed memory focus injection
   - groups retrieved memories into User / QST / Config / Recent / Project / General

2. Distilled summaries
   - injects compact bullet summaries instead of raw long snippets

3. Audit logging
   - logs query source (messages vs prompt fallback)
   - logs bucket counts and top sources before injection

## Flow

user message -> extract real query -> search memories -> group + summarize -> prependContext injection -> model response

## Version

- Core: v3.6.1
- Plugin manifest: v0.3.6.1
