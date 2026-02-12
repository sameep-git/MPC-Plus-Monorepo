using Api.Models;
using Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ReportsController : ControllerBase
{
    private readonly IReportService _reportService;

    public ReportsController(IReportService reportService)
    {
        _reportService = reportService;
    }

    /// <summary>
    /// Generates a report based on the provided request.
    /// Returns a single PDF for single-day data, or a ZIP archive
    /// containing one PDF per day for multi-day data.
    /// </summary>
    /// <param name="request">The report generation request.</param>
    /// <returns>A PDF or ZIP file download.</returns>
    [HttpPost("generate")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> GenerateReport([FromBody] ReportRequest request, CancellationToken cancellationToken)
    {
        if (request.StartDate > request.EndDate)
        {
            return BadRequest("Start date cannot be after end date.");
        }

        if (string.IsNullOrWhiteSpace(request.MachineId))
        {
            return BadRequest("Machine ID is required.");
        }

        try
        {
            var (data, contentType, fileName) = await _reportService.GenerateReportAsync(request, cancellationToken);
            Console.WriteLine($"[ReportsController] Report generated successfully. Size: {data.Length} bytes, Type: {contentType}, File: {fileName}");
            return File(data, contentType, fileName);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ReportsController] Error generating report: {ex}");
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }
}
