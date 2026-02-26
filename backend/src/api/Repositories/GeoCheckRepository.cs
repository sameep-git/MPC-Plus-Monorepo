using System.Data;
using Api.Models;
using Api.Repositories.Abstractions;
using Api.Database;
using Dapper;

namespace Api.Repositories;

public class GeoCheckRepository : IGeoCheckRepository
{
    private readonly PostgresConnectionFactory _connectionFactory;

    public GeoCheckRepository(PostgresConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IReadOnlyList<GeoCheck>> GetAllAsync(
        string? machineId = null,
        string? type = null,
        DateTime? date = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        bool includeDetails = false,
        CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        
        var sql = includeDetails 
            ? "SELECT * FROM geochecks_full WHERE 1=1" 
            : @"SELECT id, machine_id, type, timestamp, path,
                   iso_center_size, iso_center_mv_offset, iso_center_kv_offset,
                   relative_output, relative_uniformity, center_shift,
                   collimation_rotation_offset, gantry_absolute, gantry_relative,
                   couch_max_position_error, couch_lat, couch_lng, couch_vrt,
                   couch_rtn_fine, couch_rtn_large, rotation_induced_couch_shift_full_range,
                   max_offset_a, max_offset_b, mean_offset_a, mean_offset_b,
                   mlc_backlash_max_a, mlc_backlash_max_b, mlc_backlash_mean_a, mlc_backlash_mean_b,
                   jaw_x1, jaw_x2, jaw_y1, jaw_y2,
                   jaw_parallelism_x1, jaw_parallelism_x2, jaw_parallelism_y1, jaw_parallelism_y2,
                   approved_by, approved_date, note, beam_variant_id
            FROM geochecks
            WHERE 1=1";

        var parameters = new DynamicParameters();

        if (!string.IsNullOrWhiteSpace(machineId))
        {
            sql += " AND machine_id = @MachineId";
            parameters.Add("MachineId", machineId);
        }

        if (!string.IsNullOrWhiteSpace(type))
        {
            sql += " AND type = @Type";
            parameters.Add("Type", type);
        }

        if (date.HasValue)
        {
            sql += " AND timestamp::date = @Date";
            parameters.Add("Date", date.Value.Date);
        }
        else 
        {
             if (startDate.HasValue)
             {
                 sql += " AND timestamp::date >= @StartDate";
                 parameters.Add("StartDate", startDate.Value.Date);
             }
             
             if (endDate.HasValue)
             {
                 sql += " AND timestamp::date <= @EndDate";
                 parameters.Add("EndDate", endDate.Value.Date);
             }
        }

        sql += " ORDER BY timestamp DESC";
        
        var geoChecks = await connection.QueryAsync<GeoCheck>(sql, parameters);
        return geoChecks.AsList();
    }

    public async Task<GeoCheck?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        if (!Guid.TryParse(id, out var guidId)) return null;

        var sql = @"SELECT * FROM geochecks_full WHERE id = @Id";

        return await connection.QuerySingleOrDefaultAsync<GeoCheck>(sql, new { Id = guidId });
    }

    public async Task<GeoCheck> CreateAsync(GeoCheck geoCheck, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            var sql = @"
                INSERT INTO geochecks (
                    machine_id, timestamp, 
                    iso_center_size, iso_center_mv_offset, iso_center_kv_offset,
                    relative_output, relative_uniformity, center_shift,
                    collimation_rotation_offset, gantry_absolute, gantry_relative,
                    couch_max_position_error, couch_lat, couch_lng, couch_vrt, 
                    couch_rtn_fine, couch_rtn_large, rotation_induced_couch_shift_full_range,
                    max_offset_a, max_offset_b, mean_offset_a, mean_offset_b,
                    mlc_backlash_max_a, mlc_backlash_max_b, mlc_backlash_mean_a, mlc_backlash_mean_b,
                    jaw_x1, jaw_x2, jaw_y1, jaw_y2,
                    jaw_parallelism_x1, jaw_parallelism_x2, jaw_parallelism_y1, jaw_parallelism_y2,
                    path, approved_by, approved_date, note, type, beam_variant_id
                ) VALUES (
                    @MachineId, @Timestamp,
                    @IsoCenterSize, @IsoCenterMvOffset, @IsoCenterKvOffset,
                    @RelativeOutput, @RelativeUniformity, @CenterShift,
                    @CollimationRotationOffset, @GantryAbsolute, @GantryRelative,
                    @CouchMaxPositionError, @CouchLat, @CouchLng, @CouchVrt,
                    @CouchRtnFine, @CouchRtnLarge, @RotationInducedCouchShiftFullRange,
                    @MaxOffsetA, @MaxOffsetB, @MeanOffsetA, @MeanOffsetB,
                    @MlcBacklashMaxA, @MlcBacklashMaxB, @MlcBacklashMeanA, @MlcBacklashMeanB,
                    @JawX1, @JawX2, @JawY1, @JawY2,
                    @JawParallelismX1, @JawParallelismX2, @JawParallelismY1, @JawParallelismY2,
                    @Path, @ApprovedBy, @ApprovedDate, @Note, @Type, @BeamVariantId
                )
                RETURNING id, machine_id, type, timestamp, path,
                    iso_center_size, iso_center_mv_offset, iso_center_kv_offset,
                    relative_output, relative_uniformity, center_shift,
                    collimation_rotation_offset, gantry_absolute, gantry_relative,
                    couch_max_position_error, couch_lat, couch_lng, couch_vrt,
                    couch_rtn_fine, couch_rtn_large, rotation_induced_couch_shift_full_range,
                    max_offset_a, max_offset_b, mean_offset_a, mean_offset_b,
                    mlc_backlash_max_a, mlc_backlash_max_b, mlc_backlash_mean_a, mlc_backlash_mean_b,
                    jaw_x1, jaw_x2, jaw_y1, jaw_y2,
                    jaw_parallelism_x1, jaw_parallelism_x2, jaw_parallelism_y1, jaw_parallelism_y2,
                    approved_by, approved_date, note, beam_variant_id";

            var created = await connection.QuerySingleAsync<GeoCheck>(sql, geoCheck, transaction);
            
            // Helper to insert child records
            async Task InsertLeaves(Guid geoCheckId, Dictionary<string, double>? leaves, string tableName, string valueColumn)
            {
                if (leaves == null) return;
                var records = leaves.Select(kvp => new 
                { 
                    GeoCheckId = geoCheckId, 
                    LeafNumber = int.Parse(kvp.Key.Replace("Leaf", "")), 
                    Value = kvp.Value 
                });
                await connection.ExecuteAsync(
                    $"INSERT INTO {tableName} (geocheck_id, leaf_number, {valueColumn}) VALUES (@GeoCheckId, @LeafNumber, @Value)", 
                    records, transaction);
            }

            var id = Guid.Parse(created.Id);

            await InsertLeaves(id, geoCheck.MLCLeavesA, "geocheck_mlc_leaves_a", "leaf_value");
            await InsertLeaves(id, geoCheck.MLCLeavesB, "geocheck_mlc_leaves_b", "leaf_value");
            await InsertLeaves(id, geoCheck.MLCBacklashA, "geocheck_mlc_backlash_a", "backlash_value");
            await InsertLeaves(id, geoCheck.MLCBacklashB, "geocheck_mlc_backlash_b", "backlash_value");

            transaction.Commit();
             
             // Copy leaf data to the returned object so it has all the data
            created.MLCLeavesA = geoCheck.MLCLeavesA;
            created.MLCLeavesB = geoCheck.MLCLeavesB;
            created.MLCBacklashA = geoCheck.MLCBacklashA;
            created.MLCBacklashB = geoCheck.MLCBacklashB;

            return created;
        }
        catch
        {
            transaction.Rollback();
            throw;
        }
    }

    public async Task<bool> UpdateAsync(GeoCheck geoCheck, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        { 
            if (string.IsNullOrEmpty(geoCheck.Id) || !Guid.TryParse(geoCheck.Id, out var guidId))
            {
                 return false;
            }

            var sql = @"
                UPDATE geochecks SET
                    machine_id = @MachineId, timestamp = @Timestamp,
                    iso_center_size = @IsoCenterSize, iso_center_mv_offset = @IsoCenterMvOffset, iso_center_kv_offset = @IsoCenterKvOffset,
                    relative_output = @RelativeOutput, relative_uniformity = @RelativeUniformity, center_shift = @CenterShift,
                    collimation_rotation_offset = @CollimationRotationOffset, gantry_absolute = @GantryAbsolute, gantry_relative = @GantryRelative,
                    couch_max_position_error = @CouchMaxPositionError, couch_lat = @CouchLat, couch_lng = @CouchLng, couch_vrt = @CouchVrt,
                    couch_rtn_fine = @CouchRtnFine, couch_rtn_large = @CouchRtnLarge, rotation_induced_couch_shift_full_range = @RotationInducedCouchShiftFullRange,
                    max_offset_a = @MaxOffsetA, max_offset_b = @MaxOffsetB, mean_offset_a = @MeanOffsetA, mean_offset_b = @MeanOffsetB,
                    mlc_backlash_max_a = @MlcBacklashMaxA, mlc_backlash_max_b = @MlcBacklashMaxB, mlc_backlash_mean_a = @MlcBacklashMeanA, mlc_backlash_mean_b = @MlcBacklashMeanB,
                    jaw_x1 = @JawX1, jaw_x2 = @JawX2, jaw_y1 = @JawY1, jaw_y2 = @JawY2,
                    jaw_parallelism_x1 = @JawParallelismX1, jaw_parallelism_x2 = @JawParallelismX2, jaw_parallelism_y1 = @JawParallelismY1, jaw_parallelism_y2 = @JawParallelismY2,
                    path = @Path, approved_by = @ApprovedBy, approved_date = @ApprovedDate, note = @Note, type = @Type, beam_variant_id = @BeamVariantId
                WHERE id = @Id::uuid";

            var rowsAffected = await connection.ExecuteAsync(sql, geoCheck, transaction);
            
            if (rowsAffected > 0)
            {
                // Update child records: Delete all and re-insert
                // This is simpler than dif-fing
                await connection.ExecuteAsync("DELETE FROM geocheck_mlc_leaves_a WHERE geocheck_id = @Id", new { Id = guidId }, transaction);
                await connection.ExecuteAsync("DELETE FROM geocheck_mlc_leaves_b WHERE geocheck_id = @Id", new { Id = guidId }, transaction);
                await connection.ExecuteAsync("DELETE FROM geocheck_mlc_backlash_a WHERE geocheck_id = @Id", new { Id = guidId }, transaction);
                await connection.ExecuteAsync("DELETE FROM geocheck_mlc_backlash_b WHERE geocheck_id = @Id", new { Id = guidId }, transaction);
                
                async Task InsertLeaves(Guid geoCheckId, Dictionary<string, double>? leaves, string tableName, string valueColumn)
                {
                    if (leaves == null) return;
                    var records = leaves.Select(kvp => new 
                    { 
                        GeoCheckId = geoCheckId, 
                        LeafNumber = int.Parse(kvp.Key.Replace("Leaf", "")), 
                        Value = kvp.Value 
                    });
                     await connection.ExecuteAsync(
                        $"INSERT INTO {tableName} (geocheck_id, leaf_number, {valueColumn}) VALUES (@GeoCheckId, @LeafNumber, @Value)", 
                        records, transaction);
                }

                await InsertLeaves(guidId, geoCheck.MLCLeavesA, "geocheck_mlc_leaves_a", "leaf_value");
                await InsertLeaves(guidId, geoCheck.MLCLeavesB, "geocheck_mlc_leaves_b", "leaf_value");
                await InsertLeaves(guidId, geoCheck.MLCBacklashA, "geocheck_mlc_backlash_a", "backlash_value");
                await InsertLeaves(guidId, geoCheck.MLCBacklashB, "geocheck_mlc_backlash_b", "backlash_value");
                
                transaction.Commit();
                return true;
            }
            else 
            {
                transaction.Rollback();
                return false;
            }
        }
        catch
        {
            transaction.Rollback();
            throw;
        }
    }

    public async Task<bool> ApproveAsync(string id, string approvedBy, DateTime approvedDate, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        if (!Guid.TryParse(id, out var guidId)) return false;

        var sql = @"
            UPDATE geochecks SET
                approved_by = @ApprovedBy,
                approved_date = @ApprovedDate
            WHERE id = @Id";

        var rows = await connection.ExecuteAsync(sql, new { Id = guidId, ApprovedBy = approvedBy, ApprovedDate = approvedDate });
        return rows > 0;
    }

    public async Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        if (Guid.TryParse(id, out var guidId))
        {
            var rows = await connection.ExecuteAsync("DELETE FROM geochecks WHERE id = @Id", new { Id = guidId });
            return rows > 0;
        }
        return false;
    }
}
