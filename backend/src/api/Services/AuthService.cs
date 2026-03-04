using Api.Models;
using Api.Repositories;

namespace Api.Services;

public interface IAuthService
{
    Task<AuthResponse> LoginAsync(string username, string password, CancellationToken cancellationToken = default);
    Task<AuthResponse> RegisterAsync(string username, string password, string? email = null, string? fullName = null, CancellationToken cancellationToken = default);
    Task<User?> GetUserAsync(string userId, CancellationToken cancellationToken = default);
}

public class AuthService : IAuthService
{
    private readonly IUserRepository _userRepository;
    private readonly ITokenService _tokenService;
    private readonly ILogger<AuthService> _logger;

    public AuthService(IUserRepository userRepository, ITokenService tokenService, ILogger<AuthService> logger)
    {
        _userRepository = userRepository;
        _tokenService = tokenService;
        _logger = logger;
    }

    public async Task<AuthResponse> LoginAsync(string username, string password, CancellationToken cancellationToken = default)
    {
        var user = await _userRepository.GetByUsernameAsync(username, cancellationToken);
        
        if (user == null || !user.IsActive)
        {
            _logger.LogWarning($"Login failed: User '{username}' not found or inactive");
            throw new InvalidOperationException("Invalid username or password");
        }

        if (!BCrypt.Net.BCrypt.Verify(password, user.PasswordHash))
        {
            _logger.LogWarning($"Login failed: Invalid password for user '{username}'");
            throw new InvalidOperationException("Invalid username or password");
        }

        // Update last login time
        user.LastLoginAt = DateTime.UtcNow;
        await _userRepository.UpdateAsync(user, cancellationToken);

        var token = _tokenService.GenerateToken(user);
        
        return new AuthResponse
        {
            Token = token,
            User = MapToUserDto(user)
        };
    }

    public async Task<AuthResponse> RegisterAsync(string username, string password, string? email = null, string? fullName = null, CancellationToken cancellationToken = default)
    {
        // Check if username already exists
        var existingUser = await _userRepository.GetByUsernameAsync(username, cancellationToken);
        if (existingUser != null)
        {
            throw new InvalidOperationException("Username already exists");
        }

        var passwordHash = BCrypt.Net.BCrypt.HashPassword(password);
        
        var newUser = new User
        {
            Id = Guid.NewGuid().ToString(),
            Username = username,
            Email = email,
            FullName = fullName,
            PasswordHash = passwordHash,
            Role = "User",
            IsActive = true
        };

        var createdUser = await _userRepository.CreateAsync(newUser, cancellationToken);
        var token = _tokenService.GenerateToken(createdUser);

        _logger.LogInformation($"User '{username}' registered successfully");

        return new AuthResponse
        {
            Token = token,
            User = MapToUserDto(createdUser)
        };
    }

    public async Task<User?> GetUserAsync(string userId, CancellationToken cancellationToken = default)
    {
        return await _userRepository.GetByIdAsync(userId, cancellationToken);
    }

    private static UserDto MapToUserDto(User user)
    {
        return new UserDto
        {
            Id = user.Id,
            Username = user.Username,
            Email = user.Email,
            FullName = user.FullName,
            Role = user.Role
        };
    }
}
