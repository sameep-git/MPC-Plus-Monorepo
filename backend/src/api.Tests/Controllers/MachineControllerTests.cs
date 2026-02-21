using Api.Controllers;
using Api.Models;
using Api.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace Api.Tests.Controllers;

public class MachineControllerTests
{
    private readonly Mock<IMachineRepository> _mockRepository;
    private readonly MachinesController _controller;

    public MachineControllerTests()
    {
        _mockRepository = new Mock<IMachineRepository>();
    _controller = new MachinesController(_mockRepository.Object);
    }

    [Fact]
    public async Task GetAll_ReturnsOkWithMachines()
    {
        // Arrange
        var machines = new List<Machine>
        {
            new() { Id = "1", Name = "MPC-001", Type = "Varian TrueBeam", Location = "Fort Worth" },
            new() { Id = "2", Name = "MPC-002", Type = "Varian TrueBeam", Location = "Arlington" }
        };
        _mockRepository.Setup(r => r.GetAllAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(machines);

        // Act
        var result = await _controller.GetAll(CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedMachines = okResult.Value.Should().BeAssignableTo<IEnumerable<Machine>>().Subject;
        returnedMachines.Should().HaveCount(2);
        _mockRepository.Verify(r => r.GetAllAsync(It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetById_WithValidId_ReturnsOkWithMachine()
    {
        // Arrange
        var machine = new Machine { Id = "1", Name = "MPC-001", Type = "Varian TrueBeam", Location = "Fort Worth" };
        _mockRepository.Setup(r => r.GetByIdAsync("1", It.IsAny<CancellationToken>()))
            .ReturnsAsync(machine);

        // Act
        var result = await _controller.GetById("1", CancellationToken.None);

        // Assert
        var okResult = result.Result.Should().BeOfType<OkObjectResult>().Subject;
        var returnedMachine = okResult.Value.Should().BeOfType<Machine>().Subject;
        returnedMachine.Id.Should().Be("1");
    }

    [Fact]
    public async Task GetById_WithInvalidId_ReturnsNotFound()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetByIdAsync("invalid", It.IsAny<CancellationToken>()))
            .ReturnsAsync((Machine?)null);

        // Act
        var result = await _controller.GetById("invalid", CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public async Task Create_WithValidMachine_ReturnsCreatedAtActionResult()
    {
        // Arrange
        var machine = new Machine { Id = "4", Name = "New Machine", Type = "Type", Location = "Location" };
        _mockRepository.Setup(r => r.CreateAsync(machine, It.IsAny<CancellationToken>()))
            .ReturnsAsync(machine);

        // Act
        var result = await _controller.Create(machine, CancellationToken.None);

        // Assert
        var createdResult = result.Result.Should().BeOfType<CreatedAtActionResult>().Subject;
    createdResult.ActionName.Should().Be(nameof(MachinesController.GetById));
        createdResult.RouteValues!["id"].Should().Be("4");
        var returnedMachine = createdResult.Value.Should().BeOfType<Machine>().Subject;
        returnedMachine.Id.Should().Be("4");
    }

    [Fact]
    public async Task Create_WithDuplicateId_ReturnsConflict()
    {
        // Arrange
        var machine = new Machine { Id = "1", Name = "Duplicate", Type = "Type", Location = "Location" };
        _mockRepository.Setup(r => r.CreateAsync(machine, It.IsAny<CancellationToken>()))
            .ThrowsAsync(new InvalidOperationException("Machine already exists"));

        // Act
        var result = await _controller.Create(machine, CancellationToken.None);

        // Assert
        result.Result.Should().BeOfType<ConflictObjectResult>();
    }

    [Fact]
    public async Task Update_WithMatchingIds_ReturnsNoContent()
    {
        // Arrange
        var machine = new Machine { Id = "1", Name = "Updated", Type = "Type", Location = "Location" };
        _mockRepository.Setup(r => r.UpdateAsync(machine, It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Update("1", machine, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NoContentResult>();
    }

    [Fact]
    public async Task Update_WithMismatchedIds_ReturnsBadRequest()
    {
        // Arrange
        var machine = new Machine { Id = "2", Name = "Machine", Type = "Type", Location = "Location" };

        // Act
        var result = await _controller.Update("1", machine, CancellationToken.None);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Update_WithNonExistentId_ReturnsNotFound()
    {
        // Arrange
        var machine = new Machine { Id = "nonexistent", Name = "Machine", Type = "Type", Location = "Location" };
        _mockRepository.Setup(r => r.UpdateAsync(machine, It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        // Act
        var result = await _controller.Update("nonexistent", machine, CancellationToken.None);

        // Assert
        result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public async Task Delete_WithValidId_ReturnsNoContent()
    {
        // Arrange
        _mockRepository.Setup(r => r.DeleteAsync("1", It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        // Act
        var result = await _controller.Delete("1", CancellationToken.None);

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
}
