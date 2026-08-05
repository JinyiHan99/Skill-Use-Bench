# Preset Buttons with Icons and Dimensions

## Goal
Add dynamic icons and dimension text to the quick resize preset buttons in `MainWindow` using a reusable value converter so the layout matches the preset cards in `SettingsWindow`.

## Platform & Commands
- **Tech stack:** WinUI 3 (.NET 8.0, Microsoft.WindowsAppSDK 1.8)
- **Build:** `dotnet build ResizeMe.sln -c Debug`
- **Run:** `dotnet run --project ResizeMe/ResizeMe.csproj -c Debug`

### Step-by-Step Instructions

> Important: This implementation plan follows a strict per-step commit workflow. After implementing each step below, the agent MUST stop. The user must run the tests / smoke checks, stage and commit the changes, and explicitly confirm the commit before the agent moves on to the next step.

-#### Step 1: Create the width-to-icon converter
- [x] Create `ResizeMe/Shared/Converters/WidthToIconGlyphConverter.cs`.
- [ ] Copy and paste the code below into the new file:

```csharp
using System;
using Microsoft.UI.Xaml.Data;
using ResizeMe.Models;

namespace ResizeMe.Shared.Converters
{
    public sealed class WidthToIconGlyphConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, string language)
        {
            var width = ExtractWidth(value);

            return width switch
            {
                <= 1024 => "\uE7F8",
                <= 1366 => "\uE80A",
                <= 1920 => "\uE959",
                _ => "\uE9F9",
            };
        }

        public object ConvertBack(object value, Type targetType, object parameter, string language)
        {
            throw new NotSupportedException("WidthToIconGlyphConverter only supports one-way conversion.");
        }

        private static int ExtractWidth(object value)
        {
            if (value is null)
            {
                return 0;
            }

            if (value is PresetSize preset)
            {
                return preset.Width;
            }

            if (value is int integer)
            {
                return integer;
            }

            if (value is double number)
            {
                return (int)Math.Round(number, MidpointRounding.AwayFromZero);
            }

            if (value is string text && int.TryParse(text, out var parsed))
            {
                return parsed;
            }

            return 0;
        }
    }
}
```

-##### Step 1 Verification Checklist
- [x] Build the solution: `dotnet build ResizeMe.sln -c Debug`
- [ ] **STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

#### Step 2: Register the converter in application resources
- [x] Replace the contents of `ResizeMe/App.xaml` with the code below (keeps existing styles and registers the converter):

```xml
<?xml version="1.0" encoding="utf-8"?>
<Application
    x:Class="ResizeMe.App"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:local="using:ResizeMe"
    xmlns:converters="using:ResizeMe.Shared.Converters">

    <Application.Resources>
        <ResourceDictionary>
            <ResourceDictionary.MergedDictionaries>
                <XamlControlsResources xmlns="using:Microsoft.UI.Xaml.Controls" />
            </ResourceDictionary.MergedDictionaries>

            <converters:WidthToIconGlyphConverter x:Key="WidthToIconGlyphConverter" />

            <!-- Spacing tokens -->
            <x:Double x:Key="SpacingXS">4</x:Double>
            <x:Double x:Key="SpacingSM">8</x:Double>
            <x:Double x:Key="SpacingMD">12</x:Double>
            <x:Double x:Key="SpacingLG">16</x:Double>

            <!-- Base style for preset buttons (reduced for minimal floating UI) -->
            <Style x:Key="PresetButtonBaseStyle" TargetType="Button"
                BasedOn="{StaticResource DefaultButtonStyle}">
                <Setter Property="MinHeight" Value="48" />
                <Setter Property="HorizontalAlignment" Value="Stretch" />
                <Setter Property="HorizontalContentAlignment" Value="Left" />
                <Setter Property="VerticalContentAlignment" Value="Center" />
                <Setter Property="Padding" Value="10,8" />
                <Setter Property="CornerRadius" Value="8" />
                <Setter Property="Background" Value="{ThemeResource ControlFillColorSecondaryBrush}" />
                <Setter Property="BorderBrush"
                    Value="{ThemeResource ControlStrokeColorSecondaryBrush}" />
                <Setter Property="BorderThickness" Value="1" />
                <Setter Property="ToolTipService.ToolTip" Value="Resize to preset dimensions" />
                <Setter Property="Margin" Value="0,0,0,6" />
            </Style>

            <!-- Active (selected) preset style -->
            <Style x:Key="ActivePresetButtonStyle" TargetType="Button"
                BasedOn="{StaticResource PresetButtonBaseStyle}">
                <Setter Property="Background" Value="{ThemeResource AccentFillColorDefaultBrush}" />
                <Setter Property="Foreground"
                    Value="{ThemeResource TextOnAccentFillColorPrimaryBrush}" />
                <Setter Property="BorderBrush" Value="{ThemeResource AccentStrokeColorDefaultBrush}" />
            </Style>

            <!-- Preset header text -->
            <Style x:Key="PresetHeaderTextStyle" TargetType="TextBlock"
                BasedOn="{StaticResource BodyStrongTextBlockStyle}">
                <Setter Property="FontSize" Value="13" />
                <Setter Property="TextWrapping" Value="Wrap" />
            </Style>

            <!-- Preset sub text -->
            <Style x:Key="PresetSubTextStyle" TargetType="TextBlock"
                BasedOn="{StaticResource CaptionTextBlockStyle}">
                <Setter Property="Opacity" Value="0.78" />
                <Setter Property="FontSize" Value="12" />
            </Style>

            <!-- Primary action button (Settings, Add, etc.) -->
            <Style x:Key="PrimaryActionButtonStyle" TargetType="Button"
                BasedOn="{StaticResource DefaultButtonStyle}">
                <Setter Property="Padding" Value="14,8" />
                <Setter Property="CornerRadius" Value="6" />
                <Setter Property="Background" Value="{ThemeResource AccentFillColorDefaultBrush}" />
                <Setter Property="Foreground"
                    Value="{ThemeResource TextOnAccentFillColorPrimaryBrush}" />
                <Setter Property="BorderBrush"
                    Value="{ThemeResource ControlStrokeColorDefaultBrush}" />
                <Setter Property="BorderThickness" Value="1" />
            </Style>

            <!-- Subtle toolbar button -->
            <!-- Toolbar button reduced for minimal header (no icon by default) -->
            <Style x:Key="ToolbarIconButtonStyle" TargetType="Button"
                BasedOn="{StaticResource SubtleButtonStyle}">
                <Setter Property="MinWidth" Value="48" />
                <Setter Property="Height" Value="28" />
                <Setter Property="Padding" Value="6,2" />
                <Setter Property="CornerRadius" Value="4" />
                <Setter Property="FontSize" Value="12" />
            </Style>
        </ResourceDictionary>
    </Application.Resources>
</Application>
```

##### Step 2 Verification Checklist
- [x] Build the solution: `dotnet build ResizeMe.sln -c Debug`

#### Step 2 STOP
- [ ] **STOP** Return control to the user and tell them what you have changed and how to validate it.

#### Step 3: Update quick resize preset button layout
- [x] Replace the contents of `ResizeMe/MainWindow.xaml` with the code below:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Window
    x:Class="ResizeMe.MainWindow"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:local="using:ResizeMe"
    xmlns:models="using:ResizeMe.Models"
    xmlns:vm="using:ResizeMe.ViewModels"
    Title="ResizeMe">

    <Window.SystemBackdrop>
        <MicaBackdrop Kind="BaseAlt" />
    </Window.SystemBackdrop>

    <Grid x:Name="RootGrid" Background="{ThemeResource LayerFillColorDefaultBrush}"
        Padding="8" MaxWidth="340" MinWidth="280">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto" />
            <RowDefinition Height="*" />
            <RowDefinition Height="Auto" />
        </Grid.RowDefinitions>

        <!-- Header Card -->
        <Border Grid.Row="0"
            Background="{ThemeResource CardBackgroundFillColorDefaultBrush}"
            CornerRadius="8"
            BorderThickness="1"
            BorderBrush="{ThemeResource CardStrokeColorDefaultBrush}"
            Margin="0,0,0,12"
            Padding="16,12">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="Auto" />
                    <ColumnDefinition Width="*" />
                    <ColumnDefinition Width="Auto" />
                </Grid.ColumnDefinitions>

                <!-- Removed header icon for minimal UI -->

                <StackPanel Grid.Column="1"
                    Margin="12,0,12,0"
                    VerticalAlignment="Center">
                    <TextBlock Text="ResizeMe"
                        FontWeight="SemiBold"
                        FontSize="16"
                        Foreground="{ThemeResource TextFillColorPrimaryBrush}" />
                    <TextBlock x:Name="StatusText"
                        Text="Ready"
                        FontSize="12"
                        Foreground="{ThemeResource TextFillColorSecondaryBrush}" />
                </StackPanel>

                <Button x:Name="SettingsButton"
                    Grid.Column="2"
                    Style="{StaticResource ToolbarIconButtonStyle}"
                    ToolTipService.ToolTip="Settings"
                    Click="SettingsButton_Click"
                    VerticalAlignment="Center"
                    Content="Settings" />
            </Grid>
        </Border>

        <!-- Content Card -->
        <Border Grid.Row="1"
            Background="{ThemeResource CardBackgroundFillColorDefaultBrush}"
            CornerRadius="8"
            BorderThickness="1"
            BorderBrush="{ThemeResource CardStrokeColorDefaultBrush}"
            Padding="16">
            <ScrollViewer VerticalScrollBarVisibility="Auto"
                HorizontalScrollBarVisibility="Disabled">
                <StackPanel Spacing="16">
                    <TextBlock Text="Quick Resize"
                        FontWeight="SemiBold"
                        FontSize="18"
                        Foreground="{ThemeResource TextFillColorPrimaryBrush}" />

                    <ItemsControl ItemsSource="{x:Bind ViewModel.Presets, Mode=OneWay}">
                        <ItemsControl.ItemTemplate>
                            <DataTemplate x:DataType="models:PresetSize">
                                <Button Style="{StaticResource PresetButtonBaseStyle}"
                                        Command="{Binding ElementName=RootGrid, Path=DataContext.ResizeCommand}"
                                        CommandParameter="{x:Bind}">
                                    <Grid ColumnSpacing="12">
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="Auto" />
                                            <ColumnDefinition Width="*" />
                                        </Grid.ColumnDefinitions>
                                        <FontIcon Grid.Column="0"
                                            FontFamily="Segoe Fluent Icons"
                                            Glyph="{Binding Width, Converter={StaticResource WidthToIconGlyphConverter}}"
                                            FontSize="16"
                                            Foreground="{ThemeResource AccentTextFillColorSecondaryBrush}"
                                            VerticalAlignment="Center"
                                            Margin="0,0,12,0" />
                                        <StackPanel Grid.Column="1"
                                            VerticalAlignment="Center"
                                            Spacing="2">
                                            <TextBlock Text="{x:Bind Name}"
                                                Style="{StaticResource PresetHeaderTextStyle}"
                                                Foreground="{ThemeResource TextFillColorPrimaryBrush}" />
                                            <TextBlock Foreground="{ThemeResource TextFillColorSecondaryBrush}"
                                                FontSize="11">
                                                <Run Text="{x:Bind Width}" />
                                                <Run Text=" x " />
                                                <Run Text="{x:Bind Height}" />
                                            </TextBlock>
                                        </StackPanel>
                                    </Grid>
                                </Button>
                            </DataTemplate>
                        </ItemsControl.ItemTemplate>
                    </ItemsControl>

                    <TextBlock x:Name="PresetHint"
                        Text="Customize presets in Settings"
                        FontSize="12"
                        Foreground="{ThemeResource TextFillColorSecondaryBrush}"
                        HorizontalAlignment="Center"
                        Margin="0,8,0,0" />

                    <!-- Quick Resize toggle removed from ScrollViewer and moved to footer -->
                </StackPanel>
            </ScrollViewer>
        </Border>

        <!-- Footer -->
        <Border Grid.Row="2"
            Background="{ThemeResource CardBackgroundFillColorSecondaryBrush}"
            CornerRadius="8"
            BorderThickness="1"
            BorderBrush="{ThemeResource CardStrokeColorDefaultBrush}"
            Padding="16,12"
            Margin="0,12,0,0">
            <StackPanel Orientation="Vertical">
                <ToggleSwitch x:Name="CenterOnResizeToggle"
                              Header="Center after resize"
                              IsOn="{x:Bind ViewModel.CenterOnResize, Mode=TwoWay}"
                              Margin="0,0,0,8" />
                <TextBlock Text="Ctrl+Win+R to toggle"
                    FontSize="12"
                    Foreground="{ThemeResource TextFillColorSecondaryBrush}"
                    HorizontalAlignment="Center" />
            </StackPanel>
        </Border>
    </Grid>
</Window>
```

-##### Step 3 Verification Checklist
- [x] Build the solution: `dotnet build ResizeMe.sln -c Debug`
- [ ] Launch ResizeMe and confirm each preset button shows an icon, preset name, and dimensions.
- [ ] STOP HERE AND ASK THE USER TO VERIFY AND COMMIT BEFORE PROCEEDING TO NEXT STEP.
- [ ] **STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change. The user should confirm the commit (e.g., "Committed: <short-commit-sha>") before the agent continues.

### Success Criteria
- [ ] Preset icons change based on width thresholds (≤1024 ➜ "\uE7F8", ≤1366 ➜ "\uE80A", ≤1920 ➜ "\uE959", >1920 ➜ "\uE9F9").
- [ ] Each quick preset button displays name on line 1 and "Width x Height" on line 2.
- [ ] Buttons use `PresetButtonBaseStyle` for consistent spacing and theming.
- [ ] Clicking a preset still executes `ResizeCommand` and resizes the active window.

### Troubleshooting
- **Converter resource not found:** Ensure `App.xaml` includes the `xmlns:converters` namespace and registers `WidthToIconGlyphConverter` before other resources.
- **Icons not updating:** Confirm `Glyph="{Binding Width, Converter={StaticResource WidthToIconGlyphConverter}}"` is present and rebuild to pick up the converter.
- **Button spacing incorrect:** Make sure the button uses `Style="{StaticResource PresetButtonBaseStyle}"` and the `Grid ColumnSpacing` is set to `12`.
- **Build errors for missing namespace:** Reopen the solution if IntelliSense caches old metadata; the `ResizeMe.Shared.Converters` namespace must exist under `Shared/Converters`.

### Reference Documentation
- [WinUI 3 data binding and converters](https://learn.microsoft.com/windows/apps/design/style/data-binding)
- [Segoe Fluent Icons glyph reference](https://learn.microsoft.com/windows/apps/design/style/segoe-fluent-icons-font)
