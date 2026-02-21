using Api.Models;

namespace Api.Repositories.Abstractions;

/// <summary>
/// Repository interface for beam data operations.
/// </summary>
public interface IBeamRepository
{
    /// <summary>
    /// Gets all beams, optionally filtered by machine ID, beam type, and date range.
    /// </summary>
    Task<IReadOnlyList<Beam>> GetAllAsync(
        string? machineId = null,
        string? type = null,
        DateTime? date = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a specific beam by its ID.
    /// </summary>
    Task<Beam?> GetByIdAsync(string id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates a new beam entry.
    /// </summary>
    Task<Beam> CreateAsync(Beam beam, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing beam entry.
    /// </summary>
    Task<bool> UpdateAsync(Beam beam, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a beam by its ID.
    /// </summary>
    Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all available beam types.
    /// </summary>
    Task<IReadOnlyList<string>> GetBeamTypesAsync(CancellationToken cancellationToken = default);
}
