using System.Collections.Generic;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using ResizeMe.Models;

namespace ResizeMe.Features.MainLayout
{
    internal sealed class PresetPanelRenderer
    {
        public void Render(Panel panel, IEnumerable<PresetSize> presets, ResourceDictionary? resources, RoutedEventHandler clickHandler)
        {
            if (panel == null)
            {
                return;
            }

            panel.Children.Clear();
            foreach (var preset in presets)
            {
                panel.Children.Add(PresetButtonFactory.Create(preset, resources, clickHandler));
            }
        }

        public int Focus(Panel panel, int index)
        {
            if (panel == null)
            {
                return -1;
            }

            var buttons = panel.Children.OfType<Button>().ToList();
            if (buttons.Count == 0)
            {
                return -1;
            }

            if (index < 0)
            {
                index = 0;
            }
            if (index >= buttons.Count)
            {
                index = buttons.Count - 1;
            }

            buttons[index].Focus(FocusState.Programmatic);
            return index;
        }

        public void ApplyActiveStyle(Panel panel, string sizeTag, ResourceDictionary? resources)
        {
            if (panel == null || resources == null)
            {
                return;
            }

            if (!resources.TryGetValue("ActivePresetButtonStyle", out var activeObj) || activeObj is not Style activeStyle)
            {
                return;
            }

            if (!resources.TryGetValue("PresetButtonBaseStyle", out var baseObj) || baseObj is not Style baseStyle)
            {
                return;
            }

            foreach (var button in panel.Children.OfType<Button>())
            {
                if (button.Tag is string tag && tag == sizeTag)
                {
                    button.Style = activeStyle;
                }
                else
                {
                    button.Style = baseStyle;
                }
            }
        }
    }
}
