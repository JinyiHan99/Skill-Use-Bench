using System;
using System.IO;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using ResizeMe.Shared.Logging;
using WinRT.Interop;

namespace ResizeMe.Native
{
    public sealed class NativeWindowService : INativeWindowService
    {
        private readonly string _logger = nameof(NativeWindowService);

        public IntPtr EnsureWindowHandle(Window window)
        {
            ArgumentNullException.ThrowIfNull(window);
            var hwnd = WindowNative.GetWindowHandle(window);
            if (hwnd == IntPtr.Zero)
            {
                AppLog.Error(_logger, "Window handle could not be resolved.");
                throw new InvalidOperationException("Window handle unavailable");
            }
            return hwnd;
        }

        public AppWindow? GetAppWindow(Window window)
        {
            ArgumentNullException.ThrowIfNull(window);
            var hwnd = WindowNative.GetWindowHandle(window);
            if (hwnd == IntPtr.Zero)
            {
                return null;
            }

            var windowId = Microsoft.UI.Win32Interop.GetWindowIdFromWindow(hwnd);
            return AppWindow.GetFromWindowId(windowId);
        }

        public void ConfigureShell(AppWindow appWindow, string title, string iconPath, int width, int height)
        {
            ArgumentNullException.ThrowIfNull(appWindow);
            appWindow.Title = title;
            if (!string.IsNullOrWhiteSpace(iconPath) && File.Exists(iconPath))
            {
                appWindow.SetIcon(iconPath);
            }

            appWindow.Resize(new Windows.Graphics.SizeInt32(width, height));
        }

        public void ShowWindow(IntPtr hwnd)
        {
            if (hwnd == IntPtr.Zero)
            {
                return;
            }
            WindowsApi.ShowWindow(hwnd, WindowsApi.SW_SHOW);
        }

        public void HideWindow(IntPtr hwnd)
        {
            if (hwnd == IntPtr.Zero)
            {
                return;
            }
            WindowsApi.ShowWindow(hwnd, WindowsApi.SW_HIDE);
        }

        public void RestoreWindow(IntPtr hwnd)
        {
            if (hwnd == IntPtr.Zero)
            {
                return;
            }
            WindowsApi.ShowWindow(hwnd, WindowsApi.SW_RESTORE);
        }

        public void FocusWindow(IntPtr hwnd)
        {
            if (hwnd == IntPtr.Zero)
            {
                return;
            }
            WindowsApi.SetForegroundWindow(hwnd);
        }
    }
}
