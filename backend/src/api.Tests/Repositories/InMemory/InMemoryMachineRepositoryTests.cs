using Api.Models;
using Api.Repositories;

namespace Api.Tests.Repositories.InMemory;

public class InMemoryMachineRepositoryTests
{
    private readonly InMemoryMachineRepository _repository = new();

    [Fact]
    public async Task GetAllAsync_ReturnsAllSeedMachines()
    {
        // Act
        var result = await _repository.GetAllAsync();

        // Assert
        result.Should().NotBeNull().And.HaveCount(3);
        result.Should().Contain(m => m.Id == "1" && m.Name == "MPC-001");
        result.Should().Contain(m => m.Id == "2" && m.Name == "MPC-002");
        result.Should().Contain(m => m.Id == "3" && m.Name == "MPC-003");
    }

    [Theory]
    [InlineData("1")]
    [InlineData("2")]
    [InlineData("3")]
    public async Task GetByIdAsync_WithValidId_ReturnsMachine(string machineId)
    {
        // Act
        var result = await _repository.GetByIdAsync(machineId);

        // Assert
        result.Should().NotBeNull();
        result!.Id.Should().Be(machineId);
    }

    [Fact]
    public async Task GetByIdAsync_WithInvalidId_ReturnsNull()
    {
        // Act
        var result = await _repository.GetByIdAsync("invalid-id");

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task CreateAsync_WithNewMachine_AddsToRepository()
    {
        // Arrange
        var newMachine = new Machine
        {
            Id = "4",
            Name = "New Machine",
            Type = "Linear Accelerator",
            Location = "Room C"
        };

        // Act
        var result = await _repository.CreateAsync(newMachine);
        var retrieved = await _repository.GetByIdAsync("4");

        // Assert
        result.Should().NotBeNull();
        result.Id.Should().Be("4");
        retrieved.Should().NotBeNull();
        retrieved!.Name.Should().Be("New Machine");
    }

    [Fact]
    public async Task CreateAsync_WithDuplicateId_ThrowsInvalidOperationException()
    {
        // Arrange
        var duplicateMachine = new Machine
        {
            Id = "1",
            Name = "Duplicate",
            Type = "Linear Accelerator",
            Location = "Room X"
        };

        // Act & Assert
        await _repository.Invoking(r => r.CreateAsync(duplicateMachine))
            .Should().ThrowAsync<InvalidOperationException>();
    }

    [Fact]
    public async Task UpdateAsync_WithExistingMachine_UpdatesSuccessfully()
    {
        // Arrange
        var updatedMachine = new Machine
        {
            Id = "1",
            Name = "Updated Primary Gantry",
            Type = "Linear Accelerator",
            Location = "Room A Updated"
        };

        // Act
        var result = await _repository.UpdateAsync(updatedMachine);
        var retrieved = await _repository.GetByIdAsync("1");

        // Assert
        result.Should().BeTrue();
        retrieved!.Name.Should().Be("Updated Primary Gantry");
        retrieved.Location.Should().Be("Room A Updated");
    }

    [Fact]
    public async Task UpdateAsync_WithNonExistentMachine_ReturnsFalse()
    {
        // Arrange
        var nonExistentMachine = new Machine
        {
            Id = "nonexistent",
            Name = "Nonexistent",
            Type = "Linear Accelerator",
            Location = "Room X"
        };

        // Act
        var result = await _repository.UpdateAsync(nonExistentMachine);

        // Assert
        result.Should().BeFalse();
    }

    [Theory]
    [InlineData("1")]
    [InlineData("2")]
    public async Task DeleteAsync_WithExistingMachine_DeletesSuccessfully(string machineId)
    {
        // Act
        var result = await _repository.DeleteAsync(machineId);
        var retrieved = await _repository.GetByIdAsync(machineId);

        // Assert
        result.Should().BeTrue();
        retrieved.Should().BeNull();
    }

    [Fact]
    public async Task DeleteAsync_WithNonExistentMachine_ReturnsFalse()
    {
        // Act
        var result = await _repository.DeleteAsync("nonexistent");

        // Assert
        result.Should().BeFalse();
    }
}
