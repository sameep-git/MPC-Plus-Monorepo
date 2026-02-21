namespace Api.Models;

/// <summary>
/// Represents baseline information for a metric.
/// </summary>
public class Baseline
{
    /// <summary>Machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>Type of check.</summary>
    public required string CheckType { get; set; }

    /// <summary>Beam variant (e.g., 6x, 6e).</summary>
    public string? BeamVariant { get; set; }

    /// <summary>Type of metric (e.g., all beam type metrics).</summary>
    public required string MetricType { get; set; }

    /// <summary>Date of baseline.</summary>
    public required DateOnly Date { get; set; }

    /// <summary>Baseline value.</summary>
    public double? Value { get; set; }
}

