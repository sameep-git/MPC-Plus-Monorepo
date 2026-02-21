using Api.Models;
using Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class DocFactorsController : ControllerBase
{
    private readonly IDocFactorRepository _repository;
    private readonly ILogger<DocFactorsController> _logger;

    public DocFactorsController(IDocFactorRepository repository, ILogger<DocFactorsController> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    /// <summary>
    /// Get all DOC factors, optionally filtered by machine.
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<DocFactor>>> GetAll(
        [FromQuery] string? machineId,
        CancellationToken cancellationToken)
    {
        IReadOnlyList<DocFactor> docFactors;

        if (!string.IsNullOrEmpty(machineId))
        {
            docFactors = await _repository.GetByMachineAsync(machineId, cancellationToken);
        }
        else
        {
            docFactors = await _repository.GetAllAsync(cancellationToken);
        }

        return Ok(docFactors);
    }

    /// <summary>
    /// Get the applicable DOC factor for a specific date.
    /// </summary>
    [HttpGet("applicable")]
    public async Task<ActionResult<DocFactor>> GetApplicable(
        [FromQuery] string machineId,
        [FromQuery] Guid beamVariantId,
        [FromQuery] string date,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrEmpty(machineId))
        {
            return BadRequest("machineId is required.");
        }

        if (beamVariantId == Guid.Empty)
        {
            return BadRequest("beamVariantId is required.");
        }

        if (!DateOnly.TryParse(date, out var dateOnly))
        {
            return BadRequest("Invalid date format. Use YYYY-MM-DD.");
        }

        var docFactor = await _repository.GetApplicableAsync(machineId, beamVariantId, dateOnly, cancellationToken);

        if (docFactor == null)
        {
            return NotFound($"No applicable DOC factor found for date {date}.");
        }

        return Ok(docFactor);
    }

    /// <summary>
    /// Create a new DOC factor. Automatically adjusts date ranges of existing factors.
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<DocFactor>> Create([FromBody] DocFactor docFactor, CancellationToken cancellationToken)
    {
        try
        {
            var created = await _repository.CreateAsync(docFactor, cancellationToken);
            return CreatedAtAction(nameof(GetAll), new { id = created.Id }, created);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating DOC factor");
            return StatusCode(500, "An error occurred while creating the DOC factor.");
        }
    }

    /// <summary>
    /// Update an existing DOC factor.
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<DocFactor>> Update(Guid id, [FromBody] DocFactor docFactor, CancellationToken cancellationToken)
    {
        try
        {
            docFactor.Id = id;
            var updated = await _repository.UpdateAsync(docFactor, cancellationToken);
            return Ok(updated);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating DOC factor {Id}", id);
            return StatusCode(500, "An error occurred while updating the DOC factor.");
        }
    }

    /// <summary>
    /// Delete a DOC factor.
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        try
        {
            await _repository.DeleteAsync(id, cancellationToken);
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting DOC factor {Id}", id);
            return StatusCode(500, "An error occurred while deleting the DOC factor.");
        }
    }
}
