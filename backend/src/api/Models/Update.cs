namespace Api.Models;

/// <summary>
/// Represents an update entry.
/// </summary>
public class Update
{
    /// <summary>Unique identifier for the update.</summary>
    public required string Id { get; set; }

    /// <summary>Associated machine.</summary>
    public required string MachineId { get; set; }

    /// <summary>Update information.</summary>
    public required string Info { get; set; }

    /// <summary>Type of update.</summary>
    public required string Type { get; set; }
}

