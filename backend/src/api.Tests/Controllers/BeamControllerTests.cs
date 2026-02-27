using Api.Controllers;
using Api.Models;
using Api.Repositories;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Tests.Controllers;

public class BeamControllerTests
{
    private readonly Mock<IBeamRepository> _mockRepository;
    private readonly Mock<IThresholdRepository> _mockValidator; // Renaming to _mockValidator as it was used in previous code
    private readonly BeamsController _controller;

    public BeamControllerTests()
    {
        _mockRepository = new Mock<IBeamRepository>();
        _mockValidator = new Mock<IThresholdRepository>();
        // CalculateStatus needs thresholds; return an empty list by default
        _mockValidator.Setup(v => v.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<Threshold>().AsReadOnly());
        _controller = new BeamsController(_mockRepository.Object, _mockValidator.Object);
    }

    [Fact]
    public async Task GetAll_ReturnsOkWithBeams()
    {
        // Arrange
        var beams = new List<Beam>
        {
            new() { Id = "beam-001", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.2, RelOutput = 98.5 },
            new() { Id = "beam-002", Type = "9e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-002", RelUniformity = 98.9, RelOutput = 98.2 }
        };
        _mockRepository.Setup(r => r.GetAllAsync(null, null, null, null, null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams);

        // Act
        var result = await _controller.GetAll(null, null, null, null, null, CancellationToken.None);

        // Assert — controller groups beams into CheckGroup objects
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedGroups = okResult.Value.Should().BeAssignableTo<IEnumerable<CheckGroup>>().Subject;
        returnedGroups.SelectMany(g => g.Beams).Should().HaveCount(2);
    }

    [Fact]
    public async Task GetAll_WithTypeFilter_PassesFilterToRepository()
    {
        // Arrange
        var beams = new List<Beam>
        {
            new() { Id = "beam-001", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.2, RelOutput = 98.5 }
        };
        _mockRepository.Setup(r => r.GetAllAsync(null, "6e", null, null, null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams);

        // Act
        var result = await _controller.GetAll("6e", null, null, null, null, CancellationToken.None);

        // Assert
        _mockRepository.Verify(r => r.GetAllAsync(null, "6e", null, null, null, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetAll_WithMachineIdFilter_PassesFilterToRepository()
    {
        // Arrange
        var beams = new List<Beam>
        {
            new() { Id = "beam-001", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.2, RelOutput = 98.5 }
        };
        _mockRepository.Setup(r => r.GetAllAsync("MPC-001", null, null, null, null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams);

        // Act
        var result = await _controller.GetAll(null, "MPC-001", null, null, null, CancellationToken.None);

        // Assert
        _mockRepository.Verify(r => r.GetAllAsync("MPC-001", null, null, null, null, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetAll_WithDateFilter_ParsesAndPassesDateToRepository()
    {
        // Arrange
        var testDate = new DateTime(2025, 11, 9);
        var beams = new List<Beam>
        {
            new() { Id = "beam-001", Type = "6e", Timestamp = testDate, MachineId = "MPC-001", RelUniformity = 99.2, RelOutput = 98.5 }
        };
        _mockRepository.Setup(r => r.GetAllAsync(null, null, testDate, null, null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams);

        // Act
        var result = await _controller.GetAll(null, null, "2025-11-09", null, null, CancellationToken.None);

        // Assert
        _mockRepository.Verify(r => r.GetAllAsync(null, null, testDate, null, null, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetById_WithValidId_ReturnsOkWithBeam()
    {
        // Arrange
        var beam = new Beam { Id = "beam-001", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.2, RelOutput = 98.5 };
        _mockRepository.Setup(r => r.GetByIdAsync("beam-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(beam);

        // Act
        var result = await _controller.GetById("beam-001", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedBeam = okResult.Value.Should().BeOfType<Beam>().Subject;
        returnedBeam.Id.Should().Be("beam-001");
    }

    [Fact]
    public async Task GetById_WithInvalidId_ReturnsNotFound()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetByIdAsync("invalid", It.IsAny<CancellationToken>()))
            .ReturnsAsync((Beam?)null);

        // Act
        var result = await _controller.GetById("invalid", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public async Task Create_WithValidBeam_ReturnsCreatedAtActionResult()
    {
        // Arrange
        var beam = new Beam { Id = "beam-new", Type = "9e", Timestamp = new DateTime(2025, 11, 12), MachineId = "MPC-001", RelUniformity = 99.0, RelOutput = 98.0 };
        _mockRepository.Setup(r => r.CreateAsync(beam, It.IsAny<CancellationToken>()))
            .ReturnsAsync(beam);

        // Act
        var result = await _controller.Create(beam, CancellationToken.None);

        // Assert
        var createdResult = result.Result.Should().BeOfType<CreatedAtActionResult>().Subject;
    createdResult.ActionName.Should().Be(nameof(BeamsController.GetById));
        createdResult.RouteValues!["id"].Should().Be("beam-new");
    }

    [Fact]
    public async Task Create_WithDuplicateId_ReturnsConflict()
    {
        // Arrange
        var beam = new Beam { Id = "beam-001", Type = "9e", Timestamp = new DateTime(2025, 11, 12), MachineId = "MPC-001", RelUniformity = 99.0, RelOutput = 98.0 };
        _mockRepository.Setup(r => r.CreateAsync(beam, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new InvalidOperationException("Beam already exists"));

        // Act
        var result = await _controller.Create(beam, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<ConflictObjectResult>();
    }

    [Fact]
    public async Task Update_WithMatchingIds_ReturnsNoContent()
    {
        // Arrange
        var beam = new Beam { Id = "beam-001", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.5, RelOutput = 98.8 };
        _mockRepository.Setup(r => r.UpdateAsync(beam, It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Update("beam-001", beam, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NoContentResult>();
    }

    [Fact]
    public async Task Update_WithMismatchedIds_ReturnsBadRequest()
    {
        // Arrange
        var beam = new Beam { Id = "beam-002", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.5, RelOutput = 98.8 };

        // Act
        var result = await _controller.Update("beam-001", beam, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Update_WithNonExistentId_ReturnsNotFound()
    {
        // Arrange
        var beam = new Beam { Id = "nonexistent", Type = "6e", Timestamp = new DateTime(2025, 11, 9), MachineId = "MPC-001", RelUniformity = 99.5, RelOutput = 98.8 };
        _mockRepository.Setup(r => r.UpdateAsync(beam, It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Update("nonexistent", beam, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public async Task Delete_WithValidId_ReturnsNoContent()
    {
        // Arrange
        _mockRepository.Setup(r => r.DeleteAsync("beam-001", It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Delete("beam-001", CancellationToken.None);

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
    public async Task GetBeamTypes_ReturnsOkWithTypes()
    {
        // Arrange
        var types = new[] { "6e", "9e", "12e", "16e", "10x", "15x", "6xff" };
        _mockRepository.Setup(r => r.GetBeamTypesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(types.ToList().AsReadOnly());

        // Act
        var result = await _controller.GetBeamTypes(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedTypes = okResult.Value.Should().BeAssignableTo<IEnumerable<string>>().Subject;
        returnedTypes.Should().HaveCount(7);
    }

    // ─── GetBeamVariants ───────────────────────────────────────

    [Fact]
    public async Task GetBeamVariants_ReturnsOkWithVariants()
    {
        // Arrange
        var variants = new List<BeamVariantDto>
        {
            new("253c1694-12d0-4497-9bd0-8487ee7c6f6f", "6x"),
            new("ffda6e9f-8f4d-48c3-8270-621d4a99db51", "6xFFF"),
            new("e6763342-a180-444a-a869-ce57d1b086b1", "6e")
        };
        _mockRepository.Setup(r => r.GetBeamVariantsWithIdsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(variants.AsReadOnly());

        // Act
        var result = await _controller.GetBeamVariants(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<BeamVariantDto>>().Subject;
        returned.Should().HaveCount(3);
    }

    [Fact]
    public async Task GetBeamVariants_WhenEmpty_ReturnsOkWithEmptyList()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetBeamVariantsWithIdsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<BeamVariantDto>().AsReadOnly());

        // Act
        var result = await _controller.GetBeamVariants(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<BeamVariantDto>>().Subject;
        returned.Should().BeEmpty();
    }

    // ─── GetByDate ─────────────────────────────────────────────

    [Fact]
    public async Task GetByDate_WithValidParams_ReturnsOkWithBeamCheckOptions()
    {
        // Arrange
        var testDate = new DateTime(2025, 11, 9);
        var beams = new List<Beam>
        {
            new() { Id = "beam-001", Type = "6x", Timestamp = testDate, MachineId = "MPC-001", RelOutput = 98.5 },
            new() { Id = "beam-002", Type = "6x", Timestamp = testDate.AddMinutes(5), MachineId = "MPC-001", RelOutput = 99.0 }
        };
        _mockRepository.Setup(r => r.GetAllAsync("MPC-001", "6x", testDate, null, null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(beams);

        // Act
        var result = await _controller.GetByDate("MPC-001", "6x", "2025-11-09", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returned = okResult.Value.Should().BeAssignableTo<IEnumerable<BeamCheckOption>>().Subject;
        returned.Should().HaveCount(2);
    }

    [Fact]
    public async Task GetByDate_WithEmptyMachineId_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetByDate("", "6x", "2025-11-09", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetByDate_WithEmptyBeamType_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetByDate("MPC-001", "", "2025-11-09", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task GetByDate_WithInvalidDate_ReturnsBadRequest()
    {
        // Act
        var result = await _controller.GetByDate("MPC-001", "6x", "not-a-date", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<BadRequestObjectResult>();
    }

    // ─── Accept ────────────────────────────────────────────────

    [Fact]
    public async Task Accept_WithValidRequest_ReturnsOkWithApprovedIds()
    {
        // Arrange
        var request = new AcceptBeamRequest(new[] { "beam-001", "beam-002" }, "Dr. Smith");
        _mockRepository.Setup(r => r.ApproveAsync("beam-001", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        _mockRepository.Setup(r => r.ApproveAsync("beam-002", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
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
        var request = new AcceptBeamRequest(new List<string>(), "Dr. Smith");

        // Act
        var result = await _controller.Accept(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Accept_WithNullIds_ReturnsBadRequest()
    {
        // Arrange
        var request = new AcceptBeamRequest(null!, "Dr. Smith");

        // Act
        var result = await _controller.Accept(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Accept_WithPartialFailure_ReturnsOkWithErrorsList()
    {
        // Arrange
        var request = new AcceptBeamRequest(new[] { "beam-001", "beam-invalid" }, "Dr. Smith");
        _mockRepository.Setup(r => r.ApproveAsync("beam-001", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        _mockRepository.Setup(r => r.ApproveAsync("beam-invalid", "Dr. Smith", It.IsAny<DateTime>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Accept(request, CancellationToken.None);

        // Assert
        result.Should().BeOfType<OkObjectResult>();
    }
}
