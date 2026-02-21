using Api.Models;

namespace Api.Repositories;

public interface IThresholdRepository
{
    Task<IReadOnlyList<Threshold>> GetAllAsync(CancellationToken cancellationToken = default);
    Task<Threshold> SaveAsync(Threshold threshold, CancellationToken cancellationToken = default);
}
