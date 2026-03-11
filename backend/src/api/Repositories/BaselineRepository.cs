using Api.Models;
using Api.Repositories.Abstractions;
using Api.Database;
using Dapper;

namespace Api.Repositories;

public class BaselineRepository : IBaselineRepository
{
    private readonly PostgresConnectionFactory _connectionFactory;

    public BaselineRepository(PostgresConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IReadOnlyList<Baseline>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        var baselines = await connection.QueryAsync<Baseline>("SELECT * FROM baselines");
        return baselines.AsList();
    }

    public async Task<IReadOnlyList<Baseline>> GetByMachineAsync(string machineId, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        var baselines = await connection.QueryAsync<Baseline>(
            "SELECT * FROM baselines WHERE machine_id = @MachineId",
            new { MachineId = machineId });
        return baselines.AsList();
    }

    public async Task<Baseline> SaveAsync(Baseline baseline, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();

        var sql = @"
            INSERT INTO baselines (
                machine_id, check_type, beam_variant, metric_type, date, value
            ) VALUES (
                @MachineId, @CheckType, @BeamVariant, @MetricType, @Date, @Value
            )
            ON CONFLICT (machine_id, check_type, beam_variant, metric_type) 
            DO UPDATE SET
                value = EXCLUDED.value,
                date = EXCLUDED.date,
                updated_at = now()
            RETURNING *";

        var saved = await connection.QuerySingleAsync<Baseline>(sql, baseline);
        return saved;
    }
}
