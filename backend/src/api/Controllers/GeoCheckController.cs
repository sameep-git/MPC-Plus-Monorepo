using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/geochecks")]
public class GeoCheckController : ControllerBase
{
    private readonly IGeoCheckRepository _repository;
    private readonly IThresholdRepository _thresholdRepository;
    private readonly ILogger<GeoCheckController> _logger;

    public GeoCheckController(IGeoCheckRepository repository, IThresholdRepository thresholdRepository, ILogger<GeoCheckController> logger)
    {
        _repository = repository;
        _thresholdRepository = thresholdRepository;
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
            includeDetails: true, // Frontend expects full details in list view
            cancellationToken: cancellationToken);

        var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
        foreach (var gc in geoChecks)
        {
            CalculateStatus(gc, thresholds);
        }

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

        var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
        CalculateStatus(geoCheck, thresholds);

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
            
            var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
            CalculateStatus(created, thresholds);
            
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

        var approvedDate = DateTime.UtcNow;
        var results = new List<string>();
        var errors = new List<string>();

        foreach (var id in request.GeoCheckIds)
        {
            var updated = await _repository.ApproveAsync(id, request.ApprovedBy, approvedDate, cancellationToken);
            if (!updated)
            {
                errors.Add($"Geometry check with id '{id}' was not found or failed to update.");
            }
            else
            {
                results.Add(id);
            }
        }

        return Ok(new { approved = results, errors });
    }
    
    // Look up a threshold value
    private static double? FindThreshold(IEnumerable<Threshold> thresholds, string machineId, string metricType)
    {
        var match = thresholds.FirstOrDefault(t =>
            t.MachineId == machineId &&
            t.CheckType.Equals("geometry", StringComparison.OrdinalIgnoreCase) &&
            t.MetricType.Equals(metricType, StringComparison.OrdinalIgnoreCase));
        return match?.Value;
    }

    // Determine if a metric value passes the threshold (within ± threshold)
    private static bool IsWithinThreshold(double? value, double? threshold)
    {
        if (!value.HasValue || !threshold.HasValue) return true;
        return Math.Abs(value.Value) <= threshold.Value;
    }

    private void CalculateStatus(GeoCheck geo, IReadOnlyList<Threshold> thresholds)
    {
        geo.MetricStatuses ??= new Dictionary<string, string>();

        var checks = new (string metricType, string key, double? value)[] {
            ("Iso Center Size", "IsoCenterSize", geo.IsoCenterSize),
            ("Iso Center MV Offset", "IsoCenterMVOffset", geo.IsoCenterMVOffset),
            ("Iso Center KV Offset", "IsoCenterKVOffset", geo.IsoCenterKVOffset),
            ("Collimation Rotation Offset", "CollimationRotationOffset", geo.CollimationRotationOffset),
            ("Gantry Absolute", "GantryAbsolute", geo.GantryAbsolute),
            ("Gantry Relative", "GantryRelative", geo.GantryRelative),
            ("Couch Lat", "CouchLat", geo.CouchLat),
            ("Couch Lng", "CouchLng", geo.CouchLng),
            ("Couch Vrt", "CouchVrt", geo.CouchVrt),
            ("Max Position Error", "MaxPositionError", geo.CouchMaxPositionError),
            ("Mean Offset A", "MeanOffsetA", geo.MeanOffsetA),
            ("Max Offset A", "MaxOffsetA", geo.MaxOffsetA),
            ("Mean Offset B", "MeanOffsetB", geo.MeanOffsetB),
            ("Max Offset B", "MaxOffsetB", geo.MaxOffsetB),
            ("Jaw X1", "JawX1", geo.JawX1),
            ("Jaw X2", "JawX2", geo.JawX2),
            ("Jaw Y1", "JawY1", geo.JawY1),
            ("Jaw Y2", "JawY2", geo.JawY2),
            ("Parallelism X1", "ParallelismX1", geo.JawParallelismX1),
            ("Parallelism X2", "ParallelismX2", geo.JawParallelismX2),
            ("Parallelism Y1", "ParallelismY1", geo.JawParallelismY1),
            ("Parallelism Y2", "ParallelismY2", geo.JawParallelismY2)
        };

        foreach (var check in checks)
        {
            var threshold = FindThreshold(thresholds, geo.MachineId, check.metricType);
            if (!IsWithinThreshold(check.value, threshold))
            {
                geo.MetricStatuses[check.key] = "FAIL";
            }
        }

        // Special handling for leaf arrays (mlc_leaf_position and mlc_backlash keys mapped by frontend)
        var leafThreshold = FindThreshold(thresholds, geo.MachineId, "mlc_leaf_position");
        if (leafThreshold.HasValue)
        {
            if (geo.MLCLeavesA != null && geo.MLCLeavesA.Values.Any(v => !IsWithinThreshold(v, leafThreshold)))
                geo.MetricStatuses["mlc_leaf_position"] = "FAIL";
            if (geo.MLCLeavesB != null && geo.MLCLeavesB.Values.Any(v => !IsWithinThreshold(v, leafThreshold)))
                geo.MetricStatuses["mlc_leaf_position"] = "FAIL";
        }

        var backlashThreshold = FindThreshold(thresholds, geo.MachineId, "mlc_backlash");
        if (backlashThreshold.HasValue)
        {
            if (geo.MLCBacklashA != null && geo.MLCBacklashA.Values.Any(v => !IsWithinThreshold(v, backlashThreshold)))
                geo.MetricStatuses["mlc_backlash"] = "FAIL";
            if (geo.MLCBacklashB != null && geo.MLCBacklashB.Values.Any(v => !IsWithinThreshold(v, backlashThreshold)))
                geo.MetricStatuses["mlc_backlash"] = "FAIL";
        }
    }
}

public record AcceptGeoCheckRequest(IEnumerable<string> GeoCheckIds, string ApprovedBy);
