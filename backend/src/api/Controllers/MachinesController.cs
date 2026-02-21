using Api.Models;
using Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MachinesController : ControllerBase
{
    private readonly IMachineRepository _repository;

    public MachinesController(IMachineRepository repository)
    {
        _repository = repository;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Machine>>> GetAll(CancellationToken cancellationToken)
    {
        var machines = await _repository.GetAllAsync(cancellationToken);
        return Ok(machines);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Machine>> GetById(string id, CancellationToken cancellationToken)
    {
        var machine = await _repository.GetByIdAsync(id, cancellationToken);
        if (machine is null)
        {
            return NotFound($"Machine with id '{id}' was not found.");
        }

        return Ok(machine);
    }

    [HttpPost]
    public async Task<ActionResult<Machine>> Create([FromBody] Machine machine, CancellationToken cancellationToken)
    {
        try
        {
            var created = await _repository.CreateAsync(machine, cancellationToken);
            return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
        }
        catch (InvalidOperationException exception)
        {
            return Conflict(exception.Message);
        }
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(string id, [FromBody] Machine machine, CancellationToken cancellationToken)
    {
        if (!string.Equals(id, machine.Id, StringComparison.OrdinalIgnoreCase))
        {
            return BadRequest("The machine id in the route must match the payload.");
        }

        var updated = await _repository.UpdateAsync(machine, cancellationToken);
        if (!updated)
        {
            return NotFound($"Machine with id '{id}' was not found.");
        }

        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(string id, CancellationToken cancellationToken)
    {
        var deleted = await _repository.DeleteAsync(id, cancellationToken);
        if (!deleted)
        {
            return NotFound($"Machine with id '{id}' was not found.");
        }

        return NoContent();
    }
}

