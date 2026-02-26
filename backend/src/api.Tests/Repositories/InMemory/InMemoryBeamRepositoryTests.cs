using Api.Models;
using Api.Repositories;

namespace Api.Tests.Repositories.InMemory;

public class InMemoryBeamRepositoryTests
{
    private readonly InMemoryBeamRepository _repository = new();

    [Fact]
    public async Task GetAllAsync_ReturnsAllSeedBeams()
    {
        // Act
        var result = await _repository.GetAllAsync();

        // Assert
        result.Should().NotBeNull().And.HaveCount(13);
    }

    [Fact]
    public async Task GetAllAsync_WithMachineIdFilter_ReturnsOnlyBeamsForMachine()
    {
        // Act
        var result = await _repository.GetAllAsync(machineId: "MPC-001");

        // Assert
        result.Should().NotBeNull().And.AllSatisfy(b => b.MachineId.Should().Be("MPC-001"));
        result.Should().HaveCount(5); // Based on seed data
    }

    [Fact]
    public async Task GetAllAsync_WithTypeFilter_ReturnsOnlyBeamsOfType()
    {
        // Act
        var result = await _repository.GetAllAsync(type: "6e");

        // Assert
        result.Should().NotBeNull().And.AllSatisfy(b => b.Type.Should().Be("6e"));
    }

    [Fact]
    public async Task GetAllAsync_WithDateFilter_ReturnsBeamsFromThatDate()
    {
        // Act
        var testDate = new DateTime(2025, 11, 9);
        var result = await _repository.GetAllAsync(date: testDate);

        // Assert
        result.Should().NotBeNull().And.AllSatisfy(b => b.Timestamp.Date.Should().Be(testDate.Date));
    }

    [Fact]
    public async Task GetAllAsync_WithDateRangeFilter_ReturnsBeamsInRange()
    {
        // Act
        var startDate = new DateTime(2025, 11, 7);
        var endDate = new DateTime(2025, 11, 9);
        var result = await _repository.GetAllAsync(startDate: startDate, endDate: endDate);

        // Assert
        result.Should().NotBeNull()
            .And.AllSatisfy(b =>
            {
                b.Timestamp.CompareTo(startDate).Should().BeGreaterThanOrEqualTo(0);
                b.Timestamp.CompareTo(endDate).Should().BeLessThanOrEqualTo(0);
            });
    }

    [Fact]
    public async Task GetAllAsync_OrdersByDateDescending()
    {
        // Act
        var result = await _repository.GetAllAsync();

        // Assert
        var resultList = result.ToList();
        for (int i = 0; i < resultList.Count - 1; i++)
        {
            resultList[i].Timestamp.CompareTo(resultList[i + 1].Timestamp).Should().BeGreaterThanOrEqualTo(0);
        }
    }

    [Fact]
    public async Task GetByIdAsync_WithValidId_ReturnsBeam()
    {
        // Act
        var result = await _repository.GetByIdAsync("beam-001");

        // Assert
        result.Should().NotBeNull();
        result!.Id.Should().Be("beam-001");
        result.Type.Should().Be("6e");
    }

    [Fact]
    public async Task GetByIdAsync_WithInvalidId_ReturnsNull()
    {
        // Act
        var result = await _repository.GetByIdAsync("invalid-beam");

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task CreateAsync_WithNewBeam_AddsToRepository()
    {
        // Arrange
        var newBeam = new Beam
        {
            Id = "test-beam",
            Type = "9e",
            Timestamp = new DateTime(2025, 11, 12),
            MachineId = "MPC-001",
            RelUniformity = 99.0,
            RelOutput = 98.0
        };

        // Act
        var result = await _repository.CreateAsync(newBeam);
        var retrieved = await _repository.GetByIdAsync("test-beam");

        // Assert
        result.Should().NotBeNull();
        result.Id.Should().Be("test-beam");
        retrieved.Should().NotBeNull();
    }

    [Fact]
    public async Task CreateAsync_WithDuplicateId_ThrowsInvalidOperationException()
    {
        // Arrange
        var duplicateBeam = new Beam
        {
            Id = "beam-001",
            Type = "9e",
            Timestamp = new DateTime(2025, 11, 12),
            MachineId = "MPC-001",
            RelUniformity = 99.0,
            RelOutput = 98.0
        };

        // Act & Assert
        await _repository.Invoking(r => r.CreateAsync(duplicateBeam))
            .Should().ThrowAsync<InvalidOperationException>();
    }

    [Fact]
    public async Task UpdateAsync_WithExistingBeam_UpdatesSuccessfully()
    {
        // Arrange
        var updatedBeam = new Beam
        {
            Id = "beam-001",
            Type = "6e",
            Timestamp = new DateTime(2025, 11, 7),
            MachineId = "MPC-001",
            RelUniformity = 99.5,
            RelOutput = 99.0,
            Note = "Updated note"
        };

        // Act
        var result = await _repository.UpdateAsync(updatedBeam);
        var retrieved = await _repository.GetByIdAsync("beam-001");

        // Assert
        result.Should().BeTrue();
        retrieved!.Note.Should().Be("Updated note");
        retrieved.RelUniformity.Should().Be(99.5);
    }

    [Fact]
    public async Task UpdateAsync_WithNonExistentBeam_ReturnsFalse()
    {
        // Arrange
        var nonExistentBeam = new Beam
        {
            Id = "nonexistent-beam",
            Type = "9e",
            Timestamp = new DateTime(2025, 11, 12),
            MachineId = "MPC-001",
            RelUniformity = 99.0,
            RelOutput = 98.0
        };

        // Act
        var result = await _repository.UpdateAsync(nonExistentBeam);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public async Task DeleteAsync_WithExistingBeam_DeletesSuccessfully()
    {
        // Act
        var result = await _repository.DeleteAsync("beam-001");
        var retrieved = await _repository.GetByIdAsync("beam-001");

        // Assert
        result.Should().BeTrue();
        retrieved.Should().BeNull();
    }

    [Fact]
    public async Task DeleteAsync_WithNonExistentBeam_ReturnsFalse()
    {
        // Act
        var result = await _repository.DeleteAsync("nonexistent-beam");

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public async Task GetBeamTypesAsync_ReturnsAllAvailableTypes()
    {
        // Act
        var result = await _repository.GetBeamTypesAsync();

        // Assert
        result.Should().NotBeNull()
            .And.Contain("6e", "9e", "12e", "16e", "10x", "15x", "6xff");
    }
}
