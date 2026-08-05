using System.Collections.Generic;
using System.Text.Json.Serialization;
using ResizeMe.Models;

namespace ResizeMe.Shared.Config
{
    [JsonSerializable(typeof(List<PresetSize>))]
    [JsonSerializable(typeof(PresetSize))]
    internal partial class AppJsonContext : JsonSerializerContext
    {
    }
}
