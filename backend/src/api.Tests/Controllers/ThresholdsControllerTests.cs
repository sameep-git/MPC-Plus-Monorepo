using Api.Controllers;
using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace Api.Tests.Controllers;

public class ThresholdsControllerTests
{
    private readonly Mock<IThresholdRepository> _mockRepository;
    private readonly Mock<ILogger<ThresholdsController>> _mockLogger;
    private readonly ThresholdsController _controller;

    public ThresholdsControllerTests()
    {
        _mockRepository = new Mock<IThresholdRepository>();
        _mockLogger = new Mock<ILogger<ThresholdsController>>();
        _controller = new ThresholdsController(_mockRepository.Object, _mockLogger.Object);
    }

    // ─── GetAll ────────────────────────────────────────────────

    [Fact]
    public async Task GetAll_ReturnsOkWithThresholds()
    {
        // Arrange
        var thresholds = new List<Threshold>
        {
            new() { MachineId = "MPC-001", CheckType = "beam", BeamVariant = "6x", MetricType = "Relative Output", Value = 2.0 },
            new() { MachineId = "MPC-001", CheckType = "beam", BeamVariant = "6x", MetricType = "Relative Uniformity", Value = 3.0 },
            new() { MachineId = "MPC-001", CheckType = "geometry", MetricType = "IsoCenter Size", Value = 1.0 }
        };
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(thresholds);

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Threshold>>().Subject;
        returned.Should().HaveCount(3);
    }

    [Fact]
    public async Task GetAll_WithNoThresholds_ReturnsOkWithEmptyList()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<Threshold>());

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Threshold>>().Subject;
        returned.Should().BeEmpty();
    }

    // ─── Save ──────────────────────────────────────────────────

    [Fact]
    public async Task Save_WithValidThreshold_ReturnsOkWithSavedThreshold()
    {
        // Arrange
        var threshold = new Threshold { MachineId = "MPC-001", CheckType = "beam", BeamVariant = "6x", MetricType = "Relative Output", Value = 2.5 };
        _mockRepository.Setup(r => r.SaveAsync(threshold, It.IsAny<CancellationToken>()))
            .ReturnsAsync(threshold);

        // Act
        var result = await _controller.Save(threshold, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeOfType<Threshold>().Subject;
        returned.MetricType.Should().Be("Relative Output");
        returned.Value.Should().Be(2.5);
    }

    [Fact]
    public async Task Save_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var threshold = new Threshold { MachineId = "MPC-001", CheckType = "beam", MetricType = "Relative Output", Value = 2.5 };
        _mockRepository.Setup(r => r.SaveAsync(threshold, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Save(threshold, CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }
}
