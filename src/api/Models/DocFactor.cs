namespace Api.Models;

/// <summary>
/// Represents a Dose Output Correction (DOC) factor for converting MPC relative values to absolute values.
/// DOC Factor = MsdAbs / MpcRel
/// Absolute Value = MPC Relative × DOC Factor
/// </summary>
public class DocFactor
{
    /// <summary>Unique identifier for the DOC factor.</summary>
    public Guid? Id { get; set; }

    /// <summary>Associated machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>Associated beam variant ID (FK to beam_variants).</summary>
    public required Guid BeamVariantId { get; set; }

    /// <summary>Beam variant name for display purposes (not persisted).</summary>
    public string? BeamVariantName { get; set; }

    /// <summary>Reference to the specific beam check used for MPC relative value.</summary>
    public required Guid BeamId { get; set; }

    /// <summary>Measured absolute output from independent device.</summary>
    public required double MsdAbs { get; set; }

    /// <summary>MPC relative output from the selected beam check.</summary>
    public required double MpcRel { get; set; }

    /// <summary>Calculated DOC factor (MsdAbs / MpcRel).</summary>
    public double DocFactorValue { get; set; }

    /// <summary>Date when the Msd Abs measurement was taken.</summary>
    public required DateOnly MeasurementDate { get; set; }

    /// <summary>Start of validity period (inclusive).</summary>
    public required DateOnly StartDate { get; set; }

    /// <summary>End of validity period (exclusive). NULL means indefinite/current.</summary>
    public DateOnly? EndDate { get; set; }

    /// <summary>Timestamp when this record was created.</summary>
    public DateTime? CreatedAt { get; set; }

    /// <summary>Timestamp when this record was last updated.</summary>
    public DateTime? UpdatedAt { get; set; }

    /// <summary>User who created this record.</summary>
    public string? CreatedBy { get; set; }
}
