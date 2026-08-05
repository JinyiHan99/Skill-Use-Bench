# Preset Buttons with Icons and Dimensions

**Branch:** `feature/preset-buttons-icons-dimensions`
**Description:** Update MainWindow quick resize buttons to match SettingsWindow style with icons and size dimensions

## Goal
Make the preset buttons in the quick resize window (MainWindow) visually consistent with the SettingsWindow preset list by adding icons and displaying dimensions (e.g., "1920 x 1080") alongside preset names. This improves visual hierarchy and provides users with immediate size information without needing to hover or click.

## Why This Approach
The SettingsWindow already has a well-designed button template with icons and dimensions that provides better UX. By reusing the same visual language and creating a reusable converter for dynamic icon assignment, we maintain consistency across the app while keeping the PresetSize model clean (no icon property needed). The width-based icon mapping logic found in planning docs provides contextually relevant icons that help users quickly identify preset sizes visually.

## Implementation Steps

### Step 1: Add Icon Converter and Update Button Template
**Files:** 
- `ResizeMe/Shared/Converters/WidthToIconGlyphConverter.cs` (new)
- `ResizeMe/App.xaml`
- `ResizeMe/MainWindow.xaml`

**What:** 
Create a value converter that maps preset widths to appropriate Segoe Fluent Icons glyphs (≤1024: `\xE7F8`, ≤1366: `\xE80A`, ≤1920: `\xE959`, >1920: `\xE9F9`). Register the converter in App.xaml resources. Update MainWindow's button DataTemplate to use a Grid layout with FontIcon (using the converter) and StackPanel containing the preset name (FontWeight SemiBold, FontSize 13) and dimensions (FontSize 11, reduced opacity). Apply the existing `PresetButtonBaseStyle` to ensure consistent spacing, sizing, and theming.

**Testing:** 
- Build and launch ResizeMe
- Open the quick resize window (Win+Shift+R or click tray icon)
- Verify each preset button shows:
  - Appropriate icon on the left based on width
  - Preset name in bold
  - Dimensions (e.g., "1920 x 1080") below the name in smaller text
- Verify buttons match SettingsWindow visual style
- Test with different preset sizes to confirm icon mapping works correctly
- Verify theme support (light/dark mode)

## Success Criteria
- MainWindow preset buttons display icons that dynamically change based on preset width
- Each button shows preset name and dimensions in a two-line layout
- Visual styling matches SettingsWindow preset list (spacing, fonts, colors)
- Existing button functionality (clicking to resize) remains unchanged
- Converter is reusable for future features

## Commit Message
`feat(ui): add icons and dimensions to quick resize preset buttons`
