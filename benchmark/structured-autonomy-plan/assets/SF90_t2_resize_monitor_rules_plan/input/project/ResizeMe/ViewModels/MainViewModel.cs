using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Input;
using Microsoft.UI.Dispatching;
using ResizeMe.Features.MainLayout;
using ResizeMe.Features.Settings;
using ResizeMe.Features.WindowManagement;
using ResizeMe.Models;
using ResizeMe.Shared.Config;
using ResizeMe.Shared.Logging;

namespace ResizeMe.ViewModels
{
    public sealed class MainViewModel : ViewModelBase
    {
        private readonly PresetStorage _presets;
        private readonly WindowDiscoveryService _windowDiscovery;
        private readonly WindowResizeService _windowResizer;
        private readonly DispatcherQueue _dispatcherQueue;
        private readonly string _logger = nameof(MainViewModel);

        private bool _isVisible;
        private bool _centerOnResize;
        private WindowInfo? _selectedWindow;
        private string? _status;
        private ObservableCollection<PresetSize> _presetCollection = new();

        public ICommand ResizeCommand { get; }

        public ObservableCollection<PresetSize> Presets
        {
            get => _presetCollection;
            private set => SetProperty(ref _presetCollection, value);
        }

        public bool IsVisible
        {
            get => _isVisible;
            private set => SetProperty(ref _isVisible, value);
        }

        public bool CenterOnResize
        {
            get => _centerOnResize;
            set
            {
                if (SetProperty(ref _centerOnResize, value))
                {
                    UserSettingsStore.CenterOnResize = value;
                }
            }
        }

        public WindowInfo? SelectedWindow
        {
            get => _selectedWindow;
            private set => SetProperty(ref _selectedWindow, value);
        }

        public string? Status
        {
            get => _status;
            private set => SetProperty(ref _status, value);
        }

        internal MainViewModel(
            DispatcherQueue dispatcherQueue,
            PresetStorage presets,
            WindowDiscoveryService windowDiscovery,
            WindowResizeService windowResizer)
        {
            _dispatcherQueue = dispatcherQueue;
            _presets = presets;
            _windowDiscovery = windowDiscovery;
            _windowResizer = windowResizer;
            _centerOnResize = UserSettingsStore.CenterOnResize;
            ResizeCommand = new RelayCommand<PresetSize>(async (preset) => await ResizeSelectedWindowAsync(preset));
        }

        public async Task InitializeAsync()
        {
            await _presets.LoadAsync();
            RefreshPresetCollection();
            RefreshWindowSnapshot();
        }

        public void RefreshWindowSnapshot()
        {
            // Only refresh if we don't already have a captured target window
            // This preserves the window captured before ResizeMe was shown
            if (SelectedWindow == null)
            {
                CaptureTargetWindow();
            }
        }

        public void CaptureTargetWindow()
        {
            // Capture the current foreground window as the resize target
            var activeWindow = _windowDiscovery.GetActiveWindow();
            if (activeWindow != null)
            {
                SelectedWindow = activeWindow;
            }
            else
            {
                // Fall back to first available window if no active window found
                var windows = _windowDiscovery.GetWindows().ToList();
                SelectedWindow = windows.FirstOrDefault();
            }
        }

        public async Task ReloadPresetsAsync()
        {
            await _presets.LoadAsync(true);
            RefreshPresetCollection();
        }

        public async Task ResizeSelectedWindowAsync(PresetSize preset)
        {
            if (preset == null)
            {
                return;
            }

            var target = SelectedWindow;
            if (target == null)
            {
                Status = "No window";
                return;
            }

            Status = $"Resizing {preset.Name}...";
            var result = _windowResizer.Resize(target, preset.Width, preset.Height);
            if (result.Success)
            {
                if (CenterOnResize)
                {
                    WindowPositionService.CenterExternalWindow(target);
                }
                _windowResizer.Activate(target);
                Status = $"Done {preset.Name}";
                await Task.Delay(500);
                _dispatcherQueue.TryEnqueue(() => IsVisible = false);
            }
            else
            {
                Status = result.ErrorMessage ?? "Resize failed";
                AppLog.Warn(_logger, Status);
            }
        }

        public void Show()
        {
            IsVisible = true;
            // Don't call RefreshWindowSnapshot here - the target window
            // should already be captured by CaptureTargetWindow() before Show() is called
        }

        public void Hide()
        {
            IsVisible = false;
            // Clear the selected window when hiding so the next show captures fresh
            SelectedWindow = null;
        }

        private void RefreshPresetCollection()
        {
            _dispatcherQueue.TryEnqueue(() =>
            {
                Presets = new ObservableCollection<PresetSize>(_presets.Presets);
            });
        }
    }
}
