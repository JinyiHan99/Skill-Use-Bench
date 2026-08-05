# ResizeMe - Center-on-Resize Feature Plan

## Project Overview

ResizeMe is a lightweight utility that provides a floating quick-resize menu for resizing existing desktop windows to common preset sizes. Target users are developers, designers, and power users who frequently resize app windows for testing, layout checks, and productivity workflows.

This feature adds an optional behavior to automatically center the target window on its current monitor after applying a quick-resize preset, controllable directly from the floating menu and persisted across sessions.

## Architecture & Technology Stack

### Recommended Approach

Implement the feature as a small, self-contained enhancement that:
- Reuses the existing quick-resize UX (`MainWindow`) and positioning utilities (`WindowPositionHelper`).
- Persists a simple boolean preference using `ApplicationData.Current.LocalSettings` to avoid overloading the presets JSON.
- Adds minimal, focused logic in the resize flow and avoids impacting unrelated services.

### Key Technologies
- **WinUI 3 / XAML (`MainWindow.xaml`)**: To add the quick-resize toggle control and bind it to the new behavior.
- **C# + `ApplicationData.Current.LocalSettings`**: To store and retrieve the "center after resize" preference.
- **Existing `WindowPositionHelper` & P/Invoke (`WindowsApi`)**: To implement centering logic for external windows on their current monitor.

### High-Level Architecture

- `MainWindow` hosts:
  - The quick-resize preset list (`DynamicPresetsPanel`).
  - A new toggle control for "Center after resize".
  - Wiring to read/write a persisted `CenterOnResize` setting.
- `UserPreferences` (new lightweight helper) wraps `ApplicationData.Current.LocalSettings` for simple, typed access to app-level flags.
- `WindowResizer` remains responsible for size changes; post-resize positioning is invoked from `MainWindow.ResizeSelectedWindow` via `WindowPositionHelper` when the preference is enabled.
- `WindowPositionHelper` gains (or exposes) a helper that can center an external window (via `WindowInfo.Handle`) on its current monitor work area.

Data flow:
1. User toggles **Center after resize** in the quick menu.
2. `MainWindow` updates `UserPreferences.CenterOnResize`.
3. When a preset is clicked, `ResizeSelectedWindow` resizes the target window via `WindowResizer`.
4. If `CenterOnResize` is `true` and resize succeeds, `MainWindow` uses `WindowPositionHelper` to center the target window, then optionally re-activates it and hides the menu.

## Implementation Plan

### Scope & Objectives

**Primary goals**:
- Add a toggle in the quick-resize floating window to **center the target window on its current monitor after a resize**.
- Persist the toggle state across app sessions.
- Ensure centering occurs only when the resize succeeds and does not introduce flicker or interfere with existing behavior.

**User impact**:
- Users who routinely position windows in the center after resizing save time and reduce manual dragging.
- The behavior is optional and discoverable directly from the quick-resize UI.

**Success criteria**:
- With the toggle off, resize behavior is unchanged and preserves original window position.
- With the toggle on, after a successful quick-resize, the target window is centered on its current monitor.
- The toggle state persists across app restarts.

### Key Work Items

- Add a **quick-resize UI toggle** in `MainWindow.xaml` for "Center after resize".
- Introduce a **simple preferences helper** wrapping `ApplicationData.Current.LocalSettings` for bool settings.
- Implement **post-resize centering behavior** that uses the current monitor and respects multi-monitor setups.
- Wire **toggle state load/save** in `MainWindow` and integrate centering into `ResizeSelectedWindow`.
- Validate behavior manually (and via any existing tests where applicable) across both single and multi-monitor scenarios.

### Single PR Summary

**PR Name:** Add center-on-resize option to quick menu  
**Branch:** `feature-center-on-resize`  
**Description:** Adds a quick menu toggle and persisted preference to center the resized window on its current monitor after applying a preset.  
**Goal:** Allow users to optionally auto-center the target window after quick-resize while keeping the default behavior unchanged.

**Key Components/Files:**
- `ResizeMe/MainWindow.xaml`
- `ResizeMe/MainWindow.xaml.cs`
- `ResizeMe/Helpers/WindowPositionHelper.cs`
- `ResizeMe/Services` (new `UserPreferences` helper or equivalent, if created)

**Dependencies:**
- Existing WinUI 3 application structure and `WindowResizer`/`WindowPositionHelper` utilities.
- No external package dependencies.

**Tech Details:**
- Use `Windows.Storage.ApplicationData.Current.LocalSettings` to persist a `bool CenterOnResize` flag.
- Add a `ToggleSwitch` (or styled `CheckBox`) within the quick-resize card labeled "Center after resize".
- On `MainWindow` construction, read the saved flag and set the toggle and an internal `_centerOnResize` field.
- In `ResizeSelectedWindow`, after a successful resize and before hiding the menu, when `_centerOnResize` is `true`, call a new helper method (e.g., `WindowPositionHelper.CenterExternalWindowOnMonitor(WindowInfo window)`) that:
  - Uses `GetWindowRect` to get the window bounds.
  - Determines the appropriate monitor via `MonitorFromRect` or equivalent.
  - Computes centered coordinates within that monitor's work area and calls `SetWindowPos`.
- Maintain existing activation (`_windowResizer.ActivateWindow(targetWindow)`) and timing (`Task.Delay`) to avoid regressions.

**Testing Approach:**
- Manual testing paths:
  - Toggle OFF: Confirm window size changes but position remains where it was.
  - Toggle ON: Confirm window size changes and then moves to center of current monitor.
  - Restart app: Confirm the toggle state persists and behavior matches.
  - Multi-monitor: Resize a window on monitor 2 and assert it centers on monitor 2, not monitor 1.
- Run existing test suite (`dotnet test ResizeMe.sln`) to guard against regressions.

## Implementation Sequence

1. **Add preference storage helper**
   - Create a small `UserPreferences` class (e.g., in `ResizeMe/Services/UserPreferences.cs`) that exposes a `bool CenterOnResize { get; set; }` property backed by `ApplicationData.Current.LocalSettings`.
   - Implement a safe default (`false`) if no value is present and simple exception handling.

2. **Update quick-resize UI (`MainWindow.xaml`)**
   - Within the content card under "Quick Resize", add a compact toggle control labeled "Center after resize" (e.g., below the presets stack and above the hint text).
   - Ensure the control visually aligns with existing Fluent styling (font sizes, margins, and brushes).

3. **Wire up preference in `MainWindow.xaml.cs`**
   - Add a `_centerOnResize` field and a `UserPreferences` instance.
   - In the `MainWindow` constructor (after `InitializeComponent`), load the `CenterOnResize` preference and set both `_centerOnResize` and the toggle's initial state.
   - Handle the toggle's `Toggled` (or `Checked/Unchecked`) event to update `_centerOnResize`, save it via `UserPreferences`, and optionally update `StatusText` briefly.

4. **Implement external window centering helper**
   - Add a method in `WindowPositionHelper` such as `CenterExternalWindowOnMonitor(WindowInfo windowInfo)` or reuse the existing logic by introducing an overload that accepts an `IntPtr` or `WindowBounds` instead of a WinUI `Window`.
   - Use the existing P/Invoke infrastructure (`MonitorFromPoint`, `GetMonitorInfo`, `SetWindowPos`) to calculate centered coordinates within the work area of the monitor containing the window.
   - Ensure the helper no-ops safely if the handle is invalid or bounds cannot be determined.

5. **Integrate centering with resize flow**
   - In `ResizeSelectedWindow`, after a successful call to `_windowResizer.ResizeWindow(...)`:
     - If `_centerOnResize` is `true`, call the new `WindowPositionHelper` method with the `targetWindow`.
     - Preserve current behavior: update `StatusText`, activate the window, wait briefly, then hide the floating menu.
   - Consider small sequencing tweaks if necessary (e.g., centering before vs. after activation) based on behavior.

6. **Test and refine**
   - Run `dotnet test ResizeMe.sln` to ensure no regressions.
   - Perform manual tests described in the testing approach (single monitor, multi-monitor if available, app restart).
   - Adjust timing or status messages if centering feels laggy or causes flicker.

## Testing Strategy

- **Automated:**
  - Rerun existing solution tests with `dotnet test ResizeMe.sln` to ensure the new helper and preference wiring do not break current behavior.
- **Manual:**
  - Verify behavior with the toggle off (baseline) vs. on (centered) for multiple presets and different target apps.
  - Check persistence by toggling, closing the app, and re-opening the quick menu.
  - If possible, validate on a multi-monitor setup to confirm centering occurs on the correct monitor.

## Success Criteria

- A **"Center after resize"** toggle appears in the floating quick-resize UI and looks consistent with the app's Fluent design.
- When enabled, the target window is centered on its current monitor after each successful preset resize.
- When disabled, window position is unchanged by quick-resize (current behavior).
- The toggle state is remembered across application sessions.
- All existing tests continue to pass with no regressions in quick-resize behavior.

## Known Constraints & Considerations

- **DPI awareness and bounds accuracy:** Centering relies on `GetWindowRect` and monitor work area; unusual DPI or scaling configurations could slightly offset centering.
- **Window types:** Some special windows (e.g., elevated processes) may not respond to `SetWindowPos`, in which case the helper should fail silently without impacting the resize result.
- **Timing:** Restoring, resizing, and then centering a window may introduce minor visual movement; sequencing and small delays may be tuned if necessary.
- **Scope:** This plan intentionally keeps the setting local to app-level preferences rather than per-preset flags to minimize complexity.

---
