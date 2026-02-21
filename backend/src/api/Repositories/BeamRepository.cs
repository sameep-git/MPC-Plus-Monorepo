using Api.Models;
using Api.Database;
using Api.Repositories.Abstractions;
using Dapper;

namespace Api.Repositories;

public class BeamRepository(PostgresConnectionFactory connectionFactory) : IBeamRepository
{
    public async Task<IReadOnlyList<Beam>> GetAllAsync(
        string? machineId = null,
        string? type = null,
        DateTime? date = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        
        var sql = @"
            SELECT id, type, date, timestamp, path, 
                   rel_uniformity, rel_output, center_shift, 
                   machine_id, note, approved_by, approved_date,
                   image_paths::text as image_paths_json,
                   ""typeID""
            FROM beams 
            WHERE 1=1
        ";

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
            sql += " AND date = @Date";
            parameters.Add("Date", date.Value.Date);
        }

        if (startDate.HasValue)
        {
            sql += " AND date >= @StartDate";
            parameters.Add("StartDate", startDate.Value.Date);
        }

        if (endDate.HasValue)
        {
            sql += " AND date <= @EndDate";
            parameters.Add("EndDate", endDate.Value.Date);
        }

        sql += " ORDER BY timestamp DESC";

        var beams = await connection.QueryAsync<Beam>(sql, parameters);
        return beams.AsList();
    }

    public async Task<Beam?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        if (!Guid.TryParse(id, out _)) return null;
        using var connection = connectionFactory.CreateConnection();
        var sql = @"
            SELECT id, type, date, timestamp, path,
                   rel_uniformity, rel_output, center_shift,
                   machine_id, note, approved_by, approved_date,
                   image_paths::text as image_paths_json,
                   ""typeID""
            FROM beams WHERE id = @Id::uuid";
        return await connection.QuerySingleOrDefaultAsync<Beam>(sql, new { Id = id });
    }

    public async Task<Beam> CreateAsync(Beam beam, CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        // Insert and return full object
        // NOTE: We rely on Dapper to map properties to columns. 
        // For ImagePaths (Dictionary), type handler must be registered.
        // We exclude 'Value', 'Status', etc as they are computed.
        // We explicitly list columns to avoid inserting computed properties if Dapper tries to.
        var sql = @"
            INSERT INTO beams (
                id, type, date, timestamp, path, rel_uniformity, rel_output, center_shift, 
                machine_id, note, approved_by, approved_date, image_paths
            ) VALUES (
                @Id, @Type, @Date, @Timestamp, @Path, @RelUniformity, @RelOutput, @CenterShift, 
                @MachineId, @Note, @ApprovedBy, @ApprovedDate, @ImagePathsJson::jsonb
            ) RETURNING id, type, date, timestamp, path,
                       rel_uniformity, rel_output, center_shift,
                       machine_id, note, approved_by, approved_date,
                       image_paths::text as image_paths_json,
                       ""typeID""";
            
        return await connection.QuerySingleAsync<Beam>(sql, beam);
    }

    public async Task<bool> UpdateAsync(Beam beam, CancellationToken cancellationToken = default)
    {
        if (!Guid.TryParse(beam.Id, out _)) return false;
        using var connection = connectionFactory.CreateConnection();
        var sql = @"
            UPDATE beams SET
                type = @Type,
                date = @Date,
                timestamp = @Timestamp,
                path = @Path,
                rel_uniformity = @RelUniformity,
                rel_output = @RelOutput,
                center_shift = @CenterShift,
                machine_id = @MachineId,
                note = @Note,
                approved_by = @ApprovedBy,
                approved_date = @ApprovedDate,
                image_paths = @ImagePathsJson::jsonb
            WHERE id = @Id::uuid";

        var rows = await connection.ExecuteAsync(sql, beam);
        return rows > 0;
    }

    public async Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        if (!Guid.TryParse(id, out _)) return false;
        using var connection = connectionFactory.CreateConnection();
        var rows = await connection.ExecuteAsync("DELETE FROM beams WHERE id = @Id::uuid", new { Id = id });
        return rows > 0;
    }

    public async Task<IReadOnlyList<string>> GetBeamTypesAsync(CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        var types = (await connection.QueryAsync<string>(
            "SELECT variant FROM beam_variants ORDER BY variant"))
            .ToList()
            .AsReadOnly();
        return types;
    }
}
