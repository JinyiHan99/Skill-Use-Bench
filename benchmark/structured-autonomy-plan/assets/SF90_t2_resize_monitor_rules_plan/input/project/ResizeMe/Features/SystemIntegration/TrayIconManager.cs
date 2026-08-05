using System;
using ResizeMe.Native;
using ResizeMe.Shared.Config;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Features.SystemIntegration
{
    public sealed class TrayIconManager : IDisposable
    {
        private readonly string _logger = nameof(TrayIconManager);
        private readonly IntPtr _windowHandle;
        private TrayIconService? _trayIcon;

        public event EventHandler? ShowRequested;
        public event EventHandler? SettingsRequested;
        public event EventHandler? ExitRequested;

        public TrayIconManager(IntPtr windowHandle)
        {
            if (windowHandle == IntPtr.Zero)
            {
                throw new ArgumentException("Window handle must be valid", nameof(windowHandle));
            }

            _windowHandle = windowHandle;
        }

        public bool Initialize()
        {
            if (_trayIcon != null)
            {
                return true;
            }

            _trayIcon = new TrayIconService(_windowHandle, "ResizeMe");
            if (!_trayIcon.Initialize())
            {
                AppLog.Warn(_logger, "Tray icon initialization failed.");
                return false;
            }

            _trayIcon.ShowRequested += (_, _) => ShowRequested?.Invoke(this, EventArgs.Empty);
            _trayIcon.SettingsRequested += (_, _) => SettingsRequested?.Invoke(this, EventArgs.Empty);
            _trayIcon.ExitRequested += (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty);
            return true;
        }

        public int CallbackMessage => _trayIcon?.CallbackMessage ?? 0;

        public void ShowContextMenu()
        {
            _trayIcon?.ShowContextMenu();
        }

        public void ShowFirstRunBalloon()
        {
            if (UserSettingsStore.FirstMinimizeNotificationShown)
            {
                return;
            }

            var message = $"ResizeMe is running in the tray. Press {UserSettingsStore.HotKeyModifiers}+{UserSettingsStore.HotKeyCode} to open.";
            WindowsApi.MessageBoxW(IntPtr.Zero, message, "ResizeMe", WindowsApi.MB_OK | WindowsApi.MB_TOPMOST);
            UserSettingsStore.FirstMinimizeNotificationShown = true;
        }

        public void Dispose()
        {
            if (_trayIcon != null)
            {
                _trayIcon.ShowRequested -= (_, _) => ShowRequested?.Invoke(this, EventArgs.Empty);
                _trayIcon.SettingsRequested -= (_, _) => SettingsRequested?.Invoke(this, EventArgs.Empty);
                _trayIcon.ExitRequested -= (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty);
                _trayIcon.Dispose();
                _trayIcon = null;
            }
        }
    }
}
