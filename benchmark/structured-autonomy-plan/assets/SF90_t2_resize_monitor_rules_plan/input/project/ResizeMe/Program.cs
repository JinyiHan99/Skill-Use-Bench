using System;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;

namespace ResizeMe
{
    public static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            // Required for SingleFile framework-dependent deployment
            Environment.SetEnvironmentVariable("MICROSOFT_WINDOWSAPPRUNTIME_BASE_DIRECTORY", AppContext.BaseDirectory);

            WinRT.ComWrappersSupport.InitializeComWrappers();

            Application.Start((p) =>
            {
                var context = new DispatcherQueueSynchronizationContext(DispatcherQueue.GetForCurrentThread());
                System.Threading.SynchronizationContext.SetSynchronizationContext(context);
                new App();
            });
        }
    }
}
