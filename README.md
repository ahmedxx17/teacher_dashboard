# Teacher Dashboard (Class 9 & 10 — Pakistan)

A dedicated, high-performance teaching assistant web application tailored for secondary school teachers in Pakistan following the official **Punjab Curriculum and Textbook Board (PCTB)** syllabus.

Teachers select **Subject → Chapter → Topic** from dependent dropdowns and generate structured, classroom-ready 40–45 minute lesson outlines. All outlines are cached in PostgreSQL so each topic calls the AI only once.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │    OFFLINE DATA PIPELINE (Python)    │
                      │  PCTB Textbooks (PDFs)               │
                      │  1. parse_book.py (fitz, regex, AI)  │
                      │  2. JSON Review                      │
                      │  3. import_book.py (supabase-py)     │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼ Upserts
 ┌─────────────────────────┐      ┌─────────────────────────┐
 │   React Vite Frontend   │◄────►│   Supabase PostgreSQL   │
 │   - Tailwind CSS        │      │   - subjects            │
 │   - Zustand Store       │      │   - chapters            │
 │   - Zero RAG / Direct DB│      │   - topics (text cache) │
 └───────────┬─────────────┘      │   - outlines (AI cache) │
             │                    └─────────────▲───────────┘
             │ Invoke Function                  │
             ▼                                  │ Caches outline
 ┌──────────────────────────────────────────────┴───────────┐
 │ Supabase Edge Function: generate-outline (Deno / TS)     │
 │ 1. Checks cache in 'outlines' table                      │
 │ 2. If missed: Fetches textbook excerpt                   │
 │ 3. Prompts Gemini API with structured JSON Schema        │
 │ 4. Retries 429 with exponential backoff                  │
 │ 5. Saves outline to DB & returns to client               │
 └───────────────────────────┬──────────────────────────────┘
                             │
                             ▼
                  Google Gemini 1.5 Flash
```

---

## Directory Structure

```
teaching-dashboard/
├── .env.example                       # Frontend environment template
├── index.html                         # HTML template with Inter typography
├── package.json                       # React, Vite, Zustand, Tailwind dependencies
├── postcss.config.js                  # PostCSS plugins
├── tailwind.config.js                 # Tailwind CSS theme and color tokens
├── vite.config.js                     # Vite build configuration
├── data/
│   └── 9_physics_en.json              # Sample Class 9 Physics structured JSON
├── scripts/
│   ├── .env.example                   # Python pipeline env template
│   ├── requirements.txt               # PyMuPDF, supabase-py, python-dotenv
│   ├── parse_book.py                  # Multi-strategy PDF extractor
│   └── import_book.py                 # Idempotent Supabase loader
├── src/
│   ├── App.jsx                        # Application root
│   ├── main.jsx                       # React DOM entry point
│   ├── index.css                      # Tailwind base & custom scrollbars
│   ├── components/
│   │   ├── SubjectSelect.jsx          # Subject & Class dropdown
│   │   ├── ChapterSelect.jsx          # Dependent Chapter dropdown
│   │   ├── TopicSelect.jsx            # Dependent Topic dropdown (with page badges)
│   │   ├── OutlineView.jsx            # Structured outline cards, timeline, copy
│   │   ├── LoadingSkeleton.jsx        # Smooth skeleton during generation
│   │   └── ErrorBanner.jsx            # Error alert with retry action
│   ├── lib/
│   │   └── supabaseClient.js          # Supabase browser client
│   ├── pages/
│   │   └── Dashboard.jsx              # Main teacher dashboard layout
│   └── store/
│       └── useCurriculumStore.js      # Zustand state management
└── supabase/
    ├── migrations/
    │   └── 001_init.sql               # PostgreSQL tables, indexes, RLS policies
    └── functions/
        └── generate-outline/
            └── index.ts               # Deno Edge Function calling Gemini API
```

---

## Step-by-Step Setup Guide

### 1. Supabase Project Setup & Database Migration

1. Go to [Supabase](https://supabase.com) and create a new project (e.g. `teacher-dashboard-pk`).
2. Navigate to **SQL Editor** in the Supabase dashboard.
3. Open [`supabase/migrations/001_init.sql`](file:///c:/Users/Administrator/Desktop/teaching%20dashboard/supabase/migrations/001_init.sql) and execute the SQL query. This creates:
   - Tables: `subjects`, `chapters`, `topics`, `outlines`
   - Foreign key indexes & unique constraints (prevents duplicate entries during re-runs)
   - Row Level Security (RLS) policies allowing public read access and restricting writes to the service role.

---

### 2. Configure Secrets & Deploy Edge Function

The Edge Function requires your Gemini API Key and Supabase service credentials.

1. Install the [Supabase CLI](https://supabase.com/docs/guides/cli) if not already installed:
   ```bash
   npm install -g supabase
   ```
2. Link your local project to your Supabase project:
   ```bash
   supabase login
   supabase link --project-ref your-project-ref
   ```
3. Set the required secrets in Supabase:
   ```bash
   supabase secrets set GEMINI_API_KEY="AIzaSyYourActualKey"
   supabase secrets set GEMINI_MODEL="gemini-1.5-flash"
   supabase secrets set SUPABASE_URL="https://your-project-ref.supabase.co"
   supabase secrets set SUPABASE_SERVICE_ROLE_KEY="eyJh...your-service-role-key"
   ```
4. Deploy the `generate-outline` function:
   ```bash
   supabase functions deploy generate-outline --no-verify-jwt
   ```
   *(The `--no-verify-jwt` flag allows your public frontend to invoke the function without requiring teacher login).*

---

### 3. Setup Python Pipeline & Ingest Initial Book

The Python scripts prepare and load textbook data into PostgreSQL.

1. Navigate to the `scripts/` directory and create a virtual environment:
   ```bash
   cd scripts
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `scripts/.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in:
   - `SUPABASE_URL`: Your Supabase Project URL (`https://xyz.supabase.co`)
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase Service Role Secret Key (from **Project Settings → API → service_role**)
   - `GEMINI_API_KEY`: *(Optional for parse fallback)* Your Gemini API Key

4. **Test with the included seed data**:
   To immediately populate the database with Class 9 Physics (Chapter 1) without waiting to download a PDF:
   ```bash
   python import_book.py --json ../data/9_physics_en.json
   ```

---

### 4. Setup and Run the React Frontend

1. In the root directory, configure the frontend environment variables:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your public keys:
   ```env
   VITE_SUPABASE_URL=https://your-project-ref.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-public-key
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## How to Add a New Book (Zero Code Changes)

Adding additional PCTB textbooks (e.g. Class 9 Chemistry, Class 10 Biology, Class 10 Mathematics) requires **zero code changes**:

1. **Download the official PCTB textbook PDF** and place it in a `books/` folder:
   - Example: `books/9_chemistry_en.pdf`
2. **Determine the page offset**:
   - Check the PDF: Find the physical page index of Chapter 1, Page 1.
   - If printed "Page 1" is on physical PDF page 10, the `--offset` is `9`.
3. **Run `parse_book.py`**:
   ```bash
   python scripts/parse_book.py \
     --pdf books/9_chemistry_en.pdf \
     --subject "Chemistry" \
     --class 9 \
     --medium en \
     --offset 9 \
     --out data/9_chemistry_en.json
   ```
   - The script validates the text layer.
   - Extracts chapter and topic hierarchy using bookmarks, regex, or Gemini fallback.
   - Calculates page boundaries and extracts the textbook text for each topic.
   - Prints a clean review tree in your terminal.
4. **Quick review**:
   - Inspect `data/9_chemistry_en.json` in your text editor and adjust any titles or page ranges if desired.
5. **Ingest to Supabase**:
   ```bash
   python scripts/import_book.py --json data/9_chemistry_en.json
   ```
   - Automatically upserts the subject, chapters, and topics idempotently.
   - Re-running the script updates existing records without creating duplicates.
6. **Refresh the Teacher Dashboard**:
   - "Chemistry — Class 9" immediately appears in the Subject dropdown with all chapters and topics ready to generate outlines!

---

## Edge Function Features

- **Database Caching**: If an outline exists in the `outlines` table for the selected topic, it returns in **< 150ms** without invoking the Gemini API.
- **Regenerate Support**: Teachers can click **"Regenerate"** (`{ "topicId": "...", "regenerate": true }`) to overwrite cached data.
- **Rate Limit Resilience**: Catches `HTTP 429` / `HTTP 503` responses from Gemini and automatically retries with exponential backoff (up to 3 attempts).
- **JSON Schema Enforcement**: Uses Gemini's `response_mime_type: "application/json"` and strict `response_schema` to guarantee compliant JSON output containing:
  - `learning_objectives`: Aligned with BISE student learning outcomes.
  - `key_concepts`: Direct textbook terms and definitions.
  - `lesson_flow`: Timed 40–45 minute classroom period breakdown.
  - `activities`: Low-resource blackboard demonstrations and student tasks.
  - `check_questions`: Formative assessment and past-paper style questions.
- **Strict Scope**: Prompts instruct the AI to anchor all definitions directly to the extracted textbook passage, avoiding hallucinated curriculum drift.

---

## Security Notes

- The frontend **only** uses the public `VITE_SUPABASE_ANON_KEY`.
- The `GEMINI_API_KEY` and `SUPABASE_SERVICE_ROLE_KEY` are stored strictly as private Supabase Edge Function secrets and environment variables for the offline ingestion script.
- Postgres Row Level Security (RLS) grants **SELECT** access to the public while disallowing public **INSERT/UPDATE/DELETE** operations.
