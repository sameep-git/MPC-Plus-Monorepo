using Api.Models;
using Api.Repositories.Entities;
using Microsoft.Extensions.Logging;
using Supabase;
using static Supabase.Postgrest.Constants;

namespace Api.Repositories;

/// <summary>
/// Supabase implementation of IDocFactorRepository.
/// Handles DOC factor CRUD with automatic date range adjustment.
/// </summary>
public class SupabaseDocFactorRepository : IDocFactorRepository
{
    private readonly Client _client;
    private readonly ILogger<SupabaseDocFactorRepository> _logger;

    public SupabaseDocFactorRepository(Client client, ILogger<SupabaseDocFactorRepository> logger)
    {
        _client = client;
        _logger = logger;
    }

    public async Task<IReadOnlyList<DocFactor>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var response = await _client
            .From<DocFactorEntity>()
            .Order("start_date", Ordering.Descending)
            .Get();

        return response.Models.Select(e => e.ToModel()).ToList();
    }

    public async Task<IReadOnlyList<DocFactor>> GetByMachineAsync(string machineId, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var response = await _client
            .From<DocFactorEntity>()
            .Filter("machine_id", Operator.Equals, machineId)
            .Order("start_date", Ordering.Descending)
            .Get();

        return response.Models.Select(e => e.ToModel()).ToList();
    }

    public async Task<DocFactor?> GetApplicableAsync(string machineId, Guid beamVariantId, DateOnly date, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var dateStr = date.ToString("yyyy-MM-dd");

        // Find: start_date <= date, ordered by start_date desc, limit 1
        var response = await _client
            .From<DocFactorEntity>()
            .Filter("machine_id", Operator.Equals, machineId)
            .Filter("beam_variant_id", Operator.Equals, beamVariantId.ToString())
            .Filter("start_date", Operator.LessThanOrEqual, dateStr)
            .Order("start_date", Ordering.Descending)
            .Limit(1)
            .Get();

        var entity = response.Models.FirstOrDefault();
        if (entity == null) return null;

        // Check end_date condition: date < end_date (or end_date is null)
        if (entity.EndDate.HasValue)
        {
            var endDate = DateOnly.FromDateTime(entity.EndDate.Value);
            if (date >= endDate)
            {
                // Date is outside this factor's range
                return null;
            }
        }

        return entity.ToModel();
    }

    public async Task<DocFactor> CreateAsync(DocFactor docFactor, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var startDateStr = docFactor.StartDate.ToString("yyyy-MM-dd");

        // 1. Find the existing DOC factor whose range contains new start_date
        //    WHERE start_date <= new_start_date AND (end_date IS NULL OR end_date > new_start_date)
        var existingResponse = await _client
            .From<DocFactorEntity>()
            .Filter("machine_id", Operator.Equals, docFactor.MachineId)
            .Filter("beam_variant_id", Operator.Equals, docFactor.BeamVariantId.ToString())
            .Filter("start_date", Operator.LessThanOrEqual, startDateStr)
            .Order("start_date", Ordering.Descending)
            .Limit(1)
            .Get();

        var existing = existingResponse.Models.FirstOrDefault();

        if (existing != null)
        {
            // Check if new start_date falls within existing's range
            bool isWithinRange = !existing.EndDate.HasValue ||
                                 docFactor.StartDate < DateOnly.FromDateTime(existing.EndDate.Value);

            if (isWithinRange)
            {
                _logger.LogInformation(
                    "Adjusting existing DOC factor {Id}: end_date from {OldEnd} to {NewEnd}",
                    existing.Id,
                    existing.EndDate,
                    docFactor.StartDate);

                // New factor inherits existing's end_date
                docFactor.EndDate = existing.EndDate.HasValue
                    ? DateOnly.FromDateTime(existing.EndDate.Value)
                    : null;

                // Update existing factor's end_date to new factor's start_date
                existing.EndDate = docFactor.StartDate.ToDateTime(TimeOnly.MinValue);
                existing.UpdatedAt = DateTime.UtcNow;

                await _client
                    .From<DocFactorEntity>()
                    .Update(existing);
            }
        }

        // 2. Calculate doc_factor
        docFactor.DocFactorValue = docFactor.MsdAbs / docFactor.MpcRel;

        // 3. Insert the new DOC factor
        var entity = DocFactorEntity.FromModel(docFactor);

        var insertResponse = await _client
            .From<DocFactorEntity>()
            .Insert(entity);

        var result = insertResponse.Models.FirstOrDefault();
        if (result == null)
        {
            throw new InvalidOperationException("Failed to create DOC factor.");
        }

        _logger.LogInformation("Created DOC factor {Id} for machine {MachineId}, beam variant {BeamVariantId}",
            result.Id, result.MachineId, result.BeamVariantId);

        return result.ToModel();
    }

    public async Task<DocFactor> UpdateAsync(DocFactor docFactor, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!docFactor.Id.HasValue)
        {
            throw new ArgumentException("DocFactor ID is required for update.", nameof(docFactor));
        }

        // Recalculate doc_factor
        docFactor.DocFactorValue = docFactor.MsdAbs / docFactor.MpcRel;

        var entity = DocFactorEntity.FromModel(docFactor);
        entity.UpdatedAt = DateTime.UtcNow;

        var response = await _client
            .From<DocFactorEntity>()
            .Update(entity);

        var result = response.Models.FirstOrDefault();
        if (result == null)
        {
            throw new InvalidOperationException("Failed to update DOC factor.");
        }

        return result.ToModel();
    }

    public async Task DeleteAsync(Guid id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        await _client
            .From<DocFactorEntity>()
            .Filter("id", Operator.Equals, id.ToString())
            .Delete();

        _logger.LogInformation("Deleted DOC factor {Id}", id);
    }
}
