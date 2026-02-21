using Api.Models;
using Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ThresholdsController : ControllerBase
{
    private readonly IThresholdRepository _repository;
    private readonly ILogger<ThresholdsController> _logger;

    public ThresholdsController(IThresholdRepository repository, ILogger<ThresholdsController> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    [HttpGet("all")]
    public async Task<ActionResult<IEnumerable<Threshold>>> GetAll(CancellationToken cancellationToken)
    {
        var thresholds = await _repository.GetAllAsync(cancellationToken);
        return Ok(thresholds);
    }

    [HttpPost]
    public async Task<ActionResult<Threshold>> Save([FromBody] Threshold threshold, CancellationToken cancellationToken)
    {
        try
        {
            var saved = await _repository.SaveAsync(threshold, cancellationToken);
            return Ok(saved);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving threshold");
            return StatusCode(500, "An error occurred while saving the threshold.");
        }
    }
}
