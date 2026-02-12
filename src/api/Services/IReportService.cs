using Api.Models;

namespace Api.Services;

/// <summary>
/// Service for generating reports.
/// </summary>
public interface IReportService
{
    /// <summary>
    /// Generates a report based on the provided request.
    /// Returns per-day PDFs: a single PDF if only one day has data,
    /// or a ZIP archive containing one PDF per day if multiple days have data.
    /// </summary>
    /// <param name="request">The report generation request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A tuple of (file bytes, content type, suggested filename).</returns>
    Task<(byte[] Data, string ContentType, string FileName)> GenerateReportAsync(ReportRequest request, CancellationToken cancellationToken = default);
}
