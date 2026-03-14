using Api.Models;
using Api.Database;
using Dapper;

namespace Api.Repositories;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(string id, CancellationToken cancellationToken = default);
    Task<User?> GetByUsernameAsync(string username, CancellationToken cancellationToken = default);
    Task<User> CreateAsync(User user, CancellationToken cancellationToken = default);
    Task<bool> UpdateAsync(User user, CancellationToken cancellationToken = default);
    Task<IReadOnlyList<User>> GetAllAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<User>> GetPendingUsersAsync(CancellationToken cancellationToken = default);
    Task<bool> UpdateApprovalStatusAsync(string userId, string status, CancellationToken cancellationToken = default);
}

public class UserRepository : IUserRepository
{
    private readonly PostgresConnectionFactory _connectionFactory;

    public UserRepository(PostgresConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<User?> GetByIdAsync(string id, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        const string query = "SELECT id, username, email, full_name as FullName, password_hash as PasswordHash, role, is_active as IsActive, created_at as CreatedAt, last_login_at as LastLoginAt, approval_status as ApprovalStatus FROM users WHERE id = @id";
        return await connection.QueryFirstOrDefaultAsync<User>(query, new { id });
    }

    public async Task<User?> GetByUsernameAsync(string username, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        const string query = "SELECT id, username, email, full_name as FullName, password_hash as PasswordHash, role, is_active as IsActive, created_at as CreatedAt, last_login_at as LastLoginAt, approval_status as ApprovalStatus FROM users WHERE username = @username";
        return await connection.QueryFirstOrDefaultAsync<User>(query, new { username });
    }

    public async Task<User> CreateAsync(User user, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        user.Id = user.Id ?? Guid.NewGuid().ToString();
        user.CreatedAt = DateTime.UtcNow;

        const string query = @"
            INSERT INTO users (id, username, email, full_name, password_hash, role, is_active, created_at, approval_status)
            VALUES (@Id, @Username, @Email, @FullName, @PasswordHash, @Role, @IsActive, @CreatedAt, @ApprovalStatus)
            RETURNING id, username, email, full_name as FullName, password_hash as PasswordHash, role, is_active as IsActive, created_at as CreatedAt, last_login_at as LastLoginAt, approval_status as ApprovalStatus";

        return await connection.QueryFirstAsync<User>(query, user);
    }

    public async Task<bool> UpdateAsync(User user, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        const string query = @"
            UPDATE users 
            SET username = @Username, email = @Email, full_name = @FullName, 
                password_hash = @PasswordHash, role = @Role, is_active = @IsActive, 
                last_login_at = @LastLoginAt, approval_status = @ApprovalStatus
            WHERE id = @Id";

        var result = await connection.ExecuteAsync(query, user);
        return result > 0;
    }

    public async Task<IReadOnlyList<User>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        const string query = "SELECT id, username, email, full_name as FullName, password_hash as PasswordHash, role, is_active as IsActive, created_at as CreatedAt, last_login_at as LastLoginAt, approval_status as ApprovalStatus FROM users ORDER BY created_at DESC";
        var users = await connection.QueryAsync<User>(query);
        return users.ToList();
    }

    public async Task<IReadOnlyList<User>> GetPendingUsersAsync(CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        const string query = "SELECT id, username, email, full_name as FullName, password_hash as PasswordHash, role, is_active as IsActive, created_at as CreatedAt, last_login_at as LastLoginAt, approval_status as ApprovalStatus FROM users WHERE approval_status = 'PENDING' ORDER BY created_at ASC";
        var users = await connection.QueryAsync<User>(query);
        return users.ToList();
    }

    public async Task<bool> UpdateApprovalStatusAsync(string userId, string status, CancellationToken cancellationToken = default)
    {
        using var connection = _connectionFactory.CreateConnection();
        const string query = @"
            UPDATE users 
            SET approval_status = @status,
                is_active = CASE WHEN @status = 'DENIED' THEN false ELSE is_active END
            WHERE id = @userId";

        var result = await connection.ExecuteAsync(query, new { userId, status });
        return result > 0;
    }
}
