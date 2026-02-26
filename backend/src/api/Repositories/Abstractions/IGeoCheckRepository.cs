using Api.Models;

namespace Api.Repositories.Abstractions;

/// <summary>
/// Repository interface for GeoCheck operations.
/// </summary>
public interface IGeoCheckRepository
{
    /// <summary>
    /// Gets all geometry checks, optionally filtered by machine ID, type, and date range.
    /// </summary>
    Task<IReadOnlyList<GeoCheck>> GetAllAsync(
        string? machineId = null,
        string? type = null,
        DateTime? date = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        bool includeDetails = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a geometry check by ID.
    /// </summary>
    Task<GeoCheck?> GetByIdAsync(string id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates a new geometry check.
    /// </summary>
    Task<GeoCheck> CreateAsync(GeoCheck geoCheck, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing geometry check.
    /// </summary>
    Task<bool> UpdateAsync(GeoCheck geoCheck, CancellationToken cancellationToken = default);

    /// <summary>
    /// Approves a geo check by updating only the approved_by and approved_date columns.
    /// This avoids rewriting other columns (like timestamp) which can cause timezone drift.
    /// </summary>
    Task<bool> ApproveAsync(string id, string approvedBy, DateTime approvedDate, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a geometry check by ID.
    /// </summary>
    Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default);
}
