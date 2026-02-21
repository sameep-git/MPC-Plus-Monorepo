using Api.Models;

namespace Api.Repositories.Abstractions;

public interface IUpdateRepository
{
    Task<IReadOnlyList<Update>> GetAllAsync(CancellationToken cancellationToken = default);
    Task<Update?> GetByIdAsync(string id, CancellationToken cancellationToken = default);
    Task<Update> CreateAsync(Update update, CancellationToken cancellationToken = default);
    Task<bool> UpdateAsync(Update update, CancellationToken cancellationToken = default);
    Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default);
}
