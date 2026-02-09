using Api.Models;
using Supabase.Postgrest.Attributes;
using Supabase.Postgrest.Models;

namespace Api.Repositories.Entities;

[Table("doc")]
public class DocFactorEntity : BaseModel
{
    [PrimaryKey("id")]
    [Column("id")]
    public Guid Id { get; set; }

    [Column("machine_id")]
    public string MachineId { get; set; } = default!;

    [Column("beam_variant_id")]
    public Guid BeamVariantId { get; set; }

    [Column("beam_id")]
    public Guid BeamId { get; set; }

    [Column("msd_abs")]
    public double MsdAbs { get; set; }

    [Column("mpc_rel")]
    public double MpcRel { get; set; }

    [Column("doc_factor")]
    public double DocFactor { get; set; }

    [Column("measurement_date")]
    public DateTime MeasurementDate { get; set; }

    [Column("start_date")]
    public DateTime StartDate { get; set; }

    [Column("end_date")]
    public DateTime? EndDate { get; set; }

    [Column("created_at")]
    public DateTime? CreatedAt { get; set; }

    [Column("updated_at")]
    public DateTime? UpdatedAt { get; set; }

    [Column("created_by")]
    public string? CreatedBy { get; set; }

    public static DocFactorEntity FromModel(DocFactor model) =>
        new()
        {
            Id = model.Id ?? Guid.NewGuid(),
            MachineId = model.MachineId,
            BeamVariantId = model.BeamVariantId,
            BeamId = model.BeamId,
            MsdAbs = model.MsdAbs,
            MpcRel = model.MpcRel,
            DocFactor = model.DocFactorValue,
            MeasurementDate = model.MeasurementDate.ToDateTime(TimeOnly.MinValue),
            StartDate = model.StartDate.ToDateTime(TimeOnly.MinValue),
            EndDate = model.EndDate?.ToDateTime(TimeOnly.MinValue),
            CreatedAt = model.CreatedAt ?? DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow,
            CreatedBy = model.CreatedBy
        };

    public DocFactor ToModel() =>
        new()
        {
            Id = Id,
            MachineId = MachineId,
            BeamVariantId = BeamVariantId,
            BeamId = BeamId,
            MsdAbs = MsdAbs,
            MpcRel = MpcRel,
            DocFactorValue = DocFactor,
            MeasurementDate = DateOnly.FromDateTime(MeasurementDate),
            StartDate = DateOnly.FromDateTime(StartDate),
            EndDate = EndDate.HasValue ? DateOnly.FromDateTime(EndDate.Value) : null,
            CreatedAt = CreatedAt,
            UpdatedAt = UpdatedAt,
            CreatedBy = CreatedBy
        };
}
