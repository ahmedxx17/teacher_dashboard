#!/usr/bin/env python3
"""
scripts/fix_all_json.py
Fixes all structural, OCR, metadata, and schema errors across all curriculum JSON files in data/:
1. Assigns official PCTB chapter titles.
2. Removes spurious chapters and topics (e.g. table data misclassified as chapters or topics).
3. Fixes page ranges (start_page <= end_page).
4. Cleans multiline topic titles, preserving any introduction paragraph in the topic text.
5. Fixes OCR word-fusion artifacts.
6. Splits Grade 9 Biology into all 11 official chapters with correct numbers, titles, and text.
7. Ensures unique sequential order_index (1..N) within every chapter.
8. Writes formatted, validated JSON with ensure_ascii=False and indent=2.
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# --- Official Chapter Dictionaries ---

CH_TITLES_10_CHEMISTRY = {
    9: "Chapter 9: Chemical Equilibrium",
    10: "Chapter 10: Acids, Bases and Salts",
    11: "Chapter 11: Organic Chemistry",
    12: "Chapter 12: Hydrocarbons",
    13: "Chapter 13: Biochemistry",
    14: "Chapter 14: The Atmosphere",
    15: "Chapter 15: Water",
    16: "Chapter 16: Chemical Industries"
}

CH_TITLES_10_PHYSICS = {
    10: "Chapter 10: Simple Harmonic Motion and Waves",
    11: "Chapter 11: Sound",
    12: "Chapter 12: Geometrical Optics",
    13: "Chapter 13: Electrostatics",
    14: "Chapter 14: Current Electricity",
    15: "Chapter 15: Electromagnetism",
    16: "Chapter 16: Basic Electronics",
    17: "Chapter 17: Information and Communication Technology",
    18: "Chapter 18: Atomic and Nuclear Physics"
}

CH_TITLES_9_CHEMISTRY = {
    1: "Chapter 1: States of Matter & Phase Changes",
    2: "Chapter 2: Atomic Structure",
    3: "Chapter 3: Chemical Bonding",
    4: "Chapter 4: Stoichiometry",
    5: "Chapter 5: Energetics",
    6: "Chapter 6: Equilibria",
    7: "Chapter 7: Acid & Base Chemistry",
    8: "Chapter 8: Periodic Table & Periodicity",
    9: "Chapter 9: Group Properties & Elements",
    10: "Chapter 10: Environmental Chemistry",
    11: "Chapter 11: Hydrocarbons",
    12: "Chapter 12: Empirical Data Collection & Analysis",
    13: "Chapter 13: Laboratory & Practical Skills"
}

CH_TITLES_9_PHYSICS = {
    1: "Chapter 1: Physical Quantities and Measurements",
    2: "Chapter 2: Kinematics",
    3: "Chapter 3: Dynamics",
    4: "Chapter 4: Turning Effects of Force",
    5: "Chapter 5: Work, Energy and Power",
    6: "Chapter 6: Mechanical Properties of Matter",
    7: "Chapter 7: Thermal Properties of Matter",
    8: "Chapter 8: Magnetism",
    9: "Chapter 9: Nature of Science"
}

CH_TITLES_9_BIOLOGY = {
    1: "Chapter 1: The Science of Biology",
    2: "Chapter 2: Biodiversity",
    3: "Chapter 3: The Cell",
    4: "Chapter 4: Cell Cycle",
    5: "Chapter 5: Tissues, Organs and Organ Systems",
    6: "Chapter 6: Biomolecules",
    7: "Chapter 7: Enzymes",
    8: "Chapter 8: Bioenergetics",
    9: "Chapter 9: Plant Physiology",
    10: "Chapter 10: Reproduction in Plants",
    11: "Chapter 11: Biostatistics"
}


def clean_topic_title(raw_title: str) -> tuple[str, str]:
    """Returns (cleaned_title, extra_text)"""
    if not raw_title:
        return "", ""
    lines = [line.strip() for line in raw_title.split('\n') if line.strip()]
    if not lines:
        return "", ""
    title = lines[0]
    extra = "\n\n".join(lines[1:]) if len(lines) > 1 else ""

    # Common OCR fixes in titles
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'\bHUMANHEART\b', 'HUMAN HEART', title)
    title = re.sub(r'\bANDITS\b', 'AND ITS', title)
    title = re.sub(r'\bROLEOF\b', 'ROLE OF', title)
    title = re.sub(r'\bDNAANDRNA\b', 'DNA AND RNA', title)
    title = re.sub(r'\bASTEADY\b', 'A STEADY', title)
    title = re.sub(r'\bELECTRICCURRENT\b', 'ELECTRIC CURRENT', title)
    title = re.sub(r'\bsucedia and d Velocity\b', 'Speed and Velocity', title)
    title = re.sub(r'\bPrependicula\b', 'Perpendicular', title)
    title = re.sub(r'\bFree-\s*Body\b', 'Free-Body', title)
    title = re.sub(r'\bHyrocarbons\b', 'Hydrocarbons', title)
    title = re.sub(r'\s*~\s*$', '', title)
    title = re.sub(r'\s*\[=\s*$', '', title)
    title = re.sub(r'\s*\.\s*e\s*$', '', title)

    return title.strip(' ,.-_'), extra


def clean_topics_list(topics: list) -> list:
    cleaned = []
    for t in topics:
        raw_title = t.get("title", "")
        clean_t, extra = clean_topic_title(raw_title)
        if not clean_t:
            continue
        text = t.get("text", "") or ""
        if extra and not text.startswith(extra[:30]):
            text = extra + "\n\n" + text if text else extra

        # Ensure page continuity
        start_p = t.get("start_page")
        end_p = t.get("end_page")
        if start_p is not None and end_p is not None and end_p < start_p:
            end_p = start_p

        cleaned.append({
            "title": clean_t,
            "order_index": len(cleaned) + 1,
            "start_page": start_p,
            "end_page": end_p,
            "text": text.strip()
        })
    return cleaned


def fix_10_biology():
    fpath = "data/10_biology_en.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ch in data.get("chapters", []):
        ch["topics"] = clean_topics_list(ch.get("topics", []))

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Fixed: {fpath}")


def fix_10_chemistry():
    fpath = "data/10_chemistry_en.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ch in data.get("chapters", []):
        c_num = ch.get("number")
        if c_num in CH_TITLES_10_CHEMISTRY:
            ch["title"] = CH_TITLES_10_CHEMISTRY[c_num]
        ch["topics"] = clean_topics_list(ch.get("topics", []))

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Fixed: {fpath}")


def fix_10_physics():
    fpath = "data/10_physics_en.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter out spurious Chapter 1 (from table on page 43)
    valid_chapters = [c for c in data.get("chapters", []) if c.get("number") != 1]

    for ch in valid_chapters:
        c_num = ch.get("number")
        if c_num in CH_TITLES_10_PHYSICS:
            ch["title"] = CH_TITLES_10_PHYSICS[c_num]
        ch["topics"] = clean_topics_list(ch.get("topics", []))

    data["chapters"] = valid_chapters

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Fixed: {fpath}")


def fix_9_chemistry():
    fpath = "data/9_chemistry_en.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ch in data.get("chapters", []):
        c_num = ch.get("number")
        if c_num in CH_TITLES_9_CHEMISTRY:
            ch["title"] = CH_TITLES_9_CHEMISTRY[c_num]

        # Specific fix for Chapter 1
        if c_num == 1:
            topics = ch.get("topics", [])
            # Remove topic with "1.80 moles"
            topics = [t for t in topics if "1.80 moles" not in t.get("title", "")]
            # In topic 1.8, fix end_page to 23 and truncate leaked text where Chapter 2 begins
            for t in topics:
                if "1.8 Effect of Temperature" in t.get("title", ""):
                    t["end_page"] = 23
                    pos_ch2 = t["text"].lower().find("2.1 structure of atom")
                    if pos_ch2 != -1:
                        t["text"] = t["text"][:pos_ch2].strip()

            ch["topics"] = clean_topics_list(topics)
        else:
            ch["topics"] = clean_topics_list(ch.get("topics", []))

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Fixed: {fpath}")


def fix_9_physics():
    fpath = "data/9_physics_en.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ch in data.get("chapters", []):
        c_num = ch.get("number")
        if c_num in CH_TITLES_9_PHYSICS:
            ch["title"] = CH_TITLES_9_PHYSICS[c_num]

        # Specific fix for Chapter 1
        if c_num == 1:
            topics = ch.get("topics", [])
            # Remove spurious topic 1.0 kg mass
            topics = [t for t in topics if "1.0 kg mass" not in t.get("title", "")]
            for t in topics:
                if "1.13 Rounding off" in t.get("title", ""):
                    t["end_page"] = 29
                    # Truncate leaked text
                    for marker in ["in chapter 2", "addition of forces", "chapter 2", "kinematics"]:
                        pos = t["text"].lower().find(marker)
                        if pos != -1:
                            t["text"] = t["text"][:pos].strip()
                            break

            ch["topics"] = clean_topics_list(topics)
        else:
            ch["topics"] = clean_topics_list(ch.get("topics", []))

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Fixed: {fpath}")


def fix_9_biology():
    fpath = "data/9_biology_en.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # In 9_biology_en.json, chapters were concatenated:
    # Pos 0: Ch 1 (pp 5-25)
    # Pos 1: Ch 2 (pp 25-41)
    # Pos 2: Ch 3 (pp 41-63, was labeled 5)
    # Pos 3: Ch 4 & Ch 5 (pp 63-93)
    # Pos 4: Ch 6 & Ch 7 (pp 93-119)
    # Pos 5: Ch 8 (pp 119-133)
    # Pos 6: Ch 9 (pp 133-151)
    # Pos 7: Ch 10 & Ch 11 (pp 151-180)
    raw_chaps = data.get("chapters", [])

    text_pos0 = raw_chaps[0]["topics"][0]["text"]
    text_pos1 = raw_chaps[1]["topics"][0]["text"]
    text_pos2 = raw_chaps[2]["topics"][0]["text"]
    text_pos3 = raw_chaps[3]["topics"][0]["text"]
    text_pos4 = raw_chaps[4]["topics"][0]["text"]
    text_pos5 = raw_chaps[5]["topics"][0]["text"]
    text_pos6 = raw_chaps[6]["topics"][0]["text"]
    text_pos7 = raw_chaps[7]["topics"][0]["text"]

    # Split Pos 3 into Ch 4 (Cell Cycle) and Ch 5 (Tissues, Organs and Organ Systems)
    # Marker for Ch 5:
    ch5_marker_match = re.search(r'(?:NOT FOR SALE-PESRP\s*80\s*TISSUES,\s*ORGANS|TISSUES,\s*ORGANS,\s*AND\s*ORGAN\s*SYSTEMS)', text_pos3)
    if ch5_marker_match:
        split_idx_3 = ch5_marker_match.start()
        text_ch4 = text_pos3[:split_idx_3].strip()
        text_ch5 = text_pos3[split_idx_3:].strip()
    else:
        # Fallback split
        split_idx_3 = 22709
        text_ch4 = text_pos3[:split_idx_3].strip()
        text_ch5 = text_pos3[split_idx_3:].strip()

    # Split Pos 4 into Ch 6 (Biomolecules) and Ch 7 (Enzymes)
    # Marker for Ch 7:
    ch7_marker_match = re.search(r'(?:NOT FOR SALE-PESRP\s*108|Define metabolism,\s*catabolism and anabolism)', text_pos4)
    if ch7_marker_match:
        split_idx_4 = ch7_marker_match.start()
        text_ch6 = text_pos4[:split_idx_4].strip()
        text_ch7 = text_pos4[split_idx_4:].strip()
    else:
        split_idx_4 = 20153
        text_ch6 = text_pos4[:split_idx_4].strip()
        text_ch7 = text_pos4[split_idx_4:].strip()

    # Split Pos 7 into Ch 10 (Reproduction in Plants) and Ch 11 (Biostatistics)
    # Marker for Ch 11:
    ch11_marker_match = re.search(r'(?:166\s+ee\s+YS|11\s+BIOSTATISTICSSS|Define biostatistics and its uses)', text_pos7)
    if ch11_marker_match:
        split_idx_7 = ch11_marker_match.start()
        text_ch10 = text_pos7[:split_idx_7].strip()
        text_ch11 = text_pos7[split_idx_7:].strip()
    else:
        split_idx_7 = 20432
        text_ch10 = text_pos7[:split_idx_7].strip()
        text_ch11 = text_pos7[split_idx_7:].strip()

    new_chapters = [
        {
            "number": 1,
            "title": CH_TITLES_9_BIOLOGY[1],
            "start_page": 5,
            "topics": [{
                "title": "1.1 The Science of Biology",
                "order_index": 1,
                "start_page": 5,
                "end_page": 24,
                "text": text_pos0
            }]
        },
        {
            "number": 2,
            "title": CH_TITLES_9_BIOLOGY[2],
            "start_page": 25,
            "topics": [{
                "title": "2.1 Biodiversity",
                "order_index": 1,
                "start_page": 25,
                "end_page": 40,
                "text": text_pos1
            }]
        },
        {
            "number": 3,
            "title": CH_TITLES_9_BIOLOGY[3],
            "start_page": 41,
            "topics": [{
                "title": "3.1 The Cell",
                "order_index": 1,
                "start_page": 41,
                "end_page": 62,
                "text": text_pos2
            }]
        },
        {
            "number": 4,
            "title": CH_TITLES_9_BIOLOGY[4],
            "start_page": 63,
            "topics": [{
                "title": "4.1 Cell Cycle",
                "order_index": 1,
                "start_page": 63,
                "end_page": 79,
                "text": text_ch4
            }]
        },
        {
            "number": 5,
            "title": CH_TITLES_9_BIOLOGY[5],
            "start_page": 80,
            "topics": [{
                "title": "5.1 Tissues, Organs and Organ Systems",
                "order_index": 1,
                "start_page": 80,
                "end_page": 92,
                "text": text_ch5
            }]
        },
        {
            "number": 6,
            "title": CH_TITLES_9_BIOLOGY[6],
            "start_page": 93,
            "topics": [{
                "title": "6.1 Biomolecules",
                "order_index": 1,
                "start_page": 93,
                "end_page": 107,
                "text": text_ch6
            }]
        },
        {
            "number": 7,
            "title": CH_TITLES_9_BIOLOGY[7],
            "start_page": 108,
            "topics": [{
                "title": "7.1 Enzymes",
                "order_index": 1,
                "start_page": 108,
                "end_page": 118,
                "text": text_ch7
            }]
        },
        {
            "number": 8,
            "title": CH_TITLES_9_BIOLOGY[8],
            "start_page": 119,
            "topics": [{
                "title": "8.1 Bioenergetics",
                "order_index": 1,
                "start_page": 119,
                "end_page": 132,
                "text": text_pos5
            }]
        },
        {
            "number": 9,
            "title": CH_TITLES_9_BIOLOGY[9],
            "start_page": 133,
            "topics": [{
                "title": "9.1 Plant Physiology",
                "order_index": 1,
                "start_page": 133,
                "end_page": 150,
                "text": text_pos6
            }]
        },
        {
            "number": 10,
            "title": CH_TITLES_9_BIOLOGY[10],
            "start_page": 151,
            "topics": [{
                "title": "10.1 Reproduction in Plants",
                "order_index": 1,
                "start_page": 151,
                "end_page": 165,
                "text": text_ch10
            }]
        },
        {
            "number": 11,
            "title": CH_TITLES_9_BIOLOGY[11],
            "start_page": 166,
            "topics": [{
                "title": "11.1 Biostatistics",
                "order_index": 1,
                "start_page": 166,
                "end_page": 180,
                "text": text_ch11
            }]
        }
    ]

    data["chapters"] = new_chapters

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Fixed: {fpath}")


def fix_simple_physics_files():
    for fpath in ["data/9_physics_en_first20.json", "data/9_physics_en_test.json"]:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for ch in data.get("chapters", []):
            if ch.get("number") == 1:
                ch["title"] = "Chapter 1: Physical Quantities and Measurements"
            ch["topics"] = clean_topics_list(ch.get("topics", []))
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Fixed: {fpath}")


def main():
    print("=" * 70)
    print("STARTING COMPREHENSIVE CURRICULUM JSON FIXES")
    print("=" * 70)

    # 1. Backups
    backup_dir = "data/backups_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(backup_dir, exist_ok=True)
    for fname in os.listdir("data"):
        if fname.endswith(".json"):
            shutil.copy2(os.path.join("data", fname), os.path.join(backup_dir, fname))
    print(f"Backups created in: {backup_dir}")

    # 2. Fix each file
    fix_10_biology()
    fix_10_chemistry()
    fix_10_physics()
    fix_9_chemistry()
    fix_9_physics()
    fix_9_biology()
    fix_simple_physics_files()

    print("\nAll JSON files successfully cleaned and updated!")


if __name__ == "__main__":
    main()
