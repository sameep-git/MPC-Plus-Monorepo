using Api.Controllers;
using Api.Models;
using Api.Repositories.Abstractions;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc;
using Moq;
using Xunit;

namespace Api.Tests.Controllers;

public class ResultsControllerTests
{
    private readonly Mock<IBeamRepository> _mockBeamRepository;
    private readonly Mock<IGeoCheckRepository> _mockGeoCheckRepository;
    private readonly ResultsController _controller;

    public ResultsControllerTests()
    {
        _mockBeamRepository = new Mock<IBeamRepository>();
        _mockGeoCheckRepository = new Mock<IGeoCheckRepository>();
        _controller = new ResultsController(_mockBeamRepository.Object, _mockGeoCheckRepository.Object);

        // Default setup for GeoCheckRepository to return empty list
        _mockGeoCheckRepository.Setup(r => r.GetAllAsync(
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<DateTime?>(),
            It.IsAny<DateTime?>(),
            It.IsAny<DateTime?>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<GeoCheck>().AsReadOnly());
    }

    [Fact]
    public async Task Get_WithValidParameters_ReturnsOkWithMonthlyResults()
    {
        // Arrange
        var beams = new List<Beam>
        {
            new Beam
            {
                Id = "beam-1",
                MachineId = "1",
                Date = new DateTime(2025, 9, 5),
                Type = "15x"
            },
            new Beam
            {
                Id = "beam-2",
                MachineId = "1",
                Date = new DateTime(2025, 9, 10),
                Type = "6e"
            }
        };

        _mockBeamRepository.Setup(r => r.GetAllAsync(
            "1",
            null,
            null,
            new DateTime(2025, 9, 1),
            new DateTime(2025, 9, 30),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams.AsReadOnly());

        // Act
        var result = await _controller.Get(9, 2025, "1", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedResults = okResult.Value.Should().BeAssignableTo<MonthlyResults>().Subject;
        returnedResults.Month.Should().Be(9);
        returnedResults.Year.Should().Be(2025);
        returnedResults.MachineId.Should().Be("1");
        returnedResults.Checks.Should().HaveCount(2);
    }

    [Fact]
    public async Task Get_WithMonthLessThanOne_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.Get(0, 2025, "1", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
        var badRequest = result.Result as BadRequestObjectResult;
        badRequest!.Value.Should().Be("Month must be between 1 and 12.");
        _mockBeamRepository.Verify(r => r.GetAllAsync(
            It.IsAny<string>(), It.IsAny<string>(), It.IsAny<DateTime?>(), 
            It.IsAny<DateTime?>(), It.IsAny<DateTime?>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Get_WithMonthGreaterThanTwelve_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.Get(13, 2025, "1", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
        var badRequest = result.Result as BadRequestObjectResult;
        badRequest!.Value.Should().Be("Month must be between 1 and 12.");
        _mockBeamRepository.Verify(r => r.GetAllAsync(
            It.IsAny<string>(), It.IsAny<string>(), It.IsAny<DateTime?>(), 
            It.IsAny<DateTime?>(), It.IsAny<DateTime?>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Get_WithYearLessThan1900_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.Get(9, 1899, "1", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
        var badRequest = result.Result as BadRequestObjectResult;
        badRequest!.Value.Should().Be("Year must be between 1900 and 2100.");
        _mockBeamRepository.Verify(r => r.GetAllAsync(
            It.IsAny<string>(), It.IsAny<string>(), It.IsAny<DateTime?>(), 
            It.IsAny<DateTime?>(), It.IsAny<DateTime?>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Get_WithYearGreaterThan2100_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.Get(9, 2101, "1", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
        var badRequest = result.Result as BadRequestObjectResult;
        badRequest!.Value.Should().Be("Year must be between 1900 and 2100.");
        _mockBeamRepository.Verify(r => r.GetAllAsync(
            It.IsAny<string>(), It.IsAny<string>(), It.IsAny<DateTime?>(), 
            It.IsAny<DateTime?>(), It.IsAny<DateTime?>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Get_WithEmptyMachineId_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.Get(9, 2025, "", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
        var badRequest = result.Result as BadRequestObjectResult;
        badRequest!.Value.Should().Be("MachineId is required.");
        _mockBeamRepository.Verify(r => r.GetAllAsync(
            It.IsAny<string>(), It.IsAny<string>(), It.IsAny<DateTime?>(), 
            It.IsAny<DateTime?>(), It.IsAny<DateTime?>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Get_WithNullMachineId_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.Get(9, 2025, null!, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
        var badRequest = result.Result as BadRequestObjectResult;
        badRequest!.Value.Should().Be("MachineId is required.");
        _mockBeamRepository.Verify(r => r.GetAllAsync(
            It.IsAny<string>(), It.IsAny<string>(), It.IsAny<DateTime?>(), 
            It.IsAny<DateTime?>(), It.IsAny<DateTime?>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Get_WithValidBoundaryValues_ReturnsOk()
    {
        // Arrange
        var beams = new List<Beam>().AsReadOnly();
        _mockBeamRepository.Setup(r => r.GetAllAsync(
            It.IsAny<string>(),
            null,
            null,
            It.IsAny<DateTime>(),
            It.IsAny<DateTime>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams);

        // Act
        var result1 = await _controller.Get(1, 1900, "1", CancellationToken.None);
        var result2 = await _controller.Get(12, 2100, "2", CancellationToken.None);

        // Assert
        result1.Result.Should().BeOfType<OkObjectResult>();
        result2.Result.Should().BeOfType<OkObjectResult>();
    }

    [Fact]
    public async Task Get_WithNoBeams_ReturnsOkWithEmptyChecks()
    {
        // Arrange
        var emptyBeams = new List<Beam>().AsReadOnly();
        _mockBeamRepository.Setup(r => r.GetAllAsync(
            "1",
            null,
            null,
            new DateTime(2024, 6, 1),
            new DateTime(2024, 6, 30),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(emptyBeams);

        // Act
        var result = await _controller.Get(6, 2024, "1", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedResults = okResult.Value.Should().BeAssignableTo<MonthlyResults>().Subject;
        returnedResults.Checks.Should().BeEmpty();
    }

    [Fact]
    public async Task Get_WithMultipleBeamsOnSameDay_AggregatesStatus()
    {
        // Arrange
        var beams = new List<Beam>
        {
            new Beam
            {
                Id = "beam-1",
                MachineId = "1",
                Date = new DateTime(2025, 9, 5),
                Type = "15x"
            },
            new Beam
            {
                Id = "beam-2",
                MachineId = "1",
                Date = new DateTime(2025, 9, 5),
                Type = "6e"
            }
        };

        _mockBeamRepository.Setup(r => r.GetAllAsync(
            "1",
            null,
            null,
            new DateTime(2025, 9, 1),
            new DateTime(2025, 9, 30),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams.AsReadOnly());

        // Act
        var result = await _controller.Get(9, 2025, "1", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedResults = okResult.Value.Should().BeAssignableTo<MonthlyResults>().Subject;
        returnedResults.Checks.Should().HaveCount(1);
        returnedResults.Checks.First().Date.Should().Be(new DateTime(2025, 9, 5));
    }
}
