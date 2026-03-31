using Dapper;
using Api.Database;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;

namespace Api.Controllers;

[Authorize]
[ApiController]
[Route("api/[controller]")]
public class SettingsController(PostgresConnectionFactory connectionFactory) : ControllerBase
{
    /// <summary>GET /api/settings/timezone — returns the configured IANA timezone, or null.</summary>
    [HttpGet("timezone")]
    public async Task<ActionResult<object>> GetTimezone(CancellationToken cancellationToken)
    {
        using var connection = connectionFactory.CreateConnection();
        var value = await connection.QueryFirstOrDefaultAsync<string>(
            "SELECT value FROM app_settings WHERE key = 'timezone'");

        return Ok(new { timezone = value });
    }

    /// <summary>PUT /api/settings/timezone — upserts the timezone.</summary>
    [HttpPut("timezone")]
    public async Task<IActionResult> SetTimezone([FromBody] TimezoneRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Timezone))
            return BadRequest("Timezone must not be empty.");

        // Validate that it is a known IANA time zone
        try
        {
            TimeZoneConverter.TZConvert.GetTimeZoneInfo(request.Timezone);
        }
        catch
        {
            return BadRequest($"Unknown timezone: '{request.Timezone}'.");
        }

        using var connection = connectionFactory.CreateConnection();
        await connection.ExecuteAsync(@"
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('timezone', @Timezone, now())
            ON CONFLICT (key) DO UPDATE SET value = @Timezone, updated_at = now()",
            new { request.Timezone });

        return Ok(new { timezone = request.Timezone });
    }
}

public record TimezoneRequest(string Timezone);
