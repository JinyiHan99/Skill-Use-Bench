# ResizeMe - Development Plan

## Project Overview
A Windows Store application that allows users to quickly resize windows to predefined dimensions using a global hotkey and floating context menu. Users can configure custom sizes via a settings window.

## Development Phases

### Phase 1: Core Infrastructure
These PRs establish the foundation for the app.

#### PR 1.1: Global Hotkey Registration
**Goal:** Implement system-wide hotkey listening (Ctrl+Alt+R)
- Add PInvoke declarations for Windows hotkey APIs
- Create `HotKeyManager` class to register/unregister global hotkeys
- Hook into WM_HOTKEY window messages
- Add error handling for hotkey conflicts
- **Test:** Verify hotkey triggers and logs event
- **Completed:** - [x]

#### PR 1.2: Window Enumeration
**Goal:** Get list of open windows on the system
- Add PInvoke declarations for EnumWindows, GetWindowText, etc.
- Create `WindowManager` class to enumerate windows
- Filter out system windows (invisible, empty titles, etc.)
- Return collection of window handles and titles
- **Test:** Debug window list, verify filtering works
- **Completed:** - [x]

#### PR 1.3: Window Resizing Logic
**Goal:** Implement actual window resize functionality
- Add PInvoke for SetWindowPos, GetWindowRect
- Create `Resizer` class with Resize(hwnd, width, height) method
- Handle edge cases (minimized windows, modal dialogs, etc.)
- **Test:** Manually test resizing a known application
- **Completed:** - [x]

---

### Phase 2: UI Layer - Main Window
Build the primary user interface.
**Completed:** - [ ]

#### PR 2.1: Main Window Layout
**Goal:** Create the floating context menu UI
- Design XAML for floating menu (Grid with preset size buttons)
- Make window always-on-top and borderless
- Position near cursor on hotkey trigger
- **Test:** Visually verify layout and positioning
- **Completed:** - [ ]

#### PR 2.2: Preset Size Buttons
**Goal:** Add interactive buttons for common resolutions
- Add buttons for: 1920x1080, 1366x768, 1280x720, 1024x768
- Bind buttons to resize logic
- Add visual feedback on click
- **Test:** Click button, verify window resizes (test app)
- **Completed:** - [ ]

#### PR 2.3: Context Menu Toggle
**Goal:** Show/hide menu on hotkey press
- Connect HotKeyManager to toggle menu visibility
- Implement focus/unfocus behavior (auto-hide when losing focus)
- **Test:** Hotkey opens menu, clicking away closes it
- **Completed:** - [ ]

---

### Phase 3: Settings Window
Allow users to customize sizes.
**Completed:** - [ ]

#### PR 3.1: Settings Window XAML
**Goal:** Create configuration UI
- Layout with list of current presets
- Add/remove buttons
- Input fields for width/height
- Save/Cancel buttons
- **Test:** Visual verification of layout
- **Completed:** - [ ]

#### PR 3.2: Settings Data Model
**Goal:** Create persistent storage for presets
- Create `PresetSize` class (Name, Width, Height)
- Implement `PresetManager` class
- Add LocalSettings storage (ApplicationData)
- Load/save preset list to JSON or LocalSettings
- **Test:** Add preset, restart app, verify it persists
- **Completed:** - [ ]

#### PR 3.3: Settings Window Logic
**Goal:** Connect UI to data model
- Bind list to PresetManager
- Implement Add/Remove functionality
- Validation (width/height > 0)
- **Test:** Add custom size, remove size, restart and verify
- **Completed:** - [ ]

#### PR 3.4: Main Menu Integration
**Goal:** Load presets into floating menu
- Load presets from PresetManager at startup
- Dynamically generate buttons from presets
- **Test:** Add preset in settings, see button appear in floating menu
- **Completed:** - [ ]

---

### Phase 4: Polish & UX
Refine the experience.
**Completed:** - [ ]

#### PR 4.1: Keyboard Navigation
**Goal:** Add keyboard controls to floating menu
- Arrow keys to navigate buttons
- Enter to activate
- Escape to close menu
- **Test:** Use arrow keys and keyboard only to resize
- **Completed:** - [ ]

#### PR 4.2: Visual Polish
**Goal:** Improve appearance
- Add icons to buttons
- Smooth animations for show/hide
- Proper color scheme and branding
- **Test:** Visual review
- **Completed:** - [ ]

#### PR 4.3: System Tray Integration
**Goal:** Add system tray icon
- Tray icon with right-click menu
- Quick access to settings
- Show/hide main window
- Exit app
- **Test:** Right-click tray icon, verify menu works
- **Completed:** - [ ]

---

### Phase 5: Store Preparation
Get ready for distribution.
**Completed:** - [ ]

#### PR 5.1: Package Manifest Configuration
**Goal:** Prepare app for Store
- Update Package.appxmanifest with app info
- Add required capabilities (for window interaction)
- Add app icons (required by Store)
- **Test:** Build MSIX package locally
- **Completed:** - [ ]

#### PR 5.2: Testing & Validation
**Goal:** Comprehensive testing before submission
- Test on clean system
- Verify no crashes
- Test with multiple languages/regions
- Documentation/help text
- **Test:** Full manual QA pass
- **Completed:** - [ ]

#### PR 5.3: Store Submission Assets
**Goal:** Create marketing materials
- App description
- Screenshots (3-5 required)
- Privacy policy
- **Test:** Review Store listing preview
- **Completed:** - [ ]

---

## Implementation Order
Follow Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 in order. Each PR can be reviewed and tested independently before moving to the next.

## Testing Strategy
- Unit tests for business logic (HotKeyManager, WindowManager, Resizer)
- Manual UI testing for each feature addition
- Integration testing before Store submission
- Test on multiple Windows versions if possible

## Known Constraints & Considerations
- Global hotkeys require elevated permissions (may need to request admin)
- Some windows may not respond to SetWindowPos (e.g., UWP apps have restrictions)
- Need to handle DPI scaling on modern displays
- Consider privacy implications of window enumeration

