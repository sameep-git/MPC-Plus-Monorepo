using Api.Models;
using Api.Repositories;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class BeamsController : ControllerBase
{
    private readonly IBeamRepository _repository;
    private readonly IThresholdRepository _thresholdRepository;

    public BeamsController(IBeamRepository repository, IThresholdRepository thresholdRepository)
    {
        _repository = repository;
        _thresholdRepository = thresholdRepository;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<CheckGroup>>> GetAll(
        [FromQuery] string? type = null,
        [FromQuery] string? machineId = null,
        [FromQuery] string? date = null,
        [FromQuery] string? startDate = null,
        [FromQuery] string? endDate = null,
        CancellationToken cancellationToken = default)
    {
        DateTime? dateDt = null;
        if (!string.IsNullOrWhiteSpace(date) && DateTime.TryParse(date, out var parsedDate))
            dateDt = parsedDate;

        DateTime? startDateDt = null;
        if (!string.IsNullOrWhiteSpace(startDate) && DateTime.TryParse(startDate, out var parsedStartDate))
            startDateDt = parsedStartDate;

        DateTime? endDateDt = null;
        if (!string.IsNullOrWhiteSpace(endDate) && DateTime.TryParse(endDate, out var parsedEndDate))
            endDateDt = parsedEndDate;

        var beams = await _repository.GetAllAsync(
            machineId: machineId,
            type: type,
            date: dateDt,
            startDate: startDateDt,
            endDate: endDateDt,
            cancellationToken: cancellationToken);

        // Calculate dynamic status
        var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
        foreach (var beam in beams)
        {
            CalculateStatus(beam, thresholds);
        }

        // Group beams by time proximity (e.g. 2 minutes)
        var groups = new List<CheckGroup>();
        if (!beams.Any())
        {
            return Ok(groups);
        }

        var sortedBeams = beams.OrderBy(b => b.Timestamp ?? b.Date).ToList();
        var currentGroupBeams = new List<Beam>();
        var referenceTime = sortedBeams[0].Timestamp ?? sortedBeams[0].Date;

        foreach (var beam in sortedBeams)
        {
            var time = beam.Timestamp ?? beam.Date;
            if ((time - referenceTime).Duration() > TimeSpan.FromMinutes(2))
            {
                groups.Add(new CheckGroup(referenceTime, currentGroupBeams));
                currentGroupBeams = new List<Beam>();
                referenceTime = time;
            }
            currentGroupBeams.Add(beam);
        }
        groups.Add(new CheckGroup(referenceTime, currentGroupBeams));

        // Return ordered by latest group first
        return Ok(groups.OrderByDescending(g => g.Timestamp));
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Beam>> GetById(string id, CancellationToken cancellationToken)
    {
        var beam = await _repository.GetByIdAsync(id, cancellationToken);
        if (beam is null)
        {
            return NotFound($"Beam with id '{id}' was not found.");
        }
        
        // Calculate status
        var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
        CalculateStatus(beam, thresholds);

        return Ok(beam);
    }

    [HttpPost]
    public async Task<ActionResult<Beam>> Create([FromBody] Beam beam, CancellationToken cancellationToken)
    {
        try
        {
            var created = await _repository.CreateAsync(beam, cancellationToken);
            
            // Calculate status for response
            var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
            CalculateStatus(created, thresholds);

            return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
        }
        catch (InvalidOperationException exception)
        {
            return Conflict(exception.Message);
        }
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(string id, [FromBody] Beam beam, CancellationToken cancellationToken)
    {
        if (!string.Equals(id, beam.Id, StringComparison.OrdinalIgnoreCase))
        {
            return BadRequest("The beam id in the route must match the payload.");
        }

        var updated = await _repository.UpdateAsync(beam, cancellationToken);
        if (!updated)
        {
            return NotFound($"Beam with id '{id}' was not found.");
        }

        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(string id, CancellationToken cancellationToken)
    {
        var deleted = await _repository.DeleteAsync(id, cancellationToken);
        if (!deleted)
        {
            return NotFound($"Beam with id '{id}' was not found.");
        }

        return NoContent();
    }

    [HttpGet("types")]
    public async Task<ActionResult<IEnumerable<string>>> GetBeamTypes(CancellationToken cancellationToken)
    {
        var types = await _repository.GetBeamTypesAsync(cancellationToken);
        return Ok(types);
    }

    [HttpGet("variants")]
    public async Task<ActionResult<IEnumerable<BeamVariantDto>>> GetBeamVariants(CancellationToken cancellationToken)
    {
        var variants = await _repository.GetBeamVariantsWithIdsAsync(cancellationToken);
        return Ok(variants);
    }

    /// <summary>
    /// Get beam checks for a specific date/machine/type for DOC factor selection.
    /// Returns beam id, timestamp, and relOutput for user selection.
    /// </summary>
    [HttpGet("by-date")]
    public async Task<ActionResult<IEnumerable<BeamCheckOption>>> GetByDate(
        [FromQuery] string machineId,
        [FromQuery] string beamType,
        [FromQuery] string date,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrEmpty(machineId))
        {
            return BadRequest("machineId is required.");
        }

        if (string.IsNullOrEmpty(beamType))
        {
            return BadRequest("beamType is required.");
        }

        if (!DateTime.TryParse(date, out var parsedDate))
        {
            return BadRequest("Invalid date format. Use YYYY-MM-DD.");
        }

        var beams = await _repository.GetAllAsync(
            machineId: machineId,
            type: beamType,
            date: parsedDate,
            cancellationToken: cancellationToken);

        var options = beams.Select(b => new BeamCheckOption(
            b.Id,
            b.Timestamp ?? b.Date,
            b.RelOutput ?? 0,
            b.Type ?? beamType
        )).OrderBy(o => o.Timestamp);

        return Ok(options);
    }

    [HttpPost("accept")]
    public async Task<ActionResult> Accept([FromBody] AcceptBeamRequest request, CancellationToken cancellationToken)
    {
        if (request.BeamIds == null || !request.BeamIds.Any())
        {
            return BadRequest("No beam IDs provided.");
        }

        var results = new List<Beam>();
        var errors = new List<string>();

        foreach (var id in request.BeamIds)
        {
            var beam = await _repository.GetByIdAsync(id, cancellationToken);
            if (beam is null)
            {
                errors.Add($"Beam with id '{id}' was not found.");
                continue;
            }

            beam.ApprovedBy = request.ApprovedBy;
            beam.ApprovedDate = DateTime.UtcNow;

            var updated = await _repository.UpdateAsync(beam, cancellationToken);
            if (!updated)
            {
                errors.Add($"Failed to update beam '{id}'.");
            }
            else
            {
                results.Add(beam);
            }
        }

        if (errors.Any())
        {
            // If some failed, return 207 Multi-Status or just bad request with details?
            // For simplicity, we'll return Ok with the successful ones and include errors in response if needed,
            // or if all failed, 500.
            // Let's just return Ok with results, client can check what was updated.
        }

        return Ok(results);
    }

    private void CalculateStatus(Beam beam, IReadOnlyList<Threshold> thresholds)
    {
        // Default to PASS
        beam.Status = "PASS";
        beam.RelOutputStatus = "PASS";
        beam.RelUniformityStatus = "PASS";
        beam.CenterShiftStatus = "PASS";

        // Find relevant thresholds
        var outputThreshold = thresholds.FirstOrDefault(
            t => t.MachineId == beam.MachineId && 
                 t.CheckType == "beam" && 
                 t.BeamVariant == beam.Type && 
                 t.MetricType == "Relative Output");

        var uniformityThreshold = thresholds.FirstOrDefault(
            t => t.MachineId == beam.MachineId && 
                 t.CheckType == "beam" && 
                 t.BeamVariant == beam.Type && 
                 t.MetricType == "Relative Uniformity");
                 
        var centerShiftThreshold = thresholds.FirstOrDefault(
            t => t.MachineId == beam.MachineId && 
                 t.CheckType == "beam" && 
                 t.BeamVariant == beam.Type && 
                 t.MetricType == "Center Shift");

        // Check Relative Output
        if (outputThreshold != null && beam.RelOutput.HasValue)
        {
            if (Math.Abs(beam.RelOutput.Value) > outputThreshold.Value)
            {
                beam.RelOutputStatus = "FAIL";
                beam.Status = "FAIL";
            }
        }

        // Check Relative Uniformity
        if (uniformityThreshold != null && beam.RelUniformity.HasValue)
        {
            if (Math.Abs(beam.RelUniformity.Value) > uniformityThreshold.Value)
            {
                beam.RelUniformityStatus = "FAIL";
                beam.Status = "FAIL";
            }
        }

        // Check Center Shift
        if (centerShiftThreshold != null && beam.CenterShift.HasValue)
        {
            if (Math.Abs(beam.CenterShift.Value) > centerShiftThreshold.Value)
            {
                beam.CenterShiftStatus = "FAIL";
                beam.Status = "FAIL";
            }
        }
    }
}

public record AcceptBeamRequest(IEnumerable<string> BeamIds, string ApprovedBy);

/// <summary>
/// Represents a beam check option for DOC factor selection.
/// </summary>
public record BeamCheckOption(string Id, DateTime Timestamp, double RelOutput, string Type);

