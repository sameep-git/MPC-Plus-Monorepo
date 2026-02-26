namespace Api.Models;

/// <summary>
/// Represents beam data, as defined in the OpenAPI schema.
/// </summary>
public class Beam
{
    /// <summary>Unique identifier for the beam.</summary>
    public required string Id { get; set; }

    /// <summary>Type of beam (e.g., 6e, 9e, 12e, 16e, 10x, 15x, 6xff).</summary>
    public required string Type { get; set; }

    /// <summary>UTC timestamp of the beam data.</summary>
    public required DateTime Timestamp { get; set; }

    /// <summary>File path to the beam data.</summary>
    public string? Path { get; set; }

    /// <summary>Relative uniformity value.</summary>
    public double? RelUniformity { get; set; }

    /// <summary>Relative output value.</summary>
    public double? RelOutput { get; set; }

    /// <summary>Center shift value (for X-Beam only).</summary>
    public double? CenterShift { get; set; }

    /// <summary>Associated machine identifier.</summary>
    public required string MachineId { get; set; }

    /// <summary>Notes about the beam.</summary>
    public string? Note { get; set; }

    /// <summary>Name of the person who accepted/signed off the beam check.</summary>
    public string? ApprovedBy { get; set; }

    /// <summary>Date when the beam check was accepted/signed off.</summary>
    public DateTime? ApprovedDate { get; set; }

    /// <summary>Image storage paths — maps labels (e.g. "beamImage", "horzProfile") to storage URLs.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public string? ImagePathsJson { get; set; }

    /// <summary>Parsed image paths dictionary. Computed from ImagePathsJson.</summary>
    public Dictionary<string, string>? ImagePaths
    {
        get
        {
            if (string.IsNullOrEmpty(ImagePathsJson)) return null;
            try
            {
                var json = ImagePathsJson;
                // Handle double-serialized JSONB: if the value is a JSON string (starts with '"'),
                // unwrap it first to get the inner JSON object.
                if (json.StartsWith("\""))
                {
                    json = System.Text.Json.JsonSerializer.Deserialize<string>(json);
                    if (string.IsNullOrEmpty(json)) return null;
                }
                return System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, string>>(json);
            }
            catch
            {
                return null;
            }
        }
        set => ImagePathsJson = value != null
            ? System.Text.Json.JsonSerializer.Serialize(value)
            : null;
    }

    /// <summary>
    /// Convenience property representing a single numeric value to display in UIs.
    /// Priority: RelOutput, RelUniformity, CenterShift.
    /// This is not persisted to the database; it's computed by repositories.
    /// </summary>
    public double? Value { get; set; }

    /// <summary>
    /// Overall status of the beam check (e.g., PASS, FAIL). Computed dynamically.
    /// </summary>
    public string? Status { get; set; }

    /// <summary>
    /// Status of the relative output check. Computed dynamically.
    /// </summary>
    public string? RelOutputStatus { get; set; }

    /// <summary>
    /// Status of the relative uniformity check. Computed dynamically.
    /// </summary>
    public string? RelUniformityStatus { get; set; }

    /// <summary>
    /// Status of the center shift check. Computed dynamically.
    /// </summary>
    public string? CenterShiftStatus { get; set; }
}

