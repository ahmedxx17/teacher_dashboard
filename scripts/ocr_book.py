#!/usr/bin/env python3
"""
scripts/ocr_book.py
Uses Tesseract OCR to extract text from scanned PCTB textbook PDFs,
then produces the same structured JSON that import_book.py expects.

Usage:
    python ocr_book.py --pdf ../books/9_physics_en.pdf --subject "Physics" --class 9 --medium en --out ../data/9_physics_en.json

Pipeline:
    1. Render each PDF page to a high-res image (300 DPI) using PyMuPDF.
    2. Run Tesseract OCR on each image.
    3. Scan OCR'd text for Chapter and Topic headings using regex.
    4. Calculate topic page boundaries.
    5. Save full structured JSON.
    6. Print a review tree.

Prerequisites:
    - Tesseract OCR installed:
        Windows: winget install UB-Mannheim.TesseractOCR
        Or download from: https://github.com/UB-Mannheim/tesseract/wiki
    - Python packages:
        pip install pytesseract pillow pymupdf python-dotenv
"""

import os
import re
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import pymupdf as fitz  # PyMuPDF - renders pages to images
except ImportError:
    print("Error: PyMuPDF is not installed. Run: pip install pymupdf")
    sys.exit(1)

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Error: pytesseract and Pillow are not installed. Run: pip install pytesseract pillow")
    sys.exit(1)

# Common Tesseract install paths on Windows
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",  # confirmed install location
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\Administrator\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
]

# ---------------------------------------------------------------------------
# TOC detection thresholds
# A page is considered a TOC page if it has >= this many N.N pattern matches
# OR if >= this fraction of lines end with a trailing page number.
# ---------------------------------------------------------------------------
TOC_NN_THRESHOLD = 8          # ≥8 "N.N …" matches on one page → likely TOC
TOC_TRAILING_NUM_FRAC = 0.40  # ≥40 % of non-empty lines end in trailing digit


def find_and_configure_tesseract() -> bool:
    """
    Auto-detects Tesseract installation and configures pytesseract path.
    Returns True if found, False otherwise.
    """
    # Try if tesseract is already on PATH
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract detected on PATH: version {version}")
        return True
    except Exception:
        pass

    # Try known Windows install paths
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            try:
                version = pytesseract.get_tesseract_version()
                print(f"✅ Tesseract found at: {path} (version {version})")
                return True
            except Exception:
                continue

    return False


def render_page_to_image(page: fitz.Page, dpi: int = 300) -> Image.Image:
    """
    Renders a single PDF page to a PIL Image at the specified DPI.
    Higher DPI = better OCR accuracy but slower processing.
    300 DPI is the recommended minimum for quality OCR.
    """
    # PyMuPDF uses a zoom matrix: zoom = dpi / 72 (72 is default PDF DPI)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)

    # Convert pixmap bytes directly to PIL Image
    img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    return img


def ocr_page(image: Image.Image, lang: str = "eng", psm: int = 3) -> str:
    """
    Runs Tesseract OCR on a PIL Image and returns the extracted text.

    Args:
        image: PIL Image of the PDF page.
        lang:  Tesseract language code (default: eng).
        psm:   Tesseract Page Segmentation Mode (default: 3 = auto).
               Common values for textbooks:
                 3  – Fully automatic page segmentation (default)
                 6  – Assume a single uniform block of text
                 4  – Assume a single column of variable-size text
    """
    config = f"--psm {psm} --oem 3"
    text = pytesseract.image_to_string(image, lang=lang, config=config)
    return text


def sanitize_text(text: str) -> str:
    """
    Cleans extracted textbook page text:
    - Removes isolated page numbers on their own line
    - Removes common running headers
    - Collapses excessive whitespace
    """
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Drop lone small numbers (page numbers)
        if re.match(r'^\d{1,4}$', stripped):
            continue
        # Drop common running headers
        if re.match(
            r'^(?:Physics|Chemistry|Biology|Mathematics|Computer Science|Unit\s*\d+|Chapter\s*\d+)\s*\d*$',
            stripped, re.IGNORECASE
        ):
            continue
        # Drop copyright lines
        if "punjab curriculum and textbook board" in stripped.lower():
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# TOC detection
# ---------------------------------------------------------------------------

def _is_toc_page(page_text: str, nn_pattern: re.Pattern) -> bool:
    """
    Returns True if this page looks like a Table of Contents page.

    Two independent signals (either is sufficient):
      1. High heading density  – ≥ TOC_NN_THRESHOLD N.N matches on the page.
      2. Trailing page numbers – ≥ TOC_TRAILING_NUM_FRAC of non-empty lines
                                  end in one or more digits (e.g. "1.1 Intro 3").
    """
    # Signal 1: heading density
    matches = nn_pattern.findall(page_text)
    if len(matches) >= TOC_NN_THRESHOLD:
        return True

    # Signal 2: trailing page numbers
    non_empty = [l.strip() for l in page_text.splitlines() if l.strip()]
    if not non_empty:
        return False
    trailing = sum(1 for l in non_empty if re.search(r'\s\d{1,3}$', l))
    if trailing / len(non_empty) >= TOC_TRAILING_NUM_FRAC:
        return True

    return False


# ---------------------------------------------------------------------------
# Chapter / topic detection
# ---------------------------------------------------------------------------

def detect_chapters_and_topics(
    pages_text: List[Tuple[int, str]],
    debug: bool = False,
) -> List[Dict[str, Any]]:
    """
    Scans OCR'd text from each page to detect Chapter and Topic headings.

    Changes vs previous version:
      • TOC pages are detected by heading-density / trailing-number heuristics
        and skipped during heading collection (Fix #2).
      • Character offsets are stored per heading so shared-page topics can have
        their text sliced accurately later (Fix #3).
      • topic_order / seen_topics dead code removed; fallback now produces a
        single "Complete Chapter Content" topic per chapter (Fix #6).
    """
    chapters: List[Dict[str, Any]] = []

    chap_pattern = re.compile(
        r'^\s*(?:chapter|unit)\s*(\d+)\s*[:\-—]?\s*(.{0,80})$',
        re.IGNORECASE | re.MULTILINE
    )

    # More flexible topic pattern: matches "1.1 Title" or "1.1. Title"
    topic_pattern = re.compile(
        r'(?m)^\s*(\d+)\.(\d+)\.?\s+([A-Za-z][A-Za-z0-9\s,\-\(\)\'"/]{3,80})$'
    )

    # --- Pass 1: identify TOC pages ---
    toc_pages: set = set()
    for pdf_page_1based, page_text in pages_text:
        if _is_toc_page(page_text, topic_pattern):
            toc_pages.add(pdf_page_1based)

    if debug and toc_pages:
        print(f"\n[DEBUG] TOC pages detected (skipped for heading search): {sorted(toc_pages)}")

    # --- Pass 2: collect all section headings, skipping TOC pages ---
    # Each entry stores chap_num, sec_num, title, page, AND char offset within that page.
    all_sections: List[Dict] = []
    for pdf_page_1based, page_text in pages_text:
        if pdf_page_1based in toc_pages:
            continue
        for match in topic_pattern.finditer(page_text):
            chap_num = int(match.group(1))
            sec_num = int(match.group(2))
            title = match.group(3).strip()
            # Filter out false positives: titles shouldn't be purely numeric or very short
            if len(title) < 4 or title.isdigit():
                continue
            # Filter out common false positives from OCR noise
            if re.match(r'^(fig|table|example|ex\.|solved|note)\b', title, re.IGNORECASE):
                continue
            full_title = f"{chap_num}.{sec_num} {title}"
            all_sections.append({
                "chap_num": chap_num,
                "sec_num": sec_num,
                "title": full_title,
                "page": pdf_page_1based,
                "offset": match.start(),   # character offset within the page text (Fix #3)
            })

    if all_sections:
        # Group by chapter number
        chap_groups: Dict[int, List] = {}
        for sec in all_sections:
            cn = sec["chap_num"]
            if cn not in chap_groups:
                chap_groups[cn] = []
            chap_groups[cn].append(sec)

        # Deduplicate within each chapter (keep first occurrence per section code)
        for cn in sorted(chap_groups.keys()):
            sections = chap_groups[cn]
            seen_keys: set = set()
            unique_sections: List[Dict] = []
            for s in sections:
                key = f"{s['chap_num']}.{s['sec_num']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_sections.append(s)

            # Chapter's start page = first topic's page
            chap_start = unique_sections[0]["page"]

            # Try to find chapter title from explicit Chapter N heading near that page
            chap_title = f"Chapter {cn}"
            for pdf_page_1based, page_text in pages_text:
                if abs(pdf_page_1based - chap_start) <= 3:  # Within 3 pages of first topic
                    for m in chap_pattern.finditer(page_text):
                        if int(m.group(1)) == cn and m.group(2).strip():
                            chap_title = f"Chapter {cn}: {m.group(2).strip()}"
                            break

            topics_list = []
            for t_idx, sec in enumerate(unique_sections, start=1):
                topics_list.append({
                    "title": sec["title"],
                    "order_index": t_idx,
                    "start_page": sec["page"],
                    "end_page": sec["page"],   # placeholder; filled by assign_page_ranges_and_text
                    "start_offset": sec["offset"],  # used internally for text slicing
                    "text": ""
                })

            chapters.append({
                "number": cn,
                "title": chap_title,
                "start_page": chap_start,
                "topics": topics_list
            })

        print(f"  Found {len(chapters)} chapters via numbered section headings (N.N format).")
        return chapters

    # ---------------------------------------------------------------------------
    # Fallback: old-style 'Chapter N' only detection (no numbered topics)
    # Fix #6: removed topic_order/seen_topics dead code; produce one "Complete
    #          Chapter Content" topic per chapter so import_book.py still works.
    # ---------------------------------------------------------------------------
    print("  WARNING: Numbered-topic detection (N.N format) failed. Falling back to 'Chapter N' heading detection.")
    print("  Each chapter will contain a single 'Complete Chapter Content' topic. Review the output carefully.\n")

    current_chapter: Optional[Dict[str, Any]] = None
    for pdf_page_1based, page_text in pages_text:
        for match in chap_pattern.finditer(page_text):
            chap_num = int(match.group(1))
            chap_title_raw = match.group(2).strip()
            chap_title = chap_title_raw if chap_title_raw else f"Chapter {chap_num}"

            if not current_chapter or current_chapter["number"] != chap_num:
                current_chapter = {
                    "number": chap_num,
                    "title": chap_title,
                    "start_page": pdf_page_1based,
                    "topics": [
                        {
                            "title": "Complete Chapter Content",
                            "order_index": 1,
                            "start_page": pdf_page_1based,
                            "end_page": pdf_page_1based,
                            "start_offset": 0,
                            "text": ""
                        }
                    ]
                }
                chapters.append(current_chapter)

    return chapters


# ---------------------------------------------------------------------------
# Page-range assignment and text extraction
# ---------------------------------------------------------------------------

def assign_page_ranges_and_text(
    chapters: List[Dict[str, Any]],
    pages_text: List[Tuple[int, str]],
    total_pages: int,
    end_page_arg: Optional[int],
    debug: bool = False,
) -> None:
    """
    Calculates end_page for each topic and fills in the OCR'd text.

    Fix #1 (last-page boundary):
      • next_chap_start is set to total_pages + 1 (not total_pages) so that
        next_start - 1 = total_pages, i.e. the final topic reaches the real
        last page instead of stopping one page early.
      • The effective last page is further clamped to min(total_pages, end_page_arg)
        so that --end-page prevents back-matter pages from leaking in.

    Fix #3 (shared-page topics):
      • When two topics share the same start_page, page text is sliced at the
        character offset stored during heading detection, so no text is duplicated.
    """
    # Build a quick lookup: page number -> OCR text
    page_text_map: Dict[int, str] = {pno: text for pno, text in pages_text}

    # The absolute ceiling for any topic's end_page.
    # If the caller supplied --end-page, honour it to exclude back-matter.
    max_end_page = min(total_pages, end_page_arg) if end_page_arg else total_pages

    for c_idx, chap in enumerate(chapters):
        topics = chap.get("topics", [])
        if not topics:
            continue

        next_chap = chapters[c_idx + 1] if c_idx + 1 < len(chapters) else None
        # Fix #1: use total_pages + 1 so the last topic ends AT total_pages
        next_chap_start = next_chap["start_page"] if next_chap else total_pages + 1

        for t_idx, topic in enumerate(topics):
            start = topic["start_page"]
            start_offset = topic.get("start_offset", 0)

            if t_idx + 1 < len(topics):
                next_topic = topics[t_idx + 1]
                next_start = next_topic["start_page"]
                end = max(start, next_start - 1)
            else:
                end = max(start, next_chap_start - 1)

            # Clamp to the effective last page (honours --end-page, Fix #1 + #1C)
            end = min(max_end_page, end)
            topic["end_page"] = end

            # --- Fix #3: shared-page text slicing ---
            shared_page_debug: List[int] = []
            accumulated: List[str] = []

            for p in range(start, end + 1):
                raw = page_text_map.get(p, "")
                if not raw:
                    continue

                if p == start and start_offset > 0:
                    # Slice off text before this topic's heading on the first page
                    raw = raw[start_offset:]

                if t_idx + 1 < len(topics):
                    next_topic_on_same_page = topics[t_idx + 1]
                    if p == next_topic_on_same_page["start_page"]:
                        # Slice off text from the next topic's heading onwards
                        next_off = next_topic_on_same_page.get("start_offset", 0)
                        if next_off > start_offset:
                            raw = raw[:(next_off - start_offset)] if p == start else raw[:next_off]
                        shared_page_debug.append(p)

                accumulated.append(raw)

            if debug and shared_page_debug:
                print(
                    f"[DEBUG] Shared-page split — topic '{topic['title']}' "
                    f"and '{topics[t_idx + 1]['title']}' share page(s) {shared_page_debug}"
                )

            topic["text"] = sanitize_text("\n".join(accumulated))

    # Strip the internal-only start_offset key so the JSON schema stays identical
    for chap in chapters:
        for topic in chap.get("topics", []):
            topic.pop("start_offset", None)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_review_tree(data: Dict[str, Any]) -> None:
    """Prints a formatted tree to the terminal for manual review."""
    print("\n" + "=" * 70)
    print(f"EXTRACTION SUMMARY: {data['subject']} (Class {data['class']}, {data['medium'].upper()})")
    print("=" * 70)

    total_chapters = len(data["chapters"])
    total_topics = sum(len(c["topics"]) for c in data["chapters"])
    print(f"Total Chapters: {total_chapters} | Total Topics: {total_topics}\n")

    for chap in data["chapters"]:
        t_count = len(chap["topics"])
        print(f"Chapter {chap['number']}: {chap['title']} [{t_count} topics]")
        for top in chap["topics"]:
            txt_len = len(top.get("text", ""))
            status = f"({txt_len} chars)" if txt_len > 50 else "[WARNING: little text]"
            print(f"   +-- {top['order_index']}. {top['title']} (pp. {top['start_page']}-{top['end_page']}) {status}")
        print()

    print("=" * 70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="OCR a scanned PCTB textbook PDF using Tesseract and produce structured JSON."
    )
    parser.add_argument("--pdf", required=True, help="Path to scanned PDF file")
    parser.add_argument("--subject", required=True, help="Subject name (e.g. 'Physics')")
    parser.add_argument("--class", dest="class_level", type=int, required=True, choices=[9, 10])
    parser.add_argument("--medium", default="en", choices=["en", "ur"])
    parser.add_argument("--out", required=True, help="Output JSON file path")
    parser.add_argument("--dpi", type=int, default=300, help="Render DPI for OCR (default 300, higher=slower but better)")
    parser.add_argument("--lang", default="eng", help="Tesseract language code (default: eng)")
    parser.add_argument("--start-page", type=int, default=1, help="PDF page to start OCR from (1-based, skip covers)")
    parser.add_argument("--end-page", type=int, default=None, help="PDF page to end OCR at (optional, use to exclude back-matter)")
    # Fix #4: configurable PSM mode
    parser.add_argument(
        "--psm", type=int, default=3,
        help=(
            "Tesseract Page Segmentation Mode (default: 3 = auto). "
            "Common values: 3=auto, 4=single-column, 6=uniform-block. "
            "See: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html"
        )
    )
    # Debug flag
    parser.add_argument("--debug", action="store_true", help="Print debug info: TOC pages detected, shared-page topic splits")

    args = parser.parse_args()

    # Fix #5: Urdu not supported – exit early with a clear message
    if args.medium == "ur":
        print("ERROR: Urdu (--medium ur) is not supported yet.")
        print("       Only English textbooks (--medium en) are currently supported.")
        print("       Urdu OCR requires a Naskh-trained Tesseract model and RTL-aware")
        print("       heading detection, which have not been implemented.")
        sys.exit(1)

    # Validate PDF
    if not os.path.exists(args.pdf):
        print(f"Error: PDF file '{args.pdf}' not found.")
        sys.exit(1)

    # Configure Tesseract
    print("\nConfiguring Tesseract OCR...")
    if not find_and_configure_tesseract():
        print("\nTesseract not found! Please install it first:")
        print("  Windows: winget install UB-Mannheim.TesseractOCR")
        print("  Or download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  After installation, restart your terminal and try again.")
        sys.exit(1)

    # Open PDF
    print(f"\nOpening PDF: {args.pdf}")
    doc = fitz.open(args.pdf)
    total_pages = len(doc)
    print(f"Total pages in PDF: {total_pages}")

    # Determine page range to process
    start_idx = max(0, args.start_page - 1)
    end_idx = min(total_pages, args.end_page if args.end_page else total_pages)
    pages_to_process = end_idx - start_idx
    print(f"OCR range: pages {start_idx + 1} to {end_idx} ({pages_to_process} pages)")
    print(f"Render DPI: {args.dpi} | Language: {args.lang} | PSM: {args.psm}")
    print(f"\nStarting OCR... This may take {pages_to_process * 3 // 60 + 1}-{pages_to_process * 6 // 60 + 1} minutes.\n")

    # OCR each page
    pages_text: List[Tuple[int, str]] = []
    start_time = time.time()

    for i, page_idx in enumerate(range(start_idx, end_idx)):
        pdf_page_1based = page_idx + 1
        page = doc[page_idx]

        # Progress indicator
        elapsed = time.time() - start_time
        if i > 0:
            rate = i / elapsed
            remaining = (pages_to_process - i) / rate
            print(
                f"\r  [{i+1:>3}/{pages_to_process}] Page {pdf_page_1based:>3}  "
                f"| Elapsed: {int(elapsed//60)}m{int(elapsed%60):02d}s  "
                f"| ETA: {int(remaining//60)}m{int(remaining%60):02d}s",
                end="", flush=True
            )
        else:
            print(f"\r  [  1/{pages_to_process}] Page {pdf_page_1based:>3}  | Starting...", end="", flush=True)

        try:
            img = render_page_to_image(page, dpi=args.dpi)
            text = ocr_page(img, lang=args.lang, psm=args.psm)  # Fix #4: pass --psm
            pages_text.append((pdf_page_1based, text))
        except Exception as e:
            print(f"\n  Warning: Failed to OCR page {pdf_page_1based}: {e}")
            pages_text.append((pdf_page_1based, ""))

    total_elapsed = time.time() - start_time
    print(f"\n\nOCR complete in {int(total_elapsed // 60)}m {int(total_elapsed % 60)}s")

    # Detect structure from OCR text
    print("\nDetecting chapters and topics from OCR text...")
    chapters = detect_chapters_and_topics(pages_text, debug=args.debug)

    if not chapters:
        print("\nWarning: No chapters detected! The OCR text may not contain recognizable chapter/topic headings.")
        print("Tips:")
        print("  - Try increasing --dpi (e.g. --dpi 400)")
        print("  - Check that your PDF pages contain chapter headings like 'Chapter 1: ...' or numbered topics like '1.1 ...'")
        print("  - View the raw OCR output in the saved JSON to manually add structure")
        # Save raw OCR text as a flat dump so user can review
        raw_dump = {
            "subject": args.subject,
            "class": args.class_level,
            "medium": args.medium,
            "book_version": "PCTB",
            "raw_ocr_pages": [{"page": pno, "text": txt[:500]} for pno, txt in pages_text[:10]],
            "chapters": []
        }
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        debug_path = args.out.replace(".json", "_raw_ocr_debug.json")
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(raw_dump, f, indent=2, ensure_ascii=False)
        print(f"\nRaw OCR sample saved to: {debug_path}")
        print("Please review the first 10 pages to check OCR quality and heading format.")
        sys.exit(1)

    print(f"Detected: {len(chapters)} chapters")

    # Assign page ranges and fill text
    print("Calculating topic boundaries and extracting OCR text per topic...")
    assign_page_ranges_and_text(
        chapters,
        pages_text,
        total_pages,
        end_page_arg=args.end_page,  # Fix #1: pass --end-page for back-matter clamping
        debug=args.debug,
    )

    # Build output  (schema unchanged – import_book.py compatible)
    structured_data = {
        "subject": args.subject,
        "class": args.class_level,
        "medium": args.medium,
        "book_version": "PCTB",
        "chapters": chapters
    }

    # Save JSON
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"\nStructured JSON saved to: {args.out}")

    # Print review tree
    print_review_tree(structured_data)
    print("Review the JSON file, adjust any OCR errors, then run:")
    print(f"  python import_book.py --json {args.out}")


if __name__ == "__main__":
    main()
