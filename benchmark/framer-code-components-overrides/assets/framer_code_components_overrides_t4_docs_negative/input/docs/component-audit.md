# Framer Components Quality Audit

**Date:** 2026-04-05
**Audited against:** CLAUDE.md rules and README.md component standards
**Components audited:** 8

---

## Summary Table

| Category | TypewriterEffect | TextRevealPro | Tarievencalculator | SheVibesPreloader | CircularFlow | WordWheel | StepsTimeline | PodcastCarousel |
|---|---|---|---|---|---|---|---|---|
| 1. Style Prop Spreading | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| 2. Layout Annotations | WARN | PASS | FAIL | PASS | WARN | PASS | PASS | PASS |
| 3. displayName | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL |
| 4. Font Controls | PASS | PASS | WARN | FAIL | WARN | WARN | WARN | WARN |
| 5. Hardcoded Text | PASS | WARN | WARN | FAIL | PASS | PASS | WARN | FAIL |
| 6. Hardcoded Colors | PASS | WARN | WARN | WARN | PASS | PASS | PASS | WARN |
| 7. Hardcoded Spacing/Sizes | WARN | WARN | WARN | FAIL | WARN | PASS | WARN | WARN |
| 8. Reduced Motion | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS |
| 9. Canvas Safety | FAIL | FAIL | FAIL | PASS | FAIL | PASS | PASS | PASS |
| 10. Accessibility | PASS | WARN | PASS | FAIL | PASS | PASS | PASS | PASS |
| 11. RTL/Locale | FAIL | WARN | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| 12. Effect Cleanup | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 13. Browser API Guards | WARN | FAIL | WARN | PASS | PASS | PASS | PASS | WARN |
| 14. TypeScript | WARN | WARN | FAIL | FAIL | PASS | WARN | PASS | WARN |
| 15. Project-Specific Content | PASS | PASS | FAIL | FAIL | PASS | FAIL | FAIL | FAIL |

**Legend:** PASS = meets standard, WARN = partially compliant / minor issues, FAIL = does not meet standard

---

## Detailed Findings Per Component

---

### 1. TypewriterEffect.tsx

#### Critical (will break in other projects)

- **No canvas safety (line 45-384):** No `RenderTarget.current()` check. The IntersectionObserver (line 140) and multiple `setInterval`/`setTimeout` calls will fire on canvas, hurting editor performance.
- **No displayName:** `TypewriterEffect.displayName` is never set. Framer panel will show a generic name.
- **IntersectionObserver not canvas-guarded (line 140):** Per CLAUDE.md, IntersectionObserver fires excessively during canvas interactions and must be guarded.

#### Important (standards compliance)

- **RTL not supported:** Uses `marginLeft`/`marginRight` (line 377-378) instead of logical properties (`marginInlineStart`/`marginInlineEnd`). No `useLocaleInfo`/`useLocaleCode`.
- **Layout annotations incomplete (line 42-43):** Has `@framerSupportedLayoutWidth auto` and `@framerSupportedLayoutHeight auto` but missing `@framerIntrinsicWidth`/`@framerIntrinsicHeight`.
- **`window` access outside effect (line 129-131):** `prefersReducedMotion` is computed at render time using `window.matchMedia` outside `useEffect`. While guarded with `typeof window !== "undefined"`, this value won't update if the preference changes. Should use a `useEffect`+`useState` pattern like TextRevealPro does.
- **TypeScript `font: any` (line 34):** The `font` prop is typed as `any`. Should be `Record<string, any>` or a proper font interface.

#### Nice-to-have (polish)

- **No `React.memo()` wrapper:** Standards recommend wrapping components with many props in `React.memo()`.
- **No header version comment:** File has a comment but no version number.

---

### 2. TextRevealPro.tsx

#### Critical (will break in other projects)

- **No style prop spreading (line 556-655):** The root element is a fragment (`<>...</>`). The `style` prop is not received or spread. Framer cannot control this component's layout positioning.
- **No displayName:** `TextRevealPro.displayName` is never set.
- **`document` access not SSR-guarded in `useTranslationDetector` (lines 108-118):** Directly accesses `document.documentElement`, `document.querySelector`, `document.body` without `typeof document !== "undefined"` guard. Will break during SSR.

#### Important (standards compliance)

- **No canvas safety:** No `RenderTarget.current()` check. The scroll listener, MutationObservers, and per-frame span updates will all run on canvas.
- **`window` access not SSR-guarded (line 237):** `window.matchMedia` called directly in `useEffect` without a `typeof window` guard.
- **Hardcoded fallback font (line 427-430):** `fontFamily: "Inter, sans-serif"` is hardcoded as a fallback when no font prop is provided.
- **Hardcoded colors in empty state (line 437):** `color: "#999"` is hardcoded.
- **`font: any` in Props (line 193):** Should be a more specific type.
- **RTL partial (line 798):** Has an `rtl` boolean prop that sets `direction`, but does not use `useLocaleInfo`/`useLocaleCode` to auto-detect. Uses physical properties like `left`, `right`, `top`, `bottom` throughout.

#### Nice-to-have (polish)

- **No `React.memo()` on main component.**
- **Performance warning strings are hardcoded (lines 572-573, 591-592, 610-611):** Should be property controls or at least constants.

---

### 3. Tarievencalculator.tsx

#### Critical (will break in other projects)

- **No style prop spreading:** The root `<section>` (line 653) does not spread `props.style`. Framer cannot control layout.
- **69 hardcoded Dutch insurance policies (lines 10-357):** The entire tariff dataset is baked into the component. This component is entirely Netherlands-specific and cannot be reused for any other purpose.
- **Class component used (lines 399-420):** `TranslateSafeBoundary` is a class component (`extends Component`). CLAUDE.md says "Never use class components." While error boundaries require class components in React, this should be documented.
- **`@ts-ignore` on font prop (line 447):** Suppresses type checking.
- **No TypeScript props interface:** Props are destructured inline with defaults but no `interface Props` is defined.
- **No displayName** set.

#### Important (standards compliance)

- **No layout annotations:** Missing `@framerSupportedLayoutWidth/Height` JSDoc annotations entirely.
- **No reduced motion support:** Animations (CSS transitions on cards, breakdown reveal) have no `prefers-reduced-motion` check.
- **No canvas safety:** No `RenderTarget.current()` check. `ResizeObserver` (line 557) runs on canvas without guard.
- **Hardcoded Dutch text not exposed as controls (lines 714-715, 1253, 1266-1267, 1585-1586, 1593-1594, 1609, 1757):** Multiple strings like "Eigen bijdrage berekenen", "Maak een keuze", "Kies polis + behandelaar", "NZa-tarief", "Vergoeding verzekeraar", "Jij betaalt", "Wis keuzes" are hardcoded and not exposed as property controls.
- **Hardcoded colors:** `"#fff"` (line 1128), `"#ffffff"` (line 1066), `"#9ca3af"` (line 649), `"#e5e7eb"` (line 1603), `"#f3f0ff"` (line 924), `"#f0ecff"` (line 925) are not property controls.
- **Font applied as `fontFamily` only (lines 531-535, throughout):** The font prop from `ControlType.Font` returns a style object, but only `fontFamily` is extracted. All other font properties (weight, size, style, letter-spacing) are ignored and hardcoded inline. Violates the "always spread `...font`" rule.
- **RTL not supported:** Uses physical CSS properties throughout (`left`, `right`, `marginRight`, `paddingLeft`, `textAlign: "right"`).
- **`document.addEventListener` not SSR-guarded (line 580):** Direct `document` access outside `typeof document` check.

#### Nice-to-have (polish)

- **Hardcoded spacing values:** Many hardcoded px values like `padding: "10px 18px"` (line 916), `gap: 24` (line 699), `fontSize: 14` (line 840), etc. that could be property controls.
- **`Component` imported from React (line 6):** Imports `Component` for the error boundary, mixed with function-component-only paradigm.

---

### 4. SheVibesPreloader.tsx

#### Critical (will break in other projects)

- **Hardcoded "SheVibes" branding (line 218):** The text "SheVibes" is hardcoded and not a property control.
- **Hardcoded "GGZ Praktijk voor Vrouwen" (line 222):** Dutch subtitle is hardcoded and not a property control.
- **No style prop spreading (line 143-155, 170-226):** Neither the canvas placeholder nor the main overlay spread `props.style`.
- **Props typed as `any` (line 44):** `function SheVibesPreloader(props: any)` -- no interface defined at all.
- **No displayName** set.
- **Hardcoded font family (line 53):** `"Google Sans, system-ui, sans-serif"` is hardcoded and not a property control. Uses only `fontWeight` from controls, ignoring `ControlType.Font`.
- **`var` instead of `const`/`let` throughout (lines 45-71):** Uses `var` for all declarations, which is non-standard modern JavaScript.

#### Important (standards compliance)

- **No reduced motion support:** Counting animation and exit slide have no `prefers-reduced-motion` check.
- **No layout annotations for width/height flexibility:** Has `@framerSupportedLayoutWidth fixed` which is fine, but the component renders as `width: 0, height: 0` (line 171) making layout annotations somewhat misleading.
- **`createElement` instead of JSX (lines 7-33):** Uses `createElement` API instead of JSX for digit building. While functional, inconsistent with the rest of the codebase.
- **Hardcoded positioning values (lines 183-184, 210-211):** `left: 40, bottom: 40`, `bottom: 40, right: 40` are hardcoded px values.
- **No ARIA attributes:** The preloader has no `role`, `aria-label`, or screen reader announcement. No way for assistive tech to know a loading state is active.
- **RTL not supported:** Uses physical properties (`left`, `right`, `marginLeft`).
- **Session key default "sv-pre-v2" (line 52):** SheVibes-specific default.

#### Nice-to-have (polish)

- **Color defaults are SheVibes brand colors:** `rgb(122, 85, 243)` and `#FFFEF7` are the SheVibes palette. While these are property controls, the defaults limit reusability.

---

### 5. CircularFlow.tsx

#### Critical (will break in other projects)

- **No style prop spreading (line 338-391):** The root `<div>` does not spread `props.style`. Framer cannot control layout.
- **No displayName with space:** `CircularFlow.displayName = "CircularFlow"` (line 394) -- should have a display-friendly name like "Circular Flow".
- **ResizeObserver not canvas-guarded (line 225):** Runs on canvas without `RenderTarget.current()` check. Per CLAUDE.md, ResizeObserver fires excessively during canvas interactions.

#### Important (standards compliance)

- **No reduced motion support:** Scroll-driven animation and CSS transitions have no `prefers-reduced-motion` check anywhere.
- **Layout annotations incomplete (line 67-68):** Has `@framerSupportedLayoutWidth fixed` and `@framerSupportedLayoutHeight fixed` but no `@framerIntrinsicWidth`/`@framerIntrinsicHeight` to set default canvas size.
- **Font not spread correctly (lines 168-169, 301-302):** `titleFont` and `labelFont` are spread as `...titleFont` into style objects, but they also have hardcoded `lineHeight: "1.1"` (line 170) and `whiteSpace: "nowrap"` overrides. More importantly, font properties are applied individually in step labels (line 303-304): `fontWeight: isAnnotated ? 600 : labelFont.fontWeight`.
- **RTL not supported:** Uses physical CSS properties (`left`, `top`, absolute positioning). The circular diagram positions labels with absolute pixel offsets.
- **`font: any` not used -- custom `FontStyle` interface (lines 36-43):** While better than `any`, the interface is manually defined rather than using Framer's font system type.
- **No canvas safety for scroll listener (line 241-268):** The scroll event listener runs regardless of render target.

#### Nice-to-have (polish)

- **Hardcoded `gap: "4px"` (line 382)** in title container.
- **`annotations` fontSize hardcoded to `12px` (line 313).**

---

### 6. WordWheel.tsx

#### Critical (will break in other projects)

- **No style prop spreading (lines 197, 240-275):** Neither the static nor animated container spreads `props.style`. Framer cannot position or size the component.
- **No displayName** set.
- **Default words are Dutch (lines 37-45):** "Verslaving", "Persoonlijkheid", "Klinische zorg", etc. are Dutch mental health terms specific to the SheVibes project.

#### Important (standards compliance)

- **No reduced motion support:** The spring animation and interval-based rotation have no `prefers-reduced-motion` check. The `useIsStaticRenderer` check covers canvas but not the user preference.
- **Font not spread correctly (lines 70-89):** Font properties are manually extracted (`fontFamily`, `fontSize`, `fontWeight`, etc.) instead of spreading `...font`. The component has a 19-entry `variantToWeight` lookup table (lines 13-33) that reimplements what Framer's font system handles natively.
- **RTL not supported:** No logical CSS properties used. Hardcoded `textAlign: "center"` everywhere.
- **Props interface defined after component (lines 366-383):** Minor but Props should be defined before the component for readability.
- **`font?: any` in Props (line 372):** Should be typed more specifically.

#### Nice-to-have (polish)

- **Default words in property controls also Dutch (lines 412-419):** The `defaultValue` array contains the same Dutch terms.
- **`willChange: "transform, opacity"` on every word item (line 358):** May cause excessive GPU memory usage.

---

### 7. StepsTimeline.tsx

#### Critical (will break in other projects)

- **No style prop spreading (line 320-518):** The root `<div>` does not spread `props.style`.
- **No displayName** set.
- **Default step content is Dutch/SheVibes-specific (lines 100-121):** "Kennismakingsgesprek", "Intakegesprek & plan", "Behandeltraject", "Groei & afsluiting" with Dutch descriptions about GGZ therapy are hardcoded as defaults.

#### Important (standards compliance)

- **No reduced motion support:** CSS transitions (`transition: BADGE_TRANSITION`, etc.) and scroll-driven animations have no `prefers-reduced-motion` check.
- **Font not spread correctly (lines 271-291, 483-508):** Uses a custom `resolveFont()` function (lines 6-49) that manually picks apart font properties instead of spreading `...font`. Individual properties like `fontFamily`, `fontSize`, `fontWeight` are applied one by one.
- **RTL not supported:** Uses physical properties: `translateX(-8px)` (line 88), `paddingBottom` (line 474), `paddingTop` (line 475), `marginTop` (line 431), `marginBottom` (line 432).
- **`window` accessed in scroll handler without guard (line 169):** The `updateScroll` callback accesses `window.innerHeight` directly. While the effect that attaches the listener has a `shouldAnimate` guard, the callback itself doesn't guard.
- **Hardcoded colors (line 83):** `"rgba(0,0,0,0)"` used for inactive badge background. Lines 88-89: `translateX(-8px)` hardcoded offset not a prop.

#### Nice-to-have (polish)

- **Default step text in property controls also Dutch (lines 588-608).**
- **Polling interval for `activeStep` (line 316):** Uses `setInterval(checkActive, 100)` to sync DOM state to React state. While it works, it's a workaround.
- **Hardcoded `gap: 24` (line 352)** between badge column and text.
- **Badge `badgeColor` default `"#7A55F3"` is SheVibes purple.**

---

### 8. PodcastCarousel.tsx

#### Critical (will break in other projects)

- **No style prop spreading (line 493-796):** The root `<div>` does not spread `props.style`.
- **No displayName** set.
- **Hardcoded "SheVibes" branding (lines 640, 715):** The text "SheVibes" appears twice as a hardcoded wordmark on card faces, not exposed as a property control.
- **Default items are SheVibes Spotify episodes (lines 62-71):** 9 specific Spotify/YouTube URLs from the SheVibes podcast are hardcoded as defaults.
- **Dutch text hardcoded (lines 689-694, 722-723, 741-742, 755, 482-483, 514, 566, 773):** "Podcast", "Aflevering", "Luister op Spotify", "Bekijk op YouTube", "Vorige aflevering", "Volgende aflevering", "Podcast en video carousel", "Kies aflevering", "Item X van Y" are all hardcoded Dutch strings.

#### Important (standards compliance)

- **`window.matchMedia` not SSR-guarded in `useReducedMotion` (line 21):** Accesses `window.matchMedia` directly in `useEffect` without a `typeof window` check.
- **`titleFont` typed as `any` (line 814):** In the Props interface.
- **Font not spread correctly (lines 445-460):** Manually extracts `fontFamily`, `fontSize`, `fontWeight` from the font object instead of spreading.
- **`fetch` not canvas-guarded (lines 415-442):** The oEmbed fetch calls fire on preview but the `isStatic` check only covers the static renderer, not the full canvas. Per CLAUDE.md, `fetch` without canvas guards causes infinite request loops.
- **`type: "font" as any` in property controls (line 908):** Uses a type assertion hack for the font control instead of `ControlType.Font`.
- **RTL not supported:** Uses physical properties throughout (`left`, `right`, `top`, `bottom`).
- **Hardcoded colors (lines 613, 638-639, 684-685, 689, 693, 698):** Multiple `rgba(...)` and `#FFF` values that are not property controls.
- **Hardcoded font family (line 637):** `"Bricolage Grotesque, sans-serif"` is hardcoded for the SheVibes wordmark.

#### Nice-to-have (polish)

- **`PLACEHOLDER_COLORS` are SheVibes brand colors (line 73):** `#7956F3`, `#F27CA4`, `#24B0E5`, `#FFD232`.
- **Hardcoded padding/spacing values** throughout card layouts (`padding: "28px 24px"`, `gap: 8`, etc.).

---

## Cross-Cutting Issues (Affect All/Most Components)

### 1. Style Prop Spreading -- 7 of 8 components FAIL
Only `TypewriterEffect` spreads `props.style`. All others ignore it, meaning Framer cannot control their position/size on canvas. **This is the single most critical finding.**

### 2. displayName -- 7 of 8 components FAIL
Only `CircularFlow` sets `displayName`. The Framer component panel will show unhelpful names for the rest.

### 3. RTL/Locale Support -- 8 of 8 components FAIL or WARN
No component uses `useLocaleInfo`/`useLocaleCode`. Only `TextRevealPro` has a manual RTL toggle. All use physical CSS properties (`left`, `right`, `marginLeft`, etc.) instead of logical ones.

### 4. Reduced Motion -- 5 of 8 components FAIL
Only `TypewriterEffect`, `TextRevealPro`, and `PodcastCarousel` check `prefers-reduced-motion`. The rest animate without any fallback.

### 5. Font Spreading -- Most components partially comply
Most components use `ControlType.Font` with `controls: "extended"` but then manually extract individual font properties instead of spreading `...font`. This breaks when Framer passes additional font properties.

### 6. Project-Specific Content -- 4 of 8 components have SheVibes/Dutch defaults
`SheVibesPreloader`, `Tarievencalculator`, `StepsTimeline`, and `PodcastCarousel` contain hardcoded Dutch text, SheVibes branding, or domain-specific data that prevents reuse in other projects without modification. `WordWheel` has Dutch default words.

---

## Priority Remediation Roadmap

### Phase 1 -- Critical (Do First)
1. Add `...props.style` spreading to the root element of all 7 failing components
2. Add `ComponentName.displayName = "Friendly Name"` to all 7 missing components
3. Remove hardcoded "SheVibes" text from `SheVibesPreloader` and `PodcastCarousel` -- expose as property controls
4. Add `RenderTarget.current()` canvas guards to components using `IntersectionObserver`, `ResizeObserver`, `fetch`, and heavy animations
5. Add `typeof window/document` SSR guards where missing

### Phase 2 -- Important (Standards Compliance)
1. Add `prefers-reduced-motion` support to `Tarievencalculator`, `SheVibesPreloader`, `CircularFlow`, `WordWheel`, `StepsTimeline`
2. Change font application to spread `...font` instead of extracting individual properties
3. Replace hardcoded Dutch text with property controls (especially in `Tarievencalculator`, `PodcastCarousel`)
4. Add proper TypeScript interfaces where `any` is used
5. Add `@framerIntrinsicWidth/Height` annotations where missing
6. Replace physical CSS properties with logical ones for RTL support

### Phase 3 -- Polish
1. Add `useLocaleInfo`/`useLocaleCode` hooks for locale-aware behavior
2. Wrap components in `React.memo()` where beneficial
3. Replace SheVibes-specific default values with generic defaults
4. Convert `var` to `const`/`let` in `SheVibesPreloader`
5. Extract remaining hardcoded spacing/size values into property controls
