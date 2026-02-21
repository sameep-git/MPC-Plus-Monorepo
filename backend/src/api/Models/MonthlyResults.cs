namespace Api.Models;

/// <summary>
/// Represents monthly results showing calendar view of check statuses.
/// </summary>
public class MonthlyResults
{
    /// <summary>Month queried (1-12).</summary>
    public int Month { get; set; }

    /// <summary>Year queried.</summary>
    public int Year { get; set; }

    /// <summary>Machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>Daily check statuses for the month.</summary>
    public IReadOnlyList<DayCheckStatus> Checks { get; set; } = [];
}
