-- Migration: Add user approval fields to users table
-- Run this script against your PostgreSQL database to add the new approval columns

-- Add approval status column with default 'APPROVED' for existing users
ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'APPROVED';

-- Add approval requested timestamp
ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_requested_at TIMESTAMP WITH TIME ZONE;

-- Add approved by user ID (references users.id)
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_by VARCHAR(36);

-- Add approved timestamp
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE;

-- Add denial reason
ALTER TABLE users ADD COLUMN IF NOT EXISTS denial_reason TEXT;

-- Update existing users to have APPROVED status (since they were created before this system)
UPDATE users SET approval_status = 'APPROVED' WHERE approval_status IS NULL;

-- Create an index on approval_status for faster queries
CREATE INDEX IF NOT EXISTS idx_users_approval_status ON users(approval_status);

-- Create an index on approval_requested_at for sorting pending users
CREATE INDEX IF NOT EXISTS idx_users_approval_requested_at ON users(approval_requested_at);