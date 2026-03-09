using Api.Models;

namespace Api.Repositories.Abstractions;

public interface IBaselineRepository
{
    Task<IReadOnlyList<Baseline>> GetAllAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<Baseline>> GetByMachineAsync(string machineId, CancellationToken cancellationToken = default);
    Task<Baseline> SaveAsync(Baseline baseline, CancellationToken cancellationToken = default);
}
