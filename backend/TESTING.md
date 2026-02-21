# C# .NET Testing Guide & Implementation Summary

## Testing Concepts - C# vs Spring Boot

### Framework Comparison

| Feature | Spring Boot (Java) | C# .NET |
|---------|-------------------|--------|
| **Primary Framework** | JUnit 5 (Jupiter) | xUnit (recommended) |
| **Alternative Frameworks** | TestNG | NUnit, MSTest |
| **Mocking Library** | Mockito | Moq |
| **Assertion Library** | AssertJ, Hamcrest | FluentAssertions |
| **Test Attribute** | `@Test` | `[Fact]` |
| **Parameterized Tests** | `@ParameterizedTest` | `[Theory]` |
| **Parameterized Data** | `@ValueSource`, `@CsvSource` | `[InlineData]`, `[MemberData]` |
| **Setup/Teardown** | `@Before`, `@After` | Constructor, `IDisposable` |
| **Test Collection/Suite** | Test classes | xUnit collections |
| **Project Structure** | `src/test/java` | Separate `*.Tests` project |

### Key C# .NET Testing Concepts

#### 1. **[Fact] vs [Theory]**
```csharp
// [Fact] - Single test case
[Fact]
public async Task GetAll_ReturnsOkWithMachines()
{
    // Test code here
}

// [Theory] - Parameterized test (like @ParameterizedTest)
[Theory]
[InlineData("MPC-001")]
[InlineData("MPC-002")]
public async Task GetById_WithValidId_ReturnsMachine(string machineId)
{
    // Test code here - runs once for each InlineData
}
```

#### 2. **Async Testing**
C# .NET has built-in support for async tests:
```csharp
[Fact]
public async Task MyAsyncTest()
{
    // Test implementation - returns Task
    await someAsyncOperation();
}
```

#### 3. **Mocking with Moq**
Similar to Mockito:
```csharp
// Setup mock behavior
_mockRepository.Setup(r => r.GetByIdAsync("id", It.IsAny<CancellationToken>()))
    .ReturnsAsync(machine);

// Verify mock was called
_mockRepository.Verify(r => r.GetByIdAsync("id", It.IsAny<CancellationToken>()), Times.Once);
```

#### 4. **FluentAssertions - More Readable**
```csharp
// Instead of: Assert.Equal(expected, actual);
result.Should().Be(expected);

// Collections
result.Should().HaveCount(3);
result.Should().Contain(x => x.Id == "MPC-001");
result.Should().AllSatisfy(b => b.MachineId.Should().Be("MPC-001"));

// Async methods
await _repository.Invoking(r => r.CreateAsync(machine))
    .Should().ThrowAsync<InvalidOperationException>();
```

#### 5. **Test Organization**
C# .NET typically creates a separate `*.Tests` project mirroring the main project structure:
```
api/                          (Main Project)
  Controllers/
  Repositories/
  Models/

api.Tests/                     (Test Project)
  Controllers/
    MachineControllerTests.cs
    BeamControllerTests.cs
  Repositories/
    InMemory/
      InMemoryMachineRepositoryTests.cs
      InMemoryBeamRepositoryTests.cs
```

#### 6. **Global Usings in .csproj**
Avoid repetitive using statements:
```xml
<ItemGroup>
  <Using Include="Xunit" />
  <Using Include="Moq" />
  <Using Include="FluentAssertions" />
</ItemGroup>
```

---

## Our Test Implementation

### Project Setup
- **Framework**: xUnit 2.9.2
- **Mocking**: Moq 4.20.70
- **Assertions**: FluentAssertions 6.12.0
- **Structure**: Separate `api.Tests` project

### Test Coverage

#### 1. **Repository Tests**
Testing In-Memory implementations of repositories:

**InMemoryMachineRepositoryTests.cs** (11 tests)
- `GetAllAsync_ReturnsAllSeedMachines` - Verifies all 3 seed machines returned
- `GetByIdAsync_WithValidId_ReturnsMachine` - Tests retrieving by ID (3 variations with `[Theory]`)
- `GetByIdAsync_WithInvalidId_ReturnsNull` - Handles missing IDs
- `CreateAsync_WithNewMachine_AddsToRepository` - Creates new records
- `CreateAsync_WithDuplicateId_ThrowsInvalidOperationException` - Rejects duplicates
- `UpdateAsync_WithExistingMachine_UpdatesSuccessfully` - Modifies existing records
- `UpdateAsync_WithNonExistentMachine_ReturnsFalse` - Handles not found
- `DeleteAsync_WithExistingMachine_DeletesSuccessfully` - Removes records (2 variations)
- `DeleteAsync_WithNonExistentMachine_ReturnsFalse` - Handles not found

**InMemoryBeamRepositoryTests.cs** (18 tests)
- `GetAllAsync_ReturnsAllSeedBeams` - Verifies all 13 seed beams returned
- `GetAllAsync_WithMachineIdFilter_ReturnsOnlyBeamsForMachine` - Filters by machine
- `GetAllAsync_WithTypeFilter_ReturnsOnlyBeamsOfType` - Filters by type
- `GetAllAsync_WithDateFilter_ReturnsBeamsFromThatDate` - Exact date match
- `GetAllAsync_WithDateRangeFilter_ReturnsBeamsInRange` - Date range filtering
- `GetAllAsync_OrdersByDateDescending` - Verifies sort order
- `GetByIdAsync_WithValidId_ReturnsBeam` - Retrieves by ID
- `GetByIdAsync_WithInvalidId_ReturnsNull` - Handles missing
- `CreateAsync_WithNewBeam_AddsToRepository` - Creates new beams
- `CreateAsync_WithDuplicateId_ThrowsInvalidOperationException` - Rejects duplicates
- `UpdateAsync_WithExistingBeam_UpdatesSuccessfully` - Updates fields
- `UpdateAsync_WithNonExistentBeam_ReturnsFalse` - Handles not found
- `DeleteAsync_WithExistingBeam_DeletesSuccessfully` - Removes beams
- `DeleteAsync_WithNonExistentBeam_ReturnsFalse` - Handles not found
- `GetBeamTypesAsync_ReturnsAllAvailableTypes` - Returns type list

#### 2. **Controller Tests**
Testing ASP.NET Core controller endpoints with mocked repositories:

**MachineControllerTests.cs** (11 tests)
- `GetAll_ReturnsOkWithMachines` - HTTP 200 with data
- `GetById_WithValidId_ReturnsOkWithMachine` - HTTP 200 with single record
- `GetById_WithInvalidId_ReturnsNotFound` - HTTP 404
- `Create_WithValidMachine_ReturnsCreatedAtActionResult` - HTTP 201 with location
- `Create_WithDuplicateId_ReturnsConflict` - HTTP 409
- `Update_WithMatchingIds_ReturnsNoContent` - HTTP 204
- `Update_WithMismatchedIds_ReturnsBadRequest` - HTTP 400
- `Update_WithNonExistentId_ReturnsNotFound` - HTTP 404
- `Delete_WithValidId_ReturnsNoContent` - HTTP 204
- `Delete_WithNonExistentId_ReturnsNotFound` - HTTP 404

**BeamControllerTests.cs** (11 tests)
- `GetAll_ReturnsOkWithBeams` - HTTP 200 with collection
- `GetAll_WithTypeFilter_PassesFilterToRepository` - Verifies filter passed to repo
- `GetAll_WithMachineIdFilter_PassesFilterToRepository` - Verifies machine ID filter
- `GetAll_WithDateFilter_ParsesAndPassesDateToRepository` - Verifies date parsing
- `GetById_WithValidId_ReturnsOkWithBeam` - HTTP 200 with beam
- `GetById_WithInvalidId_ReturnsNotFound` - HTTP 404
- `Create_WithValidBeam_ReturnsCreatedAtActionResult` - HTTP 201
- `Create_WithDuplicateId_ReturnsConflict` - HTTP 409
- `Update_WithMatchingIds_ReturnsNoContent` - HTTP 204
- `Update_WithMismatchedIds_ReturnsBadRequest` - HTTP 400
- `Update_WithNonExistentId_ReturnsNotFound` - HTTP 404
- `Delete_WithValidId_ReturnsNoContent` - HTTP 204
- `Delete_WithNonExistentId_ReturnsNotFound` - HTTP 404
- `GetBeamTypes_ReturnsOkWithTypes` - HTTP 200 with types

### Running Tests

```bash
# Run all tests
cd src/api.Tests
dotnet test

# Run specific test class
dotnet test --filter "Api.Tests.Repositories.InMemory.InMemoryMachineRepositoryTests"

# Run with coverage
dotnet test /p:CollectCoverage=true

# Watch mode (run on file changes)
dotnet watch test
```

### Test Statistics
- **Total Tests**: 51
- **Pass Rate**: 100% ✅
- **Categories**:
  - Repository Tests: 29
  - Controller Tests: 22

---

## Best Practices Applied

1. **Arrange-Act-Assert (AAA) Pattern**
   ```csharp
   // Arrange - Set up test data
   var machine = new Machine { Id = "test", Name = "Test", ... };
   
   // Act - Execute the code
   var result = await _repository.GetByIdAsync("test");
   
   // Assert - Verify results
   result.Should().NotBeNull();
   ```

2. **Naming Convention**
   - `[MethodName]_[Condition]_[ExpectedResult]`
   - Example: `CreateAsync_WithDuplicateId_ThrowsInvalidOperationException`

3. **Test Independence**
   - Each test creates its own repository instance
   - No test depends on another test's state

4. **Mock Verification**
   - Use `Verify()` to ensure mocks were called correctly
   - Check both success and error paths

5. **Parameterized Tests**
   - Use `[Theory]` for testing multiple inputs
   - Reduces code duplication

6. **Fluent Assertions**
   - More readable and self-documenting
   - Better error messages on failure

---

## Common Patterns in C# Testing

### Testing Exceptions
```csharp
await _repository.Invoking(r => r.CreateAsync(duplicate))
    .Should().ThrowAsync<InvalidOperationException>();
```

### Testing Collections
```csharp
result.Should().HaveCount(3);
result.Should().Contain(m => m.Id == "MPC-001");
result.Should().AllSatisfy(b => b.MachineId == "MPC-001");
```

### Testing Async Methods
```csharp
[Fact]
public async Task MyTest()
{
    var result = await _controller.GetAll();
    result.Should().NotBeNull();
}
```

### Mock Setup with Named Parameters
```csharp
_mockRepository.Setup(r => r.GetAllAsync(
        machineId: "MPC-001",
        type: null,
        date: null,
        startDate: null,
        endDate: null,
        cancellationToken: It.IsAny<CancellationToken>()))
    .ReturnsAsync(beams);
```
