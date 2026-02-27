using Api.Controllers;
using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace Api.Tests.Controllers;

public class GeoCheckControllerTests
{
    private readonly Mock<IGeoCheckRepository> _mockRepository;
    private readonly Mock<ILogger<GeoCheckController>> _mockLogger;
    private readonly GeoCheckController _controller;

    public GeoCheckControllerTests()
    {
        _mockRepository = new Mock<IGeoCheckRepository>();
        _mockLogger = new Mock<ILogger<GeoCheckController>>();
        _controller = new GeoCheckController(_mockRepository.Object, _mockLogger.Object);
    }

    // ─── GetAll ────────────────────────────────────────────────

    [Fact]
    public async Task GetAll_NoFilters_ReturnsOkWithGeoChecks()
    {
        // Arrange
        var geoChecks = new List<GeoCheck>
        {
            new() { Id = "geo-001", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001" },
            new() { Id = "geo-002", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 10), MachineId = "MPC-002" }
        };
        _mockRepository.Setup(r => r.GetAllAsync(null, null, null, null, null, true, It.IsAny<CancellationToken>()))
            .ReturnsAsync(geoChecks);

        // Act
        var result = await _controller.GetAll(null, null, null, null, null, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<GeoCheck>>().Subject;
        returned.Should().HaveCount(2);
    }

    [Fact]
    public async Task GetAll_WithMachineIdFilter_PassesFilterToRepository()
    {
        // Arrange
        var geoChecks = new List<GeoCheck>
        {
            new() { Id = "geo-001", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001" }
        };
        _mockRepository.Setup(r => r.GetAllAsync("MPC-001", null, null, null, null, true, It.IsAny<CancellationToken>()))
            .ReturnsAsync(geoChecks);

        // Act
        var result = await _controller.GetAll(null, "MPC-001", null, null, null, CancellationToken.None);

        // Assert
        _mockRepository.Verify(r => r.GetAllAsync("MPC-001", null, null, null, null, true, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetAll_WithDateRangeFilter_ParsesDatesCorrectly()
    {
        // Arrange
        var geoChecks = new List<GeoCheck>();
        _mockRepository.Setup(r => r.GetAllAsync(
            null, null, null,
            new DateTime(2025, 11, 1), new DateTime(2025, 11, 30),
            true, It.IsAny<CancellationToken>()))
            .ReturnsAsync(geoChecks);

        // Act
        var result = await _controller.GetAll(null, null, null, "2025-11-01", "2025-11-30", CancellationToken.None);

        // Assert
        _mockRepository.Verify(r => r.GetAllAsync(
            null, null, null,
            new DateTime(2025, 11, 1), new DateTime(2025, 11, 30),
            true, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetAll_WithInvalidDateFormat_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetAll(null, null, "not-a-date", null, null, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetAll_WithInvalidStartDate_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetAll(null, null, null, "invalid", null, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetAll_WithInvalidEndDate_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetAll(null, null, null, null, "invalid", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    // ─── GetById ───────────────────────────────────────────────

    [Fact]
    public async Task GetById_WithValidId_ReturnsOkWithGeoCheck()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "geo-001", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001" };
        _mockRepository.Setup(r => r.GetByIdAsync("geo-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(geoCheck);

        // Act
        var result = await _controller.GetById("geo-001", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeOfType<GeoCheck>().Subject;
        returned.Id.Should().Be("geo-001");
    }

    [Fact]
    public async Task GetById_WithInvalidId_ReturnsNotFound()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetByIdAsync("invalid", It.IsAny<CancellationToken>()))
            .ReturnsAsync((GeoCheck?)null);

        // Act
        var result = await _controller.GetById("invalid", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<NotFoundObjectResult>();
    }

    // ─── Create ────────────────────────────────────────────────

    [Fact]
    public async Task Create_WithValidGeoCheck_ReturnsCreatedAtAction()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "geo-new", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 12), MachineId = "MPC-001" };
        _mockRepository.Setup(r => r.CreateAsync(geoCheck, It.IsAny<CancellationToken>()))
            .ReturnsAsync(geoCheck);

        // Act
        var result = await _controller.Create(geoCheck, CancellationToken.None);

        // Assert
        var createdResult = result.Result.Should().BeOfType<CreatedAtActionResult>().Subject;
        createdResult.ActionName.Should().Be(nameof(GeoCheckController.GetById));
        createdResult.RouteValues!["id"].Should().Be("geo-new");
    }

    [Fact]
    public async Task Create_WithDuplicate_ReturnsConflict()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "geo-001", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 12), MachineId = "MPC-001" };
        _mockRepository.Setup(r => r.CreateAsync(geoCheck, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new InvalidOperationException("Geometry check already exists"));

        // Act
        var result = await _controller.Create(geoCheck, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<ConflictObjectResult>();
    }

    [Fact]
    public async Task Create_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "geo-new", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 12), MachineId = "MPC-001" };
        _mockRepository.Setup(r => r.CreateAsync(geoCheck, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Create(geoCheck, CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── Update ────────────────────────────────────────────────

    [Fact]
    public async Task Update_WithMatchingIds_ReturnsNoContent()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "geo-001", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001" };
        _mockRepository.Setup(r => r.UpdateAsync(geoCheck, It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Update("geo-001", geoCheck, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NoContentResult>();
    }

    [Fact]
    public async Task Update_WithMismatchedIds_ReturnsBadRequest()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "geo-002", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001" };

        // Act
        var result = await _controller.Update("geo-001", geoCheck, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Update_WithNonExistentId_ReturnsNotFound()
    {
        // Arrange
        var geoCheck = new GeoCheck { Id = "nonexistent", Type = "6xFFF", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001" };
        _mockRepository.Setup(r => r.UpdateAsync(geoCheck, It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Update("nonexistent", geoCheck, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NotFoundObjectResult>();
    }

    // ─── Delete ────────────────────────────────────────────────

    [Fact]
    public async Task Delete_WithValidId_ReturnsNoContent()
    {
        // Arrange
        _mockRepository.Setup(r => r.DeleteAsync("geo-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Delete("geo-001", CancellationToken.None);

        // Assert
        result.Should().BeOfType<NoContentResult>();
    }

    [Fact]
    public async Task Delete_WithNonExistentId_ReturnsNotFound()
    {
        // Arrange
        _mockRepository.Setup(r => r.DeleteAsync("nonexistent", It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Delete("nonexistent", CancellationToken.None);

        // Assert
        result.Should().BeOfType<NotFoundObjectResult>();
    }

    // ─── Accept ────────────────────────────────────────────────

    [Fact]
    public async Task Accept_WithValidRequest_ReturnsOkWithResults()
    {
        // Arrange
        var request = new AcceptGeoCheckRequest(new[] { "geo-001", "geo-002" }, "Dr. Smith");
        _mockRepository.Setup(r => r.ApproveAsync("geo-001", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        _mockRepository.Setup(r => r.ApproveAsync("geo-002", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Accept(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<OkObjectResult>();
    }

    [Fact]
    public async Task Accept_WithEmptyIds_ReturnsBadRequest()
    {
        // Arrange
        var request = new AcceptGeoCheckRequest(new List<string>(), "Dr. Smith");

        // Act
        var result = await _controller.Accept(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Accept_WithPartialFailure_ReturnsOkWithErrors()
    {
        // Arrange
        var request = new AcceptGeoCheckRequest(new[] { "geo-001", "geo-invalid" }, "Dr. Smith");
        _mockRepository.Setup(r => r.ApproveAsync("geo-001", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        _mockRepository.Setup(r => r.ApproveAsync("geo-invalid", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Accept(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<OkObjectResult>();
    }
}
