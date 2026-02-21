using System.Collections.Concurrent;
using Api.Models;
using Api.Repositories.Abstractions;

namespace Api.Repositories.InMemory;

/// <summary>
/// In-memory implementation of the beam repository with seed data.
/// Useful for development and testing.
/// </summary>
public class InMemoryBeamRepository : IBeamRepository
{
    private static readonly IReadOnlyList<string> BeamTypes = new[] { "6e", "9e", "12e", "16e", "10x", "15x", "6xff" };

    private static readonly IReadOnlyList<Beam> SeedBeams =
    [
        // MPC-001 (Primary Gantry) - Multiple beam types across several days
    new Beam { Id = "beam-001", Type = "6e", Date = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelOutput = 98.5, RelUniformity = 99.2 },
    new Beam { Id = "beam-002", Type = "6e", Date = new DateTime(2025, 11, 8), MachineId = "MPC-001", RelOutput = 98.7, RelUniformity = 99.1 },
    new Beam { Id = "beam-003", Type = "6e", Date = new DateTime(2025, 11, 7), MachineId = "MPC-001", RelOutput = 98.9, RelUniformity = 99.3 },
    new Beam { Id = "beam-004", Type = "15x", Date = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelOutput = 97.2, RelUniformity = 98.5, CenterShift = 0.15 },
    new Beam { Id = "beam-005", Type = "15x", Date = new DateTime(2025, 11, 8), MachineId = "MPC-001", RelOutput = 97.5, RelUniformity = 98.7, CenterShift = 0.12 },

        // MPC-002 (Secondary Gantry) - Different beam types
    new Beam { Id = "beam-006", Type = "6e", Date = new DateTime(2025, 11, 9), MachineId = "MPC-002", RelOutput = 99.1, RelUniformity = 99.4 },
    new Beam { Id = "beam-007", Type = "6e", Date = new DateTime(2025, 11, 7), MachineId = "MPC-002", RelOutput = 99.2, RelUniformity = 99.5 },
    new Beam { Id = "beam-008", Type = "10x", Date = new DateTime(2025, 11, 9), MachineId = "MPC-002", RelOutput = 96.8, RelUniformity = 98.2, CenterShift = 0.08 },
    new Beam { Id = "beam-009", Type = "10x", Date = new DateTime(2025, 11, 8), MachineId = "MPC-002", RelOutput = 96.9, RelUniformity = 98.3, CenterShift = 0.10 },

        // MPC-003 (QA Test Bench) - Diagnostic machine with various beams
    new Beam { Id = "beam-010", Type = "6e", Date = new DateTime(2025, 11, 9), MachineId = "MPC-003", RelOutput = 98.0, RelUniformity = 99.0 },
    new Beam { Id = "beam-011", Type = "9e", Date = new DateTime(2025, 11, 9), MachineId = "MPC-003", RelOutput = 97.5, RelUniformity = 98.8 },
    new Beam { Id = "beam-012", Type = "12e", Date = new DateTime(2025, 11, 8), MachineId = "MPC-003", RelOutput = 96.9, RelUniformity = 98.6 },
    new Beam { Id = "beam-013", Type = "16e", Date = new DateTime(2025, 11, 7), MachineId = "MPC-003", RelOutput = 96.2, RelUniformity = 98.4 },
    ];

    private readonly ConcurrentDictionary<string, Beam> _beams;

    public InMemoryBeamRepository()
    {
        _beams = new ConcurrentDictionary<string, Beam>(
            SeedBeams.Select(beam => new KeyValuePair<string, Beam>(beam.Id, Clone(beam))));
    }

    public Task<IReadOnlyList<Beam>> GetAllAsync(
        string? machineId = null,
        string? type = null,
        DateTime? date = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var query = _beams.Values.AsEnumerable();

        if (!string.IsNullOrWhiteSpace(machineId))
        {
            query = query.Where(b => b.MachineId == machineId);
        }

        if (!string.IsNullOrWhiteSpace(type))
        {
            query = query.Where(b => b.Type == type);
        }

        if (date.HasValue)
        {
            query = query.Where(b => b.Date.Date == date.Value.Date);
        }

        if (startDate.HasValue)
        {
            query = query.Where(b => b.Date.Date >= startDate.Value.Date);
        }

        if (endDate.HasValue)
        {
            query = query.Where(b => b.Date.Date <= endDate.Value.Date);
        }

        var result = query
            .Select(Clone)
            .OrderByDescending(b => b.Date)
            .ThenBy(b => b.Type)
            .ToList()
            .AsReadOnly();

        return Task.FromResult<IReadOnlyList<Beam>>(result);
    }

    public Task<Beam?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(_beams.TryGetValue(id, out var beam) ? Clone(beam) : null);
    }

    public Task<Beam> CreateAsync(Beam beam, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!_beams.TryAdd(beam.Id, Clone(beam)))
        {
            throw new InvalidOperationException($"Beam with id '{beam.Id}' already exists.");
        }

        return Task.FromResult(Clone(beam));
    }

    public Task<bool> UpdateAsync(Beam beam, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!_beams.ContainsKey(beam.Id))
        {
            return Task.FromResult(false);
        }

        _beams[beam.Id] = Clone(beam);
        return Task.FromResult(true);
    }

    public Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(_beams.TryRemove(id, out _));
    }

    public Task<IReadOnlyList<string>> GetBeamTypesAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult<IReadOnlyList<string>>(BeamTypes);
    }

    private static Beam Clone(Beam beam) =>
        new()
        {
            Id = beam.Id,
            Type = beam.Type,
            Date = beam.Date,
            Path = beam.Path,
            RelUniformity = beam.RelUniformity,
            RelOutput = beam.RelOutput,
            CenterShift = beam.CenterShift,
            MachineId = beam.MachineId,
            Note = beam.Note
        };
}
