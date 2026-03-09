using System.Data;
using Api.Models;
using Api.Repositories.Abstractions;
using Api.Database;
using Dapper;

namespace Api.Repositories;

public class ThresholdRepository : IThresholdRepository
{
    private readonly PostgresConnectionFactory _connectionFactory;

    public ThresholdRepository(PostgresConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IReadOnlyList<Threshold>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        var thresholds = await connection.QueryAsync<Threshold>("SELECT * FROM thresholds");
        return thresholds.AsList();
    }

    public async Task<IReadOnlyList<Threshold>> GetByMachineAsync(string machineId, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        var sql = "SELECT * FROM thresholds WHERE machine_id = @MachineId";
        var thresholds = await connection.QueryAsync<Threshold>(sql, new { MachineId = machineId });
        return thresholds.AsList();
    }

    public async Task<Threshold> SaveAsync(Threshold threshold, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();

        threshold.LastUpdated = DateTime.UtcNow;

        var sql = @"
            INSERT INTO thresholds (
                machine_id, check_type, beam_variant, metric_type, value, last_updated
            ) VALUES (
                @MachineId, @CheckType, @BeamVariant, @MetricType, @Value, @LastUpdated
            )
            ON CONFLICT (machine_id, check_type, beam_variant, metric_type) 
            DO UPDATE SET
                value = EXCLUDED.value,
                last_updated = EXCLUDED.last_updated
            RETURNING *";

        var saved = await connection.QuerySingleAsync<Threshold>(sql, threshold);
        return saved;
    }
}
