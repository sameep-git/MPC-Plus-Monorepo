using System.Collections.Generic;

namespace Api.Models;

/// <summary>
/// Represents a beam check result for a specific period.
/// </summary>
public class Result
{
    /// <summary>Unique identifier for the result.</summary>
    public required string Id { get; set; }

    /// <summary>Machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>Date of the result.</summary>
    public DateTime? Date { get; set; }

    /// <summary>Month of the result.</summary>
    public int? Month { get; set; }

    /// <summary>Year of the result.</summary>
    public int? Year { get; set; }

    /// <summary>Beam check data.</summary>
    public IDictionary<string, object?>? BeamCheck { get; set; }

    /// <summary>Status of the check.</summary>
    public string? Status { get; set; }
}

