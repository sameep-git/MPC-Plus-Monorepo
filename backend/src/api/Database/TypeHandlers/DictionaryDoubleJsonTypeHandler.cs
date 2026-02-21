using System.Data;
using Dapper;
using System.Text.Json;

namespace Api.Database.TypeHandlers;

public class DictionaryDoubleJsonTypeHandler : SqlMapper.TypeHandler<Dictionary<string, double>?>
{
    public override void SetValue(IDbDataParameter parameter, Dictionary<string, double>? value)
    {
        parameter.Value = (value == null) ? DBNull.Value : JsonSerializer.Serialize(value);
        parameter.DbType = DbType.Object;
    }

    public override Dictionary<string, double>? Parse(object value)
    {
        if (value == null || value is DBNull) return null;
        var json = value.ToString();
        if (string.IsNullOrEmpty(json)) return null;

        try 
        {
             // Handle Array format from geochecks_full view: [{"leaf_number": 1, "value": 0.1}, ...]
             if (json.TrimStart().StartsWith("["))
             {
                 var list = JsonSerializer.Deserialize<List<LeafItem>>(json);
                 return list?.ToDictionary(x => $"Leaf{x.leaf_number}", x => x.value);
             }

             // Handle double-serialized JSONB (string within string)
             if (json.StartsWith("\"")) 
             {
                 json = JsonSerializer.Deserialize<string>(json);
                 if (string.IsNullOrEmpty(json)) return null;
             }

             return JsonSerializer.Deserialize<Dictionary<string, double>>(json);
        }
        catch 
        { 
            return null; 
        }
    }
    
    private class LeafItem 
    { 
        public int leaf_number { get; set; } 
        public double value { get; set; } 
    }
}