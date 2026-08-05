using System;
using Windows.Storage;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Shared.Config
{
    internal static class UserSettingsStore
    {
        private const string CenterKey = "CenterOnResize";
        private const string FirstRunKey = "FirstRunCompleted";
        private const string FirstMinimizeKey = "FirstMinimizeNotificationShown";
        private const string HotKeyModifiersKey = "HotKeyModifiers";
        private const string HotKeyCodeKey = "HotKeyKey";

        private static ApplicationDataContainer Settings => ApplicationData.Current.LocalSettings;

        public static bool CenterOnResize
        {
            get => Read(CenterKey, false);
            set => Write(CenterKey, value);
        }

        public static bool FirstRunCompleted
        {
            get => Read(FirstRunKey, false);
            set => Write(FirstRunKey, value);
        }

        public static bool FirstMinimizeNotificationShown
        {
            get => Read(FirstMinimizeKey, false);
            set => Write(FirstMinimizeKey, value);
        }

        public static string HotKeyModifiers
        {
            get
            {
                var value = Read(HotKeyModifiersKey, "CTRL+WIN");
                return string.IsNullOrWhiteSpace(value) ? "CTRL+WIN" : value.ToUpperInvariant();
            }
            set
            {
                var normalized = string.IsNullOrWhiteSpace(value) ? "CTRL+WIN" : value.ToUpperInvariant();
                Write(HotKeyModifiersKey, normalized);
            }
        }

        public static string HotKeyCode
        {
            get
            {
                var value = Read(HotKeyCodeKey, "R");
                return string.IsNullOrWhiteSpace(value) ? "R" : value.ToUpperInvariant();
            }
            set
            {
                var normalized = string.IsNullOrWhiteSpace(value) ? "R" : value.ToUpperInvariant();
                Write(HotKeyCodeKey, normalized);
            }
        }

        private static T Read<T>(string key, T fallback)
        {
            try
            {
                if (Settings.Values.TryGetValue(key, out var raw) && raw is T typed)
                {
                    return typed;
                }
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(UserSettingsStore), $"Read failure for {key}: {ex.Message}");
            }
            return fallback;
        }

        private static void Write<T>(string key, T value)
        {
            try
            {
                Settings.Values[key] = value;
            }
            catch (Exception ex)
            {
                AppLog.Warn(nameof(UserSettingsStore), $"Write failure for {key}: {ex.Message}");
            }
        }
    }
}
