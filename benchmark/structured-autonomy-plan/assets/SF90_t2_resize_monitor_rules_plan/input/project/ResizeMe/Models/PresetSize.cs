using System.Text.Json.Serialization;

namespace ResizeMe.Models
{
    /// <summary>
    /// Represents a user-defined window size preset.
    /// </summary>
    public class PresetSize
    {
        /// <summary>Display name (e.g., "Full HD").</summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>Width in pixels.</summary>
        public int Width { get; set; }

        /// <summary>Height in pixels.</summary>
        public int Height { get; set; }

        /// <summary>
        /// Gets a friendly display string for the preset dimensions (e.g., "1920 × 1080").
        /// </summary>
        [JsonIgnore]
        public string SizeDisplay => $"{Width} × {Height}";

        [JsonIgnore]
        public bool IsValid => Width > 0 && Height > 0 && !string.IsNullOrWhiteSpace(Name);

        public override string ToString() => $"{Name} ({Width}x{Height})";
    }
}
