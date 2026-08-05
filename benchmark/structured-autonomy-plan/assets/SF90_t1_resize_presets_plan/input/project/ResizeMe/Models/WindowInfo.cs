using System;

namespace ResizeMe.Models
{
    /// <summary>
    /// Represents information about a window that can be resized
    /// </summary>
    public class WindowInfo
    {
        /// <summary>
        /// Gets or sets the window handle (HWND)
        /// </summary>
        public IntPtr Handle { get; set; }

        /// <summary>
        /// Gets or sets the window title text
        /// </summary>
        public string Title { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the window class name
        /// </summary>
        public string ClassName { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the process ID that owns this window
        /// </summary>
        public uint ProcessId { get; set; }

        /// <summary>
        /// Gets or sets whether the window is currently visible
        /// </summary>
        public bool IsVisible { get; set; }

        /// <summary>
        /// Gets or sets whether the window is currently minimized
        /// </summary>
        public bool IsMinimized { get; set; }

        /// <summary>
        /// Gets or sets the current window bounds (snapshot captured at the time of enumeration)
        /// </summary>
        public WindowBounds Bounds { get; set; } = new();

        /// <summary>
        /// Gets or sets whether this window can be resized
        /// </summary>
        public bool CanResize { get; set; } = true;

        /// <summary>
        /// Gets a display-friendly string representation of the window
        /// </summary>
        public string DisplayText => string.IsNullOrWhiteSpace(Title) ? $"<Untitled> ({ClassName})" : Title;

        /// <summary>
        /// Returns a string representation of this window info
        /// </summary>
        public override string ToString()
        {
            return $"{DisplayText} (HWND: {Handle:X8}, PID: {ProcessId})";
        }

        /// <summary>
        /// Determines whether the specified object is equal to this window info
        /// </summary>
        /// <param name="obj">Object to compare</param>
        /// <returns>True if objects are equal</returns>
        public override bool Equals(object? obj)
        {
            return obj is WindowInfo other && Handle == other.Handle;
        }

        /// <summary>
        /// Returns the hash code for this window info
        /// </summary>
        /// <returns>Hash code based on window handle</returns>
        public override int GetHashCode()
        {
            return Handle.GetHashCode();
        }
    }

    /// <summary>
    /// Represents the position and size of a window
    /// </summary>
    public class WindowBounds
    {
        /// <summary>
        /// Gets or sets the X coordinate of the window's left edge
        /// </summary>
        public int X { get; set; }

        /// <summary>
        /// Gets or sets the Y coordinate of the window's top edge
        /// </summary>
        public int Y { get; set; }

        /// <summary>
        /// Gets or sets the width of the window
        /// </summary>
        public int Width { get; set; }

        /// <summary>
        /// Gets or sets the height of the window
        /// </summary>
        public int Height { get; set; }

        /// <summary>
        /// Returns a string representation of the window bounds
        /// </summary>
        public override string ToString()
        {
            return $"{Width}x{Height} at ({X}, {Y})";
        }
    }
}
