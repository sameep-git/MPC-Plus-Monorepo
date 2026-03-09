using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class BaselinesController : ControllerBase
{
    private readonly IBaselineRepository _repository;
    private readonly ILogger<BaselinesController> _logger;

    public BaselinesController(IBaselineRepository repository, ILogger<BaselinesController> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    [HttpGet("all")]
    public async Task<ActionResult<IEnumerable<Baseline>>> GetAll(CancellationToken cancellationToken)
    {
        var baselines = await _repository.GetAllAsync(cancellationToken);
        return Ok(baselines);
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Baseline>>> GetByMachine(
        [FromQuery] string machineId, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(machineId))
        {
            var all = await _repository.GetAllAsync(cancellationToken);
            return Ok(all);
        }

        var baselines = await _repository.GetByMachineAsync(machineId, cancellationToken);
        return Ok(baselines);
    }

    [HttpPost]
    public async Task<ActionResult<Baseline>> Save([FromBody] Baseline baseline, CancellationToken cancellationToken)
    {
        try
        {
            var saved = await _repository.SaveAsync(baseline, cancellationToken);
            return Ok(saved);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving baseline");
            return StatusCode(500, "An error occurred while saving the baseline.");
        }
    }
}
