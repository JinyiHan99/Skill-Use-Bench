using System;
using System.Diagnostics;
using Microsoft.UI.Xaml;
using ResizeMe.Models;
using ResizeMe.Native;
using WinRT.Interop;

namespace ResizeMe.Features.WindowManagement
{
    internal static class WindowPositionService
    {
        public static void CenterOnWindow(Window window, WindowInfo? anchor)
        {
            if (window == null)
            {
                return;
            }

            if (anchor == null)
            {
                CenterOnScreen(window);
                return;
            }

            try
            {
                var bounds = anchor.Bounds;
                var handle = WindowNative.GetWindowHandle(window);
                if (handle == IntPtr.Zero)
                {
                    return;
                }

                var width = (int)(window.Bounds.Width > 0 ? window.Bounds.Width : 280);
                var height = (int)(window.Bounds.Height > 0 ? window.Bounds.Height : 400);

                int centerX = bounds.X + (bounds.Width / 2);
                int centerY = bounds.Y + (bounds.Height / 2);

                int targetX = centerX - (width / 2);
                int targetY = centerY - (height / 2);

                var monitorPoint = new WindowsApi.POINT { X = centerX, Y = centerY };
                var monitorInfo = WindowsApi.MONITORINFO.Default;
                var monitor = WindowsApi.MonitorFromPoint(monitorPoint, WindowsApi.MONITOR_DEFAULTTONEAREST);
                if (monitor != IntPtr.Zero && WindowsApi.GetMonitorInfo(monitor, ref monitorInfo))
                {
                    AdjustToBounds(monitorInfo.rcWork, ref targetX, ref targetY, width, height);
                }

                WindowsApi.SetWindowPos(handle, IntPtr.Zero, targetX, targetY, 0, 0, WindowsApi.SWP_NOSIZE | WindowsApi.SWP_NOZORDER | WindowsApi.SWP_NOACTIVATE);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"WindowPositionService.CenterOnWindow failed: {ex.Message}");
            }
        }

        public static void CenterOnScreen(Window window)
        {
            try
            {
                if (!WindowsApi.GetCursorPos(out var cursor))
                {
                    cursor = new WindowsApi.POINT { X = 0, Y = 0 };
                }

                var monitor = WindowsApi.MonitorFromPoint(cursor, WindowsApi.MONITOR_DEFAULTTONEAREST);
                var monitorInfo = WindowsApi.MONITORINFO.Default;
                if (!WindowsApi.GetMonitorInfo(monitor, ref monitorInfo))
                {
                    return;
                }

                var handle = WindowNative.GetWindowHandle(window);
                if (handle == IntPtr.Zero)
                {
                    return;
                }

                var width = (int)(window.Bounds.Width > 0 ? window.Bounds.Width : 280);
                var height = (int)(window.Bounds.Height > 0 ? window.Bounds.Height : 400);

                int x = monitorInfo.rcWork.Left + (monitorInfo.rcWork.Width - width) / 2;
                int y = monitorInfo.rcWork.Top + (monitorInfo.rcWork.Height - height) / 2;

                WindowsApi.SetWindowPos(handle, IntPtr.Zero, x, y, 0, 0, WindowsApi.SWP_NOSIZE | WindowsApi.SWP_NOZORDER | WindowsApi.SWP_NOACTIVATE);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"WindowPositionService.CenterOnScreen failed: {ex.Message}");
            }
        }

        public static void CenterExternalWindow(WindowInfo window)
        {
            if (window?.Handle == null || window.Handle == IntPtr.Zero)
            {
                return;
            }

            try
            {
                if (!WindowsApi.GetWindowRect(window.Handle, out var rect))
                {
                    return;
                }

                var center = new WindowsApi.POINT { X = rect.Left + rect.Width / 2, Y = rect.Top + rect.Height / 2 };
                var monitorInfo = WindowsApi.MONITORINFO.Default;
                var monitor = WindowsApi.MonitorFromPoint(center, WindowsApi.MONITOR_DEFAULTTONEAREST);
                if (!WindowsApi.GetMonitorInfo(monitor, ref monitorInfo))
                {
                    return;
                }

                int width = rect.Width;
                int height = rect.Height;
                int x = monitorInfo.rcWork.Left + (monitorInfo.rcWork.Width - width) / 2;
                int y = monitorInfo.rcWork.Top + (monitorInfo.rcWork.Height - height) / 2;

                WindowsApi.SetWindowPos(window.Handle, IntPtr.Zero, x, y, 0, 0, WindowsApi.SWP_NOSIZE | WindowsApi.SWP_NOZORDER | WindowsApi.SWP_NOACTIVATE);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"WindowPositionService.CenterExternalWindow failed: {ex.Message}");
            }
        }

        private static void AdjustToBounds(WindowsApi.RECT bounds, ref int x, ref int y, int width, int height)
        {
            if (x < bounds.Left)
            {
                x = bounds.Left + 10;
            }
            else if (x + width > bounds.Right)
            {
                x = bounds.Right - width - 10;
            }

            if (y < bounds.Top)
            {
                y = bounds.Top + 10;
            }
            else if (y + height > bounds.Bottom)
            {
                y = bounds.Bottom - height - 10;
            }
        }
    }
}
