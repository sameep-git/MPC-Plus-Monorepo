namespace Api.Models;

/// <summary>
/// Represents credentials used for user authentication.
/// </summary>
public class LoginRequest
{
    /// <summary>The username credential.</summary>
    public required string Username { get; set; }

    /// <summary>The password credential.</summary>
    public required string Password { get; set; }
}

