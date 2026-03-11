using Api.Controllers;
using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Moq;
using FluentAssertions;
using Xunit;

namespace Api.Tests.Controllers;

public class BaselinesControllerTests
{
    private readonly Mock<IBaselineRepository> _mockRepository;
    private readonly Mock<ILogger<BaselinesController>> _mockLogger;
    private readonly BaselinesController _controller;

    public BaselinesControllerTests()
    {
        _mockRepository = new Mock<IBaselineRepository>();
        _mockLogger = new Mock<ILogger<BaselinesController>>();
        _controller = new BaselinesController(_mockRepository.Object, _mockLogger.Object);
    }

    // ─── GetAll ────────────────────────────────────────────────

    [Fact]
    public async Task GetAll_ReturnsOkWithBaselines()
    {
        // Arrange
        var baselines = new List<Baseline>
        {
            new() { MachineId = "MPC-001", CheckType = "beam", BeamVariant = "6x", MetricType = "Relative Output", Value = 2.0, Date = DateTime.UtcNow },
            new() { MachineId = "MPC-001", CheckType = "geometry", MetricType = "IsoCenter Size", Value = 1.0, Date = DateTime.UtcNow }
        };
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(baselines);

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Baseline>>().Subject;
        returned.Should().HaveCount(2);
    }

    [Fact]
    public async Task GetAll_WithNoBaselines_ReturnsOkWithEmptyList()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<Baseline>());

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Baseline>>().Subject;
        returned.Should().BeEmpty();
    }

    // ─── GetByMachine ──────────────────────────────────────────

    [Fact]
    public async Task GetByMachine_WithValidMachineId_ReturnsOkWithBaselines()
    {
        // Arrange
        var machineId = "MPC-001";
        var baselines = new List<Baseline>
        {
            new() { MachineId = machineId, CheckType = "beam", MetricType = "Relative Output", Value = 2.0, Date = DateTime.UtcNow }
        };
        _mockRepository.Setup(r => r.GetByMachineAsync(machineId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(baselines);

        // Act
        var result = await _controller.GetByMachine(machineId, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Baseline>>().Subject;
        returned.Should().HaveCount(1);
        returned.First().MachineId.Should().Be(machineId);
    }

    [Fact]
    public async Task GetByMachine_WithEmptyMachineId_ReturnsAllBaselines()
    {
        // Arrange
        var baselines = new List<Baseline>
        {
            new() { MachineId = "MPC-001", CheckType = "beam", MetricType = "Relative Output", Value = 2.0, Date = DateTime.UtcNow },
            new() { MachineId = "MPC-002", CheckType = "geometry", MetricType = "IsoCenter Size", Value = 1.0, Date = DateTime.UtcNow }
        };
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(baselines);

        // Act
        var result = await _controller.GetByMachine(string.Empty, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Baseline>>().Subject;
        returned.Should().HaveCount(2);
    }

    // ─── Save ──────────────────────────────────────────────────

    [Fact]
    public async Task Save_WithValidBaseline_ReturnsOkWithSavedBaseline()
    {
        // Arrange
        var baseline = new Baseline { MachineId = "MPC-001", CheckType = "beam", BeamVariant = "6x", MetricType = "Relative Output", Value = 2.5, Date = DateTime.UtcNow };
        _mockRepository.Setup(r => r.SaveAsync(baseline, It.IsAny<CancellationToken>()))
            .ReturnsAsync(baseline);

        // Act
        var result = await _controller.Save(baseline, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeOfType<Baseline>().Subject;
        returned.MetricType.Should().Be("Relative Output");
        returned.Value.Should().Be(2.5);
    }

    [Fact]
    public async Task Save_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var baseline = new Baseline { MachineId = "MPC-001", CheckType = "beam", MetricType = "Relative Output", Value = 2.5, Date = DateTime.UtcNow };
        _mockRepository.Setup(r => r.SaveAsync(baseline, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Save(baseline, CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }
}
