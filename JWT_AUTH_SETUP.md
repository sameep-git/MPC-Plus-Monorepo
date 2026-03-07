# JWT Authentication Implementation for MPC Plus

This document describes the complete JWT-based authentication system implementation for MPC Plus.

## Overview

The system includes:
- ✅ User registration (sign-up)
- ✅ User login (sign-in) with JWT tokens
- ✅ User logout (sign-out)
- ✅ Protected routes (auto-redirect to sign-in if not authenticated)
- ✅ PostgreSQL database storage for users
- ✅ Default admin user credentials
- ✅ Password hashing with BCrypt
- ✅ JWT token generation and validation
- ✅ Frontend and backend integration

## Backend Setup

### Database Migration

Run the SQL migration to create the users table:

```bash
psql -U postgres -d your_db < backend/data/migrations/001_create_users_table.sql
```

This creates:
- `users` table with columns for username, email, password_hash, role, etc.
- Default admin user with credentials:
  - Username: `admin`
  - Password: `admin123`
  - Role: `Admin`

### JWT Configuration

Set the JWT secret in `appsettings.json` or as an environment variable:

```json
{
  "Jwt": {
    "Secret": "your-very-secure-secret-key-at-least-32-characters-long",
    "Issuer": "MPC-Plus",
    "Audience": "MPC-Plus-Users",
    "ExpirationMinutes": 60
  }
}
```

**Important**: Change the secret in production! Use a strong, random string at least 32 characters long.

### Backend Endpoints

#### POST /api/auth/login
Sign in with username and password

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "00000000-0000-0000-0000-000000000001",
    "username": "admin",
    "email": "admin@mpc-plus.local",
    "fullName": "Admin User",
    "role": "Admin"
  }
}
```

#### POST /api/auth/register
Create a new user account

**Request:**
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "fullName": "New User"
}
```

**Response:**
Same as login response

#### GET /api/auth/me
Get current user info (requires Authorization header)

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user-id",
  "username": "username",
  "email": "user@example.com",
  "fullName": "User Name",
  "role": "User"
}
```

## Frontend Setup

### Sign-In Page

Navigate to `/signin` to access the sign-in form:
- Username field
- Password field
- Default admin credentials hint
- Sign-up link
- Error handling

### Sign-Up Page

Navigate to `/signup` to create a new account:
- Username field (min 3 characters)
- Email field (optional)
- Full Name field (optional)
- Password field (min 6 characters)
- Password confirmation
- Form validation
- Success confirmation

### Authentication Flow

1. **Initial Load**: AuthProvider checks for stored token in localStorage
2. **Unauthenticated User**: Redirected to `/signin`
3. **Sign In**: Credentials sent to backend, token stored in localStorage
4. **Protected Routes**: Token included in all API requests via Authorization header
5. **Sign Out**: Token removed from localStorage, user redirected to `/signin`

### Using Authentication in Components

#### Getting Current User

```tsx
import { useAuth } from '@/lib/AuthProvider';

export function MyComponent() {
  const { user, loading, isAuthenticated } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Not authenticated</div>;
  
  return <div>Welcome, {user?.username}!</div>;
}
```

#### Making Authenticated API Calls

```tsx
import { getFetchOptions } from '@/lib/auth';

const response = await fetch('/api/some-endpoint', getFetchOptions());
```

Or use the existing `api.ts` functions which already include auth headers:

```tsx
import { fetchMachines, fetchUser } from '@/lib/api';

const machines = await fetchMachines();
const user = await fetchUser();
```

#### Logging Out

```tsx
import { signOut } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export function LogoutButton() {
  const router = useRouter();
  
  const handleLogout = () => {
    signOut();
    router.push('/signin');
  };
  
  return <button onClick={handleLogout}>Sign Out</button>;
}
```

## Token Management

### Token Storage

Tokens are stored in browser localStorage:
- Key: `authToken`
- Value: JWT token string

User info is also stored:
- Key: `user`
- Value: JSON string of user object

### Token Lifetime

Default: 60 minutes

Configurable via `Jwt:ExpirationMinutes` setting.

### Refreshing Tokens

Currently, tokens are not automatically refreshed. After expiration, users must sign in again.

To implement refresh tokens, modify `JwtTokenService` to generate both access and refresh tokens.

## Security Considerations

1. **JWT Secret**: Change the default secret in production
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiration**: Set appropriate expiration times (60 minutes recommended)
4. **Password Hashing**: Passwords are hashed with BCrypt (10 rounds)
5. **CORS**: Frontend URL should be in the CORS allowlist
6. **Auth Header**: All authenticated requests include `Authorization: Bearer <token>` header

## Database Schema

```sql
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255),
  full_name VARCHAR(255),
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'User',
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Files Created/Modified

### Backend
- `Models/User.cs` - User model and DTOs
- `Repositories/UserRepository.cs` - Data access for users
- `Services/JwtTokenService.cs` - JWT token generation/validation
- `Services/AuthService.cs` - Authentication business logic
- `Controllers/AuthController.cs` - Auth endpoints
- `Extensions/AuthenticationExtensions.cs` - Dependency injection setup
- `Program.cs` - Added auth services registration
- `appsettings.json` - JWT configuration

### Frontend
- `lib/auth.ts` - Authentication service (signIn, signUp, signOut, etc.)
- `lib/AuthProvider.tsx` - Auth context and useAuth hook
- `app/signin/page.tsx` - Sign-in page
- `app/signup/page.tsx` - Sign-up page
- `app/layout.tsx` - Added AuthProvider wrapper
- `components/ui/UserMenu.tsx` - Added logout functionality
- `lib/api.ts` - Updated to include auth token in requests

## Testing

### Test Admin Login
1. Navigate to http://localhost:3000/signin
2. Username: `admin`
3. Password: `admin123`
4. Click Sign In

### Test User Registration
1. Navigate to http://localhost:3000/signup
2. Fill in form
3. Click Create Account
4. Automatically redirected to dashboard

### Test Protected Routes
1. Sign out
2. Try to navigate to any protected route (e.g., http://localhost:3000/results)
3. Should be redirected to `/signin`

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:5132/api
```

### Backend (.env)
```
JWT_SECRET=your-secret-key-here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=mpc_plus
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Troubleshooting

### "JWT secret is not configured"
- Check `appsettings.json` has `Jwt:Secret` set
- Or set `JWT_SECRET` environment variable

### "Invalid token" errors
- Ensure token hasn't expired
- Check token is being sent in Authorization header
- Verify secret matches between server and token generation

### Users can't access protected routes after login
- Check token is being stored in localStorage
- Check AuthProvider is wrapping the app in layout.tsx
- Check browser developer tools for console errors

### Sign-up doesn't create user
- Check PostgreSQL is running
- Check database connection string is correct
- Check migration was run successfully
