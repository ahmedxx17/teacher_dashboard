-- Supabase Migration: 001_init.sql
-- Teacher Dashboard Database Schema

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Subjects Table
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    class INT NOT NULL CHECK (class IN (9, 10)),
    medium TEXT NOT NULL DEFAULT 'en' CHECK (medium IN ('en', 'ur')),
    book_version TEXT DEFAULT 'PCTB',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_subject UNIQUE (name, class, medium)
);

-- 2. Chapters Table
CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    number INT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_subject_chapter UNIQUE (subject_id, number)
);

-- 3. Topics Table
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    order_index INT NOT NULL,
    start_page INT,
    end_page INT,
    text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_chapter_topic_order UNIQUE (chapter_id, order_index)
);

-- 4. Outlines Table (Cached AI Outlines)
CREATE TABLE IF NOT EXISTS outlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_topic_outline UNIQUE (topic_id)
);

-- Foreign Key & Performance Indexes
CREATE INDEX IF NOT EXISTS idx_chapters_subject_id ON chapters(subject_id);
CREATE INDEX IF NOT EXISTS idx_topics_chapter_id ON topics(chapter_id);
CREATE INDEX IF NOT EXISTS idx_topics_order ON topics(chapter_id, order_index);
CREATE INDEX IF NOT EXISTS idx_outlines_topic_id ON outlines(topic_id);

-- Enable Row Level Security (RLS)
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE outlines ENABLE ROW LEVEL SECURITY;

-- Read Policies: Public read access for the web app (anon and authenticated users)
CREATE POLICY "Allow public read access on subjects"
    ON subjects FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Allow public read access on chapters"
    ON chapters FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Allow public read access on topics"
    ON topics FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Allow public read access on outlines"
    ON outlines FOR SELECT
    TO anon, authenticated
    USING (true);

-- Write Policies: Writes are strictly reserved for service_role (Edge Functions and Python import script).
-- Note: In Supabase, requests using the SERVICE_ROLE_KEY bypass RLS automatically.
-- By not granting INSERT/UPDATE/DELETE to anon/authenticated, clients cannot tamper with curriculum or outline data directly.
