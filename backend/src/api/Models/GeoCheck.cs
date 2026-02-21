namespace Api.Models;

/// <summary>
/// Represents geometry check data with all measurement groups.
/// </summary>
public class GeoCheck
{
    /// <summary>Unique identifier for the geometry check.</summary>
    public required string Id { get; set; }

    /// <summary>Type of beam (e.g., 6xff).</summary>
    public required string Type { get; set; }

    /// <summary>Date of the geometry check.</summary>
    public required DateTime Date { get; set; }

    /// <summary>High-precision timestamp of the geometry check.</summary>
    public DateTime? Timestamp { get; set; }

    /// <summary>Associated machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>File path to the geometry check data.</summary>
    public string? Path { get; set; }

    // ---- IsoCenterGroup ----
    /// <summary>Iso center size measurement.</summary>
    public double? IsoCenterSize { get; set; }

    /// <summary>Iso center MV offset measurement.</summary>
    public double? IsoCenterMVOffset { get; set; }

    /// <summary>Iso center KV offset measurement.</summary>
    public double? IsoCenterKVOffset { get; set; }

    // ---- BeamGroup ----
    /// <summary>Relative output value.</summary>
    public double? RelativeOutput { get; set; }

    /// <summary>Relative uniformity value.</summary>
    public double? RelativeUniformity { get; set; }

    /// <summary>Center shift value.</summary>
    public double? CenterShift { get; set; }

    // ---- CollimationGroup ----
    /// <summary>Collimation rotation offset measurement.</summary>
    public double? CollimationRotationOffset { get; set; }

    // ---- GantryGroup ----
    /// <summary>Gantry absolute measurement.</summary>
    public double? GantryAbsolute { get; set; }

    /// <summary>Gantry relative measurement.</summary>
    public double? GantryRelative { get; set; }

    // ---- EnhancedCouchGroup ----
    /// <summary>Couch maximum position error.</summary>
    public double? CouchMaxPositionError { get; set; }

    /// <summary>Couch lateral measurement.</summary>
    public double? CouchLat { get; set; }

    /// <summary>Couch longitudinal measurement.</summary>
    public double? CouchLng { get; set; }

    /// <summary>Couch vertical measurement.</summary>
    public double? CouchVrt { get; set; }

    /// <summary>Couch rotation fine measurement.</summary>
    public double? CouchRtnFine { get; set; }

    /// <summary>Couch rotation large measurement.</summary>
    public double? CouchRtnLarge { get; set; }

    /// <summary>Rotation induced couch shift full range.</summary>
    public double? RotationInducedCouchShiftFullRange { get; set; }

    // ---- MLCGroup ----
    /// <summary>Raw JSON for MLC leaves A from DB.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public string? MLCLeavesAJson { get; set; }

    /// <summary>Raw JSON for MLC leaves B from DB.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public string? MLCLeavesBJson { get; set; }

    /// <summary>MLC leaves A measurements (Leaf11-Leaf50).</summary>
    public Dictionary<string, double>? MLCLeavesA
    {
        get => ParseJsonDict(MLCLeavesAJson);
        set => MLCLeavesAJson = value != null ? System.Text.Json.JsonSerializer.Serialize(value) : null;
    }

    /// <summary>MLC leaves B measurements (Leaf11-Leaf50).</summary>
    public Dictionary<string, double>? MLCLeavesB
    {
        get => ParseJsonDict(MLCLeavesBJson);
        set => MLCLeavesBJson = value != null ? System.Text.Json.JsonSerializer.Serialize(value) : null;
    }

    /// <summary>Maximum offset for MLC bank A.</summary>
    public double? MaxOffsetA { get; set; }

    /// <summary>Maximum offset for MLC bank B.</summary>
    public double? MaxOffsetB { get; set; }

    /// <summary>Mean offset for MLC bank A.</summary>
    public double? MeanOffsetA { get; set; }

    /// <summary>Mean offset for MLC bank B.</summary>
    public double? MeanOffsetB { get; set; }

    // ---- MLCBacklashGroup ----
    /// <summary>Raw JSON for MLC backlash A from DB.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public string? MLCBacklashAJson { get; set; }

    /// <summary>Raw JSON for MLC backlash B from DB.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public string? MLCBacklashBJson { get; set; }

    /// <summary>MLC backlash A measurements (Leaf11-Leaf50).</summary>
    public Dictionary<string, double>? MLCBacklashA
    {
        get => ParseJsonDict(MLCBacklashAJson);
        set => MLCBacklashAJson = value != null ? System.Text.Json.JsonSerializer.Serialize(value) : null;
    }

    /// <summary>MLC backlash B measurements (Leaf11-Leaf50).</summary>
    public Dictionary<string, double>? MLCBacklashB
    {
        get => ParseJsonDict(MLCBacklashBJson);
        set => MLCBacklashBJson = value != null ? System.Text.Json.JsonSerializer.Serialize(value) : null;
    }

    /// <summary>Maximum backlash for MLC bank A.</summary>
    public double? MLCBacklashMaxA { get; set; }

    /// <summary>Maximum backlash for MLC bank B.</summary>
    public double? MLCBacklashMaxB { get; set; }

    /// <summary>Mean backlash for MLC bank A.</summary>
    public double? MLCBacklashMeanA { get; set; }

    /// <summary>Mean backlash for MLC bank B.</summary>
    public double? MLCBacklashMeanB { get; set; }

    // ---- JawsGroup ----
    /// <summary>Jaw X1 measurement.</summary>
    public double? JawX1 { get; set; }

    /// <summary>Jaw X2 measurement.</summary>
    public double? JawX2 { get; set; }

    /// <summary>Jaw Y1 measurement.</summary>
    public double? JawY1 { get; set; }

    /// <summary>Jaw Y2 measurement.</summary>
    public double? JawY2 { get; set; }

    // ---- JawsParallelismGroup ----
    /// <summary>Jaw parallelism X1 measurement.</summary>
    public double? JawParallelismX1 { get; set; }

    /// <summary>Jaw parallelism X2 measurement.</summary>
    public double? JawParallelismX2 { get; set; }

    /// <summary>Jaw parallelism Y1 measurement.</summary>
    public double? JawParallelismY1 { get; set; }

    /// <summary>Jaw parallelism Y2 measurement.</summary>
    public double? JawParallelismY2 { get; set; }

    /// <summary>Notes about the geometry check.</summary>
    public string? Note { get; set; }

    /// <summary>Name of the person who accepted/signed off the geometry check.</summary>
    public string? ApprovedBy { get; set; }

    /// <summary>Date when the geometry check was accepted/signed off.</summary>
    public DateTime? ApprovedDate { get; set; }

    /// <summary>ID of the beam variant (e.g. 6xff).</summary>
    public Guid? BeamVariantId { get; set; }

    /// <summary>Helper to parse potentially double-serialized JSONB dictionaries.</summary>
    private static Dictionary<string, double>? ParseJsonDict(string? json)
    {
        if (string.IsNullOrEmpty(json)) return null;
        try
        {
            // Handle double-serialized JSONB: if the value is a JSON string (starts with '"'),
            // unwrap it first to get the inner JSON object.
            if (json.StartsWith("\""))
            {
                json = System.Text.Json.JsonSerializer.Deserialize<string>(json);
                if (string.IsNullOrEmpty(json)) return null;
            }
            return System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, double>>(json);
        }
        catch
        {
            return null;
        }
    }
}
