using System;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;

namespace ResizeMe.Native
{
    public interface INativeWindowService
    {
        IntPtr EnsureWindowHandle(Window window);
        AppWindow? GetAppWindow(Window window);
        void ConfigureShell(AppWindow appWindow, string title, string iconPath, int width, int height);
        void ShowWindow(IntPtr hwnd);
        void HideWindow(IntPtr hwnd);
        void RestoreWindow(IntPtr hwnd);
        void FocusWindow(IntPtr hwnd);
    }
}
