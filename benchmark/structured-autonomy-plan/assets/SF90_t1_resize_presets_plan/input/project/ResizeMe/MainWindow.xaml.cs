using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using ResizeMe.Features.MainLayout;
using ResizeMe.Features.Settings;
using ResizeMe.Features.SystemIntegration;
using ResizeMe.Features.WindowManagement;
using ResizeMe.Models;
using ResizeMe.Native;
using ResizeMe.Shared.Config;
using ResizeMe.Shared.Logging;
using ResizeMe.ViewModels;
using WinRT.Interop;

namespace ResizeMe
{
    public sealed partial class MainWindow : Window
    {
        private readonly MainViewModel _viewModel;
        public MainViewModel ViewModel => _viewModel;
        
        public string? Status => _viewModel.Status;
        public bool CenterOnResize
        {
            get => _viewModel.CenterOnResize;
            set => _viewModel.CenterOnResize = value;
        }
        
        private readonly PresetStorage _presets = new();
        private readonly WindowDiscoveryService _windowDiscovery = new();
        private readonly WindowResizeService _windowResizer = new();
        private readonly INativeWindowService _nativeWindowService = new NativeWindowService();
        private readonly IWindowSubclassService _subclassService = new WindowSubclassService();
        private TrayIconManager? _trayManager;
        private HotKeyService? _hotKey;
        private IntPtr _windowHandle;
        private AppWindow? _appWindow;
        
        private DateTime _lastToggle = DateTime.MinValue;

        public MainWindow()
        {
            _viewModel = new MainViewModel(DispatcherQueue, _presets, _windowDiscovery, _windowResizer);
            InitializeComponent();
            if (Content is FrameworkElement root)
            {
                root.DataContext = _viewModel;
            }
            AttachRootHandlers();
            Activated += OnActivated;
            Closed += OnClosed;

            _viewModel.PropertyChanged += ViewModel_PropertyChanged;
        }

        private void AttachRootHandlers()
        {
            if (Content is FrameworkElement root)
            {
                root.KeyDown -= OnKeyDown;
                root.KeyDown += OnKeyDown;
                root.Loaded -= OnRootLoaded;
                root.Loaded += OnRootLoaded;
            }
        }

        private async void OnRootLoaded(object sender, RoutedEventArgs e)
        {
            if (sender is FrameworkElement root)
            {
                root.Loaded -= OnRootLoaded;
            }

            EnsureWindowHandle();
            ConfigureShell();
            InitializeIntegration();
            AttachSubclass();

            await _viewModel.InitializeAsync();
            
            HideWindow();
            ShowFirstRunFlows();
        }

        private void EnsureWindowHandle()
        {
            if (_windowHandle != IntPtr.Zero)
            {
                return;
            }

            _windowHandle = _nativeWindowService.EnsureWindowHandle(this);
            _appWindow = _nativeWindowService.GetAppWindow(this);
        }

        private void ConfigureShell()
        {
            try
            {
                Title = "ResizeMe";
                if (_appWindow == null)
                {
                    return;
                }

                var iconPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "AppIcon.ico");
                _nativeWindowService.ConfigureShell(_appWindow, "ResizeMe", iconPath, 320, 540);
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(MainWindow), $"ConfigureShell failed: {ex.Message}");
            }
        }

        private async void AttachSubclass()
        {
            if (_windowHandle == IntPtr.Zero)
            {
                return;
            }
            var handler = new AppWindowMessageHandler(
                onClose: HideWindow,
                trayManager: _trayManager,
                hotKeyService: _hotKey,
                onTrayShow: () => DispatcherQueue.TryEnqueue(ToggleVisibility)
            );
            await _subclassService.AttachAsync(_windowHandle, handler);
        }

        private void InitializeIntegration()
        {
            InitializeHotKey();
            InitializeTray();
        }

        private void InitializeHotKey()
        {
            if (_windowHandle == IntPtr.Zero || _hotKey != null)
            {
                return;
            }

            _hotKey = new HotKeyService(_windowHandle);
            _hotKey.HotKeyTriggered += (_, _) => DispatcherQueue.TryEnqueue(ToggleVisibility);
            _hotKey.TryRegister();
        }

        private void InitializeTray()
        {
            if (_windowHandle == IntPtr.Zero || _trayManager != null)
            {
                return;
            }

            _trayManager = new TrayIconManager(_windowHandle);
            if (_trayManager.Initialize())
            {
                _trayManager.ShowRequested += OnTrayShowRequested;
                _trayManager.SettingsRequested += OnTraySettingsRequested;
                _trayManager.ExitRequested += OnTrayExitRequested;
            }
        }

        private void OnTrayShowRequested(object? sender, EventArgs e)
        {
            DispatcherQueue.TryEnqueue(ToggleVisibility);
        }

        private void OnTraySettingsRequested(object? sender, EventArgs e)
        {
            DispatcherQueue.TryEnqueue(OpenSettingsWindow);
        }

        private void OnTrayExitRequested(object? sender, EventArgs e)
        {
            DispatcherQueue.TryEnqueue(PerformExit);
        }



        private void ShowFirstRunFlows()
        {
            _trayManager?.ShowFirstRunBalloon();
            CheckFirstRunSettings();
        }

        private void ShowTrayNotificationOnce()
        {
            if (UserSettingsStore.FirstMinimizeNotificationShown)
            {
                return;
            }

            try
            {
                var message = $"ResizeMe is running in the tray. Press {UserSettingsStore.HotKeyModifiers}+{UserSettingsStore.HotKeyCode} to open.";
                WindowsApi.MessageBoxW(IntPtr.Zero, message, "ResizeMe", WindowsApi.MB_OK | WindowsApi.MB_TOPMOST);
                UserSettingsStore.FirstMinimizeNotificationShown = true;
                HideWindow();
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(MainWindow), $"Tray notification failed: {ex.Message}");
            }
        }

        private void CheckFirstRunSettings()
        {
            if (UserSettingsStore.FirstRunCompleted)
            {
                return;
            }

            var window = new SettingsWindow();
            window.PresetsChanged += SettingsPresetsChangedAsync;
            window.Closed += async (_, _) =>
            {
                window.PresetsChanged -= SettingsPresetsChangedAsync;
                UserSettingsStore.FirstRunCompleted = true;
                await _viewModel.ReloadPresetsAsync();
            };
            window.Activate();
        }

        private void ToggleVisibility()
        {
            if ((DateTime.UtcNow - _lastToggle).TotalMilliseconds < 150)
            {
                return;
            }

            _lastToggle = DateTime.UtcNow;
            if (_viewModel.IsVisible)
            {
                _viewModel.Hide();
            }
            else
            {
                // Capture the foreground window BEFORE showing ResizeMe window
                // This ensures we get the window that had focus when the hotkey was pressed
                _viewModel.CaptureTargetWindow();
                _viewModel.Show();
            }
        }

        private async Task ShowWindowAsync()
        {
            try
            {
                EnsureWindowHandle();
                await _viewModel.ReloadPresetsAsync();
                // Don't call RefreshWindowSnapshot here - the target window is already captured
                // by CaptureTargetWindow() before the visibility toggle

                var anchor = _viewModel.SelectedWindow;
                if (anchor != null)
                {
                    WindowPositionService.CenterOnWindow(this, anchor);
                }
                else
                {
                    WindowPositionService.CenterOnScreen(this);
                }

                if (_windowHandle != IntPtr.Zero)
                {
                    _nativeWindowService.RestoreWindow(_windowHandle);
                    _nativeWindowService.FocusWindow(_windowHandle);
                }

                Activate();
                _viewModel.Show();
            }
            catch (Exception ex)
            {
                AppLog.Error(nameof(MainWindow), "ShowWindowAsync failed", ex);
            }
        }

        private void HideWindow()
        {
            if (_windowHandle != IntPtr.Zero)
            {
                _nativeWindowService.HideWindow(_windowHandle);
            }
            _viewModel.Hide();
        }

        private void ViewModel_PropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
        {
            if (e.PropertyName == nameof(MainViewModel.IsVisible))
            {
                if (_viewModel.IsVisible)
                {
                    _ = ShowWindowAsync();
                }
                else
                {
                    HideWindow();
                }
            }
            else if (e.PropertyName == nameof(MainViewModel.Status))
            {
                if (StatusText != null && _viewModel.Status != null)
                {
                    StatusText.Text = _viewModel.Status;
                }
            }
        }

        private void OnKeyDown(object sender, KeyRoutedEventArgs e)
        {
            if (!_viewModel.IsVisible)
            {
                return;
            }

            switch (e.Key)
            {
                case Windows.System.VirtualKey.Escape:
                    HideWindow();
                    e.Handled = true;
                    break;
            }
        }

        private void OnActivated(object sender, WindowActivatedEventArgs args)
        {
            if (args.WindowActivationState == WindowActivationState.Deactivated && _viewModel.IsVisible)
            {
                _ = Task.Run(async () =>
                {
                    await Task.Delay(150);
                    DispatcherQueue.TryEnqueue(HideWindow);
                });
                return;
            }

            InitializeHotKey();
        }

        private void OnClosed(object sender, WindowEventArgs args)
        {
            if (_trayManager != null)
            {
                _trayManager.ShowRequested -= OnTrayShowRequested;
                _trayManager.SettingsRequested -= OnTraySettingsRequested;
                _trayManager.ExitRequested -= OnTrayExitRequested;
                _trayManager.Dispose();
                _trayManager = null;
            }
            _hotKey?.Dispose();
            _subclassService.Detach();
            _subclassService.Dispose();
        }

        private void CenterOnResizeToggle_Toggled(object sender, RoutedEventArgs e)
        {
            // Handled by binding
        }

        private void SettingsButton_Click(object sender, RoutedEventArgs e)
        {
            OpenSettingsWindow();
        }

        private void OpenSettingsWindow()
        {
            try
            {
                var window = new SettingsWindow();
                window.PresetsChanged += SettingsPresetsChangedAsync;
                window.Closed += async (_, _) =>
                {
                    window.PresetsChanged -= SettingsPresetsChangedAsync;
                    await _viewModel.ReloadPresetsAsync();
                };
                window.Activate();
            }
            catch (Exception ex)
            {
                AppLog.Error(nameof(MainWindow), "Failed to open SettingsWindow", ex);
                WindowsApi.MessageBoxW(IntPtr.Zero, $"Failed to open settings: {ex}", "ResizeMe Error", WindowsApi.MB_OK | WindowsApi.MB_ICONERROR);
            }
        }

        private async void SettingsPresetsChangedAsync(object? sender, EventArgs e)
        {
            await _viewModel.ReloadPresetsAsync();
        }

        private void PerformExit()
        {
            try
            {
                if (_trayManager != null)
                {
                    _trayManager.ShowRequested -= OnTrayShowRequested;
                    _trayManager.SettingsRequested -= OnTraySettingsRequested;
                    _trayManager.ExitRequested -= OnTrayExitRequested;
                    _trayManager.Dispose();
                    _trayManager = null;
                }
                _hotKey?.Dispose();
            }
            finally
            {
                DispatcherQueue.TryEnqueue(Close);
            }
        }

        public void RefreshHotKeyRegistration()
        {
            if (_hotKey == null)
            {
                InitializeHotKey();
            }
            else
            {
                _hotKey.ReRegister();
            }
        }
    }
}
