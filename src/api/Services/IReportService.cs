using Api.Models;

namespace Api.Services;

/// <summary>
/// Service for generating reports.
/// </summary>
public interface IReportService
{
    /// <summary>
    /// Generates a PDF report based on the provided request.
    /// </summary>
    /// <param name="request">The report generation request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The PDF file content as a byte array.</returns>
    Task<byte[]> GenerateReportAsync(ReportRequest request, CancellationToken cancellationToken = default);
}
