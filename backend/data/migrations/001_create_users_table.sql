-- Create users table for authentication
-- make sure we have bcrypt functions available
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'User',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Insert default admin user (password: admin123)
-- This can be changed through the API after first deployment
INSERT INTO users (id, username, email, full_name, password_hash, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin',
    'admin@mpc-plus.local',
    'Admin User',
    crypt('admin123', gen_salt('bf')),  -- compute bcrypt hash in the database so we don't hardcode it here
    'Admin',
    true
)
ON CONFLICT (username) DO NOTHING;
