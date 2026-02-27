using Api.Controllers;
using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace Api.Tests.Controllers;

public class UpdatesControllerTests
{
    private readonly Mock<IUpdateRepository> _mockRepository;
    private readonly Mock<ILogger<UpdatesController>> _mockLogger;
    private readonly UpdatesController _controller;

    public UpdatesControllerTests()
    {
        _mockRepository = new Mock<IUpdateRepository>();
        _mockLogger = new Mock<ILogger<UpdatesController>>();
        _controller = new UpdatesController(_mockRepository.Object, _mockLogger.Object);
    }

    // ─── GetAll ────────────────────────────────────────────────

    [Fact]
    public async Task GetAll_ReturnsOkWithUpdates()
    {
        // Arrange
        var updates = new List<Update>
        {
            new() { Id = "upd-001", MachineId = "MPC-001", Info = "Calibration completed", Type = "Maintenance" },
            new() { Id = "upd-002", MachineId = "MPC-002", Info = "Beam adjusted", Type = "Adjustment" }
        };
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(updates);

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<Update>>().Subject;
        returned.Should().HaveCount(2);
    }

    [Fact]
    public async Task GetAll_WhenExceptionThrown_Returns500()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── GetById ───────────────────────────────────────────────

    [Fact]
    public async Task GetById_WithValidId_ReturnsOkWithUpdate()
    {
        // Arrange
        var update = new Update { Id = "upd-001", MachineId = "MPC-001", Info = "Calibration completed", Type = "Maintenance" };
        _mockRepository.Setup(r => r.GetByIdAsync("upd-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(update);

        // Act
        var result = await _controller.GetById("upd-001", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeOfType<Update>().Subject;
        returned.Id.Should().Be("upd-001");
    }

    [Fact]
    public async Task GetById_WithInvalidId_ReturnsNotFound()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetByIdAsync("invalid", It.IsAny<CancellationToken>()))
            .ReturnsAsync((Update?)null);

        // Act
        var result = await _controller.GetById("invalid", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public async Task GetById_WhenExceptionThrown_Returns500()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetByIdAsync("upd-001", It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.GetById("upd-001", CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── Create ────────────────────────────────────────────────

    [Fact]
    public async Task Create_WithValidUpdate_ReturnsCreatedAtAction()
    {
        // Arrange
        var update = new Update { Id = "upd-new", MachineId = "MPC-001", Info = "New entry", Type = "Note" };
        _mockRepository.Setup(r => r.CreateAsync(update, It.IsAny<CancellationToken>()))
            .ReturnsAsync(update);

        // Act
        var result = await _controller.Create(update, CancellationToken.None);

        // Assert
        var createdResult = result.Result.Should().BeOfType<CreatedAtActionResult>().Subject;
        createdResult.ActionName.Should().Be(nameof(UpdatesController.GetById));
        createdResult.RouteValues!["id"].Should().Be("upd-new");
    }

    [Fact]
    public async Task Create_WithInvalidOperation_ReturnsBadRequest()
    {
        // Arrange
        var update = new Update { Id = "upd-001", MachineId = "MPC-001", Info = "Duplicate", Type = "Note" };
        _mockRepository.Setup(r => r.CreateAsync(update, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new InvalidOperationException("Update creation failed"));

        // Act
        var result = await _controller.Create(update, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Create_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var update = new Update { Id = "upd-new", MachineId = "MPC-001", Info = "Entry", Type = "Note" };
        _mockRepository.Setup(r => r.CreateAsync(update, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Create(update, CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── Update (PUT) ──────────────────────────────────────────

    [Fact]
    public async Task Update_WithValidUpdate_ReturnsOk()
    {
        // Arrange
        var update = new Update { Id = "upd-001", MachineId = "MPC-001", Info = "Updated info", Type = "Maintenance" };
        _mockRepository.Setup(r => r.UpdateAsync(update, It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Update(update, CancellationToken.None);

        // Assert
        result.Should().BeOfType<OkResult>();
    }

    [Fact]
    public async Task Update_WithNonExistentId_ReturnsNotFound()
    {
        // Arrange
        var update = new Update { Id = "nonexistent", MachineId = "MPC-001", Info = "Info", Type = "Note" };
        _mockRepository.Setup(r => r.UpdateAsync(update, It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Update(update, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public async Task Update_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var update = new Update { Id = "upd-001", MachineId = "MPC-001", Info = "Info", Type = "Note" };
        _mockRepository.Setup(r => r.UpdateAsync(update, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Update(update, CancellationToken.None);

        // Assert
        var statusResult = result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── Delete ────────────────────────────────────────────────

    [Fact]
    public async Task Delete_WithValidId_ReturnsNoContent()
    {
        // Arrange
        _mockRepository.Setup(r => r.DeleteAsync("upd-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Delete("upd-001", CancellationToken.None);

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

    [Fact]
    public async Task Delete_WhenExceptionThrown_Returns500()
    {
        // Arrange
        _mockRepository.Setup(r => r.DeleteAsync("upd-001", It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Delete("upd-001", CancellationToken.None);

        // Assert
        var statusResult = result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }
}
