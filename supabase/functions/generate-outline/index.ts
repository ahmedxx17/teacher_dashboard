// Supabase Edge Function: generate-outline
// Runtime: Deno / TypeScript
// Invocation: POST { "topicId": "<UUID>", "regenerate": false }

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

interface GenerateRequestBody {
  topicId: string;
  regenerate?: boolean;
}

interface OutlineKeyConcept {
  term: string;
  explanation: string;
}

interface OutlineLessonStep {
  step: string;
  duration_minutes: number;
  details: string;
}

interface OutlineContent {
  title: string;
  learning_objectives: string[];
  key_concepts: OutlineKeyConcept[];
  lesson_flow: OutlineLessonStep[];
  activities: string[];
  check_questions: string[];
}

/**
 * Structured schema definition for Gemini's structured JSON output mode
 */
const outlineJsonSchema = {
  type: "OBJECT",
  properties: {
    title: { type: "STRING", description: "Clear topic title for the lesson" },
    learning_objectives: {
      type: "ARRAY",
      items: { type: "STRING" },
      description: "3 to 4 specific, measurable student learning outcomes (SLOs) aligned with BISE standards",
    },
    key_concepts: {
      type: "ARRAY",
      items: {
        type: "OBJECT",
        properties: {
          term: { type: "STRING", description: "Scientific term, formula, or core concept" },
          explanation: { type: "STRING", description: "Concise, textbook-accurate explanation" },
        },
        required: ["term", "explanation"],
      },
      description: "Key concepts and terminology derived directly from the textbook passage",
    },
    lesson_flow: {
      type: "ARRAY",
      items: {
        type: "OBJECT",
        properties: {
          step: { type: "STRING", description: "Name of the lesson segment (e.g. Introduction & Motivation, Concept Delivery, Guided Practice, Wrap-up)" },
          duration_minutes: { type: "INTEGER", description: "Duration in minutes (total must sum to 40-45 minutes)" },
          details: { type: "STRING", description: "Specific pedagogical instructions and teacher actions" },
        },
        required: ["step", "duration_minutes", "details"],
      },
      description: "A timed 40-45 minute classroom period breakdown",
    },
    activities: {
      type: "ARRAY",
      items: { type: "STRING" },
      description: "Low-resource classroom activities, board problems, or quick demonstrations possible in Pakistani schools",
    },
    check_questions: {
      type: "ARRAY",
      items: { type: "STRING" },
      description: "4 to 5 concept-check questions or past-paper style assessment questions to ask students at the end",
    },
  },
  required: [
    "title",
    "learning_objectives",
    "key_concepts",
    "lesson_flow",
    "activities",
    "check_questions",
  ],
};

/**
 * Validates whether the returned object conforms to the expected OutlineContent shape.
 */
function isValidOutline(obj: unknown): obj is OutlineContent {
  if (!obj || typeof obj !== "object") return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.title === "string" &&
    Array.isArray(o.learning_objectives) &&
    Array.isArray(o.key_concepts) &&
    Array.isArray(o.lesson_flow) &&
    Array.isArray(o.activities) &&
    Array.isArray(o.check_questions)
  );
}

/**
 * Sleep helper for exponential backoff retry
 */
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Call Gemini API with rate-limit handling and JSON validation retries
 */
async function callGeminiWithRetry(
  apiKey: string,
  modelName: string,
  systemInstruction: string,
  userPrompt: string,
  maxRetries = 3
): Promise<OutlineContent> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;

  let attempts = 0;
  let lastError: Error | null = null;

  while (attempts < maxRetries) {
    attempts++;
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system_instruction: {
            parts: [{ text: systemInstruction }],
          },
          contents: [
            {
              role: "user",
              parts: [{ text: userPrompt }],
            },
          ],
          generationConfig: {
            response_mime_type: "application/json",
            response_schema: outlineJsonSchema,
            temperature: 0.2, // Low temperature for high textbook adherence
          },
        }),
      });

      if (response.status === 429 || response.status === 503) {
        // Rate limited or temporary model overload: apply exponential backoff
        const delayMs = Math.pow(2, attempts) * 1000;
        console.warn(`[Gemini API] Received HTTP ${response.status}. Retrying attempt ${attempts}/${maxRetries} after ${delayMs}ms...`);
        await sleep(delayMs);
        continue;
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Gemini API error (HTTP ${response.status}): ${errorText}`);
      }

      const responseData = await response.json();
      const rawText = responseData.candidates?.[0]?.content?.parts?.[0]?.text;

      if (!rawText) {
        throw new Error("Gemini returned empty or invalid content structure");
      }

      let parsed: unknown;
      try {
        parsed = JSON.parse(rawText.trim());
      } catch (parseErr) {
        console.warn(`[JSON Parse Error] Raw text was not valid JSON. Attempt ${attempts}/${maxRetries}`);
        if (attempts < maxRetries) {
          await sleep(1000);
          continue;
        }
        throw new Error(`Failed to parse Gemini response as JSON: ${(parseErr as Error).message}`);
      }

      if (!isValidOutline(parsed)) {
        console.warn(`[Validation Error] Parsed JSON does not conform to Outline schema. Attempt ${attempts}/${maxRetries}`);
        if (attempts < maxRetries) {
          await sleep(1000);
          continue;
        }
        throw new Error("Generated outline did not match required schema");
      }

      return parsed;
    } catch (err) {
      lastError = err as Error;
      if (attempts >= maxRetries) {
        break;
      }
      const backoffMs = Math.pow(2, attempts) * 1000;
      await sleep(backoffMs);
    }
  }

  throw lastError ?? new Error("Failed to generate outline after multiple attempts");
}

serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    if (req.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed. Use POST." }), {
        status: 405,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { topicId, regenerate = false }: GenerateRequestBody = await req.json();

    if (!topicId) {
      return new Response(JSON.stringify({ error: "Missing required parameter: topicId" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Initialize Supabase admin client using environment secrets
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    if (!supabaseUrl || !serviceRoleKey) {
      return new Response(
        JSON.stringify({ error: "Supabase credentials missing on server environment." }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const supabase = createClient(supabaseUrl, serviceRoleKey);

    // ==========================================
    // 1. Caching Check
    // ==========================================
    if (!regenerate) {
      const { data: cachedRow, error: cacheErr } = await supabase
        .from("outlines")
        .select("id, content, model, created_at")
        .eq("topic_id", topicId)
        .maybeSingle();

      if (cacheErr) {
        console.error("Cache lookup error:", cacheErr);
      } else if (cachedRow) {
        return new Response(
          JSON.stringify({
            cached: true,
            model: cachedRow.model,
            createdAt: cachedRow.created_at,
            outline: cachedRow.content,
          }),
          { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
    }

    // ==========================================
    // 2. Fetch Topic Details & Context
    // ==========================================
    const { data: topicData, error: topicErr } = await supabase
      .from("topics")
      .select(`
        id,
        title,
        order_index,
        start_page,
        end_page,
        text,
        chapters:chapter_id (
          id,
          number,
          title,
          subjects:subject_id (
            id,
            name,
            class,
            medium,
            book_version
          )
        )
      `)
      .eq("id", topicId)
      .single();

    if (topicErr || !topicData) {
      return new Response(
        JSON.stringify({ error: `Topic not found: ${topicErr?.message ?? "Invalid ID"}` }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Extract nested relation objects
    const chapter = Array.isArray(topicData.chapters) ? topicData.chapters[0] : topicData.chapters;
    const subject = Array.isArray(chapter?.subjects) ? chapter?.subjects[0] : chapter?.subjects;

    const subjectName = subject?.name ?? "General Science";
    const classLevel = subject?.class ?? 9;
    const medium = subject?.medium === "ur" ? "Urdu Medium" : "English Medium";
    const bookVersion = subject?.book_version ?? "Punjab Curriculum and Textbook Board (PCTB)";
    const chapterNumber = chapter?.number ?? 1;
    const chapterTitle = chapter?.title ?? "General";
    const topicTitle = topicData.title;
    const topicText = topicData.text?.trim() || "";

    if (!topicText) {
      return new Response(
        JSON.stringify({
          error: "Selected topic does not contain extracted textbook content. Please re-run the parsing/import script.",
        }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // ==========================================
    // 3. AI Generation with Gemini
    // ==========================================
    const apiKey = Deno.env.get("GEMINI_API_KEY");
    // Model name dynamically read from environment variable - do not hardcode
    const modelName = Deno.env.get("GEMINI_MODEL") || "gemini-1.5-flash";

    if (!apiKey) {
      return new Response(
        JSON.stringify({ error: "GEMINI_API_KEY environment secret is not configured on Supabase." }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const systemInstruction = `You are an expert pedagogical curriculum specialist for secondary education in Pakistan (Punjab Curriculum and Textbook Board / BISE Matriculation standard for Class ${classLevel}).
Your task is to produce a practical, classroom-ready 40 to 45-minute lesson outline for high school teachers.

CRITICAL INSTRUCTIONS:
1. STRICT ADHERENCE: Base all definitions, concepts, and formulas STRICTLY on the supplied textbook content excerpt. Do NOT hallucinate information not present or implied by the textbook text.
2. CONTEXTUAL RELEVANCE: Keep classroom activities simple, low-cost, and viable for Pakistani classroom settings (blackboard/whiteboard, paper, everyday physical items).
3. PEDAGOGICAL STRUCTURE: The lesson flow must span a standard 40 to 45 minute class session.
4. LANGUAGE: Produce the content in clear, accessible English appropriate for Pakistani English-medium matriculation students.
5. FORMAT: You MUST return strictly valid JSON matching the specified JSON schema.`;

    const userPrompt = `SUBJECT: ${subjectName} (Class ${classLevel}, ${medium})
CURRICULUM: ${bookVersion}
CHAPTER: Unit/Chapter ${chapterNumber}: ${chapterTitle}
TOPIC: ${topicTitle} (Pages ${topicData.start_page ?? "?"} - ${topicData.end_page ?? "?"})

OFFICIAL TEXTBOOK CONTENT FOR THIS TOPIC:
---
${topicText}
---

Generate the complete structured lesson outline for this topic adhering to the JSON schema.`;

    const generatedOutline = await callGeminiWithRetry(apiKey, modelName, systemInstruction, userPrompt);

    // ==========================================
    // 4. Save to Database (Cache Outline)
    // ==========================================
    const { error: upsertErr } = await supabase
      .from("outlines")
      .upsert(
        {
          topic_id: topicId,
          content: generatedOutline,
          model: modelName,
          created_at: new Date().toISOString(),
        },
        { onConflict: "topic_id" }
      );

    if (upsertErr) {
      console.error("Failed to cache outline in database:", upsertErr);
      // Still return the generated outline to the teacher even if caching failed
    }

    return new Response(
      JSON.stringify({
        cached: false,
        model: modelName,
        createdAt: new Date().toISOString(),
        outline: generatedOutline,
      }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Unhandled error in generate-outline:", error);
    return new Response(
      JSON.stringify({
        error: (error as Error).message || "An unexpected error occurred during outline generation.",
      }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
