using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using ResizeMe.Models;
using ResizeMe.Native;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Features.WindowManagement
{
    internal sealed class WindowDiscoveryService
    {
        private static readonly HashSet<string> ExcludedClassNames = new(StringComparer.OrdinalIgnoreCase)
        {
            "Shell_TrayWnd",
            "Shell_SecondaryTrayWnd",
            "DV2ControlHost",
            "MsgrIMEWindowClass",
            "SysShadow",
            "Button",
            "Progman",
            "WorkerW",
            "ImmersiveLauncher",
            "Windows.UI.Core.CoreWindow",
            "ApplicationFrameWindow",
            "ForegroundStaging"
        };

        private static readonly HashSet<string> ExcludedTitles = new(StringComparer.OrdinalIgnoreCase)
        {
            string.Empty,
            "Program Manager",
            "Settings"
        };

        public IReadOnlyList<WindowInfo> GetWindows()
        {
            var windows = new List<WindowInfo>();
            bool EnumWindowCallback(IntPtr hWnd, IntPtr lParam)
            {
                try
                {
                    var info = GetWindowInfo(hWnd);
                    if (info != null && IsCandidate(info))
                    {
                        windows.Add(info);
                    }
                }
                catch (Exception ex)
                {
                    AppLog.Warn(nameof(WindowDiscoveryService), $"Enum failure: {ex.Message}");
                }
                return true;
            }

            WindowsApi.EnumWindows(EnumWindowCallback, IntPtr.Zero);
            return windows.OrderBy(w => w.Title).ToList();
        }

        public WindowInfo? GetActiveWindow()
        {
            try
            {
                var foreground = WindowsApi.GetForegroundWindow();
                if (foreground == IntPtr.Zero)
                {
                    return null;
                }
                var info = GetWindowInfo(foreground);
                return info != null && IsCandidate(info) ? info : null;
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(WindowDiscoveryService), $"Active window lookup failed: {ex.Message}");
                return null;
            }
        }

        private static WindowInfo? GetWindowInfo(IntPtr handle)
        {
            try
            {
                int titleLength = WindowsApi.GetWindowTextLength(handle);
                var titleBuilder = new StringBuilder(titleLength + 1);
                WindowsApi.GetWindowText(handle, titleBuilder, titleBuilder.Capacity);

                var classBuilder = new StringBuilder(256);
                WindowsApi.GetClassName(handle, classBuilder, classBuilder.Capacity);

                WindowsApi.GetWindowThreadProcessId(handle, out uint processId);
                WindowsApi.GetWindowRect(handle, out var rect);

                return new WindowInfo
                {
                    Handle = handle,
                    Title = titleBuilder.ToString(),
                    ClassName = classBuilder.ToString(),
                    ProcessId = processId,
                    IsVisible = WindowsApi.IsWindowVisible(handle),
                    IsMinimized = WindowsApi.IsIconic(handle),
                    Bounds = new WindowBounds
                    {
                        X = rect.Left,
                        Y = rect.Top,
                        Width = rect.Width,
                        Height = rect.Height
                    },
                    CanResize = true
                };
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(WindowDiscoveryService), $"GetWindowInfo failed: {ex.Message}");
                return null;
            }
        }

        private static bool IsCandidate(WindowInfo info)
        {
            if (ExcludedClassNames.Contains(info.ClassName))
            {
                return false;
            }

            if (ExcludedTitles.Contains(info.Title))
            {
                return false;
            }

            if (!info.IsVisible)
            {
                return false;
            }

            if (info.Bounds.Width < 50 || info.Bounds.Height < 50)
            {
                return false;
            }

            long exStyle = WindowsApi.GetWindowLongPtr(info.Handle, WindowsApi.GWL_EXSTYLE);
            if ((exStyle & WindowsApi.WS_EX_TOOLWINDOW) != 0)
            {
                return false;
            }

            try
            {
                int result = WindowsApi.DwmGetWindowAttribute(info.Handle, WindowsApi.DWMWA_CLOAKED, out bool isCloaked, sizeof(bool));
                if (result == 0 && isCloaked)
                {
                    return false;
                }
            }
            catch
            {
                // Ignore DWM errors.
            }

            try
            {
                var currentProcess = Process.GetCurrentProcess();
                if (info.ProcessId == currentProcess.Id)
                {
                    return false;
                }
            }
            catch
            {
                // Cannot inspect process; allow window.
            }

            var title = info.Title.ToLowerInvariant();
            if (title.Contains("task view") || title.Contains("cortana"))
            {
                return false;
            }

            if (title.Contains("search") && info.ClassName.Contains("Windows.UI", StringComparison.OrdinalIgnoreCase))
            {
                return false;
            }

            return true;
        }
    }
}
