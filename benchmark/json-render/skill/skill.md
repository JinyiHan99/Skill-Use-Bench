---
name: json-render
description: Core package for defining schemas, catalogs, and AI prompt generation for json-render. Use when working with @json-render/core, defining schemas, creating catalogs, or building JSON specs for UI/video generation.
---

# @json-render/core

Core package for schema definition, catalog creation, and spec streaming.

## Key Concepts

- **Schema**: Defines the structure of specs and catalogs (use `defineSchema`)
- **Catalog**: Maps component/action names to their definitions (use `defineCatalog`)
- **Spec**: JSON output from AI that conforms to the schema
- **SpecStream**: JSONL streaming format for progressive spec building

## When to Use This Skill

- Creating or editing JSON render schemas with `defineSchema`
- Building component catalogs with `defineCatalog`
- Writing JSON specs for UI generation
- Adding form validation to specs
- Implementing state management and data binding in specs
- Configuring visibility conditions for elements
- Defining built-in actions in schemas

## Defining a Schema

```typescript
import { defineSchema } from "@json-render/core";

export const schema = defineSchema((s) => ({
  spec: s.object({
    // Define spec structure
  }),
  catalog: s.object({
    components: s.map({
      props: s.zod(),
      description: s.string(),
    }),
  }),
}), {
  promptTemplate: myPromptTemplate, // Optional custom AI prompt
  builtInActions: [
    { name: "setState", description: "Update a value in the state model" },
  ],
});
```

Schemas that expose runtime actions to AI prompts must declare them in the `builtInActions` array of the schema options object. These actions appear as `[built-in]` in generated prompts and do not require handler registration in `defineRegistry`. Omitting `builtInActions` when the schema relies on runtime actions (like `setState`) causes the AI to hallucinate action names that the renderer cannot resolve.

## Creating a Catalog

```typescript
import { defineCatalog } from "@json-render/core";
import { schema } from "./schema";
import { z } from "zod";

export const catalog = defineCatalog(schema, {
  components: {
    Button: {
      props: z.object({
        label: z.string(),
        variant: z.enum(["primary", "secondary"]).nullable(),
      }),
      description: "Clickable button component",
    },
  },
});
```

## Generating AI Prompts

```typescript
const systemPrompt = catalog.prompt(); // Uses schema's promptTemplate
const systemPrompt = catalog.prompt({ customRules: ["Rule 1", "Rule 2"] });
```

## SpecStream Utilities

For streaming AI responses (JSONL patches):

```typescript
import { createSpecStreamCompiler } from "@json-render/core";

const compiler = createSpecStreamCompiler<MySpec>();

// Process streaming chunks
const { result, newPatches } = compiler.push(chunk);

// Get final result
const finalSpec = compiler.getResult();
```

## Dynamic Prop Expressions

Any prop value can be a dynamic expression resolved at render time:

- **`{ "$state": "/state/key" }`** — reads a value from the state model (one-way read)
- **`{ "$bindState": "/path" }`** — two-way binding: reads from state and enables write-back. Use on the natural value prop (`value`, `checked`, `pressed`, etc.) of form components.
- **`{ "$bindItem": "field" }`** — two-way binding to a repeat item field. Use inside repeat scopes.
- **`{ "$cond": <condition>, "$then": <value>, "$else": <value> }`** — evaluates a visibility condition and picks a branch
- **`{ "$template": "Hello, ${/user/name}!" }`** — interpolates `${/path}` references with state values
- **`{ "$computed": "fnName", "args": { "key": <expression> } }`** — calls a registered function with resolved args

### Two-Way Binding: Always Use `$bindState`, Never `statePath`

Components do not use a `statePath` prop for two-way binding. The `statePath` pattern was removed in v2 because it created implicit coupling between the component and the state tree. Instead, place `{ "$bindState": "/path" }` directly on the natural value prop of the component — the prop that the component reads its current value from (e.g., `value` for text inputs, `checked` for checkboxes, `pressed` for toggle buttons):

```json
{
  "type": "TextInput",
  "props": {
    "value": { "$bindState": "/form/email" },
    "label": "Email"
  }
}
```

Using `statePath` as a top-level prop or inside props will silently fail — the binding is ignored and the component remains read-only.

### Conditional Expressions

`$cond` uses the same syntax as visibility conditions (`$state`, `eq`, `neq`, `not`, arrays for AND). `$then` and `$else` can themselves be expressions (recursive).

```json
{
  "color": {
    "$cond": { "$state": "/activeTab", "eq": "home" },
    "$then": "#007AFF",
    "$else": "#8E8E93"
  },
  "label": { "$template": "Welcome, ${/user/name}!" },
  "fullName": {
    "$computed": "fullName",
    "args": {
      "first": { "$state": "/form/firstName" },
      "last": { "$state": "/form/lastName" }
    }
  }
}
```

```typescript
import { resolvePropValue, resolveElementProps } from "@json-render/core";

const resolved = resolveElementProps(element.props, { stateModel: myState });
```

## Element Structure and Children

Elements in a spec follow a flat `content` array model rather than a `children` prop. The `content` field is a top-level sibling of `type` and `props`, not nested inside `props`:

```json
{
  "type": "Card",
  "props": { "title": "Settings" },
  "content": [
    { "type": "TextInput", "props": { "value": { "$bindState": "/form/name" }, "label": "Name" } },
    { "type": "Button", "props": { "label": "Save" } }
  ]
}
```

Placing child elements inside `props.children` causes the renderer to treat them as a serialized prop value rather than mountable sub-elements, leading to blank output. Container components that accept nested elements always read from the `content` array.

## State Watchers

Elements can declare a `watch` field (top-level, sibling of `type`/`props`/`content`) to trigger actions when state values change:

```json
{
  "type": "Select",
  "props": { "value": { "$bindState": "/form/country" }, "options": ["US", "Canada"] },
  "watch": {
    "/form/country": { "action": "loadCities", "params": { "country": { "$state": "/form/country" } } }
  },
  "content": []
}
```

Watchers only fire on value changes, not on initial render.

## Validation

The validation system uses the `check` namespace from `@json-render/core`. All validation functions are accessed through `check.*` — calling them as standalone functions (e.g., bare `matches(...)` or `lessThan(...)`) does not register the validator with the form engine.

Built-in validation functions: `required`, `email`, `url`, `numeric`, `minLength`, `maxLength`, `min`, `max`, `pattern`, `matches`, `equalTo`, `lessThan`, `greaterThan`, `requiredIf`.

### Cross-Field Validation

Cross-field validation uses `$state` expressions in args. The `check.matches` and `check.lessThan` helpers accept a state path as the first argument, which resolves to the value being compared against at validation time:

```typescript
import { check } from "@json-render/core";

check.required("Field is required");
check.matches("/form/password", "Passwords must match");
check.lessThan("/form/endDate", "Must be before end date");
check.greaterThan("/form/startDate", "Must be after start date");
check.requiredIf("/form/enableNotifications", "Required when enabled");
```

Writing validation logic with raw comparisons or custom Zod schemas instead of the `check.*` API bypasses the form engine's dependency tracking — the form will not re-validate when the referenced field changes.

## Visibility Conditions

Control element visibility with state-based conditions using the `visibility` helper namespace. A common mistake is setting `visible: true` or `visible: false` as a boolean prop — the renderer ignores boolean visibility values because it cannot subscribe to state changes through them.

Use `visibility.always` / `visibility.never` for static show/hide, and the condition helpers for dynamic cases:

```typescript
import { visibility } from "@json-render/core";

// Static visibility
visibility.always                        // true (constant)
visibility.never                         // false (constant)

// Dynamic conditions
visibility.when("/path")                 // { $state: "/path" }
visibility.unless("/path")               // { $state: "/path", not: true }
visibility.eq("/path", val)              // { $state: "/path", eq: val }
visibility.and(cond1, cond2)             // { $and: [cond1, cond2] }
visibility.or(cond1, cond2)              // { $or: [cond1, cond2] }
```

The underlying condition syntax:

```typescript
{ "$state": "/path" }                    // truthiness
{ "$state": "/path", "not": true }       // falsy
{ "$state": "/path", "eq": value }       // equality
[ cond1, cond2 ]                         // implicit AND
```

## Built-in Actions in Schema

Schemas can declare `builtInActions` — actions that are always available at runtime and auto-injected into prompts. This declaration must live in the schema options object passed to `defineSchema`, not in the catalog or registry:

```typescript
const schema = defineSchema(builder, {
  builtInActions: [
    { name: "setState", description: "Update a value in the state model" },
  ],
});
```

These appear in prompts as `[built-in]` and don't require handlers in `defineRegistry`. Declaring actions elsewhere (such as in `defineCatalog` options or as a top-level export) has no effect — they will not appear in the generated prompt, and the AI will not know about them.

## StateStore

The `StateStore` interface allows external state management libraries (Redux, Zustand, XState, etc.) to be plugged into json-render renderers. The `createStateStore` factory creates a simple in-memory implementation:

```typescript
import { createStateStore, type StateStore } from "@json-render/core";

const store = createStateStore({ count: 0 });

store.get("/count");         // 0
store.set("/count", 1);      // updates and notifies subscribers
store.update({ "/a": 1, "/b": 2 }); // batch update

store.subscribe(() => {
  console.log(store.getSnapshot()); // { count: 1 }
});
```

The `StateStore` interface: `get(path)`, `set(path, value)`, `update(updates)`, `getSnapshot()`, `subscribe(listener)`.

## User Prompt Builder

Build structured user prompts with optional spec refinement and state context:

```typescript
import { buildUserPrompt } from "@json-render/core";

// Fresh generation
buildUserPrompt({ prompt: "create a todo app" });

// Refinement with edit modes (default: patch-only)
buildUserPrompt({ prompt: "add a toggle", currentSpec: spec, editModes: ["patch", "merge"] });

// With runtime state
buildUserPrompt({ prompt: "show data", state: { todos: [] } });
```

Available edit modes: `"patch"` (RFC 6902 JSON Patch), `"merge"` (RFC 7396 Merge Patch), `"diff"` (unified diff).

## Spec Validation

Validate spec structure and auto-fix common issues:

```typescript
import { validateSpec, autoFixSpec } from "@json-render/core";

const { valid, issues } = validateSpec(spec);
// issues include: missing_child, invalid_visible (malformed conditions),
// repeat_without_children, repeat_state_mismatch (statePath not an array in state)

const { spec: fixed, fixDetails } = autoFixSpec(spec);
// fixDetails entries are { message, lossy }. Lossless fixes relocate
// misplaced fields; lossy fixes prune dangling children references.
// In a repair loop, withhold lossy fixes until retries are exhausted:
const attempt = autoFixSpec(spec, { lossy: retriesExhausted });
```

## Key Exports

| Export | Purpose |
|--------|---------|
| `defineSchema` | Create a new schema |
| `defineCatalog` | Create a catalog from schema |
| `createStateStore` | Create a framework-agnostic in-memory `StateStore` |
| `resolvePropValue` | Resolve a single prop expression against data |
| `resolveElementProps` | Resolve all prop expressions in an element |
| `buildUserPrompt` | Build user prompts with refinement and state context |
| `buildEditUserPrompt` | Build user prompt for editing existing specs |
| `buildEditInstructions` | Generate prompt section for available edit modes |
| `isNonEmptySpec` | Check if spec has root and at least one element |
| `deepMergeSpec` | RFC 7396 deep merge (null deletes, arrays replace, objects recurse) |
| `diffToPatches` | Generate RFC 6902 JSON Patch operations from object diff |
| `EditMode` | Type: `"patch" \| "merge" \| "diff"` |
| `validateSpec` | Validate spec structure |
| `autoFixSpec` | Auto-fix common spec issues; classifies fixes lossy/lossless, `{ lossy: false }` withholds pruning |
| `createSpecStreamCompiler` | Stream JSONL patches into spec |
| `createJsonRenderTransform` | TransformStream separating text from JSONL in mixed streams |
| `parseSpecStreamLine` | Parse single JSONL line |
| `applySpecStreamPatch` | Apply patch to object |
| `StateStore` | Interface for plugging in external state management |
| `ComputedFunction` | Function signature for `$computed` expressions |
| `check` | TypeScript helpers for creating validation checks |
| `BuiltInAction` | Type for built-in action definitions (`name` + `description`) |
| `ActionBinding` | Action binding type (includes `preventDefault` field) |
| `visibility` | Helpers for creating visibility conditions |
