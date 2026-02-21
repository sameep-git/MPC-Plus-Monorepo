namespace Api.Models;

/// <summary>
/// Represents the check statuses for a specific day in the calendar view.
/// </summary>
public class DayCheckStatus
{
    /// <summary>Date of the checks.</summary>
    public required DateTime Date { get; set; }

    /// <summary>Overall beam check status for the day (null if no checks).</summary>
    public string? BeamCheckStatus { get; set; }

    /// <summary>Overall geometry check status for the day (null if no checks).</summary>
    public string? GeometryCheckStatus { get; set; }

    /// <summary>
    /// Convenience numeric value to show in the UI table for the beam check.
    /// This is derived from beam metrics (relOutput, relUniformity, centerShift) when available.
    /// </summary>
    public double? BeamValue { get; set; }

    /// <summary>
    /// Convenience numeric value to show in the UI table for the geometry check.
    /// This is derived from geo metrics (relativeOutput, relativeUniformity, centerShift, isoCenterSize) when available.
    /// </summary>
    /// <summary>
    /// Convenience numeric value to show in the UI table for the geometry check.
    /// This is derived from geo metrics (relativeOutput, relativeUniformity, centerShift, isoCenterSize) when available.
    /// </summary>
    public double? GeometryValue { get; set; }

    /// <summary>Whether the daily beam check is approved.</summary>
    public bool BeamApproved { get; set; }

    /// <summary>Whether the daily geometry check is approved.</summary>
    public bool GeometryApproved { get; set; }

    /// <summary>Number of beam checks for the day.</summary>
    public int BeamCount { get; set; }

    /// <summary>Number of geometry checks for the day.</summary>
    public int GeometryCheckCount { get; set; }
}
