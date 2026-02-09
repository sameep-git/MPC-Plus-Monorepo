using Api.Models;
using Supabase.Postgrest.Attributes;
using Supabase.Postgrest.Models;
using System.Text.Json;

namespace Api.Repositories.Entities;

/// <summary>
/// Base entity model for geometry check data.
/// </summary>
public abstract class GeoCheckEntityBase : BaseModel
{
    [PrimaryKey("id", false)]
    public string Id { get; set; } = default!;

    [Column("type")]
    public string Type { get; set; } = default!;

    [Column("date")]
    public DateTime Date { get; set; }

    [Column("timestamp")]
    public DateTime? Timestamp { get; set; }

    [Column("machine_id")]
    public string MachineId { get; set; } = default!;

    [Column("path")]
    public string? Path { get; set; }

    // ---- IsoCenterGroup ----
    [Column("iso_center_size")]
    public double? IsoCenterSize { get; set; }

    [Column("iso_center_mv_offset")]
    public double? IsoCenterMVOffset { get; set; }

    [Column("iso_center_kv_offset")]
    public double? IsoCenterKVOffset { get; set; }

    // ---- BeamGroup ----
    [Column("relative_output")]
    public double? RelativeOutput { get; set; }

    [Column("relative_uniformity")]
    public double? RelativeUniformity { get; set; }

    [Column("center_shift")]
    public double? CenterShift { get; set; }

    // ---- CollimationGroup ----
    [Column("collimation_rotation_offset")]
    public double? CollimationRotationOffset { get; set; }

    // ---- GantryGroup ----
    [Column("gantry_absolute")]
    public double? GantryAbsolute { get; set; }

    [Column("gantry_relative")]
    public double? GantryRelative { get; set; }

    // ---- EnhancedCouchGroup ----
    [Column("couch_max_position_error")]
    public double? CouchMaxPositionError { get; set; }

    [Column("couch_lat")]
    public double? CouchLat { get; set; }

    [Column("couch_lng")]
    public double? CouchLng { get; set; }

    [Column("couch_vrt")]
    public double? CouchVrt { get; set; }

    [Column("couch_rtn_fine")]
    public double? CouchRtnFine { get; set; }

    [Column("couch_rtn_large")]
    public double? CouchRtnLarge { get; set; }

    [Column("rotation_induced_couch_shift_full_range")]
    public double? RotationInducedCouchShiftFullRange { get; set; }

    // ---- MLCGroup ----
    [Column("mlc_leaves_a")]
    public object? MLCLeavesAJson { get; set; }

    [Column("mlc_leaves_b")]
    public object? MLCLeavesBJson { get; set; }

    [Column("max_offset_a")]
    public double? MaxOffsetA { get; set; }

    [Column("max_offset_b")]
    public double? MaxOffsetB { get; set; }

    [Column("mean_offset_a")]
    public double? MeanOffsetA { get; set; }

    [Column("mean_offset_b")]
    public double? MeanOffsetB { get; set; }

    // ---- MLCBacklashGroup ----
    [Column("mlc_backlash_a")]
    public object? MLCBacklashAJson { get; set; }

    [Column("mlc_backlash_b")]
    public object? MLCBacklashBJson { get; set; }

    [Column("mlc_backlash_max_a")]
    public double? MLCBacklashMaxA { get; set; }

    [Column("mlc_backlash_max_b")]
    public double? MLCBacklashMaxB { get; set; }

    [Column("mlc_backlash_mean_a")]
    public double? MLCBacklashMeanA { get; set; }

    [Column("mlc_backlash_mean_b")]
    public double? MLCBacklashMeanB { get; set; }

    // ---- JawsGroup ----
    [Column("jaw_x1")]
    public double? JawX1 { get; set; }

    [Column("jaw_x2")]
    public double? JawX2 { get; set; }

    [Column("jaw_y1")]
    public double? JawY1 { get; set; }

    [Column("jaw_y2")]
    public double? JawY2 { get; set; }

    // ---- JawsParallelismGroup ----
    [Column("jaw_parallelism_x1")]
    public double? JawParallelismX1 { get; set; }

    [Column("jaw_parallelism_x2")]
    public double? JawParallelismX2 { get; set; }

    [Column("jaw_parallelism_y1")]
    public double? JawParallelismY1 { get; set; }

    [Column("jaw_parallelism_y2")]
    public double? JawParallelismY2 { get; set; }

    [Column("note")]
    public string? Note { get; set; }

    [Column("approved_by")]
    public string? ApprovedBy { get; set; }

    [Column("approved_date")]
    public DateTime? ApprovedDate { get; set; }

    /// <summary>
    /// Converts this entity to a domain model.
    /// </summary>
    public GeoCheck ToModel()
    {
        return new GeoCheck
        {
            Id = Id,
            Type = Type,
            Date = Date,
            Timestamp = Timestamp,
            MachineId = MachineId,
            Path = Path,
            IsoCenterSize = IsoCenterSize,
            IsoCenterMVOffset = IsoCenterMVOffset,
            IsoCenterKVOffset = IsoCenterKVOffset,
            RelativeOutput = RelativeOutput,
            RelativeUniformity = RelativeUniformity,
            CenterShift = CenterShift,
            CollimationRotationOffset = CollimationRotationOffset,
            GantryAbsolute = GantryAbsolute,
            GantryRelative = GantryRelative,
            CouchMaxPositionError = CouchMaxPositionError,
            CouchLat = CouchLat,
            CouchLng = CouchLng,
            CouchVrt = CouchVrt,
            CouchRtnFine = CouchRtnFine,
            CouchRtnLarge = CouchRtnLarge,
            RotationInducedCouchShiftFullRange = RotationInducedCouchShiftFullRange,
            MLCLeavesA = DeserializeLeaves(MLCLeavesAJson),
            MLCLeavesB = DeserializeLeaves(MLCLeavesBJson),
            MaxOffsetA = MaxOffsetA,
            MaxOffsetB = MaxOffsetB,
            MeanOffsetA = MeanOffsetA,
            MeanOffsetB = MeanOffsetB,
            MLCBacklashA = DeserializeLeaves(MLCBacklashAJson),
            MLCBacklashB = DeserializeLeaves(MLCBacklashBJson),
            MLCBacklashMaxA = MLCBacklashMaxA,
            MLCBacklashMaxB = MLCBacklashMaxB,
            MLCBacklashMeanA = MLCBacklashMeanA,
            MLCBacklashMeanB = MLCBacklashMeanB,
            JawX1 = JawX1,
            JawX2 = JawX2,
            JawY1 = JawY1,
            JawY2 = JawY2,
            JawParallelismX1 = JawParallelismX1,
            JawParallelismX2 = JawParallelismX2,
            JawParallelismY1 = JawParallelismY1,
            JawParallelismY2 = JawParallelismY2,
            Note = Note,
            ApprovedBy = ApprovedBy,
            ApprovedDate = ApprovedDate
        };
    }

    /// <summary>
    /// Converts a domain model to this entity.
    /// </summary>
    public static void UpdateEntityFromModel(GeoCheckEntityBase entity, GeoCheck geoCheck)
    {
        entity.Id = geoCheck.Id;
        entity.Type = geoCheck.Type;
        entity.Date = geoCheck.Date;
        entity.MachineId = geoCheck.MachineId;
        entity.Path = geoCheck.Path;
        entity.IsoCenterSize = geoCheck.IsoCenterSize;
        entity.IsoCenterMVOffset = geoCheck.IsoCenterMVOffset;
        entity.IsoCenterKVOffset = geoCheck.IsoCenterKVOffset;
        entity.RelativeOutput = geoCheck.RelativeOutput;
        entity.RelativeUniformity = geoCheck.RelativeUniformity;
        entity.CenterShift = geoCheck.CenterShift;
        entity.CollimationRotationOffset = geoCheck.CollimationRotationOffset;
        entity.GantryAbsolute = geoCheck.GantryAbsolute;
        entity.GantryRelative = geoCheck.GantryRelative;
        entity.CouchMaxPositionError = geoCheck.CouchMaxPositionError;
        entity.CouchLat = geoCheck.CouchLat;
        entity.CouchLng = geoCheck.CouchLng;
        entity.CouchVrt = geoCheck.CouchVrt;
        entity.CouchRtnFine = geoCheck.CouchRtnFine;
        entity.CouchRtnLarge = geoCheck.CouchRtnLarge;
        entity.RotationInducedCouchShiftFullRange = geoCheck.RotationInducedCouchShiftFullRange;
        entity.MLCLeavesAJson = SerializeLeaves(geoCheck.MLCLeavesA);
        entity.MLCLeavesBJson = SerializeLeaves(geoCheck.MLCLeavesB);
        entity.MaxOffsetA = geoCheck.MaxOffsetA;
        entity.MaxOffsetB = geoCheck.MaxOffsetB;
        entity.MeanOffsetA = geoCheck.MeanOffsetA;
        entity.MeanOffsetB = geoCheck.MeanOffsetB;
        entity.MLCBacklashAJson = SerializeLeaves(geoCheck.MLCBacklashA);
        entity.MLCBacklashBJson = SerializeLeaves(geoCheck.MLCBacklashB);
        entity.MLCBacklashMaxA = geoCheck.MLCBacklashMaxA;
        entity.MLCBacklashMaxB = geoCheck.MLCBacklashMaxB;
        entity.MLCBacklashMeanA = geoCheck.MLCBacklashMeanA;
        entity.MLCBacklashMeanB = geoCheck.MLCBacklashMeanB;
        entity.JawX1 = geoCheck.JawX1;
        entity.JawX2 = geoCheck.JawX2;
        entity.JawY1 = geoCheck.JawY1;
        entity.JawY2 = geoCheck.JawY2;
        entity.JawParallelismX1 = geoCheck.JawParallelismX1;
        entity.JawParallelismX2 = geoCheck.JawParallelismX2;
        entity.JawParallelismY1 = geoCheck.JawParallelismY1;
        entity.JawParallelismY2 = geoCheck.JawParallelismY2;
        entity.Note = geoCheck.Note;
        entity.ApprovedBy = geoCheck.ApprovedBy;
        entity.ApprovedDate = geoCheck.ApprovedDate;
    }

    private static Dictionary<string, double>? DeserializeLeaves(object? data)
    {
        if (data == null)
            return null;

        if (data is string json)
        {
            if (string.IsNullOrWhiteSpace(json)) return null;
            try
            {
               return JsonSerializer.Deserialize<Dictionary<string, double>>(json);
            }
            catch { return null; }
        }

        if (data is Newtonsoft.Json.Linq.JObject jObj)
        {
             return jObj.ToObject<Dictionary<string, double>>();
        }

        if (data is Newtonsoft.Json.Linq.JArray jArr)
        {
             // Attempt to convert array of objects to dictionary.
             // Assumption: array elements are objects like { "key": "Leaf...", "value": 0.1 }
             // We try to find string property and double property.
             var dict = new Dictionary<string, double>();
             foreach (var token in jArr)
             {
                 if (token is Newtonsoft.Json.Linq.JObject item)
                 {
                     string? key = null;
                     double? val = null;
                     foreach (var prop in item.Properties())
                     {
                         var name = prop.Name.ToLowerInvariant();
                         var value = prop.Value;

                         // Heuristic: check name first
                         bool isKeyName = name.Contains("leaf") || name.Contains("id") || name.Contains("no") || name.Contains("idx") || name.Contains("key");
                         bool isValueName = name.Contains("val") || name.Contains("pos") || name.Contains("off") || name.Contains("mm") || name.Contains("data");

                         if (value.Type == Newtonsoft.Json.Linq.JTokenType.String)
                         {
                             // String is almost always the key (e.g. "Leaf11")
                             key = value.ToObject<string>();
                         }
                         else if (value.Type == Newtonsoft.Json.Linq.JTokenType.Float)
                         {
                             // Float is almost always the value
                             val = value.ToObject<double>();
                         }
                         else if (value.Type == Newtonsoft.Json.Linq.JTokenType.Integer)
                         {
                             // Integer is ambiguous: could be leaf index (key) or value (e.g. 0mm)
                             if (isKeyName && !isValueName)
                                 key = value.ToString();
                             else if (isValueName && !isKeyName)
                                 val = value.ToObject<double>();
                             else
                             {
                                 // Fallback: if we don't have a key yet, assume this is it
                                 if (key == null) key = value.ToString();
                                 else val = value.ToObject<double>();
                             }
                         }
                     }
                     if (key != null && val.HasValue)
                         dict[key] = val.Value;
                 }
             }
             return dict.Count > 0 ? dict : null;
        }

        return null;
    }

    private static string? SerializeLeaves(Dictionary<string, double>? leaves)
    {
        if (leaves == null || leaves.Count == 0)
            return null;

        return JsonSerializer.Serialize(leaves);
    }
}
