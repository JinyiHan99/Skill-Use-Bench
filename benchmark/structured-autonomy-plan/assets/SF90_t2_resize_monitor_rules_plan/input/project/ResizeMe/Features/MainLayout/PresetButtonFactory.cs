using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Text;
using ResizeMe.Models;

namespace ResizeMe.Features.MainLayout
{
    internal static class PresetButtonFactory
    {
        public static Button Create(PresetSize preset, ResourceDictionary? resources, RoutedEventHandler clickHandler)
        {
            var container = new Border
            {
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(8, 6, 8, 6),
                Margin = new Thickness(0, 1, 0, 1)
            };

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var icon = new FontIcon
            {
                FontFamily = new FontFamily("Segoe Fluent Icons"),
                Glyph = "\xE7C4",
                FontSize = 14,
                Opacity = 0.9,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 8, 0)
            };
            Grid.SetColumn(icon, 0);

            var stack = new StackPanel { Orientation = Orientation.Vertical, VerticalAlignment = VerticalAlignment.Center };
            var header = new TextBlock { Text = preset.Name, FontWeight = FontWeights.SemiBold };
            var sizeText = new TextBlock { Text = $"{preset.Width} x {preset.Height}", Opacity = 0.8 };

            if (resources != null)
            {
                if (resources.TryGetValue("PresetHeaderTextStyle", out var headerStyle) && headerStyle is Style hs)
                {
                    header.Style = hs;
                }
                else
                {
                    header.FontSize = 13;
                }

                if (resources.TryGetValue("PresetSubTextStyle", out var subStyle) && subStyle is Style ss)
                {
                    sizeText.Style = ss;
                }
                else
                {
                    sizeText.FontSize = 11;
                }

                if (resources.TryGetValue("ControlFillColorDefaultBrush", out var brush) && brush is Brush bg)
                {
                    container.Background = bg;
                }
            }

            stack.Children.Add(header);
            stack.Children.Add(sizeText);
            Grid.SetColumn(stack, 1);

            grid.Children.Add(icon);
            grid.Children.Add(stack);
            container.Child = grid;

            var button = new Button
            {
                Content = container,
                Tag = $"{preset.Width}x{preset.Height}",
                DataContext = preset,
                MinHeight = 44,
                Padding = new Thickness(0),
                HorizontalContentAlignment = HorizontalAlignment.Left,
                VerticalContentAlignment = VerticalAlignment.Center
            };

            if (resources != null && resources.TryGetValue("PresetButtonBaseStyle", out var baseStyle) && baseStyle is Style style)
            {
                button.Style = style;
            }

            button.Click += clickHandler;
            return button;
        }
    }
}
