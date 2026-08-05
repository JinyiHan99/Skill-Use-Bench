using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using ResizeMe.Native;
using ResizeMe.Shared.Config;
using ResizeMe.Shared.Logging;

namespace ResizeMe.Features.SystemIntegration
{
    public sealed class HotKeyService : IDisposable
    {
        private const int HotKeyId = 9000;
        private readonly IntPtr _windowHandle;
        private bool _registered;
        private bool _disposed;

        private static readonly HashSet<string> ReservedHotkeys = new(StringComparer.OrdinalIgnoreCase)
        {
            "ALT+TAB", "ALT+F4", "CTRL+ALT+DELETE", "WIN+D", "WIN+L", "WIN+R",
            "WIN+E", "WIN+V", "WIN+M", "WIN+SHIFT+S"
        };

        public HotKeyService(IntPtr windowHandle)
        {
            _windowHandle = windowHandle;
        }

        public event EventHandler? HotKeyTriggered;

        public bool TryRegister()
        {
            if (_windowHandle == IntPtr.Zero)
            {
                AppLog.Warn(nameof(HotKeyService), "Cannot register without window handle");
                return false;
            }

            if (_registered)
            {
                Unregister();
            }

            var (modifierMask, keyCode) = BuildHotKey();
            bool success = WindowsApi.RegisterHotKey(_windowHandle, HotKeyId, modifierMask, keyCode);
            if (success)
            {
                _registered = true;
                AppLog.Info(nameof(HotKeyService), $"Registered {UserSettingsStore.HotKeyModifiers}+{UserSettingsStore.HotKeyCode}");
            }
            else
            {
                var error = Marshal.GetLastWin32Error();
                AppLog.Warn(nameof(HotKeyService), $"RegisterHotKey failed: {error}");
            }

            return success;
        }

        public void ReRegister()
        {
            TryRegister();
        }

        public bool HandleMessage(uint msg, IntPtr wParam, IntPtr lParam)
        {
            if (msg == WindowsApi.WM_HOTKEY && wParam.ToInt32() == HotKeyId)
            {
                HotKeyTriggered?.Invoke(this, EventArgs.Empty);
                return true;
            }
            return false;
        }

        public static bool IsReserved(string modifiers, string key)
        {
            var normalized = Normalize(modifiers, key);
            return ReservedHotkeys.Contains(normalized);
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        private void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (_registered)
                {
                    Unregister();
                }
                _disposed = true;
            }
        }

        private void Unregister()
        {
            if (_windowHandle == IntPtr.Zero || !_registered)
            {
                return;
            }

            if (WindowsApi.UnregisterHotKey(_windowHandle, HotKeyId))
            {
                _registered = false;
            }
            else
            {
                var error = Marshal.GetLastWin32Error();
                AppLog.Warn(nameof(HotKeyService), $"UnregisterHotKey failed: {error}");
            }
        }

        private static (uint modifiers, uint key) BuildHotKey()
        {
            uint modifiers = 0;
            var parts = UserSettingsStore.HotKeyModifiers
                .Split('+', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .Select(p => p.ToUpperInvariant());

            foreach (var p in parts)
            {
                modifiers |= p switch
                {
                    "CTRL" => (uint)WindowsApi.MOD_CONTROL,
                    "ALT" => (uint)WindowsApi.MOD_ALT,
                    "SHIFT" => (uint)WindowsApi.MOD_SHIFT,
                    "WIN" => (uint)WindowsApi.MOD_WIN,
                    _ => 0u
                };
            }

            if (modifiers == 0)
            {
                modifiers = WindowsApi.MOD_WIN;
            }

            uint keyCode = TranslateKey(UserSettingsStore.HotKeyCode);
            return (modifiers, keyCode);
        }

        private static uint TranslateKey(string token)
        {
            var value = token.ToUpperInvariant();
            if (value.StartsWith("F") && int.TryParse(value[1..], out int fNum) && fNum is >= 1 and <= 24)
            {
                return (uint)(0x70 + (fNum - 1));
            }

            if (value.Length == 1)
            {
                char c = value[0];
                if (c is >= '0' and <= '9' or >= 'A' and <= 'Z')
                {
                    return (uint)c;
                }
            }

            return value switch
            {
                "+" => WindowsApi.VK_OEM_PLUS,
                "," => WindowsApi.VK_OEM_COMMA,
                "-" => WindowsApi.VK_OEM_MINUS,
                "." => WindowsApi.VK_OEM_PERIOD,
                _ => WindowsApi.VK_F12
            };
        }

        private static string Normalize(string modifiers, string key)
        {
            var order = new[] { "CTRL", "ALT", "SHIFT", "WIN" };
            var modifierTokens = modifiers
                .Split('+', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .Select(m => m.ToUpperInvariant())
                .Where(order.Contains)
                .Distinct()
                .OrderBy(m => Array.IndexOf(order, m));

            var keyToken = key.ToUpperInvariant();
            return string.Join('+', modifierTokens.Append(keyToken));
        }
    }
}
