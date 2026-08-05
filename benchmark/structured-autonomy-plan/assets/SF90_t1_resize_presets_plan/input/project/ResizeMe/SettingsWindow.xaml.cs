using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.UI.Input;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using ResizeMe.Features.Settings;
using ResizeMe.Features.SystemIntegration;
using ResizeMe.Models;
using ResizeMe.Shared.Config;
using Windows.Storage;
using Windows.UI.Core;

namespace ResizeMe
{
    public sealed partial class SettingsWindow : Window
    {
        private readonly PresetStorage _storage = new();
        private readonly ObservableCollection<PresetSize> _view = new();

        public event EventHandler? PresetsChanged;

        public SettingsWindow()
        {
            InitializeComponent();
            Title = "ResizeMe Settings";
            PresetList.ItemsSource = _view;
            WidthInput.KeyUp += OnDimensionKeyUp;
            HeightInput.KeyUp += OnDimensionKeyUp;
            SetWindowSize();
            _ = InitializeAsync();
            LoadHotkeyDisplay();

            try
            {
#if DEBUG
                ResetPrefsButton.Visibility = Visibility.Visible;
#else
                ResetPrefsButton.Visibility = Visibility.Collapsed;
#endif
            }
            catch
            {
                // Ignore failures to toggle visibility.
            }
        }

        private async Task InitializeAsync()
        {
            await _storage.LoadAsync();
            RefreshView();
        }

        private void RefreshView()
        {
            _view.Clear();
            foreach (var preset in _storage.Presets.OrderBy(p => p.Name))
            {
                _view.Add(preset);
            }
        }

        private void SetWindowSize()
        {
            try
            {
                var hWnd = WinRT.Interop.WindowNative.GetWindowHandle(this);
                if (hWnd == IntPtr.Zero)
                {
                    return;
                }

                var windowId = Microsoft.UI.Win32Interop.GetWindowIdFromWindow(hWnd);
                var appWindow = Microsoft.UI.Windowing.AppWindow.GetFromWindowId(windowId);
                if (appWindow == null)
                {
                    return;
                }

                try
                {
                    var iconPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "AppIcon.ico");
                    if (System.IO.File.Exists(iconPath))
                    {
                        appWindow.SetIcon(iconPath);
                    }
                }
                catch (Exception iconEx)
                {
                    System.Diagnostics.Debug.WriteLine($"Failed to set settings window icon: {iconEx.Message}");
                }

                appWindow.Resize(new Windows.Graphics.SizeInt32(700, 600));
            }
            catch (ArgumentException)
            {
                // Ignore sizing failures.
            }
        }

        private void LoadHotkeyDisplay()
        {
            try
            {
                CurrentHotkeyText.Text = $"Current: {UserSettingsStore.HotKeyModifiers}+{UserSettingsStore.HotKeyCode}";
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"LoadHotkeyDisplay error: {ex.Message}");
            }
        }

        private async void AddButton_Click(object sender, RoutedEventArgs e)
        {
            ValidationText.Text = string.Empty;
            ValidationText.Visibility = Visibility.Collapsed;

            string name = NameInput.Text.Trim();
            if (!int.TryParse(WidthInput.Text, out int width) || !int.TryParse(HeightInput.Text, out int height))
            {
                ValidationText.Text = "Width and Height must be valid numbers";
                ValidationText.Visibility = Visibility.Visible;
                return;
            }

            if (width <= 0 || height <= 0)
            {
                ValidationText.Text = "Dimensions must be greater than 0";
                ValidationText.Visibility = Visibility.Visible;
                return;
            }

            if (string.IsNullOrWhiteSpace(name))
            {
                name = $"{width}x{height}";
            }

            var preset = new PresetSize { Name = name, Width = width, Height = height };
            bool added = await _storage.AddAsync(preset);
            if (!added)
            {
                ValidationText.Text = "A preset with this name already exists";
                ValidationText.Visibility = Visibility.Visible;
                return;
            }

            RefreshView();
            NotifyPresetsChanged();
            NameInput.Text = WidthInput.Text = HeightInput.Text = string.Empty;
            NameInput.Focus(FocusState.Programmatic);
        }

        private async void RemoveButton_Click(object sender, RoutedEventArgs e)
        {
            ValidationText.Text = string.Empty;
            if (PresetList.SelectedItem is PresetSize ps)
            {
                bool removed = await _storage.RemoveAsync(ps.Name);
                if (removed)
                {
                    RefreshView();
                    NotifyPresetsChanged();
                }
            }
            else
            {
                ValidationText.Text = "Select preset first";
            }
        }

        private async void ResetButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new ContentDialog
            {
                Title = "Reset Presets",
                Content = "Are you sure you want to reset presets to defaults? This cannot be undone.",
                PrimaryButtonText = "Reset",
                CloseButtonText = "Cancel"
            };

            if (Content is FrameworkElement fe)
            {
                dialog.XamlRoot = fe.XamlRoot;
            }

            var result = await dialog.ShowAsync();
            if (result == ContentDialogResult.Primary)
            {
                await _storage.ResetAsync();
                RefreshView();
                NotifyPresetsChanged();
            }
        }

        private void OnDimensionKeyUp(object sender, KeyRoutedEventArgs e)
        {
            if (e.Key == Windows.System.VirtualKey.Enter)
            {
                AddButton_Click(sender, e);
            }
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e) => Close();

        private void ResetPrefsButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                ApplicationData.Current.LocalSettings.Values.Remove("FirstMinimizeNotificationShown");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Reset prefs error: {ex.Message}");
            }
        }

        private string _capturedModifiers = string.Empty;
        private string _capturedKey = string.Empty;
        private bool _capturing;
        private TextBlock? _captureFlyoutStatusControl;

        private async void CustomizeHotkeyButton_Click(object sender, RoutedEventArgs e)
        {
            HotkeyErrorText.Visibility = Visibility.Collapsed;
            _capturedModifiers = string.Empty;
            _capturedKey = string.Empty;
            _capturing = true;

            var flyout = new Flyout();
            var panel = new StackPanel { Spacing = 8, Padding = new Thickness(12) };
            var instruction = new TextBlock { Text = "Press key combination now...", FontSize = 14 };
            var captureStatus = new TextBlock { Text = string.Empty, FontSize = 13 };
            _captureFlyoutStatusControl = captureStatus;
            var btnPanel = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, HorizontalAlignment = HorizontalAlignment.Right };
            var applyBtn = new Button { Content = "Apply", Padding = new Thickness(12, 6, 12, 6) };
            var cancelBtn = new Button { Content = "Cancel", Padding = new Thickness(12, 6, 12, 6) };
            btnPanel.Children.Add(cancelBtn);
            btnPanel.Children.Add(applyBtn);
            panel.Children.Add(instruction);
            panel.Children.Add(captureStatus);
            panel.Children.Add(btnPanel);
            flyout.Content = panel;

            var tcs = new TaskCompletionSource<bool?>();
            applyBtn.Click += (_, _) => tcs.TrySetResult(true);
            cancelBtn.Click += (_, _) => tcs.TrySetResult(false);

            if (Content is FrameworkElement fe)
            {
                fe.KeyDown += SettingsCapture_KeyDown;
            }

            flyout.ShowAt(CustomizeHotkeyButton);
            var result = await tcs.Task;
            flyout.Hide();

            if (Content is FrameworkElement feDetach)
            {
                feDetach.KeyDown -= SettingsCapture_KeyDown;
            }

            _captureFlyoutStatusControl = null;
            _capturing = false;

            if (result == true)
            {
                if (string.IsNullOrWhiteSpace(_capturedKey))
                {
                    HotkeyErrorText.Text = "No key captured.";
                    HotkeyErrorText.Visibility = Visibility.Visible;
                    return;
                }

                var mods = string.IsNullOrWhiteSpace(_capturedModifiers) ? "CTRL+WIN" : _capturedModifiers;
                if (HotKeyService.IsReserved(mods, _capturedKey))
                {
                    HotkeyErrorText.Text = "This hotkey is reserved by Windows.";
                    HotkeyErrorText.Visibility = Visibility.Visible;
                    return;
                }

                UserSettingsStore.HotKeyModifiers = mods;
                UserSettingsStore.HotKeyCode = _capturedKey;

                TryReRegisterFromMainWindow();
                LoadHotkeyDisplay();
            }
        }

        private void SettingsCapture_KeyDown(object sender, KeyRoutedEventArgs e)
        {
            if (!_capturing)
            {
                return;
            }

            var mods = new List<string>();

            if ((InputKeyboardSource.GetKeyStateForCurrentThread(Windows.System.VirtualKey.Control) & CoreVirtualKeyStates.Down) != 0)
            {
                mods.Add("CTRL");
            }

            if ((InputKeyboardSource.GetKeyStateForCurrentThread(Windows.System.VirtualKey.Menu) & CoreVirtualKeyStates.Down) != 0)
            {
                mods.Add("ALT");
            }

            if ((InputKeyboardSource.GetKeyStateForCurrentThread(Windows.System.VirtualKey.Shift) & CoreVirtualKeyStates.Down) != 0)
            {
                mods.Add("SHIFT");
            }

            if ((InputKeyboardSource.GetKeyStateForCurrentThread(Windows.System.VirtualKey.LeftWindows) & CoreVirtualKeyStates.Down) != 0 ||
                (InputKeyboardSource.GetKeyStateForCurrentThread(Windows.System.VirtualKey.RightWindows) & CoreVirtualKeyStates.Down) != 0)
            {
                mods.Add("WIN");
            }

            var key = e.Key;
            if (IsModifier(key))
            {
                _capturedModifiers = string.Join("+", mods);
                UpdateCaptureStatus();
                return;
            }

            _capturedKey = MapKey(key);
            _capturedModifiers = string.Join("+", mods);
            UpdateCaptureStatus();
            e.Handled = true;
        }

        private static bool IsModifier(Windows.System.VirtualKey key)
        {
            return key == Windows.System.VirtualKey.Control ||
                   key == Windows.System.VirtualKey.Menu ||
                   key == Windows.System.VirtualKey.Shift ||
                   key == Windows.System.VirtualKey.LeftControl ||
                   key == Windows.System.VirtualKey.RightControl ||
                   key == Windows.System.VirtualKey.LeftShift ||
                   key == Windows.System.VirtualKey.RightShift ||
                   key == Windows.System.VirtualKey.LeftWindows ||
                   key == Windows.System.VirtualKey.RightWindows;
        }

        private void UpdateCaptureStatus()
        {
            var live = string.Join("+", new[] { _capturedModifiers, _capturedKey }.Where(s => !string.IsNullOrWhiteSpace(s)));
            if (_captureFlyoutStatusControl != null)
            {
                _captureFlyoutStatusControl.Text = live;
            }
        }

        private static string MapKey(Windows.System.VirtualKey key)
        {
            if (key >= Windows.System.VirtualKey.Number0 && key <= Windows.System.VirtualKey.Number9)
            {
                return ((char)key).ToString();
            }

            if (key >= Windows.System.VirtualKey.A && key <= Windows.System.VirtualKey.Z)
            {
                return ((char)key).ToString();
            }

            if (key >= Windows.System.VirtualKey.F1 && key <= Windows.System.VirtualKey.F24)
            {
                int fNum = (int)key - (int)Windows.System.VirtualKey.F1 + 1;
                return $"F{fNum}";
            }

            return key switch
            {
                (Windows.System.VirtualKey)0xBB => "+",
                (Windows.System.VirtualKey)0xBC => ",",
                (Windows.System.VirtualKey)0xBD => "-",
                (Windows.System.VirtualKey)0xBE => ".",
                _ => key.ToString().ToUpperInvariant()
            };
        }

        private void ResetHotkeyButton_Click(object sender, RoutedEventArgs e)
        {
            UserSettingsStore.HotKeyModifiers = "CTRL+WIN";
            UserSettingsStore.HotKeyCode = "R";
            TryReRegisterFromMainWindow();
            LoadHotkeyDisplay();
            HotkeyErrorText.Visibility = Visibility.Collapsed;
        }

        private void NotifyPresetsChanged()
        {
            PresetsChanged?.Invoke(this, EventArgs.Empty);
        }

        private void TryReRegisterFromMainWindow()
        {
            try
            {
                var main = (Application.Current as App)?.Window as MainWindow;
                main?.RefreshHotKeyRegistration();
            }
            catch (Exception ex)
            {
                HotkeyErrorText.Text = $"Re-register failed: {ex.Message}";
                HotkeyErrorText.Visibility = Visibility.Visible;
            }
        }
    }
}
