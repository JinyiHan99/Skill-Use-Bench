using System;
using System.Threading.Tasks;

namespace ResizeMe.Native
{
    public interface IWindowMessageHandler
    {
        IntPtr HandleWindowMessage(IntPtr hwnd, uint msg, IntPtr wParam, IntPtr lParam);
    }

    public interface IWindowSubclassService : IDisposable
    {
        Task<bool> AttachAsync(IntPtr hwnd, IWindowMessageHandler handler);
        void Detach();
    }
}
