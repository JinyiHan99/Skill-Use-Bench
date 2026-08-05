using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Windows.Storage;
using ResizeMe.Models;
using ResizeMe.Shared.Config;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Features.Settings
{
    internal sealed class PresetStorage
    {
        private const string FileName = "presets.json";
        private readonly object _syncRoot = new();
        private readonly List<PresetSize> _presets = new();
        private bool _loaded;

        public bool IsLoaded => _loaded;

        public IReadOnlyList<PresetSize> Presets
        {
            get
            {
                lock (_syncRoot)
                {
                    return _presets.ToList();
                }
            }
        }

        public async Task LoadAsync(bool forceReload = false)
        {
            if (_loaded && !forceReload)
            {
                return;
            }

            try
            {
                var folder = ApplicationData.Current.LocalFolder;
                StorageFile? file = null;
                try
                {
                    file = await folder.GetFileAsync(FileName);
                }
                catch
                {
                    // File missing on first run.
                }

                if (file == null)
                {
                    SeedDefaults();
                    await SaveAsync();
                    _loaded = true;
                    return;
                }

                var json = await FileIO.ReadTextAsync(file);
                var data = JsonSerializer.Deserialize(json, AppJsonContext.Default.ListPresetSize) ?? new List<PresetSize>();
                lock (_syncRoot)
                {
                    _presets.Clear();
                    _presets.AddRange(data.Where(p => p.IsValid));
                    if (_presets.Count == 0)
                    {
                        SeedDefaults();
                    }
                }
                _loaded = true;
            }
            catch (Exception ex)
            {
                AppLog.Error(nameof(PresetStorage), "Load failed", ex);
                lock (_syncRoot)
                {
                    _presets.Clear();
                    SeedDefaults();
                }
                _loaded = true;
            }
        }

        public async Task<bool> AddAsync(PresetSize preset)
        {
            if (preset == null || !preset.IsValid)
            {
                return false;
            }

            bool added = false;
            lock (_syncRoot)
            {
                if (_presets.Any(p => p.Name.Equals(preset.Name, StringComparison.OrdinalIgnoreCase)))
                {
                    return false;
                }
                _presets.Add(preset);
                added = true;
            }

            if (added)
            {
                await SaveAsync();
            }
            return added;
        }

        public async Task<bool> RemoveAsync(string name)
        {
            if (string.IsNullOrWhiteSpace(name))
            {
                return false;
            }

            bool removed;
            lock (_syncRoot)
            {
                var match = _presets.FirstOrDefault(p => p.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
                removed = match != null && _presets.Remove(match);
            }

            if (removed)
            {
                await SaveAsync();
            }
            return removed;
        }

        public async Task ResetAsync()
        {
            lock (_syncRoot)
            {
                _presets.Clear();
                SeedDefaults();
            }
            await SaveAsync();
        }

        private async Task SaveAsync()
        {
            List<PresetSize> snapshot;
            lock (_syncRoot)
            {
                snapshot = _presets.ToList();
            }

            var folder = ApplicationData.Current.LocalFolder;
            var file = await folder.CreateFileAsync(FileName, CreationCollisionOption.OpenIfExists);
            var json = JsonSerializer.Serialize(snapshot, AppJsonContext.Default.ListPresetSize);
            await FileIO.WriteTextAsync(file, json);
        }

        private void SeedDefaults()
        {
            _presets.AddRange(new[]
            {
                new PresetSize { Name = "HD", Width = 1280, Height = 720 },
                new PresetSize { Name = "Full HD", Width = 1920, Height = 1080 },
                new PresetSize { Name = "Laptop", Width = 1366, Height = 768 },
                new PresetSize { Name = "Classic", Width = 1024, Height = 768 }
            });
        }
    }
}
