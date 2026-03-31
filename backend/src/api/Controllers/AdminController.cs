using Api.Models;
using Api.Repositories;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;

namespace Api.Controllers;

[ApiController]
[Route("api/admin")]
[Authorize]
public class AdminController : ControllerBase
{
    private readonly IUserRepository _userRepository;
    private readonly ILogger<AdminController> _logger;

    public AdminController(IUserRepository userRepository, ILogger<AdminController> logger)
    {
        _userRepository = userRepository;
        _logger = logger;
    }

    /// <summary>
    /// Get all users (Admin only)
    /// </summary>
    [HttpGet("users")]
    public async Task<ActionResult<IReadOnlyList<UserDto>>> GetAllUsers(CancellationToken cancellationToken)
    {
        // Check if user is admin
        var userRole = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;
        if (userRole != "Admin")
        {
            return Forbid();
        }

        try
        {
            var users = await _userRepository.GetAllAsync(cancellationToken);
            var userDtos = users.Select(u => new UserDto
            {
                Id = u.Id,
                Username = u.Username,
                Email = u.Email,
                FullName = u.FullName,
                Role = u.Role,
                ApprovalStatus = u.ApprovalStatus
            }).ToList();

            return Ok(userDtos);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting all users");
            return StatusCode(500, new { message = "An error occurred" });
        }
    }

    /// <summary>
    /// Get pending user approvals (Admin only)
    /// </summary>
    [HttpGet("users/pending")]
    public async Task<ActionResult<IReadOnlyList<UserDto>>> GetPendingUsers(CancellationToken cancellationToken)
    {
        // Check if user is admin
        var userRole = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;
        if (userRole != "Admin")
        {
            return Forbid();
        }

        try
        {
            var users = await _userRepository.GetPendingUsersAsync(cancellationToken);
            var userDtos = users.Select(u => new UserDto
            {
                Id = u.Id,
                Username = u.Username,
                Email = u.Email,
                FullName = u.FullName,
                Role = u.Role,
                ApprovalStatus = u.ApprovalStatus
            }).ToList();

            return Ok(userDtos);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting pending users");
            return StatusCode(500, new { message = "An error occurred" });
        }
    }

    /// <summary>
    /// Approve a user (Admin only)
    /// </summary>
    [HttpPost("users/{userId}/approve")]
    public async Task<IActionResult> ApproveUser(string userId, CancellationToken cancellationToken)
    {
        // Check if user is admin
        var userRole = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;
        if (userRole != "Admin")
        {
            return Forbid();
        }

        var adminId = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
        if (string.IsNullOrWhiteSpace(adminId))
        {
            return Unauthorized();
        }

        try
        {
            var success = await _userRepository.UpdateApprovalStatusAsync(userId, "APPROVED", cancellationToken);
            if (!success)
            {
                return NotFound(new { message = "User not found" });
            }

            _logger.LogInformation($"User {userId} approved");
            return Ok(new { message = "User approved successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Error approving user {userId}");
            return StatusCode(500, new { message = "An error occurred" });
        }
    }

    /// <summary>
    /// Deny a user (Admin only)
    /// </summary>
    [HttpPost("users/{userId}/deny")]
    public async Task<IActionResult> DenyUser(string userId, CancellationToken cancellationToken)
    {
        // Check if user is admin
        var userRole = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;
        if (userRole != "Admin")
        {
            return Forbid();
        }

        try
        {
            var success = await _userRepository.UpdateApprovalStatusAsync(userId, "DENIED", cancellationToken);
            if (!success)
            {
                return NotFound(new { message = "User not found" });
            }

            _logger.LogInformation($"User {userId} denied");
            return Ok(new { message = "User denied successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Error denying user {userId}");
            return StatusCode(500, new { message = "An error occurred" });
        }
    }

    /// <summary>
    /// Update user role (Admin only)
    /// </summary>
    [HttpPut("users/{userId}/role")]
    public async Task<IActionResult> UpdateUserRole(string userId, [FromBody] UpdateRoleRequest request, CancellationToken cancellationToken)
    {
        // Check if user is admin
        var userRole = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;
        if (userRole != "Admin")
        {
            return Forbid();
        }

        if (string.IsNullOrWhiteSpace(request.Role) || (request.Role != "User" && request.Role != "Admin"))
        {
            return BadRequest(new { message = "Invalid role. Must be 'User' or 'Admin'" });
        }

        // Get the user first to check current role
        var user = await _userRepository.GetByIdAsync(userId, cancellationToken);
        if (user == null)
        {
            return NotFound(new { message = "User not found" });
        }

        // Prevent demoting the last admin
        if (request.Role == "User")
        {
            var allUsers = await _userRepository.GetAllAsync(cancellationToken);
            var activeAdmins = allUsers.Count(u => u.IsActive && u.Role == "Admin");
            if (activeAdmins <= 1 && user.Role == "Admin")
            {
                return BadRequest(new { message = "Cannot demote the last admin. There must always be at least one admin." });
            }
        }

        try
        {
            user.Role = request.Role;
            var success = await _userRepository.UpdateAsync(user, cancellationToken);
            if (!success)
            {
                return StatusCode(500, new { message = "Failed to update user role" });
            }

            _logger.LogInformation($"User {userId} role updated to {request.Role}");
            return Ok(new { message = "User role updated successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Error updating user role for {userId}");
            return StatusCode(500, new { message = "An error occurred" });
        }
    }
}

/// <summary>
/// Request model for updating user role.
/// </summary>
public class UpdateRoleRequest
{
    /// <summary>New role for the user ('User' or 'Admin').</summary>
    public required string Role { get; set; }
}