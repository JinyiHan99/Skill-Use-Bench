using System;

namespace ResizeMe.Models
{
    /// <summary>
    /// Represents the result of a window resize operation
    /// </summary>
    public class ResizeResult
    {
        /// <summary>
        /// Gets or sets whether the resize operation was successful
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// Gets or sets the error message if the operation failed
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Gets or sets the error code from the Windows API (if applicable)
        /// </summary>
        public uint? ErrorCode { get; set; }

        /// <summary>
        /// Gets or sets the window that was being resized
        /// </summary>
        public WindowInfo? TargetWindow { get; set; }

        /// <summary>
        /// Gets or sets the requested size
        /// </summary>
        public WindowSize? RequestedSize { get; set; }

        /// <summary>
        /// Gets or sets the actual size after the operation
        /// </summary>
        public WindowSize? ActualSize { get; set; }

        /// <summary>
        /// Gets or sets whether the window was restored from a minimized/maximized state
        /// </summary>
        public bool WindowStateChanged { get; set; }

        /// <summary>
        /// Gets a display-friendly message about the resize operation
        /// </summary>
        public string DisplayMessage
        {
            get
            {
                if (Success)
                {
                    var target = TargetWindow?.DisplayText ?? "Window";
                    var size = RequestedSize?.ToString() ?? "unknown size";
                    return $"Successfully resized {target} to {size}";
                }
                else
                {
                    return ErrorMessage ?? "Resize operation failed";
                }
            }
        }

        /// <summary>
        /// Creates a successful resize result
        /// </summary>
        /// <param name="targetWindow">The window that was resized</param>
        /// <param name="requestedSize">The requested size</param>
        /// <param name="actualSize">The actual resulting size</param>
        /// <param name="windowStateChanged">Whether window state was changed</param>
        /// <returns>ResizeResult indicating success</returns>
        public static ResizeResult CreateSuccess(WindowInfo targetWindow, WindowSize requestedSize, WindowSize actualSize, bool windowStateChanged = false)
        {
            return new ResizeResult
            {
                Success = true,
                TargetWindow = targetWindow,
                RequestedSize = requestedSize,
                ActualSize = actualSize,
                WindowStateChanged = windowStateChanged
            };
        }

        /// <summary>
        /// Creates a failed resize result
        /// </summary>
        /// <param name="targetWindow">The window that failed to resize</param>
        /// <param name="requestedSize">The requested size</param>
        /// <param name="errorMessage">Description of the error</param>
        /// <param name="errorCode">Windows API error code if applicable</param>
        /// <returns>ResizeResult indicating failure</returns>
        public static ResizeResult CreateFailure(WindowInfo targetWindow, WindowSize requestedSize, string errorMessage, uint? errorCode = null)
        {
            return new ResizeResult
            {
                Success = false,
                TargetWindow = targetWindow,
                RequestedSize = requestedSize,
                ErrorMessage = errorMessage,
                ErrorCode = errorCode
            };
        }

        /// <summary>
        /// Returns a string representation of the resize result
        /// </summary>
        public override string ToString()
        {
            return DisplayMessage;
        }
    }

    /// <summary>
    /// Represents a window size with width and height
    /// </summary>
    public class WindowSize
    {
        /// <summary>
        /// Gets or sets the width of the window
        /// </summary>
        public int Width { get; set; }

        /// <summary>
        /// Gets or sets the height of the window
        /// </summary>
        public int Height { get; set; }

        /// <summary>
        /// Initializes a new instance of WindowSize
        /// </summary>
        /// <param name="width">Width of the window</param>
        /// <param name="height">Height of the window</param>
        public WindowSize(int width, int height)
        {
            Width = width;
            Height = height;
        }

        /// <summary>
        /// Gets whether this is a valid window size
        /// </summary>
        public bool IsValid => Width > 0 && Height > 0;

        /// <summary>
        /// Returns a string representation of the window size
        /// </summary>
        public override string ToString()
        {
            return $"{Width}x{Height}";
        }

        /// <summary>
        /// Determines whether the specified object is equal to this window size
        /// </summary>
        /// <param name="obj">Object to compare</param>
        /// <returns>True if objects are equal</returns>
        public override bool Equals(object? obj)
        {
            return obj is WindowSize other && Width == other.Width && Height == other.Height;
        }

        /// <summary>
        /// Returns the hash code for this window size
        /// </summary>
        /// <returns>Hash code based on width and height</returns>
        public override int GetHashCode()
        {
            return HashCode.Combine(Width, Height);
        }
    }
}
