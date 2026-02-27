using Api.Controllers;
using Api.Models;
using Api.Repositories;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace Api.Tests.Controllers;

public class DocFactorsControllerTests
{
    private readonly Mock<IDocFactorRepository> _mockRepository;
    private readonly Mock<ILogger<DocFactorsController>> _mockLogger;
    private readonly DocFactorsController _controller;

    public DocFactorsControllerTests()
    {
        _mockRepository = new Mock<IDocFactorRepository>();
        _mockLogger = new Mock<ILogger<DocFactorsController>>();
        _controller = new DocFactorsController(_mockRepository.Object, _mockLogger.Object);
    }

    private static readonly Guid TestVariantId = Guid.Parse("253c1694-12d0-4497-9bd0-8487ee7c6f6f");
    private static readonly Guid TestBeamId = Guid.Parse("11111111-1111-1111-1111-111111111111");

    private DocFactor CreateTestDocFactor(Guid? id = null) => new()
    {
        Id = id ?? Guid.NewGuid(),
        MachineId = "MPC-001",
        BeamVariantId = TestVariantId,
        BeamId = TestBeamId,
        MsdAbs = 100.5,
        MpcRel = 99.8,
        DocFactorValue = 1.007,
        MeasurementDate = new DateOnly(2025, 11, 9),
        StartDate = new DateOnly(2025, 11, 9)
    };

    // ─── GetAll ────────────────────────────────────────────────

    [Fact]
    public async Task GetAll_WithNoFilter_ReturnsAllDocFactors()
    {
        // Arrange
        var factors = new List<DocFactor> { CreateTestDocFactor(), CreateTestDocFactor() };
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(factors);

        // Act
        var result = await _controller.GetAll(null, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<DocFactor>>().Subject;
        returned.Should().HaveCount(2);
        _mockRepository.Verify(r => r.GetAllAsync(It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetAll_WithMachineIdFilter_ReturnsFilteredDocFactors()
    {
        // Arrange
        var factors = new List<DocFactor> { CreateTestDocFactor() };
        _mockRepository.Setup(r => r.GetByMachineAsync("MPC-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(factors);

        // Act
        var result = await _controller.GetAll("MPC-001", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        _mockRepository.Verify(r => r.GetByMachineAsync("MPC-001", It.IsAny<CancellationToken>()), Times.Once);
        _mockRepository.Verify(r => r.GetAllAsync(It.IsAny<CancellationToken>()), Times.Never);
    }

    // ─── GetApplicable ─────────────────────────────────────────

    [Fact]
    public async Task GetApplicable_WithValidParams_ReturnsOkWithDocFactor()
    {
        // Arrange
        var factor = CreateTestDocFactor();
        _mockRepository.Setup(r => r.GetApplicableAsync("MPC-001", TestVariantId, new DateOnly(2025, 11, 9), It.IsAny<CancellationToken>()))
            .ReturnsAsync(factor);

        // Act
        var result = await _controller.GetApplicable("MPC-001", TestVariantId, "2025-11-09", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        okResult.Value.Should().BeOfType<DocFactor>();
    }

    [Fact]
    public async Task GetApplicable_WithEmptyMachineId_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetApplicable("", TestVariantId, "2025-11-09", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetApplicable_WithEmptyBeamVariantId_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetApplicable("MPC-001", Guid.Empty, "2025-11-09", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetApplicable_WithInvalidDate_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetApplicable("MPC-001", TestVariantId, "not-a-date", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetApplicable_WhenNotFound_ReturnsNotFound()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetApplicableAsync("MPC-001", TestVariantId, new DateOnly(2025, 11, 9), It.IsAny<CancellationToken>()))
            .ReturnsAsync((DocFactor?)null);

        // Act
        var result = await _controller.GetApplicable("MPC-001", TestVariantId, "2025-11-09", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<NotFoundObjectResult>();
    }

    // ─── Create ────────────────────────────────────────────────

    [Fact]
    public async Task Create_WithValidDocFactor_ReturnsCreatedAtAction()
    {
        // Arrange
        var factor = CreateTestDocFactor();
        _mockRepository.Setup(r => r.CreateAsync(factor, It.IsAny<CancellationToken>()))
            .ReturnsAsync(factor);

        // Act
        var result = await _controller.Create(factor, CancellationToken.None);

        // Assert
        var createdResult = result.Result.Should().BeOfType<CreatedAtActionResult>().Subject;
        createdResult.ActionName.Should().Be(nameof(DocFactorsController.GetAll));
    }

    [Fact]
    public async Task Create_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var factor = CreateTestDocFactor();
        _mockRepository.Setup(r => r.CreateAsync(factor, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Create(factor, CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── Update ────────────────────────────────────────────────

    [Fact]
    public async Task Update_WithValidDocFactor_ReturnsOk()
    {
        // Arrange
        var id = Guid.NewGuid();
        var factor = CreateTestDocFactor(id);
        _mockRepository.Setup(r => r.UpdateAsync(It.Is<DocFactor>(f => f.Id == id), It.IsAny<CancellationToken>()))
            .ReturnsAsync(factor);

        // Act
        var result = await _controller.Update(id, factor, CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        okResult.Value.Should().BeOfType<DocFactor>();
    }

    [Fact]
    public async Task Update_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var id = Guid.NewGuid();
        var factor = CreateTestDocFactor(id);
        _mockRepository.Setup(r => r.UpdateAsync(It.IsAny<DocFactor>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Update(id, factor, CancellationToken.None);

        // Assert
        var statusResult = result.Result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }

    // ─── Delete ────────────────────────────────────────────────

    [Fact]
    public async Task Delete_WithValidId_ReturnsNoContent()
    {
        // Arrange
        var id = Guid.NewGuid();
        _mockRepository.Setup(r => r.DeleteAsync(id, It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        // Act
        var result = await _controller.Delete(id, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NoContentResult>();
    }

    [Fact]
    public async Task Delete_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var id = Guid.NewGuid();
        _mockRepository.Setup(r => r.DeleteAsync(id, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("DB error"));

        // Act
        var result = await _controller.Delete(id, CancellationToken.None);

        // Assert
        var statusResult = result.Should().BeOfType<ObjectResult>().Subject;
        statusResult.StatusCode.Should().Be(500);
    }
}
