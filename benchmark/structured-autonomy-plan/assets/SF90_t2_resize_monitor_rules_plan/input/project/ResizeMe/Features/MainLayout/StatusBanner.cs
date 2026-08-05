using System;
using System.Threading.Tasks;
using Microsoft.UI.Xaml.Controls;

namespace ResizeMe.Features.MainLayout
{
    internal sealed class StatusBanner
    {
        private readonly TextBlock _target;
        private readonly TimeSpan _defaultDelay = TimeSpan.FromSeconds(3);

        public StatusBanner(TextBlock target)
        {
            _target = target;
        }

        public void Show(string text, TimeSpan? clearAfter = null)
        {
            if (_target.DispatcherQueue == null)
            {
                _target.Text = text;
            }
            else
            {
                _target.DispatcherQueue.TryEnqueue(() => _target.Text = text);
            }

            var delay = clearAfter ?? _defaultDelay;
            if (delay > TimeSpan.Zero)
            {
                _ = ClearAsync(delay);
            }
        }

        private async Task ClearAsync(TimeSpan delay)
        {
            await Task.Delay(delay);
            if (_target.DispatcherQueue != null)
            {
                _target.DispatcherQueue.TryEnqueue(() => _target.Text = "Ready");
            }
            else
            {
                _target.Text = "Ready";
            }
        }
    }
}
