using Api.Configuration;
using Api.Database;
using Api.Database.TypeHandlers;
using Api.Repositories;
using Api.Repositories.Abstractions;
using Dapper;
using Microsoft.Extensions.DependencyInjection;

namespace Api.Extensions;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        // Bind DatabaseOptions
        services.Configure<DatabaseOptions>(configuration.GetSection(DatabaseOptions.SectionName));

        // Register PostgresConnectionFactory
        services.AddSingleton<PostgresConnectionFactory>();

        // Configure Dapper
        DefaultTypeMap.MatchNamesWithUnderscores = true;
        
        // Register TypeHandlers for JSON columns
        SqlMapper.AddTypeHandler(new JsonTypeHandler<List<string>>());
        SqlMapper.AddTypeHandler(new DictionaryDoubleJsonTypeHandler()); // Replaces JsonTypeHandler<Dictionary<string, double>>
        SqlMapper.AddTypeHandler(new JsonTypeHandler<Dictionary<string, string>>());
        SqlMapper.AddTypeHandler(new StringTypeHandler());
        SqlMapper.AddTypeHandler(new DateOnlyTypeHandler());
        SqlMapper.AddTypeHandler(new NullableDateOnlyTypeHandler());

        // Register Repositories
        services.AddScoped<IMachineRepository, MachineRepository>();
        services.AddScoped<IBeamRepository, BeamRepository>();
        services.AddScoped<IGeoCheckRepository, GeoCheckRepository>();
        services.AddScoped<IThresholdRepository, ThresholdRepository>();
        services.AddScoped<IBaselineRepository, BaselineRepository>();
        services.AddScoped<IUpdateRepository, UpdateRepository>();
        services.AddScoped<IDocFactorRepository, DocFactorRepository>();

        return services;
    }
}
