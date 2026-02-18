using System.Data;
using Api.Configuration;
using Microsoft.Extensions.Options;
using Npgsql;

namespace Api.Database;

public class PostgresConnectionFactory(IOptions<DatabaseOptions> options)
{
    private readonly string _connectionString = options.Value.ConnectionString;

    public IDbConnection CreateConnection()
    {
        return new NpgsqlConnection(_connectionString);
    }
}
