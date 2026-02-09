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
    /// Generates a PDF report based on the provided request.
    /// </summary>
    /// <param name="request">The report generation request.</param>
    /// <returns>A PDF file download.</returns>
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
            var pdfBytes = await _reportService.GenerateReportAsync(request, cancellationToken);
            var fileName = $"MPC_Report_{DateTime.Now:yyyyMMdd_HHmmss}.pdf";
            Console.WriteLine($"[ReportsController] PDF generated successfully. Size: {pdfBytes.Length} bytes.");
            return File(pdfBytes, "application/pdf", fileName);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ReportsController] Error generating report: {ex}");
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }
}
