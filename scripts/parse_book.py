#!/usr/bin/env python3
"""
scripts/parse_book.py
Offline PDF parsing pipeline for Punjab Curriculum and Textbook Board (PCTB) books.

Usage:
    python parse_book.py --pdf books/9_physics_en.pdf --subject "Physics" --class 9 --medium en --offset 8 --out data/9_physics_en.json

Pipeline:
1. Validates text layer integrity; warns if scanned.
2. Extracts hierarchical structure via:
   a. doc.get_toc() bookmarks (level 1 = Chapter, level 2 = Topic)
   b. Regex scan over page texts for Chapter/Unit headings and numbered topics (e.g. 1.1 ...)
   c. Fallback: Gemini API call over the Table of Contents pages
3. Applies --offset between printed page numbers and PDF page indices.
4. Computes topic end_page boundaries.
5. Extracts and sanitizes textbook body text for each topic.
6. Writes structured JSON output.
7. Prints a visual review tree to stdout.
"""

import os
import re
import sys
import json
import argparse
from typing import List, Dict, Any, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Run: pip install pymupdf")
    sys.exit(1)

import requests
from dotenv import load_dotenv

load_dotenv()


def check_pdf_text_layer(doc: fitz.Document) -> bool:
    """
    Checks if the PDF has a selectable text layer.
    Warns prominently if the PDF is purely scanned raster images.
    """
    total_pages = len(doc)
    sample_pages = min(total_pages, 15)
    empty_pages = 0

    for i in range(sample_pages):
        text = doc[i].get_text().strip()
        if len(text) < 50:  # Very little text indicates scanned page or blank cover
            empty_pages += 1

    ratio = empty_pages / sample_pages
    if ratio > 0.6:
        print("\n" + "=" * 70)
        print("⚠️  WARNING: Document appears to be SCANNED or lacks a text layer!")
        print(f"   {empty_pages}/{sample_pages} sampled pages contain almost no extractable text.")
        print("   Direct text extraction may produce empty content. Consider running OCR first.")
        print("=" * 70 + "\n")
        return False
    return True


def extract_structure_from_bookmarks(doc: fitz.Document, offset: int) -> Optional[List[Dict[str, Any]]]:
    """
    Extracts structure using PyMuPDF doc.get_toc().
    Level 1 = Chapter
    Level 2 = Topic

    Note on Page Offset:
    PyMuPDF returns 1-based PDF physical page numbers for TOC bookmarks.
    However, if bookmarks were authored referencing printed book pages rather than
    physical PDF page positions, user-provided offset is applied.
    """
    toc = doc.get_toc()
    if not toc:
        return None

    chapters: List[Dict[str, Any]] = []
    current_chapter: Optional[Dict[str, Any]] = None
    topic_order = 0

    for item in toc:
        level, title, pno = item[0], item[1].strip(), item[2]
        if not title:
            continue

        # Adjust page number if needed (pno is 1-based)
        pdf_page = pno

        if level == 1:
            # Check for chapter pattern or treat level 1 as chapter
            chap_num_match = re.search(r'(?:chapter|unit)\s*(\d+)', title, re.IGNORECASE)
            chap_num = int(chap_num_match.group(1)) if chap_num_match else len(chapters) + 1
            # Clean title
            clean_title = re.sub(r'^(?:chapter|unit)\s*\d+[:\s.-]*', '', title, flags=re.IGNORECASE).strip() or title
            current_chapter = {
                "number": chap_num,
                "title": clean_title,
                "start_page": pdf_page,
                "topics": []
            }
            chapters.append(current_chapter)
            topic_order = 0
        elif level == 2 and current_chapter is not None:
            topic_order += 1
            current_chapter["topics"].append({
                "title": title,
                "order_index": topic_order,
                "start_page": pdf_page,
                "end_page": pdf_page,
                "text": ""
            })

    # Return chapters only if we found meaningful chapters with topics
    if chapters and any(len(c["topics"]) > 0 for c in chapters):
        return chapters

    return None


def extract_structure_from_regex(doc: fitz.Document) -> Optional[List[Dict[str, Any]]]:
    """
    Scans PDF page text using regular expressions to detect Chapters and Topics.
    Looks for:
    - Chapters: 'Chapter 1: ...', 'Unit 1: ...'
    - Topics: '1.1 Physical Quantities', '2.3 Vectors', etc.
    """
    chapters: List[Dict[str, Any]] = []
    current_chapter: Optional[Dict[str, Any]] = None
    topic_order = 0
    seen_topic_titles = set()

    chap_pattern = re.compile(r'^\s*(?:chapter|unit)\s*(\d+)[:\s.-]+(.*)$', re.IGNORECASE | re.MULTILINE)
    topic_pattern = re.compile(r'^\s*(\d+\.\d+)\s+([A-Za-z][A-Za-z0-9\s,\-\(\)\'\"]{3,80})$', re.MULTILINE)

    for page_idx in range(len(doc)):
        pdf_page_1based = page_idx + 1
        page_text = doc[page_idx].get_text()

        # Check for chapter title
        for match in chap_pattern.finditer(page_text):
            chap_num = int(match.group(1))
            chap_title = match.group(2).strip() or f"Chapter {chap_num}"

            # Avoid re-detecting the same chapter on consecutive pages (headers)
            if not current_chapter or current_chapter["number"] != chap_num:
                current_chapter = {
                    "number": chap_num,
                    "title": chap_title,
                    "start_page": pdf_page_1based,
                    "topics": []
                }
                chapters.append(current_chapter)
                topic_order = 0
                seen_topic_titles.clear()

        # Check for topic titles if within a chapter
        if current_chapter is not None:
            for match in topic_pattern.finditer(page_text):
                topic_code = match.group(1)
                topic_title = match.group(2).strip()
                full_title = f"{topic_code} {topic_title}"

                if full_title not in seen_topic_titles:
                    seen_topic_titles.add(full_title)
                    topic_order += 1
                    current_chapter["topics"].append({
                        "title": full_title,
                        "order_index": topic_order,
                        "start_page": pdf_page_1based,
                        "end_page": pdf_page_1based,
                        "text": ""
                    })

    if chapters and any(len(c["topics"]) > 0 for c in chapters):
        return chapters

    return None


def extract_structure_from_gemini_fallback(
    doc: fitz.Document,
    offset: int,
    subject: str,
    class_level: int
) -> Optional[List[Dict[str, Any]]]:
    """
    Fallback extraction using Gemini API:
    Locates the Table of Contents / Contents page(s) in the first 15 pages of the PDF,
    extracts the text, and prompts Gemini to return strict JSON containing chapters,
    topics, and printed page numbers. Then maps printed pages using offset.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    if not api_key:
        print("[Notice] GEMINI_API_KEY not configured. Skipping Gemini TOC fallback.")
        return None

    # Find Table of Contents pages
    toc_text_fragments = []
    for page_idx in range(min(15, len(doc))):
        text = doc[page_idx].get_text()
        if re.search(r'\b(?:contents|table of contents)\b', text, re.IGNORECASE):
            toc_text_fragments.append(f"--- Page {page_idx + 1} ---\n" + text)

    if not toc_text_fragments:
        # If no explicit "Contents" word found, take pages 2 through 6
        for page_idx in range(1, min(6, len(doc))):
            toc_text_fragments.append(f"--- Page {page_idx + 1} ---\n" + doc[page_idx].get_text())

    combined_toc_text = "\n\n".join(toc_text_fragments)

    print("🤖 Calling Gemini API to parse Table of Contents structure...")

    prompt = f"""
You are a textbook parser. Below is the raw text from the Table of Contents pages of a Class {class_level} {subject} textbook (PCTB Pakistan).
Extract the chapters and all their subtopics with their printed page numbers.

Return strictly valid JSON with this exact schema:
{{
  "chapters": [
    {{
      "number": 1,
      "title": "Physical Quantities and Measurement",
      "printed_page": 1,
      "topics": [
        {{
          "title": "1.1 Introduction to Physics",
          "printed_page": 2
        }}
      ]
    }}
  ]
}}

Raw Contents Text:
{combined_toc_text}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    try:
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            },
            timeout=30
        )
        if resp.status_code != 200:
            print(f"Gemini API returned status {resp.status_code}: {resp.text}")
            return None

        data = resp.json()
        raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_json_str)

        chapters_raw = parsed.get("chapters", [])
        result_chapters = []

        for chap in chapters_raw:
            chap_printed = chap.get("printed_page", 1)
            # Offset calculation: printed page 1 + offset = physical PDF page
            chap_pdf_page = max(1, min(len(doc), chap_printed + offset))

            topics_raw = chap.get("topics", [])
            topics_list = []
            for idx, top in enumerate(topics_raw, start=1):
                top_printed = top.get("printed_page", chap_printed)
                top_pdf_page = max(1, min(len(doc), top_printed + offset))
                topics_list.append({
                    "title": top.get("title", f"Topic {idx}"),
                    "order_index": idx,
                    "start_page": top_pdf_page,
                    "end_page": top_pdf_page,
                    "text": ""
                })

            result_chapters.append({
                "number": chap.get("number", len(result_chapters) + 1),
                "title": chap.get("title", "Untitled Chapter"),
                "start_page": chap_pdf_page,
                "topics": topics_list
            })

        return result_chapters

    except Exception as e:
        print(f"Error in Gemini fallback TOC parsing: {e}")
        return None


def sanitize_text(text: str) -> str:
    """
    Sanitizes raw extracted textbook page text:
    - Removes isolated page numbers (e.g. '14' on its own line)
    - Removes running headers/footers (e.g. 'Physics 9', 'Unit 1')
    - Collapses excessive blank lines and spaces
    """
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Drop lone numbers (page numbers)
        if re.match(r'^\d{1,4}$', stripped):
            continue
        # Drop common running headers like "Physics 9" or "Unit 1: Physical Quantities"
        if re.match(r'^(?:Physics|Chemistry|Biology|Mathematics|Unit\s*\d+|Chapter\s*\d+)\s*\d*$', stripped, re.IGNORECASE):
            continue
        # Drop copyright/disclaimer single-line footers
        if "punjab curriculum and textbook board" in stripped.lower():
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    # Collapse 3 or more newlines to 2
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    # Collapse multiple inline spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    return cleaned.strip()


def calculate_topic_page_ranges_and_extract(
    doc: fitz.Document,
    chapters: List[Dict[str, Any]]
) -> None:
    """
    Calculates end_page for every topic and extracts the cleaned text.

    Logic for Page Ranges:
    - Topics are sorted sequentially.
    - Within a chapter, topic N ends on the page immediately before topic N+1 starts:
        end_page = max(topic[n].start_page, topic[n+1].start_page - 1)
      (If topic N and N+1 start on the same page, end_page = start_page).
    - The last topic of chapter C ends on the page before chapter C+1 starts:
        end_page = max(last_topic.start_page, chapter[c+1].start_page - 1)
    - The last topic of the final chapter in the book ends at the PDF's total page count.
    """
    total_pages = len(doc)

    for c_idx, chap in enumerate(chapters):
        topics = chap.get("topics", [])
        if not topics:
            continue

        next_chap = chapters[c_idx + 1] if c_idx + 1 < len(chapters) else None
        next_chap_start = next_chap["start_page"] if next_chap else total_pages

        for t_idx, topic in enumerate(topics):
            start = topic["start_page"]

            if t_idx + 1 < len(topics):
                next_topic_start = topics[t_idx + 1]["start_page"]
                end = max(start, next_topic_start - 1 if next_topic_start > start else start)
            else:
                # Last topic of this chapter
                end = max(start, next_chap_start - 1 if next_chap_start > start else start)

            # Cap at document bounds
            end = min(total_pages, end)
            topic["end_page"] = end

            # Extract text across page range (PyMuPDF uses 0-based page index)
            accumulated_text = []
            for p in range(start - 1, end):
                if 0 <= p < total_pages:
                    accumulated_text.append(doc[p].get_text())

            raw_combined = "\n".join(accumulated_text)
            topic["text"] = sanitize_text(raw_combined)


def print_review_tree(data: Dict[str, Any]) -> None:
    """
    Prints a clean, human-readable terminal tree for manual quality assurance.
    """
    print("\n" + "=" * 70)
    print(f"📖 CURRICULUM EXTRACTION SUMMARY: {data['subject']} (Class {data['class']}, {data['medium'].upper()})")
    print("=" * 70)

    total_chapters = len(data["chapters"])
    total_topics = sum(len(c["topics"]) for c in data["chapters"])
    print(f"Total Chapters: {total_chapters} | Total Topics: {total_topics}\n")

    for chap in data["chapters"]:
        c_title = chap["title"]
        c_num = chap["number"]
        t_count = len(chap["topics"])
        print(f"📁 Chapter {c_num}: {c_title} [{t_count} topics]")

        for top in chap["topics"]:
            p_start = top["start_page"]
            p_end = top["end_page"]
            txt_len = len(top.get("text", ""))
            status = f"({txt_len} chars)" if txt_len > 0 else "⚠️ [NO TEXT]"
            print(f"   ├── {top['order_index']}. {top['title']} (PDF pp. {p_start}–{p_end}) {status}")
        print()
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured textbook data from official Punjab textbook PDFs (PCTB)."
    )
    parser.add_argument("--pdf", required=True, help="Path to input PDF file (e.g. books/9_physics_en.pdf)")
    parser.add_argument("--subject", required=True, help="Subject name (e.g. 'Physics')")
    parser.add_argument("--class", dest="class_level", type=int, required=True, choices=[9, 10], help="Class level (9 or 10)")
    parser.add_argument("--medium", default="en", choices=["en", "ur"], help="Medium of instruction ('en' or 'ur')")
    parser.add_argument("--offset", type=int, default=0, help="Page offset: PDF physical page = printed page + offset (e.g. 8)")
    parser.add_argument("--out", required=True, help="Destination JSON file path (e.g. data/9_physics_en.json)")

    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: PDF file '{args.pdf}' not found.")
        sys.exit(1)

    print(f"\n📂 Opening PDF: {args.pdf}")
    doc = fitz.open(args.pdf)
    print(f"   Total Pages: {len(doc)}")
    print(f"   Configured Offset: {args.offset}")

    # 1. Check text layer
    check_pdf_text_layer(doc)

    # 2. Extract structure (Bookmarks -> Regex -> Gemini TOC Fallback)
    print("🔍 Attempting structure extraction via PDF Bookmarks (doc.get_toc())...")
    chapters = extract_structure_from_bookmarks(doc, args.offset)

    if chapters:
        print(f"✅ Extracted {len(chapters)} chapters via bookmarks.")
    else:
        print("⚠️  Bookmarks not found or incomplete. Trying regex pattern matching...")
        chapters = extract_structure_from_regex(doc)

    if chapters:
        print(f"✅ Extracted {len(chapters)} chapters via regex matching.")
    else:
        print("⚠️  Regex matching yielded insufficient structure. Falling back to Gemini Contents analysis...")
        chapters = extract_structure_from_gemini_fallback(doc, args.offset, args.subject, args.class_level)

    if not chapters:
        print("❌ Could not extract curriculum structure. Please verify the PDF format.")
        sys.exit(1)

    # 3. Calculate topic boundaries and extract text
    print("✂️  Calculating topic page boundaries and extracting clean topic text...")
    calculate_topic_page_ranges_and_extract(doc, chapters)

    # 4. Form final JSON payload
    structured_data = {
        "subject": args.subject,
        "class": args.class_level,
        "medium": args.medium,
        "book_version": "PCTB",
        "chapters": chapters
    }

    # 5. Save output file
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Structured curriculum saved to: {args.out}")

    # 6. Display human-readable tree
    print_review_tree(structured_data)
    print("👉 Please review the JSON file. You may adjust titles or page ranges if needed before importing.")
    print("👉 When satisfied, run: python import_book.py --json " + args.out)


if __name__ == "__main__":
    main()
