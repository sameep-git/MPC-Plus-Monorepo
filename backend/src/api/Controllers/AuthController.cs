using Api.Models;
using Api.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;
    private readonly ILogger<AuthController> _logger;

    public AuthController(IAuthService authService, ILogger<AuthController> logger)
    {
        _authService = authService;
        _logger = logger;
    }

    /// <summary>
    /// Sign in with username and password
    /// </summary>
    [HttpPost("login")]
    public async Task<ActionResult<AuthResponse>> Login(
        [FromBody] LoginRequest request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Username) || string.IsNullOrWhiteSpace(request.Password))
        {
            return BadRequest("Username and password are required");
        }

        try
        {
            var response = await _authService.LoginAsync(request.Username, request.Password, cancellationToken);
            return Ok(response);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning($"Login failed: {ex.Message}");
            return Unauthorized(new { message = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Login error");
            return StatusCode(500, new { message = "An error occurred during login" });
        }
    }

    /// <summary>
    /// Register a new user account
    /// </summary>
    [HttpPost("register")]
    public async Task<ActionResult<AuthResponse>> Register(
        [FromBody] RegisterRequest request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Username) || string.IsNullOrWhiteSpace(request.Password))
        {
            return BadRequest("Username and password are required");
        }

        if (request.Password.Length < 6)
        {
            return BadRequest("Password must be at least 6 characters");
        }

        try
        {
            var response = await _authService.RegisterAsync(
                request.Username,
                request.Password,
                request.Email,
                request.FullName,
                cancellationToken);
            return Ok(response);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning($"Registration failed: {ex.Message}");
            return BadRequest(new { message = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError($"Registration error: {ex.Message}");
            return StatusCode(500, new { message = "An error occurred during registration" });
        }
    }

    /// <summary>
    /// Get current user info (requires authentication)
    /// </summary>
    [Authorize]
    [HttpGet("me")]
    public async Task<ActionResult<UserDto>> GetCurrentUser(CancellationToken cancellationToken)
    {
        var userId = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
        
        if (string.IsNullOrWhiteSpace(userId))
        {
            return Unauthorized();
        }

        try
        {
            var user = await _authService.GetUserAsync(userId, cancellationToken);
            if (user == null)
            {
                return NotFound();
            }

            return Ok(new UserDto
            {
                Id = user.Id,
                Username = user.Username,
                Email = user.Email,
                FullName = user.FullName,
                Role = user.Role
            });
        }
        catch (Exception ex)
        {
            _logger.LogError($"Error getting current user: {ex.Message}");
            return StatusCode(500, new { message = "An error occurred" });
        }
    }
}

/// <summary>
/// Request model for user registration.
/// </summary>
public class RegisterRequest
{
    /// <summary>Username for the new account.</summary>
    public required string Username { get; set; }

    /// <summary>Password for the new account.</summary>
    public required string Password { get; set; }

    /// <summary>Email address (optional).</summary>
    public string? Email { get; set; }

    /// <summary>Full name (optional).</summary>
    public string? FullName { get; set; }
}
