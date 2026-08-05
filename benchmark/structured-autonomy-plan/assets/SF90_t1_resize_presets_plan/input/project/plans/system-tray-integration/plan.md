# PR 1.0: System Tray Integration & First-Run Experience

**Branch:** `system-tray-integration`
**Description:** Implement minimize-to-tray behavior, settings access from tray, first-run notification on initial minimize, and keyboard shortcut customization with reserved hotkey validation.

## Goal
Transform ResizeMe into a true system tray application where users can minimize to tray instead of closing, access settings from the tray icon, see a one-time first-run notification explaining the tray and hotkey, and customize their keyboard shortcut with safeguards against Windows reserved hotkeys.

## Why This Approach
The tray icon and hotkey infrastructure already exists but isn't fully integrated. This approach:
- Reuses existing TrayIconManager events and minimal new logic to hook window close behavior
- Adds first-run state tracking to UserPreferences (simple boolean flag)
- Uses simple message boxes for notifications (no extra dependencies, App Store compatible)
- Leverages WinRT validator APIs to check for reserved hotkeys before registration
- Breaks into 4 steps allowing independent testing of each layer

## Implementation Steps

### Step 1: Tray Context Menu & Minimize-to-Tray Behavior
**Files:**
- `ResizeMe/MainWindow.xaml.cs` (modify close handler)
- `ResizeMe/Services/TrayIconManager.cs` (add context menu wiring)
- `ResizeMe/Native/WindowsApi.cs` (may need P/Invoke for context menu)

**What:**
Hook the window close button to hide the window instead of exiting the app. Create and wire a context menu on the tray icon with "Show", "Settings", and "Exit" options. When user clicks "Exit" from the context menu, then the app closes completely. Minimize-to-tray happens on window close button click or when manually minimizing.

**Testing:**
- [ ] Click window close button → app hides to tray, tray icon remains visible
- [ ] Right-click tray icon → context menu appears with "Show", "Settings", "Exit" options
- [ ] Click "Show" in context menu → MainWindow reappears in foreground
- [ ] Click "Exit" in context menu → app closes completely
- [ ] Window is centered on screen when restored from tray

### Step 2: Settings Window on Tray Click & First-Run Detection
**Files:**
- `ResizeMe/Services/UserPreferences.cs` (add FirstRunCompleted property)
- `ResizeMe/Services/TrayIconManager.cs` (ensure SettingsRequested event fires on interaction)
- `ResizeMe/MainWindow.xaml.cs` (subscribe to tray events, show settings on first run)
- `ResizeMe/App.xaml.cs` (optional: handle app-level first-run logic)

**What:**
Add a `FirstRunCompleted` boolean preference (default false). On app startup after MainWindow loads, if FirstRunCompleted is false, immediately show SettingsWindow as a modal dialog. Wire the TrayIconManager.SettingsRequested event (triggered by double-click or "Settings" menu item) to show SettingsWindow. Once SettingsWindow is closed, set FirstRunCompleted to true and save preferences.

**Testing:**
- [ ] First app run → SettingsWindow appears automatically after main window loads
- [ ] SettingsWindow is modal and focused on user
- [ ] Close SettingsWindow → MainWindow appears, FirstRunCompleted saved as true
- [ ] Restart app → SettingsWindow does NOT auto-appear (FirstRunCompleted is true)
- [ ] Double-click tray icon → SettingsWindow appears again
- [ ] Right-click tray icon, select "Settings" → SettingsWindow appears

### Step 3: First-Run Toast Notification on First Minimize
**Files:**
- `ResizeMe/MainWindow.xaml.cs` (add minimize event handler)
- `ResizeMe/Services/UserPreferences.cs` (add FirstMinimizeNotificationShown property)

**What:**
Add a new UserPreferences property `FirstMinimizeNotificationShown` (default false). When MainWindow is hidden/minimized to tray for the first time (and FirstMinimizeNotificationShown is false), show a simple message box with the message: "ResizeMe is running in the system tray. Right-click the tray icon to access settings or exit. Press [HOTKEY] to open the quick resize window." where [HOTKEY] is replaced with the current hotkey string (e.g., "Win+Shift+F12"). After user dismisses the message, set FirstMinimizeNotificationShown to true and save.

**Testing:**
- [ ] First run, close MainWindow → message box appears with tray explanation and hotkey
- [ ] Message is dismissible with OK button
- [ ] After dismissing, FirstMinimizeNotificationShown is true
- [ ] Restart app, minimize again → message does NOT appear (notification only shown once ever)
- [ ] Hotkey displayed in message matches actual registered hotkey

### Step 4: Keyboard Shortcut Display & Customization with Reserved Hotkey Validation
**Files:**
- `ResizeMe/SettingsWindow.xaml` (add hotkey display and customize button UI)
- `ResizeMe/SettingsWindow.xaml.cs` (add hotkey customization logic)
- `ResizeMe/Services/UserPreferences.cs` (add HotKeyModifiers and HotKeyCode properties)
- `ResizeMe/Services/HotKeyManager.cs` (make hotkey registration parameters configurable)
- `ResizeMe/Native/WindowsApi.cs` (add helper to validate hotkeys against reserved list)

**What:**
Add a section in SettingsWindow showing the current hotkey (e.g., "Win+Shift+F12"). Add a "Customize Hotkey" button. When clicked, open a dialog that waits for the user to press a key combination and validates it against Windows reserved hotkeys (e.g., Alt+Tab, Win+D, Ctrl+Alt+Delete, etc.). If the hotkey is reserved or already registered, show an error message. If valid, register the new hotkey, update the display, and save to preferences. Handle re-registration on app startup.

**Testing:**
- [ ] SettingsWindow displays current hotkey: "Win+Shift+F12"
- [ ] Click "Customize Hotkey" button → dialog appears waiting for keypress
- [ ] Press a new key combination (e.g., Alt+F12) → hotkey updated and displayed
- [ ] Close and reopen SettingsWindow → new hotkey still displayed
- [ ] Press the new hotkey → MainWindow appears/toggles visibility
- [ ] Try to register reserved hotkey (e.g., Alt+Tab) → error message: "This hotkey is reserved by Windows"
- [ ] Restart app → new hotkey still works without re-registration needed

## Success Criteria
- [ ] App minimizes to tray on window close button click, never exits the app unless "Exit" is selected from tray context menu
- [ ] Tray context menu has "Show", "Settings", and "Exit" options; right-click opens menu
- [ ] Settings window shows on first run automatically; user must close it to proceed
- [ ] First-run notification appears once when user first minimizes to tray, explains tray icon and hotkey
- [ ] Settings window displays current keyboard shortcut
- [ ] User can customize hotkey from Settings window with keypress capture
- [ ] Reserved Windows hotkeys (Alt+Tab, Win+D, etc.) are blocked from registration with clear error message
- [ ] All hotkey and preference changes persist across app restarts
- [ ] App Store compatible (no additional dependencies beyond existing WinUI 3)

## Commit Message
`feat(tray): implement minimize-to-tray, first-run experience, and hotkey customization with reserved key validation`

---

## Implementation Notes for Reviewers

**Architecture Decisions:**
1. **First-run detection:** Uses simple boolean flags in UserPreferences rather than timestamp checks. Keeps state machine simple.
2. **Notifications:** Uses MessageBox instead of WinRT Toast to avoid DispatcherQueue complexity and ensure App Store compatibility. Simple but effective.
3. **Reserved hotkey validation:** Uses a whitelist of common Windows reserved hotkeys rather than trying to query the system. This is reliable and doesn't require additional P/Invoke.
4. **Hotkey re-registration:** On startup, the app unregisters the old hotkey and registers the potentially new one from preferences. Allows seamless hotkey changes.

**Testing Sequence:**
- Step 1 before Step 2: Tray menu must exist before we can show settings from it
- Step 2 before Step 3: First-run window must complete before first-minimize notification
- Step 3 before Step 4: First-minimize notification should show before hotkey customization UI
- Step 4 can be tested in parallel with Step 1-2 but needs Step 3 to show accurate hotkey in notification

**Potential Gotchas:**
- Window close event fires on both close button and programmatic close; need to distinguish "user close" from "app-initiated close"
- Message boxes are blocking; ensure they don't freeze the app during tray interaction
- Reserved hotkey list must be maintained if new Windows versions add new reserved hotkeys

## What Comes Next

Once this PR is merged:
- Consider "restore to last position" feature to restore window position when brought back from tray
- Consider system-wide hotkey indicator in system tray icon tooltip
- Consider customizable startup behavior (auto-start with Windows, launch minimized, etc.)
