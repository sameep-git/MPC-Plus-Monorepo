using Api.Configuration;
using Api.Repositories;
using Api.Repositories.Abstractions;
using Api.Repositories.InMemory;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Supabase;

namespace Api.Extensions;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddMachineDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        var databaseProvider = configuration[$"{DatabaseOptions.SectionName}:Provider"] ?? new DatabaseOptions().Provider;

        switch (databaseProvider.ToLowerInvariant())
        {
            case "supabase":
                services.AddSingleton<InMemoryMachineRepository>();
                services.AddSupabaseMachineDataAccess(configuration);
                break;
            case "inmemory":
            case "mock":
                services.AddSingleton<InMemoryMachineRepository>();
                services.AddInMemoryMachineDataAccess();
                break;
            default:
                throw new InvalidOperationException($"Unsupported database provider '{databaseProvider}'.");
        }

        return services;
    }

    private static IServiceCollection AddSupabaseMachineDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<SupabaseSettings>(configuration.GetSection(SupabaseSettings.SectionName));

        services.AddScoped<IMachineRepository>(provider =>
        {
            var settings = provider.GetRequiredService<IOptions<SupabaseSettings>>().Value;
            var loggerFactory = provider.GetRequiredService<ILoggerFactory>();

            if (string.IsNullOrWhiteSpace(settings.Url) || string.IsNullOrWhiteSpace(settings.Key))
            {
                loggerFactory
                    .CreateLogger("DataAccess")
                    .LogWarning("Supabase credentials missing. Using in-memory machine repository.");

                return provider.GetRequiredService<InMemoryMachineRepository>();
            }

            var options = new SupabaseOptions
            {
                AutoConnectRealtime = false
            };

            var client = new Client(settings.Url, settings.Key, options);
            client.InitializeAsync().GetAwaiter().GetResult();

            var logger = loggerFactory.CreateLogger<SupabaseMachineRepository>();
            return new SupabaseMachineRepository(client, logger);
        });

        return services;
    }

    private static IServiceCollection AddInMemoryMachineDataAccess(this IServiceCollection services)
    {
        services.AddSingleton<IMachineRepository>(provider => provider.GetRequiredService<InMemoryMachineRepository>());
        return services;
    }

    public static IServiceCollection AddBeamDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        var databaseProvider = configuration[$"{DatabaseOptions.SectionName}:Provider"] ?? new DatabaseOptions().Provider;

        switch (databaseProvider.ToLowerInvariant())
        {
            case "supabase":
                services.AddSingleton<InMemoryBeamRepository>();
                services.AddSupabaseBeamDataAccess(configuration);
                break;
            case "inmemory":
            case "mock":
                services.AddSingleton<InMemoryBeamRepository>();
                services.AddInMemoryBeamDataAccess();
                break;
            default:
                throw new InvalidOperationException($"Unsupported database provider '{databaseProvider}'.");
        }

        return services;
    }

    private static IServiceCollection AddSupabaseBeamDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<SupabaseSettings>(configuration.GetSection(SupabaseSettings.SectionName));

        services.AddScoped<IBeamRepository>(provider =>
        {
            var settings = provider.GetRequiredService<IOptions<SupabaseSettings>>().Value;
            var loggerFactory = provider.GetRequiredService<ILoggerFactory>();

            if (string.IsNullOrWhiteSpace(settings.Url) || string.IsNullOrWhiteSpace(settings.Key))
            {
                loggerFactory
                    .CreateLogger("DataAccess")
                    .LogWarning("Supabase credentials missing. Using in-memory beam repository.");

                return provider.GetRequiredService<InMemoryBeamRepository>();
            }

            var options = new SupabaseOptions
            {
                AutoConnectRealtime = false
            };

            var client = new Client(settings.Url, settings.Key, options);
            client.InitializeAsync().GetAwaiter().GetResult();

            var logger = loggerFactory.CreateLogger<SupabaseBeamRepository>();
            return new SupabaseBeamRepository(client, logger);
        });

        return services;
    }

    private static IServiceCollection AddInMemoryBeamDataAccess(this IServiceCollection services)
    {
        services.AddSingleton<IBeamRepository>(provider => provider.GetRequiredService<InMemoryBeamRepository>());
        return services;
    }

    public static IServiceCollection AddUpdateDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<SupabaseSettings>(configuration.GetSection(SupabaseSettings.SectionName));

        services.AddScoped<IUpdateRepository>(provider =>
        {
            var settings = provider.GetRequiredService<IOptions<SupabaseSettings>>().Value;
            var loggerFactory = provider.GetRequiredService<ILoggerFactory>();

            if (string.IsNullOrWhiteSpace(settings.Url) || string.IsNullOrWhiteSpace(settings.Key))
            {
                throw new InvalidOperationException("Supabase credentials are required for Update repository.");
            }

            var options = new SupabaseOptions
            {
                AutoConnectRealtime = false
            };

            var client = new Client(settings.Url, settings.Key, options);
            client.InitializeAsync().GetAwaiter().GetResult();

            var logger = loggerFactory.CreateLogger<SupabaseUpdateRepository>();
            return new SupabaseUpdateRepository(client, logger);
        });

        return services;
    }

    public static IServiceCollection AddGeoCheckDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<SupabaseSettings>(configuration.GetSection(SupabaseSettings.SectionName));

        services.AddScoped<IGeoCheckRepository>(provider =>
        {
            var settings = provider.GetRequiredService<IOptions<SupabaseSettings>>().Value;
            var loggerFactory = provider.GetRequiredService<ILoggerFactory>();

            if (string.IsNullOrWhiteSpace(settings.Url) || string.IsNullOrWhiteSpace(settings.Key))
            {
                throw new InvalidOperationException("Supabase credentials are required for GeoCheck repository.");
            }

            var options = new SupabaseOptions
            {
                AutoConnectRealtime = false
            };

            var client = new Client(settings.Url, settings.Key, options);
            client.InitializeAsync().GetAwaiter().GetResult();

            var logger = loggerFactory.CreateLogger<SupabaseGeoCheckRepository>();
            return new SupabaseGeoCheckRepository(client, logger);
        });

        return services;
    }

    public static IServiceCollection AddThresholdDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<SupabaseSettings>(configuration.GetSection(SupabaseSettings.SectionName));

        services.AddScoped<IThresholdRepository>(provider =>
        {
            var settings = provider.GetRequiredService<IOptions<SupabaseSettings>>().Value;
            var loggerFactory = provider.GetRequiredService<ILoggerFactory>();

            if (string.IsNullOrWhiteSpace(settings.Url) || string.IsNullOrWhiteSpace(settings.Key))
            {
                throw new InvalidOperationException("Supabase credentials are required for Threshold repository.");
            }

            var options = new SupabaseOptions
            {
                AutoConnectRealtime = false
            };

            var client = new Client(settings.Url, settings.Key, options);
            client.InitializeAsync().GetAwaiter().GetResult();

            var logger = loggerFactory.CreateLogger<SupabaseThresholdRepository>();
            return new SupabaseThresholdRepository(client, logger);
        });

        return services;
    }

    public static IServiceCollection AddDocFactorDataAccess(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<SupabaseSettings>(configuration.GetSection(SupabaseSettings.SectionName));

        services.AddScoped<IDocFactorRepository>(provider =>
        {
            var settings = provider.GetRequiredService<IOptions<SupabaseSettings>>().Value;
            var loggerFactory = provider.GetRequiredService<ILoggerFactory>();

            if (string.IsNullOrWhiteSpace(settings.Url) || string.IsNullOrWhiteSpace(settings.Key))
            {
                throw new InvalidOperationException("Supabase credentials are required for DocFactor repository.");
            }

            var options = new SupabaseOptions
            {
                AutoConnectRealtime = false
            };

            var client = new Client(settings.Url, settings.Key, options);
            client.InitializeAsync().GetAwaiter().GetResult();

            var logger = loggerFactory.CreateLogger<SupabaseDocFactorRepository>();
            return new SupabaseDocFactorRepository(client, logger);
        });

        return services;
    }
}

