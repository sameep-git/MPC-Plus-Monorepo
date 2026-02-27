using Api.Controllers;
using Api.Models;
using Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Api.Tests.Controllers;

public class ReportsControllerTests
{
    private readonly Mock<IReportService> _mockReportService;
    private readonly ReportsController _controller;

    public ReportsControllerTests()
    {
        _mockReportService = new Mock<IReportService>();
        _controller = new ReportsController(_mockReportService.Object);
    }

    [Fact]
    public async Task GenerateReport_WithValidRequest_ReturnsFileResult()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 1),
            EndDate = new DateTime(2025, 11, 30),
            MachineId = "MPC-001",
            SelectedChecks = new List<string> { "beam-6x", "geo-gantry" }
        };
        var pdfBytes = new byte[] { 0x25, 0x50, 0x44, 0x46 }; // %PDF header
        _mockReportService.Setup(s => s.GenerateReportAsync(request, It.IsAny<CancellationToken>()))
            .ReturnsAsync((pdfBytes, "application/pdf", "report_2025-11-01.pdf"));

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        var fileResult = result.Should().BeOfType<FileContentResult>().Subject;
        fileResult.ContentType.Should().Be("application/pdf");
        fileResult.FileDownloadName.Should().Be("report_2025-11-01.pdf");
        fileResult.FileContents.Should().BeEquivalentTo(pdfBytes);
    }

    [Fact]
    public async Task GenerateReport_WithMultiDay_ReturnsZipFile()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 1),
            EndDate = new DateTime(2025, 11, 5),
            MachineId = "MPC-001",
            SelectedChecks = new List<string> { "beam-6x" }
        };
        var zipBytes = new byte[] { 0x50, 0x4B, 0x03, 0x04 }; // PK zip header
        _mockReportService.Setup(s => s.GenerateReportAsync(request, It.IsAny<CancellationToken>()))
            .ReturnsAsync((zipBytes, "application/zip", "reports_2025-11-01_to_2025-11-05.zip"));

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        var fileResult = result.Should().BeOfType<FileContentResult>().Subject;
        fileResult.ContentType.Should().Be("application/zip");
    }

    [Fact]
    public async Task GenerateReport_WithStartDateAfterEndDate_ReturnsBadRequest()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 30),
            EndDate = new DateTime(2025, 11, 1),
            MachineId = "MPC-001",
            SelectedChecks = new List<string> { "beam-6x" }
        };

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
        _mockReportService.Verify(s => s.GenerateReportAsync(It.IsAny<ReportRequest>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task GenerateReport_WithEmptyMachineId_ReturnsBadRequest()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 1),
            EndDate = new DateTime(2025, 11, 30),
            MachineId = "",
            SelectedChecks = new List<string> { "beam-6x" }
        };

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
        _mockReportService.Verify(s => s.GenerateReportAsync(It.IsAny<ReportRequest>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task GenerateReport_WithWhitespaceMachineId_ReturnsBadRequest()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 1),
            EndDate = new DateTime(2025, 11, 30),
            MachineId = "   ",
            SelectedChecks = new List<string> { "beam-6x" }
        };

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GenerateReport_WhenServiceThrows_Returns500()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 1),
            EndDate = new DateTime(2025, 11, 30),
            MachineId = "MPC-001",
            SelectedChecks = new List<string> { "beam-6x" }
        };
        _mockReportService.Setup(s => s.GenerateReportAsync(request, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("PDF generation failed"));

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        var statusResult = result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    [Fact]
    public async Task GenerateReport_WithTimezone_PassesTimezoneToService()
    {
        // Arrange
        var request = new ReportRequest
        {
            StartDate = new DateTime(2025, 11, 1),
            EndDate = new DateTime(2025, 11, 30),
            MachineId = "MPC-001",
            SelectedChecks = new List<string> { "beam-6x" },
            TimeZone = "America/Chicago"
        };
        var pdfBytes = new byte[] { 0x25, 0x50, 0x44, 0x46 };
        _mockReportService.Setup(s => s.GenerateReportAsync(
                It.Is<ReportRequest>(r => r.TimeZone == "America/Chicago"),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync((pdfBytes, "application/pdf", "report.pdf"));

        // Act
        var result = await _controller.GenerateReport(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<FileContentResult>();
        _mockReportService.Verify(s => s.GenerateReportAsync(
            It.Is<ReportRequest>(r => r.TimeZone == "America/Chicago"),
            It.IsAny<CancellationToken>()), Times.Once);
    }
}
