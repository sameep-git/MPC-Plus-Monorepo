namespace Api.Models;

/// <summary>
/// Represents threshold configuration data.
/// </summary>
public class Threshold
{
    /// <summary>Machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>Type of check.</summary>
    public required string CheckType { get; set; }

    /// <summary>Beam variant.</summary>
    public string? BeamVariant { get; set; }

    /// <summary>Type of metric.</summary>
    public required string MetricType { get; set; }

    /// <summary>Last update timestamp.</summary>
    public DateTime? LastUpdated { get; set; }

    /// <summary>Threshold value.</summary>
    public double? Value { get; set; }
}

