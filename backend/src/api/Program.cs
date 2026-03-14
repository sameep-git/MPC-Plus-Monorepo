using Api.Extensions;
using Api.Services;
using DotNetEnv;
using QuestPDF.Infrastructure;

// Enable legacy timestamp behavior for PostgreSQL (fixes strict Utc mapping issues)
AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);

// Load environment variables dynamically by searching upwards for .env files.
// Files are loaded from root → local so that local (closer) .env files override root ones.
var currentDir = new DirectoryInfo(AppContext.BaseDirectory);
var envFiles = new List<string>();
while (currentDir != null)
{
    var path = Path.Combine(currentDir.FullName, ".env");
    if (File.Exists(path)) envFiles.Add(path);
    currentDir = currentDir.Parent;
}

// Also check from CurrentDirectory if not already covered
var currentSearch = new DirectoryInfo(Directory.GetCurrentDirectory());
while (currentSearch != null)
{
    var path = Path.Combine(currentSearch.FullName, ".env");
    if (File.Exists(path) && !envFiles.Contains(path)) envFiles.Add(path);
    currentSearch = currentSearch.Parent;
}

if (envFiles.Any())
{
    // Load in reverse order (highest parent first)
    foreach (var envPath in envFiles.AsEnumerable().Reverse())
    {
        Env.Load(envPath);
    }
}
else
{
    Env.Load();
}

QuestPDF.Settings.License = LicenseType.Community;

var builder = WebApplication.CreateBuilder(args);

// Ensure the Database:ConnectionString is populated from ENV if missing in appsettings.json
var connString = builder.Configuration["Database:ConnectionString"];
if (string.IsNullOrWhiteSpace(connString))
{
    // Try standard ConnectionStrings__Database (used in docker-compose)
    connString = builder.Configuration.GetConnectionString("Database");
    
    // If still empty, construct from individual .env components
    if (string.IsNullOrWhiteSpace(connString))
    {
        var pgUser = Environment.GetEnvironmentVariable("POSTGRES_USER");
        var pgPass = Environment.GetEnvironmentVariable("POSTGRES_PASSWORD");
        var pgDb = Environment.GetEnvironmentVariable("POSTGRES_DB");
        var pgHost = Environment.GetEnvironmentVariable("POSTGRES_HOST") ?? "localhost";
        var pgPort = Environment.GetEnvironmentVariable("POSTGRES_PORT") ?? "5432";
        
        if (!string.IsNullOrWhiteSpace(pgUser) && !string.IsNullOrWhiteSpace(pgPass) && !string.IsNullOrWhiteSpace(pgDb))
        {
            connString = $"Host={pgHost};Port={pgPort};Database={pgDb};Username={pgUser};Password={pgPass}";
        }
    }
}

// Force set the value directly in the Configuration object BEFORE configuring services
if (!string.IsNullOrWhiteSpace(connString))
{
    builder.Configuration["Database:ConnectionString"] = connString;
}
else
{
    Console.WriteLine("Warning: Database connection string is not configured. Ensure POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB are set in your environment.");
}

// Register Data Access Layer (Npgsql + Dapper)
builder.Services.AddDataAccess(builder.Configuration);

// Load JWT secret from environment variable if not already set in config
var jwtSecret = Environment.GetEnvironmentVariable("JWT_SECRET");
if (!string.IsNullOrWhiteSpace(jwtSecret))
{
    builder.Configuration["Jwt:Secret"] = jwtSecret;
}

// Register Authentication Services
builder.Services.AddAuthenticationServices(builder.Configuration);

builder.Services.AddScoped<IReportService, ReportService>();

// Add services to the container.
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });
builder.Services.AddOpenApi();

// CORS origins: configurable via CORS_ORIGINS env var (comma-separated), defaults to localhost:3000
var corsOrigins = Environment.GetEnvironmentVariable("CORS_ORIGINS")?.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
    ?? new[] { "http://localhost:3000" };

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins(corsOrigins)
              .AllowAnyMethod()
              .AllowAnyHeader();
    });   
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.UseStaticFiles(); // Enable static file serving for images

if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}

app.MapControllers();

app.Run();
