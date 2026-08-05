namespace ResizeMe.Features.MainLayout
{
    internal sealed class MainWindowState
    {
        public bool IsVisible { get; private set; }
        public int FocusIndex { get; private set; } = -1;
        public string? ActivePresetTag { get; private set; }
        public bool CenterOnResize { get; private set; }

        public void Show()
        {
            IsVisible = true;
        }

        public void Hide()
        {
            IsVisible = false;
            FocusIndex = -1;
        }

        public void SetFocusIndex(int index)
        {
            FocusIndex = index;
        }

        public void SetActivePreset(string? tag)
        {
            ActivePresetTag = tag;
        }

        public void SetCenterOnResize(bool value)
        {
            CenterOnResize = value;
        }
    }
}
