using Api.Models;
using Api.Repositories.Entities;
using Microsoft.Extensions.Logging;
using Supabase;
using Supabase.Postgrest.Exceptions;

namespace Api.Repositories;

public class SupabaseMachineRepository : IMachineRepository
{
    private readonly Client _client;
    private readonly ILogger<SupabaseMachineRepository> _logger;

    public SupabaseMachineRepository(Client client, ILogger<SupabaseMachineRepository> logger)
    {
        _client = client;
        _logger = logger;
    }

    public async Task<IReadOnlyList<Machine>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var response = await _client
            .From<MachineEntity>()
            .Get();

        return response.Models.Select(entity => entity.ToModel()).ToList();
    }

    public async Task<Machine?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var response = await _client
            .From<MachineEntity>()
            .Filter("id", Supabase.Postgrest.Constants.Operator.Equals, id)
            .Get();

        return response.Models.FirstOrDefault()?.ToModel();
    }

    public async Task<Machine> CreateAsync(Machine machine, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var entity = MachineEntity.FromModel(machine);

        try
        {
            var response = await _client.From<MachineEntity>().Insert(entity);
            var created = response.Models.FirstOrDefault();

            if (created is null)
            {
                _logger.LogWarning("Supabase insert returned no models for machine {MachineId}", machine.Id);
                return machine;
            }

            return created.ToModel();
        }
        catch (PostgrestException exception) when (IsUniqueConstraintViolation(exception))
        {
            throw new InvalidOperationException($"Machine with id '{machine.Id}' already exists.", exception);
        }
    }

    public async Task<bool> UpdateAsync(Machine machine, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var entity = MachineEntity.FromModel(machine);

        var response = await _client
            .From<MachineEntity>()
            .Filter("id", Supabase.Postgrest.Constants.Operator.Equals, machine.Id)
            .Update(entity);

        return response.Models.Any();
    }

    public async Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var existing = await GetByIdAsync(id, cancellationToken);
        if (existing is null)
        {
            return false;
        }

        await _client
            .From<MachineEntity>()
            .Filter("id", Supabase.Postgrest.Constants.Operator.Equals, id)
            .Delete();

        return true;
    }

    private static bool IsUniqueConstraintViolation(PostgrestException exception) =>
        exception.Message.Contains("duplicate key", StringComparison.OrdinalIgnoreCase);
}

