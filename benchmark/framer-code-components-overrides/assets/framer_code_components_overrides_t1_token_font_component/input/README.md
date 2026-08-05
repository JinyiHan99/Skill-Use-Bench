# Framer Components Library

A curated storage repository of production-ready **Framer code components** built with React, designed for reuse across Framer projects. Every component follows strict accessibility, performance, internationalization, and motion best practices.

## Project: SheVibes

Primary Framer project consuming these components.

---

## Repository Structure

```
Framer-Components/
├── components/          # All Framer code components (.tsx)
├── docs/                # Extended documentation and references
│   └── framer-guide.md  # Comprehensive Framer development guide
├── CLAUDE.md            # AI assistant development guidelines
└── README.md            # This file
```

## Component Standards

Every component in this repo adheres to the following principles:

### 1. Framer-Native Architecture
- Each component is a **single `.tsx` file** that imports React and Framer APIs
- Uses `addPropertyControls` and `ControlType` for visual editing in Framer
- Exports a default function component compatible with Framer's rendering pipeline
- Respects `RenderTarget` for canvas vs. preview vs. published behavior

### 2. Accessibility First
- All interactive elements have proper ARIA attributes (`role`, `aria-label`, `aria-live`, etc.)
- Keyboard navigation support (focus management, tab order, escape handling)
- Sufficient color contrast ratios (WCAG 2.1 AA minimum)
- Screen reader friendly content and announcements
- `prefers-reduced-motion` respected for all animations
- Semantic HTML elements used over generic `<div>` wrappers

### 3. Framer Extended Font Control
- Uses `ControlType.Font` with `controls: "extended"` for full typography control
- Font properties are **never hardcoded** - always exposed via property controls
- Supports `fontSize`, `fontWeight`, `fontFamily`, `lineHeight`, `letterSpacing`, `textTransform`
- Font styles applied via Framer's font system, not raw CSS where possible
- Example pattern:
  ```tsx
  font: {
    type: ControlType.Font,
    controls: "extended",
    displayFontSize: true,
    displayTextAlignment: true,
  }
  ```

### 4. Locale Awareness & Browser Translation
- All user-facing text exposed as **property controls** (never hardcoded strings)
- Components use `lang` attribute propagation from parent context
- Text content is translation-friendly: no text baked into images or SVGs
- RTL layout support via logical CSS properties (`inline-start`/`inline-end` over `left`/`right`)
- Date, number, and currency formatting uses `Intl` APIs when applicable
- Framer's `useLocaleInfo()` and `useLocaleCode()` hooks used for locale-aware behavior

### 5. Motion & Animation
- **Framer Motion** (`motion` from `framer-motion`) as the primary animation library
- All animations respect `prefers-reduced-motion` media query
- Entrance/exit animations use `AnimatePresence` for clean mount/unmount
- Spring-based animations preferred over duration-based for natural feel
- Animation values exposed as property controls where appropriate (duration, easing, delay)
- Canvas-safe: animations disabled or simplified on `RenderTarget.canvas` for editor performance

### 6. UX Props & No Hardcoding
- **Every visual property** is configurable via Framer property controls
- Colors, spacing, sizes, text, border radius - all exposed, never hardcoded
- Sensible defaults provided for every prop
- Enum controls use `displaySegmentedControl: true` with `optionIcons` for visual clarity
- Conditional property visibility via `hidden()` function for clean UI
- Object and array controls for complex nested configurations

### 7. Performance Optimization
- Components wrapped in `React.memo()` where beneficial
- Expensive computations memoized with `useMemo` / `useCallback`
- Event listeners cleaned up in `useEffect` return functions
- Images use `ControlType.ResponsiveImage` for optimized loading
- No unnecessary re-renders: state kept minimal and local
- Heavy operations gated behind `RenderTarget.current() !== "canvas"` checks
- Lazy loading for heavy dependencies

### 8. Clean Code & Documentation
- Each component file includes a header comment block with:
  - Component name and brief description
  - Property controls documentation
  - Usage notes and known limitations
- TypeScript interfaces for all props
- Consistent naming: PascalCase for components, camelCase for props
- No unused imports, variables, or dead code

---

## How to Use Components

### Adding to Framer
1. Open your Framer project
2. Navigate to **Assets** panel > **Code** tab
3. Create a new **Code Component**
4. Copy the contents of the desired `.tsx` file from `components/`
5. Paste into the Framer code editor
6. The component will appear in your components panel with all property controls

### Updating Components
When modifying components, always:
1. Test in Framer's canvas mode (drag onto canvas, verify property controls)
2. Test in preview mode (click Play, verify interactions and animations)
3. Verify accessibility (keyboard nav, screen reader, reduced motion)
4. Update the component's header comment if behavior changes

---

## Property Controls Quick Reference

| Control Type | Use Case |
|---|---|
| `ControlType.String` | Text inputs, labels, URLs |
| `ControlType.Number` | Sizes, counts, numeric values |
| `ControlType.Boolean` | Toggles, show/hide flags |
| `ControlType.Enum` | Predefined option sets |
| `ControlType.Color` | Any color value |
| `ControlType.Font` | Typography with extended controls |
| `ControlType.ResponsiveImage` | Optimized image with srcSet |
| `ControlType.File` | File uploads (video, audio, etc.) |
| `ControlType.ComponentInstance` | Child component slots |
| `ControlType.Link` | Navigation links |
| `ControlType.Cursor` | CSS cursor selection |
| `ControlType.Object` | Grouped nested properties |
| `ControlType.Array` | Repeatable item lists |
| `ControlType.EventHandler` | Click/interaction handlers |
| `ControlType.Transition` | Animation transitions |
| `ControlType.BoxShadow` | Shadow configuration |

---

## Tech Stack

| Technology | Purpose |
|---|---|
| React 18+ | Component framework |
| TypeScript / TSX | Type safety and Framer compatibility |
| Framer Motion | Animation and gestures |
| Framer API | Property controls, RenderTarget, locale hooks |

---

## Contributing

1. Follow the component standards above
2. Use the component template in `docs/` as a starting point
3. Test thoroughly in Framer before committing
4. Keep components self-contained (single file, no external file dependencies)

## License

Private repository - components for internal use across Framer projects.
