using System.Data;
using Api.Models;
using Api.Repositories.Abstractions;
using Api.Database;
using Dapper;

namespace Api.Repositories;

public class UpdateRepository : IUpdateRepository
{
    private readonly PostgresConnectionFactory _connectionFactory;

    public UpdateRepository(PostgresConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IReadOnlyList<Update>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        var updates = await connection.QueryAsync<Update>("SELECT * FROM updates");
        return updates.AsList();
    }

    public async Task<Update?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        if (!Guid.TryParse(id, out _)) return null;
        
        return await connection.QuerySingleOrDefaultAsync<Update>(
            "SELECT * FROM updates WHERE id = @Id::uuid", 
            new { Id = id });
    }

    public async Task<Update> CreateAsync(Update update, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        
        // Supabase implementation throws InvalidOperationException on unique constraint violation.
        // We can replicate this or just let it throw PostgresException.
        // Let's use INSERT ... ON CONFLICT DO NOTHING RETURNING * to detect duplication
        // Or simply INSERT and catch exception. 
        // The Supabase repo catches PostgrestException.
        // We'll use simple INSERT for now, assuming ID is unique (guid or string).
        
        var sql = @"
            INSERT INTO updates (id, machine_id, info, type) 
            VALUES (@Id, @MachineId, @Info, @Type) 
            RETURNING *";

        try 
        {
            var created = await connection.QuerySingleAsync<Update>(sql, update);
            return created;
        }
        catch (Npgsql.PostgresException ex) when (ex.SqlState == "23505") // Unique violation
        {
            throw new InvalidOperationException($"Update with id '{update.Id}' already exists.", ex);
        }
    }

    public async Task<bool> UpdateAsync(Update update, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        if (!Guid.TryParse(update.Id, out _)) return false;
        
        var sql = @"
            UPDATE updates 
            SET machine_id = @MachineId, info = @Info, type = @Type
            WHERE id = @Id::uuid";
            
        var affected = await connection.ExecuteAsync(sql, update);
        return affected > 0;
    }

    public async Task<bool> DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        if (!Guid.TryParse(id, out _)) return false;
        
        var affected = await connection.ExecuteAsync("DELETE FROM updates WHERE id = @Id::uuid", new { Id = id });
        return affected > 0;
    }
}
