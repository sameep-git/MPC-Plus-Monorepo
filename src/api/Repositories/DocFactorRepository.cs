using System.Data;
using Api.Models;
using Api.Repositories.Abstractions;
using Api.Database;
using Dapper;

namespace Api.Repositories;

/// <summary>
/// Npgsql implementation of IDocFactorRepository.
/// Handles DOC factor CRUD with automatic date range adjustment.
/// </summary>
public class DocFactorRepository : IDocFactorRepository
{
    private readonly PostgresConnectionFactory _connectionFactory;

    public DocFactorRepository(PostgresConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IReadOnlyList<DocFactor>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        // Alias doc_factor to Match DocFactorValue property
        var sql = "SELECT *, doc_factor as DocFactorValue FROM doc ORDER BY start_date DESC";
        var factors = await connection.QueryAsync<DocFactor>(sql);
        return factors.AsList();
    }

    public async Task<IReadOnlyList<DocFactor>> GetByMachineAsync(string machineId, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        var sql = "SELECT *, doc_factor as DocFactorValue FROM doc WHERE machine_id = @MachineId ORDER BY start_date DESC";
        var factors = await connection.QueryAsync<DocFactor>(sql, new { MachineId = machineId });
        return factors.AsList();
    }

    public async Task<DocFactor?> GetApplicableAsync(string machineId, Guid beamVariantId, DateOnly date, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        
        // Find factor where start_date <= date, ordered desc limit 1
        var sql = @"
            SELECT *, doc_factor as DocFactorValue FROM doc
            WHERE machine_id = @MachineId
              AND beam_variant_id = @BeamVariantId
              AND start_date <= @Date
            ORDER BY start_date DESC
            LIMIT 1";

        var factor = await connection.QuerySingleOrDefaultAsync<DocFactor>(
            sql, 
            new { MachineId = machineId, BeamVariantId = beamVariantId, Date = date });

        if (factor == null) return null;

        // Check end_date condition: date < end_date (or end_date is null)
        if (factor.EndDate.HasValue && date >= factor.EndDate.Value)
        {
            return null;
        }

        return factor;
    }

    public async Task<DocFactor> CreateAsync(DocFactor docFactor, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            // 1. Find overlapping existing factor to adjust
            var findSql = @"
                SELECT *, doc_factor as DocFactorValue FROM doc
                WHERE machine_id = @MachineId
                  AND beam_variant_id = @BeamVariantId
                  AND start_date <= @StartDate
                ORDER BY start_date DESC
                LIMIT 1";

            var existing = await connection.QuerySingleOrDefaultAsync<DocFactor>(
                findSql, 
                new { 
                    docFactor.MachineId, 
                    docFactor.BeamVariantId, 
                    docFactor.StartDate 
                }, 
                transaction);

            if (existing != null)
            {
                bool isWithinRange = !existing.EndDate.HasValue || docFactor.StartDate < existing.EndDate.Value;

                if (isWithinRange)
                {
                    // Update existing factor's end_date to new factor's start_date
                    var updateSql = @"
                        UPDATE doc
                        SET end_date = @EndDate, updated_at = @UpdatedAt
                        WHERE id = @Id";

                    await connection.ExecuteAsync(
                        updateSql, 
                        new { 
                            EndDate = docFactor.StartDate, 
                            UpdatedAt = DateTime.UtcNow, 
                            Id = existing.Id 
                        }, 
                        transaction);
                }
            }

            // MpcRel is a percentage change (e.g. 1.8% = 1.8)
            // Formula: DocFactor = MsdAbs / (1 + MpcRel / 100)
            docFactor.DocFactorValue = docFactor.MsdAbs / (1.0 + docFactor.MpcRel / 100.0);
            docFactor.CreatedAt = DateTime.UtcNow;
            docFactor.UpdatedAt = DateTime.UtcNow;

            // 3. Insert new factor
            var insertSql = @"
                INSERT INTO doc (
                    machine_id, beam_variant_id, beam_id,
                    msd_abs, mpc_rel, doc_factor,
                    measurement_date, start_date, end_date,
                    created_at, updated_at, created_by
                ) VALUES (
                    @MachineId, @BeamVariantId, @BeamId,
                    @MsdAbs, @MpcRel, @DocFactorValue,
                    @MeasurementDate, @StartDate, @EndDate,
                    @CreatedAt, @UpdatedAt, @CreatedBy
                )
                RETURNING *, doc_factor as DocFactorValue";
            
            var created = await connection.QuerySingleAsync<DocFactor>(insertSql, docFactor, transaction);
            
            transaction.Commit();
            return created;
        }
        catch
        {
            transaction.Rollback();
            throw;
        }
    }

    public async Task<DocFactor> UpdateAsync(DocFactor docFactor, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        
        if (!docFactor.Id.HasValue)
        {
            throw new ArgumentException("DocFactor ID is required for update.", nameof(docFactor));
        }

        // MpcRel is a percentage change (e.g. 1.8% = 1.8)
        // Formula: DocFactor = MsdAbs / (1 + MpcRel / 100)
        docFactor.DocFactorValue = docFactor.MsdAbs / (1.0 + docFactor.MpcRel / 100.0);
        docFactor.UpdatedAt = DateTime.UtcNow;

        var sql = @"
            UPDATE doc
            SET 
                machine_id = @MachineId,
                beam_variant_id = @BeamVariantId,
                beam_id = @BeamId,
                msd_abs = @MsdAbs,
                mpc_rel = @MpcRel,
                doc_factor = @DocFactorValue,
                measurement_date = @MeasurementDate,
                start_date = @StartDate,
                end_date = @EndDate,
                updated_at = @UpdatedAt,
                created_by = @CreatedBy
            WHERE id = @Id
            RETURNING *, doc_factor as DocFactorValue";

        var updated = await connection.QuerySingleAsync<DocFactor>(sql, docFactor);
        return updated;
    }

    public async Task DeleteAsync(Guid id, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        await connection.ExecuteAsync("DELETE FROM doc WHERE id = @Id", new { Id = id });
    }
}
