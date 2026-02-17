using System.Data;
using Dapper;

namespace Api.Database.TypeHandlers;

/// <summary>
/// Handles implicit conversion of database types (like GUID) to string properties.
/// Necessary because Dapper/Npgsql fails to cast Guid to String automatically.
/// </summary>
public class StringTypeHandler : SqlMapper.TypeHandler<string?>
{
    public override void SetValue(IDbDataParameter parameter, string? value)
    {
        parameter.Value = (object?)value ?? DBNull.Value;
    }

    public override string? Parse(object value)
    {
        return value?.ToString();
    }
}
