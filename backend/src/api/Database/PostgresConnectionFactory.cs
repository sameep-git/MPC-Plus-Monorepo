using System.Data;
using Api.Configuration;
using Microsoft.Extensions.Options;
using Npgsql;

namespace Api.Database;

public class PostgresConnectionFactory(IOptions<DatabaseOptions> options)
{
    public IDbConnection CreateConnection()
    {
        var connectionString = options.Value.ConnectionString;
        
        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new InvalidOperationException("The database connection string is not initialized. Please ensure POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB are set in your .env file or environment.");
        }
        
        return new NpgsqlConnection(connectionString);
    }
}
