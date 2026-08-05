# PR 1: Add center-on-resize option to quick menu

**Branch Name:** `feature-center-on-resize`

**Description:** Adds a toggle to the floating quick-resize UI that persists a boolean preference and centers the target external window on its current monitor after a successful preset resize.

**Technology Stack:** WinUI 3 (C# / .NET 8), Windows APIs via P/Invoke, local storage via `Windows.Storage.ApplicationData`.

**Dependencies:** None (standalone). Builds on existing `WindowResizer`, `WindowPositionHelper`, and `MainWindow` code.

**Part of Phase:** Phase: Center-on-Resize - implements the user-visible toggle and centering flow.

## Pre-Implementation Checklist

- [ ] **Branch Creation:** If not already on the main/default branch, run:
   ```bash
   cd ResizeMe
   git checkout main
   git pull
   git checkout -b feature-center-on-resize
   ```

- [ ] **Verify Project Setup:** Ensure the project builds successfully
 - [x] **Verify Project Setup:** Ensure the project builds successfully
   ```bash
   dotnet build ResizeMe.sln
   ```
   Expected output: Build succeeds with no errors. `Build succeeded.` appears in CLI output.

## Implementation Steps

### Step 1: Add `UserPreferences` helper

**Goal:** Persist a typed `bool` flag using `ApplicationData.Current.LocalSettings` with a safe default.

**File to Create:** `ResizeMe/Services/UserPreferences.cs`

**Checklist:**
- [ ] Create the file `ResizeMe/Services/UserPreferences.cs`
- [ ] Add the typed static property `CenterOnResize` which reads/writes to `LocalSettings` with a default of `false`.
- [ ] Ensure no exceptions escape; fail silently (logging only) and return default.
- [ ] Validate by reading and writing the setting from immediate code.
- [x] Create the file `ResizeMe/Services/UserPreferences.cs`
- [x] Add the typed static property `CenterOnResize` which reads/writes to `LocalSettings` with a default of `false`.
- [x] Ensure no exceptions escape; fail silently (logging only) and return default.
- [x] Validate by reading and writing the setting from immediate code.

- [ ] **Copy and paste the entire content below:**

```csharp
// ResizeMe/Services/UserPreferences.cs
using System;
using Windows.Storage;

namespace ResizeMe.Services
{
    /// <summary>
    /// Small typed wrapper around ApplicationData.Current.LocalSettings for simple flags.
    /// </summary>
    public static class UserPreferences
    {
        private const string CenterKey = "CenterOnResize";

        /// <summary>
        /// Gets or sets whether windows should be centered after a quick resize.
        /// </summary>
        public static bool CenterOnResize
        {
            get
            {
                try
                {
                    var settings = ApplicationData.Current.LocalSettings;
                    if (settings.Values.TryGetValue(CenterKey, out var val) && val is bool b)
                    {
                        return b;
                    }
                }
                catch
                {
                    // Swallow - preferences should never crash the app.
                }
                return false;
            }
            set
            {
                try
                {
                    var settings = ApplicationData.Current.LocalSettings;
                    settings.Values[CenterKey] = value;
                }
                catch
                {
                    // Swallow - ignore preferences save failures
                }
            }
        }
    }
}
```

**Verification:**
- [ ] Build succeeds: `dotnet build ResizeMe.sln`.
- [ ] Confirm file created with no compilation errors.
- [ ] Optionally verify by calling `UserPreferences.CenterOnResize = true; Console.WriteLine(UserPreferences.CenterOnResize);` in debug code.

---

### Step 2: Add external window centering helper to `WindowPositionHelper`

**Goal:** Implement a method `CenterExternalWindowOnMonitor(WindowInfo windowInfo)` that centers an external (non-WinUI) window on its current monitor work area.

**File to Edit:** `ResizeMe/Helpers/WindowPositionHelper.cs`

**Checklist:**
- [ ] Add `using ResizeMe.Native;` at top (for `WindowsApi` methods and structs)
- [ ] Add a public helper method `CenterExternalWindowOnMonitor(WindowInfo windowInfo)` to compute monitor and center coordinates, using `WindowsApi.GetWindowRect` to get current bounds and `MonitorFromPoint/GetMonitorInfo` to determine the monitor work area.
- [ ] Use `SetWindowPos` with `SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE` to reposition the window but not change size.
- [ ] No exceptions should escape; log debug messages where appropriate.
- [x] Add `using ResizeMe.Native;` at top (for `WindowsApi` methods and structs)
- [x] Add a public helper method `CenterExternalWindowOnMonitor(WindowInfo windowInfo)` to compute monitor and center coordinates, using `WindowsApi.GetWindowRect` to get current bounds and `MonitorFromPoint/GetMonitorInfo` to determine the monitor work area.
- [x] Use `SetWindowPos` with `SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE` to reposition the window but not change size.
- [x] No exceptions should escape; log debug messages where appropriate.

- [ ] **Copy and paste the entire content below (insert into the `WindowPositionHelper` class):**

```csharp
// Add to ResizeMe/Helpers/WindowPositionHelper.cs inside the WindowPositionHelper class
using ResizeMe.Native; // add near other using statements

/// <summary>
/// Centers an external window (not the WinUI menu itself) on the monitor containing the window.
/// Safe no-op if the handle is invalid or monitor info can't be determined.
/// </summary>
/// <param name="windowInfo">WindowInfo representing the external window</param>
public static void CenterExternalWindowOnMonitor(WindowInfo windowInfo)
{
    if (windowInfo == null || windowInfo.Handle == IntPtr.Zero) return;

    try
    {
        // Get the current bounds (more accurate than cached WindowInfo at times)
        if (!WindowsApi.GetWindowRect(windowInfo.Handle, out var rect))
        {
            Debug.WriteLine("WindowPositionHelper: Failed to GetWindowRect for target window.");
            return;
        }

        var windowWidth = rect.Width;
        var windowHeight = rect.Height;

        // Compute center point of the window to find the correct monitor
        var center = new POINT { X = rect.Left + (windowWidth / 2), Y = rect.Top + (windowHeight / 2) };

        IntPtr monitor = MonitorFromPoint(center, MONITOR_DEFAULTTONEAREST);
        var monitorInfo = MONITORINFO.Default;
        if (!GetMonitorInfo(monitor, ref monitorInfo))
        {
            Debug.WriteLine("WindowPositionHelper: Failed to get monitor info for external window.");
            return;
        }

        var workArea = monitorInfo.rcWork;

        int targetX = workArea.Left + (workArea.Width - windowWidth) / 2;
        int targetY = workArea.Top + (workArea.Height - windowHeight) / 2;

        bool success = SetWindowPos(windowInfo.Handle, IntPtr.Zero, targetX, targetY, 0, 0,
            SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);

        if (!success)
        {
            Debug.WriteLine($"WindowPositionHelper: Failed to center external window, error {Marshal.GetLastWin32Error()}");
        }
        else
        {
            Debug.WriteLine($"WindowPositionHelper: Centered external window at {targetX},{targetY}");
        }
    }
    catch (Exception ex)
    {
        Debug.WriteLine($"WindowPositionHelper: Exception centering external window: {ex.Message}");
    }
}
```

**Verification:**
- [ ] Build the project: `dotnet build ResizeMe.sln` and confirm no failures.
- [ ] Manual verification: call `WindowPositionHelper.CenterExternalWindowOnMonitor(someWindowInfo)` from debugger or temporary code and confirm the window moves.

---

### Step 3: Add toggle UI and wire preference in `MainWindow`

**Goal:** Add a `ToggleSwitch` to the quick-resize floating UI and wire it to `UserPreferences.CenterOnResize`. When toggled on, center the external window after a successful resize.

**Files to Edit:**
- `ResizeMe/MainWindow.xaml` — add a `ToggleSwitch` in the content area.
- `ResizeMe/MainWindow.xaml.cs` — add `_centerOnResize` field, load saved preference in constructor, set toggle initial state, handle `Toggled` event, and call `WindowPositionHelper.CenterExternalWindowOnMonitor` after a successful resize.

**Checklist:**
- [ ] Insert a `ToggleSwitch` under `DynamicPresetsPanel` (or under `PresetHint`), set `x:Name="CenterOnResizeToggle"` and hook `Toggled="CenterOnResizeToggle_Toggled"`.
- [ ] Add a private field `private bool _centerOnResize;` to `MainWindow`.
- [ ] In the constructor, after loading presets, read `UserPreferences.CenterOnResize` into `_centerOnResize` and set `CenterOnResizeToggle.IsOn` accordingly if not null.
- [ ] Add the `CenterOnResizeToggle_Toggled` event handler to persist the new preference and update UI `StatusText` to a short message.
- [ ] Modify `ResizeSelectedWindow` to call `WindowPositionHelper.CenterExternalWindowOnMonitor(targetWindow)` when `_centerOnResize` is `true` and the resize succeeded (before `ActivateWindow`).
- [x] Insert a `ToggleSwitch` into the footer `Border` (moved out of ScrollViewer) with `x:Name="CenterOnResizeToggle"` and `Toggled="CenterOnResizeToggle_Toggled"`.
- [x] Add a private field `private bool _centerOnResize;` to `MainWindow`.
- [x] In the constructor, after loading presets, read `UserPreferences.CenterOnResize` into `_centerOnResize` and set `CenterOnResizeToggle.IsOn` accordingly if not null.
- [x] Add the `CenterOnResizeToggle_Toggled` event handler to persist the new preference and update UI `StatusText` to a short message.
- [x] Modify `ResizeSelectedWindow` to call `WindowPositionHelper.CenterExternalWindowOnMonitor(targetWindow)` when `_centerOnResize` is `true` and the resize succeeded (before `ActivateWindow`).

- [ ] **Copy and paste the exact modifications below:**

MainWindow.xaml (add this toggle to the footer `Border` so it is outside the scroll container):

```xml
<!-- Quick Resize toggle: Center after resize -->
<ToggleSwitch x:Name="CenterOnResizeToggle"
              Header="Center after resize"
              Toggled="CenterOnResizeToggle_Toggled"
              Margin="0,4,0,0" />
```

MainWindow.xaml.cs (additions and edits):

```csharp
// 1) Add new private field near other fields
private bool _centerOnResize;

// 2) Load saved preference in constructor after InitializeComponent
public MainWindow()
{
    InitializeComponent();
    _windowManager = new WindowManager();
    _windowResizer = new WindowResizer();
    AttachWindowLoadedHandler();
    Loaded += async (_, _) => { await _presetManager.LoadAsync(); LoadPresetButtons(); };

    // Load persisted "center on resize" preference
    try
    {
        _centerOnResize = ResizeMe.Services.UserPreferences.CenterOnResize;
        if (CenterOnResizeToggle != null)
        {
            CenterOnResizeToggle.IsOn = _centerOnResize;
        }
    }
    catch (Exception ex)
    {
        Debug.WriteLine($"MainWindow: Error reading CenterOnResize preference: {ex.Message}");
    }

    SetupWindowAppearance();
    AttachKeyDownHandler();
    Activated += OnWindowActivated;
    Closed += Window_Closed;
}

// 3) Event handler for toggle
private void CenterOnResizeToggle_Toggled(object sender, RoutedEventArgs e)
{
    try
    {
        if (CenterOnResizeToggle != null)
        {
            _centerOnResize = CenterOnResizeToggle.IsOn;
            ResizeMe.Services.UserPreferences.CenterOnResize = _centerOnResize;
            StatusText.Text = _centerOnResize ? "Center on resize: On" : "Center on resize: Off";
        }
    }
    catch (Exception ex)
    {
        Debug.WriteLine($"MainWindow: Error writing CenterOnResize preference: {ex.Message}");
    }
}

// 4) Call centering after successful resize in ResizeSelectedWindow
if (result.Success)
{
    StatusText.Text = $"✅ {sizeTag}";

    // If user enabled center-on-resize, center the external window on its monitor
    if (_centerOnResize)
    {
        try
        {
            WindowPositionHelper.CenterExternalWindowOnMonitor(targetWindow);
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"MainWindow: Error centering window after resize: {ex.Message}");
        }
    }

    _windowResizer.ActivateWindow(targetWindow);
    SetActivePreset(sizeTag);
    await Task.Delay(600);
    HideWindow();
}
```

**Verification:**
 - [x] Build the app: `dotnet build ResizeMe.sln` — no errors.
- [ ] Run the app, open quick menu, verify new "Center after resize" toggle present and initial state matches preference.
- [ ] Toggle ON, perform a resize on an external window — verify it is centered after resizing (single monitor and multi-monitor).
- [ ] Toggle OFF — verify resizing does not change the position.
- [ ] Restart the app to verify preference is persisted.

---

## Build and Final Verification

**Checklist:**
- [ ] **Build/Test the project:**
   ```bash
   dotnet build ResizeMe.sln
   dotnet test ResizeMe.sln # runs test projects (no tests currently)
   ```
   Expected: `Build succeeded.`; `dotnet test` may show 0 tests if none exist.

- [ ] **Check for errors:** There should be none. If you see errors:
   - [ ] Verify `UserPreferences.cs` is in `ResizeMe/Services` and namespace matches `ResizeMe.Services`.
   - [ ] Confirm `using ResizeMe.Native;` added to `WindowPositionHelper.cs`.
   - [ ] Check `MainWindow.xaml` toggle is added inside the `StackPanel` under the `Content Card` block.

- [ ] **Optional: Manual Testing**
   - [ ] Start application. Use quick-resize to resize an open window and verify centering.
   - [ ] Test multi-monitor: move target window to another monitor and run resize; it should center on the same monitor.

## Expected Behavior After Completion

- [ ] Quick menu displays "Center after resize" toggle and default is OFF.
- [ ] Toggling ON: a subsequent quick-resize centers the target window within the work area of its current monitor.
- [ ] Toggling OFF: quick-resize only changes size; position is unchanged.
- [ ] The preference persists between app restarts.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Toggle doesn't appear | Verify `MainWindow.xaml` was modified in the right location in the `StackPanel` (under `DynamicPresetsPanel`/`PresetHint`) and that project built. |
| `UserPreferences` not saving | Ensure `ResizeMe/Services/UserPreferences.cs` uses `Windows.Storage.ApplicationData.Current.LocalSettings`. If inaccessible, check permissions and OS version for LocalSettings. |
| External window doesn't move after centering | Some windows may refuse to move due to privilege or process protection. This is expected — the helper should fail silently. Confirm `WindowResizer` can resize first and that the target is not an elevated process. |
| Multi-monitor centering wrong monitor | Implementation uses the external window's center point to search for the monitor using `MonitorFromPoint` which is robust; if it picks wrong monitor, check DPI scaling and monitor coordinates. |

## Files Created/Modified

- [ ] ✅ {Created}: `ResizeMe/Services/UserPreferences.cs`
- [ ] ✅ {Modified}: `ResizeMe/Helpers/WindowPositionHelper.cs` (added `CenterExternalWindowOnMonitor`)
- [ ] ✅ {Modified}: `ResizeMe/MainWindow.xaml` (added `ToggleSwitch` UI)
- [ ] ✅ {Modified}: `ResizeMe/MainWindow.xaml.cs` (load/save toggle state, toggle event handler, centering call)

## Commit Message Template

```
feat(center-on-resize): add an option to center resized windows on their monitor

Add a quick menu ToggleSwitch for "Center after resize" and persist the preference
using ApplicationData.LocalSettings via a small `UserPreferences` helper.

- Add `UserPreferences` helper
- Add `CenterExternalWindowOnMonitor` to `WindowPositionHelper`
- Add toggle UI and wiring to `MainWindow`

Fixes: none
```

## Implementation Notes for Reviewers

- The preference is intentionally app-global and not per-preset to keep scope minimal.
- The centering helper uses the window center to determine the monitor; this is robust across multi-monitor setups with the usual Windows API calls.
- We use `ApplicationData.Current.LocalSettings` for lightweight persistence — it’s fast and compatible across Windows App SDK. No new packages.

## What Comes Next

Once this PR is merged:
- PR 2 (optional): add unit tests for `UserPreferences` and `WindowPositionHelper` behavior (non-P/Invoke parts).
- PR 3 (optional): expose the pref in `SettingsWindow` for cross-platform parity (persist the same setting in UI Settings dialog).
- Consider future: add a `CenterOnResize` per-preset option (if requested) and unit tests for Positioning code (mocked).