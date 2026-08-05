using System;
using System.Runtime.InteropServices;
using System.Text;

namespace ResizeMe.Native
{
    /// <summary>
    /// P/Invoke declarations for Windows API functions needed for global hotkey registration
    /// </summary>
    internal static class WindowsApi
    {
        // Constants for hotkey registration
        public const int WM_HOTKEY = 0x0312;
        public const int MOD_ALT = 0x0001;
        public const int MOD_CONTROL = 0x0002;
        public const int MOD_SHIFT = 0x0004;
        public const int MOD_WIN = 0x0008;

        // Virtual key codes
        public const int VK_R = 0x52;
        public const int VK_F12 = 0x7B; // F12 virtual key code
        // OEM virtual keys (common punctuation) - used for keys like +/- and punctuation
        public const int VK_OEM_PLUS = 0xBB; // '+' key (US)
        public const int VK_OEM_COMMA = 0xBC; // ',' key
        public const int VK_OEM_MINUS = 0xBD; // '-' key
        public const int VK_OEM_PERIOD = 0xBE; // '.' key

        /// <summary>
        /// Registers a hotkey with the system
        /// </summary>
        /// <param name="hWnd">Handle to window that will receive WM_HOTKEY messages</param>
        /// <param name="id">Application-defined identifier for the hotkey</param>
        /// <param name="fsModifiers">Modifier keys (MOD_ALT, MOD_CONTROL, etc.)</param>
        /// <param name="vk">Virtual key code</param>
        /// <returns>True if successful, false if failed</returns>
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        /// <summary>
        /// Unregisters a hotkey that was registered by RegisterHotKey
        /// </summary>
        /// <param name="hWnd">Handle to window that registered the hotkey</param>
        /// <param name="id">Application-defined identifier for the hotkey</param>
        /// <returns>True if successful, false if failed</returns>
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        // Additional constants for window enumeration
        public const int GWL_STYLE = -16;
        public const int GWL_EXSTYLE = -20;
        public const uint WS_VISIBLE = 0x10000000;
        public const uint WS_MINIMIZE = 0x20000000;
        public const uint WS_DISABLED = 0x08000000;
        public const uint WS_EX_TOOLWINDOW = 0x00000080;
        public const uint WS_EX_APPWINDOW = 0x00040000;
        public const int DWMWA_CLOAKED = 14;

        /// <summary>
        /// Changes the size, position, and Z order of a child, pop-up, or top-level window
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="hWndInsertAfter">Handle to the window to precede this window in Z order</param>
        /// <param name="x">New position of the left side of the window</param>
        /// <param name="y">New position of the top of the window</param>
        /// <param name="cx">New width of the window</param>
        /// <param name="cy">New height of the window</param>
        /// <param name="flags">Window sizing and positioning flags</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int x, int y, int cx, int cy, uint flags);

        /// <summary>
        /// Sets the specified window's show state
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="nCmdShow">Controls how the window is to be shown</param>
        /// <returns>True if the window was previously visible, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        /// <summary>
        /// Brings the specified window to the top of the Z order
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool BringWindowToTop(IntPtr hWnd);

        /// <summary>
        /// Activates a window and displays it in its current size and position
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool SetForegroundWindow(IntPtr hWnd);

        /// <summary>
        /// Retrieves the handle of the foreground window
        /// </summary>
        /// <returns>Handle to the foreground window</returns>
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();

        /// <summary>
        /// Determines whether the specified window is maximized
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <returns>True if the window is maximized, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool IsZoomed(IntPtr hWnd);

        /// <summary>
        /// Retrieves information about the specified window's placement
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="lpwndpl">Pointer to structure that receives placement information</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GetWindowPlacement(IntPtr hWnd, ref WINDOWPLACEMENT lpwndpl);

        /// <summary>
        /// Sets the show state and the restored, minimized, and maximized positions of the specified window
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="lpwndpl">Pointer to structure that specifies the new position and show state</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool SetWindowPlacement(IntPtr hWnd, ref WINDOWPLACEMENT lpwndpl);

        /// <summary>
        /// Structure containing information about the placement of a window on the screen
        /// </summary>
        [StructLayout(LayoutKind.Sequential)]
        public struct WINDOWPLACEMENT
        {
            public int length;
            public int flags;
            public int showCmd;
            public POINT ptMinPosition;
            public POINT ptMaxPosition;
            public RECT rcNormalPosition;

            public static WINDOWPLACEMENT Default
            {
                get
                {
                    var result = new WINDOWPLACEMENT();
                    result.length = Marshal.SizeOf(result);
                    return result;
                }
            }
        }

        /// <summary>
        /// Structure representing a point
        /// </summary>
        [StructLayout(LayoutKind.Sequential)]
        public struct POINT
        {
            public int X;
            public int Y;

            public POINT(int x, int y)
            {
                X = x;
                Y = y;
            }
        }

        /// <summary>
        /// Retrieves the DWM window attribute
        /// </summary>
        /// <param name="hwnd">Handle to the window</param>
        /// <param name="dwAttribute">Attribute to retrieve</param>
        /// <param name="pvAttribute">Pointer to buffer to receive attribute</param>
        /// <param name="cbAttribute">Size of buffer</param>
        /// <returns>S_OK if successful</returns>
        [DllImport("dwmapi.dll")]
        public static extern int DwmGetWindowAttribute(IntPtr hwnd, int dwAttribute, out bool pvAttribute, int cbAttribute);

        /// <summary>
        /// Structure representing a rectangle
        /// </summary>
        [StructLayout(LayoutKind.Sequential)]
        public struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;

            public int Width => Right - Left;
            public int Height => Bottom - Top;
        }

        // Window positioning constants
        public const uint SWP_NOSIZE = 0x0001;
        public const uint SWP_NOMOVE = 0x0002;
        public const uint SWP_NOZORDER = 0x0004;
        public const uint SWP_NOREDRAW = 0x0008;
        public const uint SWP_NOACTIVATE = 0x0010;
        public const uint SWP_FRAMECHANGED = 0x0020;
        public const uint SWP_SHOWWINDOW = 0x0040;
        public const uint SWP_HIDEWINDOW = 0x0080;
        public const uint SWP_NOCOPYBITS = 0x0100;
        public const uint SWP_NOOWNERZORDER = 0x0200;
        public const uint SWP_NOSENDCHANGING = 0x0400;

        // Special HWND values for SetWindowPos
        public static readonly IntPtr HWND_TOP = new IntPtr(0);
        public static readonly IntPtr HWND_BOTTOM = new IntPtr(1);
        public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
        public static readonly IntPtr HWND_NOTOPMOST = new IntPtr(-2);

        // ShowWindow constants
        public const int SW_HIDE = 0;
        public const int SW_SHOWNORMAL = 1;
        public const int SW_SHOWMINIMIZED = 2;
        public const int SW_SHOWMAXIMIZED = 3;
        public const int SW_SHOWNOACTIVATE = 4;
        public const int SW_SHOW = 5;
        public const int SW_MINIMIZE = 6;
        public const int SW_SHOWMINNOACTIVE = 7;
        public const int SW_SHOWNA = 8;
        public const int SW_RESTORE = 9;

        // Delegate for EnumWindows callback
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        // Delegate used for win32 SetWindowSubclass/DefSubclassProc callbacks
        public delegate IntPtr SubClassProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam, IntPtr uIdSubclass, IntPtr dwRefData);

        /// <summary>
        /// Enumerates all top-level windows on the desktop
        /// </summary>
        /// <param name="enumFunc">Application-defined callback function</param>
        /// <param name="lParam">Application-defined value to be passed to the callback</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool EnumWindows(EnumWindowsProc enumFunc, IntPtr lParam);

        /// <summary>
        /// Retrieves the length of the specified window's title bar text
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <returns>Length of the text in characters</returns>
        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        public static extern int GetWindowTextLength(IntPtr hWnd);

        /// <summary>
        /// Copies the text of the specified window's title bar into a buffer
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="text">Buffer to receive the text</param>
        /// <param name="count">Maximum number of characters to copy</param>
        /// <returns>Length of the copied string</returns>
        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        /// <summary>
        /// Retrieves information about the specified window
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="nIndex">Zero-based offset to the value to be retrieved</param>
        /// <returns>The requested value</returns>
        [DllImport("user32.dll", SetLastError = true)]
        public static extern long GetWindowLongPtr(IntPtr hWnd, int nIndex);

        /// <summary>
        /// Determines the visibility state of the specified window
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <returns>True if the window is visible, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool IsWindowVisible(IntPtr hWnd);

        /// <summary>
        /// Determines whether the specified window is minimized (iconic)
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <returns>True if the window is minimized, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool IsIconic(IntPtr hWnd);

        /// <summary>
        /// Retrieves the name of the class to which the specified window belongs
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="lpClassName">Buffer to receive the class name</param>
        /// <param name="nMaxCount">Length of the buffer</param>
        /// <returns>Number of characters copied</returns>
        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

        /// <summary>
        /// Retrieves the identifier of the thread that created the specified window
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="lpdwProcessId">Pointer to variable to receive process identifier</param>
        /// <returns>Thread identifier</returns>
        [DllImport("user32.dll", SetLastError = true)]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        /// <summary>
        /// Retrieves the dimensions of the bounding rectangle of the specified window
        /// </summary>
        /// <param name="hWnd">Handle to the window</param>
        /// <param name="lpRect">Pointer to structure to receive rectangle</param>
        /// <returns>True if successful, false otherwise</returns>
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        /// <summary>
        /// Retrieves the calling thread's last-error code value
        /// </summary>
        /// <returns>Last error code</returns>
        public static uint GetLastError()
        {
            return (uint)Marshal.GetLastWin32Error();
        }

        // Simple MessageBox wrapper for one-time notifications
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern int MessageBoxW(IntPtr hWnd, string lpText, string lpCaption, uint uType);

        public const uint MB_OK = 0x00000000; // Using simple OK button
        public const uint MB_TOPMOST = 0x00040000;
        public const uint MB_ICONERROR = 0x00000010;

        // --- Tray icon and menu related declarations ---
        public const int WM_USER_TRAY = 0x0400 + 500;
        public const int NIF_MESSAGE = 0x0001;
        public const int NIF_ICON = 0x0002;
        public const int NIF_TIP = 0x0004;
        public const int NIM_ADD = 0x00000000;
        public const int NIM_MODIFY = 0x00000001;
        public const int NIM_DELETE = 0x00000002;

        public const uint TPM_RIGHTBUTTON = 0x0002;
        public const uint TPM_RETURNCMD = 0x0100;

        public const uint IMAGE_ICON = 1;
        public const uint LR_LOADFROMFILE = 0x00000010;
        public const uint LR_DEFAULTSIZE = 0x00000040;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct NOTIFYICONDATA
        {
            public int cbSize;
            public IntPtr hWnd;
            public int uID;
            public int uFlags;
            public int uCallbackMessage;
            public IntPtr hIcon;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)]
            public string szTip;
        }

        [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool Shell_NotifyIcon(int dwMessage, ref NOTIFYICONDATA lpdata);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern IntPtr CreatePopupMenu();

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern bool DestroyMenu(IntPtr hMenu);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern bool AppendMenu(IntPtr hMenu, uint uFlags, uint uIDNewItem, string lpNewItem);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern uint TrackPopupMenuEx(IntPtr hMenu, uint uFlags, int x, int y, IntPtr hWnd, IntPtr lpTpm);

        [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT lpPoint);

        [DllImport("user32.dll")] public static extern IntPtr LoadIcon(IntPtr hInstance, IntPtr lpIconName);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern IntPtr LoadImage(IntPtr hInstance, string lpszName, uint uType, int cxDesired, int cyDesired, uint fuLoad);

        // Monitor and cursor constants and structures
        public const uint MONITOR_DEFAULTTONEAREST = 2;

        // Small user-level positioning constants
        public const int OFFSET_FROM_CURSOR = 20;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct MONITORINFO
        {
            public int cbSize;
            public RECT rcMonitor;
            public RECT rcWork;
            public uint dwFlags;

            public static MONITORINFO Default
            {
                get
                {
                    var mi = new MONITORINFO();
                    mi.cbSize = Marshal.SizeOf(mi);
                    return mi;
                }
            }
        }

        [DllImport("user32.dll")] public static extern IntPtr MonitorFromPoint(POINT pt, uint dwFlags);
        [DllImport("user32.dll")] [return: MarshalAs(UnmanagedType.Bool)] public static extern bool GetMonitorInfo(IntPtr hMonitor, ref MONITORINFO lpmi);
    }
}
