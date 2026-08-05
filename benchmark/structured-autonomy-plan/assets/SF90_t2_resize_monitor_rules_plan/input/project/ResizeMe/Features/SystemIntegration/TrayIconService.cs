using System;
using System.Runtime.InteropServices;
using ResizeMe.Native;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Features.SystemIntegration
{
    internal sealed class TrayIconService : IDisposable
    {
        private readonly IntPtr _windowHandle;
        private readonly string _tooltip;
        private bool _added;

        private const int CmdShow = 10001;
        private const int CmdSettings = 10002;
        private const int CmdExit = 10003;

        public TrayIconService(IntPtr windowHandle, string tooltip)
        {
            _windowHandle = windowHandle;
            _tooltip = tooltip;
        }

        public event EventHandler? ShowRequested;
        public event EventHandler? SettingsRequested;
        public event EventHandler? ExitRequested;

        public int CallbackMessage => WindowsApi.WM_USER_TRAY;

        public bool Initialize()
        {
            if (_added || _windowHandle == IntPtr.Zero)
            {
                return _added;
            }

            var icon = LoadIcon();
            var data = new WindowsApi.NOTIFYICONDATA
            {
                cbSize = Marshal.SizeOf<WindowsApi.NOTIFYICONDATA>(),
                hWnd = _windowHandle,
                uID = 1,
                uFlags = WindowsApi.NIF_MESSAGE | WindowsApi.NIF_ICON | WindowsApi.NIF_TIP,
                uCallbackMessage = CallbackMessage,
                hIcon = icon,
                szTip = _tooltip
            };

            _added = WindowsApi.Shell_NotifyIcon(WindowsApi.NIM_ADD, ref data);
            if (!_added)
            {
                AppLog.Warn(nameof(TrayIconService), "Shell_NotifyIcon failed");
            }
            return _added;
        }

        public void ShowContextMenu()
        {
            if (_windowHandle == IntPtr.Zero)
            {
                return;
            }

            WindowsApi.SetForegroundWindow(_windowHandle);
            var menu = WindowsApi.CreatePopupMenu();
            if (menu == IntPtr.Zero)
            {
                return;
            }

            WindowsApi.AppendMenu(menu, 0, CmdShow, "Show/Hide");
            WindowsApi.AppendMenu(menu, 0, CmdSettings, "Settings...");
            WindowsApi.AppendMenu(menu, 0, CmdExit, "Exit");

            WindowsApi.GetCursorPos(out var cursor);
            uint command = WindowsApi.TrackPopupMenuEx(menu, WindowsApi.TPM_RIGHTBUTTON | WindowsApi.TPM_RETURNCMD, cursor.X, cursor.Y, _windowHandle, IntPtr.Zero);
            WindowsApi.DestroyMenu(menu);

            if (command == CmdShow)
            {
                ShowRequested?.Invoke(this, EventArgs.Empty);
            }
            else if (command == CmdSettings)
            {
                SettingsRequested?.Invoke(this, EventArgs.Empty);
            }
            else if (command == CmdExit)
            {
                ExitRequested?.Invoke(this, EventArgs.Empty);
            }
        }

        public void Dispose()
        {
            if (!_added)
            {
                return;
            }

            var data = new WindowsApi.NOTIFYICONDATA
            {
                cbSize = Marshal.SizeOf<WindowsApi.NOTIFYICONDATA>(),
                hWnd = _windowHandle,
                uID = 1
            };
            WindowsApi.Shell_NotifyIcon(WindowsApi.NIM_DELETE, ref data);
            _added = false;
        }

        private static IntPtr LoadIcon()
        {
            try
            {
                var iconPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "AppIcon.ico");
                if (System.IO.File.Exists(iconPath))
                {
                    var handle = WindowsApi.LoadImage(IntPtr.Zero, iconPath, WindowsApi.IMAGE_ICON, 16, 16, WindowsApi.LR_LOADFROMFILE | WindowsApi.LR_DEFAULTSIZE);
                    if (handle != IntPtr.Zero)
                    {
                        return handle;
                    }
                }
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(TrayIconService), $"Icon load failed: {ex.Message}");
            }

            return WindowsApi.LoadIcon(IntPtr.Zero, new IntPtr(32512));
        }
    }
}
