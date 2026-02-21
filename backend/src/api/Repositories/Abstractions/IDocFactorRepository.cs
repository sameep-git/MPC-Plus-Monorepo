using Api.Models;

namespace Api.Repositories;

/// <summary>
/// Repository interface for DOC (Dose Output Correction) factor operations.
/// </summary>
public interface IDocFactorRepository
{
    /// <summary>
    /// Get all DOC factors.
    /// </summary>
    Task<IReadOnlyList<DocFactor>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all DOC factors for a specific machine.
    /// </summary>
    Task<IReadOnlyList<DocFactor>> GetByMachineAsync(string machineId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the applicable DOC factor for a specific date.
    /// Uses rule: start_date &lt;= date AND (end_date IS NULL OR date &lt; end_date)
    /// </summary>
    Task<DocFactor?> GetApplicableAsync(string machineId, Guid beamVariantId, DateOnly date, CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a new DOC factor. Automatically adjusts date ranges of existing factors.
    /// When inserting in middle of existing range:
    /// - New factor inherits existing factor's end_date
    /// - Existing factor's end_date is updated to new factor's start_date
    /// </summary>
    Task<DocFactor> CreateAsync(DocFactor docFactor, CancellationToken cancellationToken = default);

    /// <summary>
    /// Update an existing DOC factor.
    /// </summary>
    Task<DocFactor> UpdateAsync(DocFactor docFactor, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a DOC factor by ID.
    /// </summary>
    Task DeleteAsync(Guid id, CancellationToken cancellationToken = default);
}
