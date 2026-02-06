using Api.Models;
using Api.Repositories.Abstractions;
using Api.Repositories.Entities;
using Microsoft.Extensions.Logging;
using Supabase;
using Supabase.Postgrest.Exceptions;

namespace Api.Repositories;

public class SupabaseBeamRepository : IBeamRepository
{
    private readonly Client _client;
    private readonly ILogger<SupabaseBeamRepository> _logger;

    public SupabaseBeamRepository(Client client, ILogger<SupabaseBeamRepository> logger)
    {
        _client = client;
        _logger = logger;
    }

    public async Task<IReadOnlyList<Beam>> GetAllAsync(
        string? machineId = null, string? type = null, DateTime? date = null,
        DateTime? startDate = null, DateTime? endDate = null,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        try
        {
            Supabase.Postgrest.Interfaces.IPostgrestTable<BeamEntity> query = _client.From<BeamEntity>();

            if (!string.IsNullOrWhiteSpace(machineId))
                query = query.Filter("machine_id", Supabase.Postgrest.Constants.Operator.Equals, machineId);
            
            if (!string.IsNullOrWhiteSpace(type))
                query = query.Filter("type", Supabase.Postgrest.Constants.Operator.Equals, type);
            
            // When filtering by a specific date, use timestamp range (start of day to end of day)
            if (date.HasValue)
            {
                var dayStart = date.Value.Date.ToString("yyyy-MM-ddT00:00:00Z");
                var dayEnd = date.Value.Date.ToString("yyyy-MM-ddT23:59:59Z");
                query = query.Filter("timestamp", Supabase.Postgrest.Constants.Operator.GreaterThanOrEqual, dayStart);
                query = query.Filter("timestamp", Supabase.Postgrest.Constants.Operator.LessThanOrEqual, dayEnd);
            }
            
            // For date range queries, also use timestamp
            if (startDate.HasValue)
                query = query.Filter("timestamp", Supabase.Postgrest.Constants.Operator.GreaterThanOrEqual, startDate.Value.Date.ToString("yyyy-MM-ddT00:00:00Z"));
            
            if (endDate.HasValue)
                query = query.Filter("timestamp", Supabase.Postgrest.Constants.Operator.LessThanOrEqual, endDate.Value.Date.ToString("yyyy-MM-ddT23:59:59Z"));

            var response = await query
                .Order("timestamp", Supabase.Postgrest.Constants.Ordering.Descending)
                .Get();

            return response.Models.Select(e => e.ToModel()).ToList().AsReadOnly();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving beams");
            throw;
        }
    }

    public async Task<Beam?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        try
        {
            var response = await _client.From<BeamEntity>()
                .Filter("id", Supabase.Postgrest.Constants.Operator.Equals, id).Get();
            return response.Models.FirstOrDefault()?.ToModel();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving beam {BeamId}", id);
            return null;
        }
    }

    public async Task<Beam> CreateAsync(Beam beam, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        try
        {
            var response = await _client.From<BeamEntity>().Insert(BeamEntity.FromModel(beam));
            return response.Models.First().ToModel();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating beam");
            throw;
        }
    }

    public async Task<bool> UpdateAsync(Beam beam, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        try
        {
            var response = await _client.From<BeamEntity>()
                .Filter("id", Supabase.Postgrest.Constants.Operator.Equals, beam.Id)
                .Update(BeamEntity.FromModel(beam));
            return response.Models.Any();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating beam {BeamId}", beam.Id);
            return false;
        }
    }

    public async Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        try
        {
            await _client.From<BeamEntity>()
                .Filter("id", Supabase.Postgrest.Constants.Operator.Equals, id)
                .Delete();
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting beam {BeamId}", id);
            return false;
        }
    }

    public async Task<IReadOnlyList<string>> GetBeamTypesAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var types = new[] { "6e", "9e", "12e", "16e", "10x", "15x", "6xff" };
        return await Task.FromResult(types.ToList().AsReadOnly());
    }
}
