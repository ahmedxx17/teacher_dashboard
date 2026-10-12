-- ============================================================================
-- Supabase Migration: 002_user_outlines.sql
-- Description: User Saved Outlines table with Row Level Security (RLS)
--              Strictly restricted to auth.uid() = user_id
-- NOTE: Do NOT run automatically. Execute manually in Supabase SQL Editor.
-- ============================================================================

-- Enable UUID extension if not already present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create or update the 'outlines' table for teacher-saved outlines
CREATE TABLE IF NOT EXISTS outlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    class INT NOT NULL CHECK (class IN (9, 10)),
    subject TEXT NOT NULL,
    chapter_title TEXT NOT NULL,
    topic_ids UUID[] NOT NULL DEFAULT '{}',
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure all required columns exist even if an earlier cache table was present
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS class INT CHECK (class IN (9, 10));
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS subject TEXT;
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS chapter_title TEXT;
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS topic_ids UUID[] DEFAULT '{}';
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;
ALTER TABLE outlines ADD COLUMN IF NOT EXISTS content JSONB;

-- 2. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_outlines_user_id ON outlines(user_id);
CREATE INDEX IF NOT EXISTS idx_outlines_created_at ON outlines(created_at DESC);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE outlines ENABLE ROW LEVEL SECURITY;

-- 4. Clean up any previous public or legacy policies
DROP POLICY IF EXISTS "Allow public read access on outlines" ON outlines;
DROP POLICY IF EXISTS "Users can read own outlines" ON outlines;
DROP POLICY IF EXISTS "Users can insert own outlines" ON outlines;
DROP POLICY IF EXISTS "Users can delete own outlines" ON outlines;

-- 5. Strict RLS Policies: Authenticated users (including Supabase Anonymous Users)
--    can ONLY read, insert, and delete rows where user_id equals their auth.uid().
--    No client-supplied ID bypass is permitted.

-- SELECT Policy
CREATE POLICY "Users can read own outlines"
    ON outlines FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- INSERT Policy
CREATE POLICY "Users can insert own outlines"
    ON outlines FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- DELETE Policy
CREATE POLICY "Users can delete own outlines"
    ON outlines FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);
