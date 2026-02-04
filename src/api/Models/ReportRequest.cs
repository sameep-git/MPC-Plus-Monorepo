using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Api.Models;

/// <summary>
/// Request model for generating a PDF report.
/// </summary>
public class ReportRequest
{
    /// <summary>
    /// Start date for the report data (inclusive).
    /// </summary>
    [Required]
    public DateTime StartDate { get; set; }

    /// <summary>
    /// End date for the report data (inclusive).
    /// </summary>
    [Required]
    public DateTime EndDate { get; set; }

    /// <summary>
    /// ID of the machine to generate the report for.
    /// </summary>
    [Required]
    public string MachineId { get; set; } = string.Empty;

    /// <summary>
    /// List of selected check IDs to include in the report (e.g., "beam-6x", "geo-gantry").
    /// </summary>
    [Required]
    public List<string> SelectedChecks { get; set; } = new List<string>();
}
