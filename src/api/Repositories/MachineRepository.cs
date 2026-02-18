using Api.Models;
using Api.Database;
using Dapper;

namespace Api.Repositories;

public class MachineRepository(PostgresConnectionFactory connectionFactory) : IMachineRepository
{
    public async Task<IReadOnlyList<Machine>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        // Dapper caches schema, so MatchNamesWithUnderscores should be set globally at startup
        var machines = await connection.QueryAsync<Machine>("SELECT * FROM machines");
        return machines.AsList();
    }

    public async Task<Machine?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        return await connection.QuerySingleOrDefaultAsync<Machine>(
            "SELECT * FROM machines WHERE id = @Id", new { Id = id });
    }

    public async Task<Machine> CreateAsync(Machine machine, CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        // Return * to get potentially db-generated fields (though ID is usually provided)
        var created = await connection.QuerySingleAsync<Machine>(
            @"INSERT INTO machines (id, name, type, location) 
              VALUES (@Id, @Name, @Type, @Location) 
              RETURNING *", 
            machine);
        return created;
    }

    public async Task<bool> UpdateAsync(Machine machine, CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        var rowsAffected = await connection.ExecuteAsync(
            @"UPDATE machines 
              SET name = @Name, type = @Type, location = @Location 
              WHERE id = @Id", 
            machine);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = connectionFactory.CreateConnection();
        var rowsAffected = await connection.ExecuteAsync(
            "DELETE FROM machines WHERE id = @Id", new { Id = id });
        return rowsAffected > 0;
    }
}
