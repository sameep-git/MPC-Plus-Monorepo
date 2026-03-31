namespace Api.Models;

/// <summary>
/// Represents a user in the system.
/// </summary>
public class User
{
    /// <summary>User unique identifier.</summary>
    public required string Id { get; set; }

    /// <summary>Username for login.</summary>
    public required string Username { get; set; }

    /// <summary>Email address.</summary>
    public string? Email { get; set; }

    /// <summary>User's full name.</summary>
    public string? FullName { get; set; }

    /// <summary>Hashed password (bcrypt).</summary>
    public required string PasswordHash { get; set; }

    /// <summary>User role (Admin, User, etc).</summary>
    public string Role { get; set; } = "User";

    /// <summary>Whether the user account is active.</summary>
    public bool IsActive { get; set; } = true;

    /// <summary>When the user account was created.</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    /// <summary>When the user last logged in.</summary>
    public DateTime? LastLoginAt { get; set; }

    /// <summary>Approval status for new user accounts.</summary>
    public string ApprovalStatus { get; set; } = "APPROVED";
}

/// <summary>
/// Response model for authentication endpoints.
/// </summary>
public class AuthResponse
{
    /// <summary>JWT access token.</summary>
    public required string Token { get; set; }

    /// <summary>User information.</summary>
    public required UserDto User { get; set; }
}

/// <summary>
/// DTO for user information in responses.
/// </summary>
public class UserDto
{
    /// <summary>User unique identifier.</summary>
    public required string Id { get; set; }

    /// <summary>Username.</summary>
    public required string Username { get; set; }

    /// <summary>Email address.</summary>
    public string? Email { get; set; }

    /// <summary>User's full name.</summary>
    public string? FullName { get; set; }

    /// <summary>User role.</summary>
    public required string Role { get; set; }

    /// <summary>Approval status.</summary>
    public required string ApprovalStatus { get; set; }
}
