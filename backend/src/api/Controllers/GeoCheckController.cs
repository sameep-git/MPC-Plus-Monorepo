using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/geochecks")]
public class GeoCheckController : ControllerBase
{
    private readonly IGeoCheckRepository _repository;
    private readonly ILogger<GeoCheckController> _logger;

    public GeoCheckController(IGeoCheckRepository repository, ILogger<GeoCheckController> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    /// <summary>
    /// Get geometry check data filtered by various parameters.
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<GeoCheck>>> GetAll(
        [FromQuery] string? type = null,
        [FromQuery(Name = "machine-id")] string? machineId = null,
        [FromQuery] string? date = null,
        [FromQuery(Name = "start-date")] string? startDate = null,
        [FromQuery(Name = "end-date")] string? endDate = null,
        CancellationToken cancellationToken = default)
    {
        DateTime? dateDt = null;
        if (!string.IsNullOrWhiteSpace(date))
        {
            if (!DateTime.TryParse(date, out var parsedDate))
            {
                return BadRequest($"Invalid date format: {date}");
            }
            dateDt = parsedDate;
        }

        DateTime? startDateDt = null;
        if (!string.IsNullOrWhiteSpace(startDate))
        {
            if (!DateTime.TryParse(startDate, out var parsedStartDate))
            {
                return BadRequest($"Invalid start-date format: {startDate}");
            }
            startDateDt = parsedStartDate;
        }

        DateTime? endDateDt = null;
        if (!string.IsNullOrWhiteSpace(endDate))
        {
            if (!DateTime.TryParse(endDate, out var parsedEndDate))
            {
                return BadRequest($"Invalid end-date format: {endDate}");
            }
            endDateDt = parsedEndDate;
        }

        var geoChecks = await _repository.GetAllAsync(
            machineId: machineId,
            type: type,
            date: dateDt,
            startDate: startDateDt,
            endDate: endDateDt,
            cancellationToken: cancellationToken);

        return Ok(geoChecks);
    }

    /// <summary>
    /// Get a specific geometry check by ID.
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<GeoCheck>> GetById(string id, CancellationToken cancellationToken)
    {
        var geoCheck = await _repository.GetByIdAsync(id, cancellationToken);
        if (geoCheck is null)
        {
            return NotFound($"Geometry check with id '{id}' was not found.");
        }

        return Ok(geoCheck);
    }

    /// <summary>
    /// Create a new geometry check.
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<GeoCheck>> Create([FromBody] GeoCheck geoCheck, CancellationToken cancellationToken)
    {
        try
        {
            var created = await _repository.CreateAsync(geoCheck, cancellationToken);
            return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
        }
        catch (InvalidOperationException exception)
        {
            _logger.LogWarning(exception, "Conflict creating geometry check");
            return Conflict(exception.Message);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating geometry check");
            return StatusCode(500, "An error occurred while creating the geometry check.");
        }
    }

    /// <summary>
    /// Update an existing geometry check.
    /// </summary>
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(string id, [FromBody] GeoCheck geoCheck, CancellationToken cancellationToken)
    {
        if (!string.Equals(id, geoCheck.Id, StringComparison.OrdinalIgnoreCase))
        {
            return BadRequest("The geometry check id in the route must match the payload.");
        }

        var updated = await _repository.UpdateAsync(geoCheck, cancellationToken);
        if (!updated)
        {
            return NotFound($"Geometry check with id '{id}' was not found.");
        }

        return NoContent();
    }

    /// <summary>
    /// Delete a geometry check.
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(string id, CancellationToken cancellationToken)
    {
        var deleted = await _repository.DeleteAsync(id, cancellationToken);
        if (!deleted)
        {
            return NotFound($"Geometry check with id '{id}' was not found.");
        }

        return NoContent();
    }
    [HttpPost("accept")]
    public async Task<ActionResult> Accept([FromBody] AcceptGeoCheckRequest request, CancellationToken cancellationToken)
    {
        if (request.GeoCheckIds == null || !request.GeoCheckIds.Any())
        {
            return BadRequest("No geometry check IDs provided.");
        }

        var results = new List<GeoCheck>();
        var errors = new List<string>();

        foreach (var id in request.GeoCheckIds)
        {
            var geoCheck = await _repository.GetByIdAsync(id, cancellationToken);
            if (geoCheck is null)
            {
                errors.Add($"Geometry check with id '{id}' was not found.");
                continue;
            }

            geoCheck.ApprovedBy = request.ApprovedBy;
            geoCheck.ApprovedDate = DateTime.UtcNow;

            var updated = await _repository.UpdateAsync(geoCheck, cancellationToken);
            if (!updated)
            {
                errors.Add($"Failed to update geometry check '{id}'.");
            }
            else
            {
                results.Add(geoCheck);
            }
        }

        return Ok(results);
    }
}

public record AcceptGeoCheckRequest(IEnumerable<string> GeoCheckIds, string ApprovedBy);
