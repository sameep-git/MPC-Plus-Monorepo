using Api.Extensions;
using Api.Services;
using DotNetEnv;
using QuestPDF.Infrastructure;

// Load environment variables from .env file in project root
// Navigate up from bin/Debug/net9.0/ to project root (typically 5 levels up)
var rootDir = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
var envPath = Path.Combine(rootDir, ".env");
if (File.Exists(envPath))
{
    Env.Load(envPath);
}
else
{
    Env.Load();
}

QuestPDF.Settings.License = LicenseType.Community;

var builder = WebApplication.CreateBuilder(args);

// Override configuration with environment variables
var supabaseUrl = Environment.GetEnvironmentVariable("SUPABASE_URL");
var supabaseKey = Environment.GetEnvironmentVariable("SUPABASE_KEY");

Console.WriteLine($"[DEBUG] SUPABASE_URL: {supabaseUrl}");
Console.WriteLine($"[DEBUG] SUPABASE_KEY: {(string.IsNullOrWhiteSpace(supabaseKey) ? "EMPTY" : "SET")}");

builder.Configuration["Supabase:Url"] = supabaseUrl;
builder.Configuration["Supabase:Key"] = supabaseKey;

builder.Services.AddMachineDataAccess(builder.Configuration);
builder.Services.AddBeamDataAccess(builder.Configuration);
builder.Services.AddUpdateDataAccess(builder.Configuration);
builder.Services.AddGeoCheckDataAccess(builder.Configuration);
builder.Services.AddThresholdDataAccess(builder.Configuration);

builder.Services.AddScoped<IReportService, ReportService>();

// Add services to the container.
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });
builder.Services.AddOpenApi();

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("http://localhost:3000")
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

if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}

app.UseCors("AllowFrontend");

app.MapControllers();

app.Run();
