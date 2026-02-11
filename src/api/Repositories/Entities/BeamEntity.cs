using Api.Models;
using Newtonsoft.Json;
using Supabase.Postgrest.Attributes;
using Supabase.Postgrest.Models;

namespace Api.Repositories.Entities;

/// <summary>
/// Supabase entity model for beam data.
/// </summary>
[Table("beams")]
public class BeamEntity : BaseModel
{
    [PrimaryKey("id", false)]
    public string Id { get; set; } = default!;

    [Column("type")]
    public string Type { get; set; } = default!;

    [Column("date")]
    public DateTime Date { get; set; }

    [Column("path")]
    public string? Path { get; set; }

    [Column("rel_uniformity")]
    public double? RelUniformity { get; set; }

    [Column("rel_output")]
    public double? RelOutput { get; set; }

    [Column("center_shift")]
    public double? CenterShift { get; set; }

    [Column("machine_id")]
    public string MachineId { get; set; } = default!;

    [Column("note")]
    public string? Note { get; set; }

    [Column("approved_by")]
    public string? ApprovedBy { get; set; }

    [Column("approved_date")]
    public DateTime? ApprovedDate { get; set; }

    [Column("timestamp")]
    public DateTime? Timestamp { get; set; }

    [Column("image_paths")]
    public string? ImagePaths { get; set; }

    /// <summary>
    /// Converts this entity to a domain model.
    /// </summary>
    public Beam ToModel()
    {
        Dictionary<string, string>? parsedImagePaths = null;
        if (!string.IsNullOrWhiteSpace(ImagePaths))
        {
            try
            {
                parsedImagePaths = JsonConvert.DeserializeObject<Dictionary<string, string>>(ImagePaths);
            }
            catch
            {
                // If parsing fails, leave as null
            }
        }

        return new()
        {
            Id = Id,
            Type = Type,
            Date = Date,
            Timestamp = Timestamp,
            Path = Path,
            RelUniformity = RelUniformity,
            RelOutput = RelOutput,
            CenterShift = CenterShift,
            MachineId = MachineId,
            Note = Note,
            ApprovedBy = ApprovedBy,
            ApprovedDate = ApprovedDate,
            ImagePaths = parsedImagePaths
        };
    }

    /// <summary>
    /// Converts a domain model to this entity.
    /// </summary>
    public static BeamEntity FromModel(Beam beam) =>
        new()
        {
            Id = beam.Id,
            Type = beam.Type,
            Date = beam.Date,
            Timestamp = beam.Timestamp,
            Path = beam.Path,
            RelUniformity = beam.RelUniformity,
            RelOutput = beam.RelOutput,
            CenterShift = beam.CenterShift,
            MachineId = beam.MachineId,
            Note = beam.Note,
            ApprovedBy = beam.ApprovedBy,
            ApprovedDate = beam.ApprovedDate,
            ImagePaths = beam.ImagePaths != null ? JsonConvert.SerializeObject(beam.ImagePaths) : null
        };
}
