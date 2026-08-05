using System;
using ResizeMe.Features.SystemIntegration;

namespace ResizeMe.Native
{
    public class AppWindowMessageHandler : IWindowMessageHandler
    {
        private readonly Action _onClose;
        private readonly TrayIconManager? _trayManager;
        private readonly HotKeyService? _hotKeyService;
        private readonly Action _onTrayShow;

        private const int WM_SYSCOMMAND = 0x0112;
        private const int SC_CLOSE = 0xF060;
        private const int WM_RBUTTONUP = 0x0205;
        private const int WM_LBUTTONUP = 0x0202;

        public AppWindowMessageHandler(
            Action onClose,
            TrayIconManager? trayManager,
            HotKeyService? hotKeyService,
            Action onTrayShow)
        {
            _onClose = onClose;
            _trayManager = trayManager;
            _hotKeyService = hotKeyService;
            _onTrayShow = onTrayShow;
        }

        public IntPtr HandleWindowMessage(IntPtr hwnd, uint msg, IntPtr wParam, IntPtr lParam)
        {
            if (msg == WM_SYSCOMMAND && wParam.ToInt32() == SC_CLOSE)
            {
                _onClose();
                return new IntPtr(1);
            }

            if (_trayManager != null && msg == _trayManager.CallbackMessage)
            {
                int param = lParam.ToInt32();
                if (param == WM_RBUTTONUP)
                {
                    _trayManager.ShowContextMenu();
                    return new IntPtr(1);
                }
                if (param == WM_LBUTTONUP)
                {
                    _onTrayShow();
                    return new IntPtr(1);
                }
            }

            if (_hotKeyService != null && _hotKeyService.HandleMessage(msg, wParam, lParam))
            {
                return new IntPtr(1);
            }

            return IntPtr.Zero;
        }
    }
}
