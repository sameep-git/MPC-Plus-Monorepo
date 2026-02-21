using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class UpdatesController : ControllerBase
{
    private readonly IUpdateRepository _repository;
    private readonly ILogger<UpdatesController> _logger;

    public UpdatesController(IUpdateRepository repository, ILogger<UpdatesController> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    /// <summary>
    /// Get all updates
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<Update>>> GetAll(CancellationToken cancellationToken)
    {
        try
        {
            var updates = await _repository.GetAllAsync(cancellationToken);
            return Ok(updates);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving updates");
            return StatusCode(500, "An error occurred while retrieving updates");
        }
    }

    /// <summary>
    /// Get update by ID
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<Update>> GetById(string id, CancellationToken cancellationToken)
    {
        try
        {
            var update = await _repository.GetByIdAsync(id, cancellationToken);
            if (update == null)
            {
                return NotFound($"Update with ID '{id}' not found");
            }
            return Ok(update);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving update {UpdateId}", id);
            return StatusCode(500, "An error occurred while retrieving the update");
        }
    }

    /// <summary>
    /// Create a new update
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<Update>> Create([FromBody] Update update, CancellationToken cancellationToken)
    {
        try
        {
            var created = await _repository.CreateAsync(update, cancellationToken);
            return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "Update creation failed: {Message}", ex.Message);
            return BadRequest(ex.Message);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating update");
            return StatusCode(500, "An error occurred while creating the update");
        }
    }

    /// <summary>
    /// Update an existing update
    /// </summary>
    [HttpPut]
    public async Task<IActionResult> Update([FromBody] Update update, CancellationToken cancellationToken)
    {
        try
        {
            var success = await _repository.UpdateAsync(update, cancellationToken);
            if (!success)
            {
                return NotFound($"Update with ID '{update.Id}' not found");
            }
            return Ok();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating update {UpdateId}", update.Id);
            return StatusCode(500, "An error occurred while updating the update");
        }
    }

    /// <summary>
    /// Delete an update
    /// </summary>
    [HttpDelete]
    public async Task<IActionResult> Delete([FromQuery] string id, CancellationToken cancellationToken)
    {
        try
        {
            var success = await _repository.DeleteAsync(id, cancellationToken);
            if (!success)
            {
                return NotFound($"Update with ID '{id}' not found");
            }
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting update {UpdateId}", id);
            return StatusCode(500, "An error occurred while deleting the update");
        }
    }
}
