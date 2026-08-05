using System;
using System.Threading;
using ResizeMe.Models;
using ResizeMe.Native;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Features.WindowManagement
{
    internal sealed class WindowResizeService
    {
        public ResizeResult Resize(WindowInfo window, int width, int height)
        {
            var request = new WindowSize(width, height);
            if (window?.Handle == null || window.Handle == IntPtr.Zero)
            {
                return ResizeResult.CreateFailure(window ?? new WindowInfo(), request, "Invalid window handle");
            }

            if (!request.IsValid)
            {
                return ResizeResult.CreateFailure(window, request, "Width and height must be greater than zero");
            }

            if (!WindowsApi.GetWindowRect(window.Handle, out var currentRect))
            {
                var error = WindowsApi.GetLastError();
                return ResizeResult.CreateFailure(window, request, "Unable to read current bounds", error);
            }

            var state = GetWindowState(window.Handle);
            var stateChanged = false;
            if (state != WindowState.Normal)
            {
                if (!RestoreWindow(window.Handle, state))
                {
                    return ResizeResult.CreateFailure(window, request, $"Failed to restore from {state}");
                }
                stateChanged = true;
            }

            bool success = WindowsApi.SetWindowPos(
                window.Handle,
                WindowsApi.HWND_TOP,
                currentRect.Left,
                currentRect.Top,
                width,
                height,
                WindowsApi.SWP_NOZORDER | WindowsApi.SWP_NOACTIVATE | WindowsApi.SWP_SHOWWINDOW);

            if (!success)
            {
                uint errorCode = WindowsApi.GetLastError();
                return ResizeResult.CreateFailure(window, request, DescribeError(errorCode), errorCode);
            }

            if (!WindowsApi.GetWindowRect(window.Handle, out var newRect))
            {
                newRect = currentRect;
            }

            var actual = new WindowSize(newRect.Width, newRect.Height);
            return ResizeResult.CreateSuccess(window, request, actual, stateChanged);
        }

        public bool Activate(WindowInfo window)
        {
            if (window?.Handle == null || window.Handle == IntPtr.Zero)
            {
                return false;
            }

            if (WindowsApi.IsIconic(window.Handle))
            {
                WindowsApi.ShowWindow(window.Handle, WindowsApi.SW_RESTORE);
            }

            if (WindowsApi.SetForegroundWindow(window.Handle))
            {
                return true;
            }

            return WindowsApi.BringWindowToTop(window.Handle);
        }

        private static WindowState GetWindowState(IntPtr handle)
        {
            if (WindowsApi.IsIconic(handle))
            {
                return WindowState.Minimized;
            }
            if (WindowsApi.IsZoomed(handle))
            {
                return WindowState.Maximized;
            }
            return WindowState.Normal;
        }

        private static bool RestoreWindow(IntPtr handle, WindowState state)
        {
            try
            {
                if (WindowsApi.ShowWindow(handle, WindowsApi.SW_RESTORE))
                {
                    Thread.Sleep(100);
                    if (!WindowsApi.IsIconic(handle) && !WindowsApi.IsZoomed(handle))
                    {
                        return true;
                    }
                }

                var placement = WindowsApi.WINDOWPLACEMENT.Default;
                if (WindowsApi.GetWindowPlacement(handle, ref placement))
                {
                    placement.showCmd = WindowsApi.SW_SHOWNORMAL;
                    return WindowsApi.SetWindowPlacement(handle, ref placement);
                }
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(WindowResizeService), $"RestoreWindow failed: {ex.Message}");
            }
            return false;
        }

        private static string DescribeError(uint code)
        {
            return code switch
            {
                0 => "Operation completed successfully",
                5 => "Access denied",
                6 => "Invalid handle",
                87 => "Invalid parameter",
                1400 => "Invalid window handle",
                _ => $"Windows API error {code}"
            };
        }
    }

    internal enum WindowState
    {
        Normal,
        Minimized,
        Maximized
    }
}
