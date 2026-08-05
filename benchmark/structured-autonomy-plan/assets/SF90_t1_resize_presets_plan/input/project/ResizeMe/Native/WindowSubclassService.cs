using System;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Native
{
    public sealed class WindowSubclassService : IWindowSubclassService
    {
        private readonly string _logger = nameof(WindowSubclassService);
        private IWindowMessageHandler? _handler;
        private WindowsApi.SubClassProc? _callback;
        private IntPtr _hwnd;
        private IntPtr _subclassId = new(1001);
        private bool _attached;

        public async Task<bool> AttachAsync(IntPtr hwnd, IWindowMessageHandler handler)
        {
            ArgumentNullException.ThrowIfNull(handler);
            if (hwnd == IntPtr.Zero)
            {
                throw new ArgumentException("HWND must be valid", nameof(hwnd));
            }
            if (_attached)
            {
                return true;
            }

            _handler = handler;
            _hwnd = hwnd;
            _callback = HandleMessage;
            _attached = WinApiSubClass.SetWindowSubclass(hwnd, _callback, _subclassId, IntPtr.Zero);
            if (!_attached)
            {
                AppLog.Warn(_logger, "SetWindowSubclass returned false.");
            }
            return await Task.FromResult(_attached);
        }

        public void Detach()
        {
            if (!_attached || _callback == null || _hwnd == IntPtr.Zero)
            {
                return;
            }

            WinApiSubClass.RemoveWindowSubclass(_hwnd, _callback, _subclassId);
            _attached = false;
            _handler = null;
            _callback = null;
            _hwnd = IntPtr.Zero;
        }

        public void Dispose()
        {
            Detach();
            GC.SuppressFinalize(this);
        }

        private IntPtr HandleMessage(IntPtr hwnd, uint msg, IntPtr wParam, IntPtr lParam, IntPtr subclassId, IntPtr refData)
        {
            if (_handler != null)
            {
                var handled = _handler.HandleWindowMessage(hwnd, msg, wParam, lParam);
                if (handled != IntPtr.Zero)
                {
                    return handled;
                }
            }

            return WinApiSubClass.DefSubclassProc(hwnd, msg, wParam, lParam);
        }

        private static class WinApiSubClass
        {
            [DllImport("comctl32.dll", ExactSpelling = true)]
            public static extern bool SetWindowSubclass(IntPtr hWnd, WindowsApi.SubClassProc pfnSubclass, IntPtr uIdSubclass, IntPtr dwRefData);

            [DllImport("comctl32.dll", ExactSpelling = true)]
            public static extern bool RemoveWindowSubclass(IntPtr hWnd, WindowsApi.SubClassProc pfnSubclass, IntPtr uIdSubclass);

            [DllImport("comctl32.dll", ExactSpelling = true)]
            public static extern IntPtr DefSubclassProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
        }
    }
}
