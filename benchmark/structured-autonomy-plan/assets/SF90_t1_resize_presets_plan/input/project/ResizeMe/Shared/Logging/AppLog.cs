using System;
using System.Diagnostics;

namespace ResizeMe.Shared.Logging
{
    internal static class AppLog
    {
        private static readonly object SyncRoot = new();

        public static void Info(string area, string message) => Write("INFO", area, message);
        public static void Warn(string area, string message) => Write("WARN", area, message);
        public static void Error(string area, string message, Exception? ex = null)
        {
            var detail = ex == null ? message : $"{message} :: {ex.Message}";
            Write("ERROR", area, detail);
        }

        private static void Write(string level, string area, string message)
        {
            lock (SyncRoot)
            {
                Debug.WriteLine($"{DateTime.UtcNow:O} [{level}] {area} :: {message}");
            }
        }
    }
}
