# PR 1.0: Refactor MainWindow to MVVM and Decouple Services

**Branch:** `refactor/mainwindow-mvvm`
**Description:** Refactor `MainWindow.xaml.cs` by extracting native window logic, tray management, and business logic into a ViewModel and dedicated services.

## Goal
Decouple the monolithic `MainWindow.xaml.cs` to improve testability and maintainability. This involves moving native interop to a service, extracting tray icon logic, and implementing the MVVM pattern for the main UI.

## Why This Approach
`MainWindow` currently violates the Single Responsibility Principle. By extracting `INativeWindowService` and `TrayIconManager`, and introducing `MainViewModel`, we separate concerns and make the code "LLM-friendly" (linear, explicit, testable).

## Implementation Steps

### Step 1: Extract Native Window Service & Subclassing
**Folder:** `1-extract-native-service/`
**Files:** `Native/INativeWindowService.cs`, `Native/NativeWindowService.cs`, `Native/WindowSubclassService.cs`, `ResizeMe/MainWindow.xaml.cs`
**What:** Create an abstraction for Win32 APIs and window subclassing. Move `WindowMessageBridge` logic to `WindowSubclassService`.
**Testing:** Verify app still launches and handles messages (hotkeys/tray) correctly.

### Step 2: Extract Tray Management
**Folder:** `2-extract-tray-manager/`
**Files:** `Features/SystemIntegration/TrayIconManager.cs`, `ResizeMe/MainWindow.xaml.cs`
**What:** Move tray icon initialization and event handling from `MainWindow` to a new `TrayIconManager` that subscribes to `WindowSubclassService`.
**Testing:** Verify tray icon appears, context menu works, and clicking opens the app.

### Step 3: Implement MainViewModel
**Folder:** `3-implement-main-vm/`
**Files:** `ViewModels/MainViewModel.cs`, `ResizeMe/MainWindow.xaml`, `ResizeMe/MainWindow.xaml.cs`
**What:** Create `MainViewModel` to hold state (`Presets`, `WindowList`) and logic (`ResizeWindow`). Bind `MainWindow` to this VM.
**Testing:** Verify all UI interactions (resizing, preset loading) work as before.

## Success Criteria
- `MainWindow.xaml.cs` should be significantly smaller (< 200 lines ideally).
- No direct `WindowsApi` calls in `MainWindow`.
- Tray logic is isolated in `TrayIconManager`.
- Application behavior remains unchanged.

## Commit Message
`refactor(core): decouple MainWindow to MVVM and extract services`
