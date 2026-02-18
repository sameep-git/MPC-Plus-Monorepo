using System.Data;
using Dapper;
using System.Text.Json;

namespace Api.Database.TypeHandlers;

public class JsonTypeHandler<T> : SqlMapper.TypeHandler<T?>
{
    public override void SetValue(IDbDataParameter parameter, T? value)
    {
        parameter.Value = (value == null) ? DBNull.Value : JsonSerializer.Serialize(value);
        parameter.DbType = DbType.Object; // Postgres JSON/JSONB
    }

    public override T? Parse(object value)
    {
        if (value == null || value is DBNull) return default;
        return JsonSerializer.Deserialize<T>(value.ToString() ?? "");
    }
}
