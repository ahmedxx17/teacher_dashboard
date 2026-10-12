#!/usr/bin/env python3
"""
scripts/apply_all_topic_updates.py

Updates and completes curriculum topics for:
1. Class 10 Biology (data/10_biology_en.json)
2. Class 10 Chemistry (data/10_chemistry_en.json)
3. Class 9 Biology (data/9_biology_en.json) - granular extraction of all 56 topics across 11 chapters
"""

import os
import sys
import json
import concurrent.futures
from PIL import Image

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import fitz
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==============================================================================
# 1. UPDATE 10 BIOLOGY
# ==============================================================================
def update_10_biology(cache):
    print("\n" + "=" * 70)
    print("APPLYING UPDATES TO CLASS 10 BIOLOGY...")
    print("=" * 70)

    json_path = os.path.join(PROJECT_ROOT, "data", "10_biology_en.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ch in data["chapters"]:
        c_num = ch["number"]

        if c_num == 3:
            ch["title"] = "Chapter 3: Human Blood Circulatory System"
        elif c_num == 4:
            ch["title"] = "Chapter 4: Human Urinary System"
        elif c_num == 5:
            ch["title"] = "Chapter 5: Coordination and Control"
        elif c_num == 7:
            ch["title"] = "Chapter 7: Inheritance"
        elif c_num == 9:
            ch["title"] = "Chapter 9: Diseases and Immunity"

        if c_num == 2:
            existing_topics = ch["topics"]
            t2_1 = existing_topics[0]
            t2_3 = existing_topics[1]
            t2_1["title"] = "2.1 Human Respiratory System"
            t2_1["start_page"] = 17
            t2_1["end_page"] = 20

            new_t2_2 = {
                "title": "2.2 The Mechanism of Breathing",
                "order_index": 2,
                "start_page": 20,
                "end_page": 21,
                "text": cache["bio10_2_2"].strip()
            }

            t2_3["title"] = "2.3 Respiratory Disorders"
            t2_3["order_index"] = 3
            t2_3["start_page"] = 21
            t2_3["end_page"] = 29

            ch["topics"] = [t2_1, new_t2_2, t2_3]

        if c_num == 8:
            for t in ch["topics"]:
                if "POTENTIALRISKS" in t["title"]:
                    t["title"] = "8.4 Potential Risks of Biotechnology"

        if c_num == 10:
            existing_topics = ch["topics"]
            new_t10_1 = {
                "title": "10.1 Darwin's Observations",
                "order_index": 1,
                "start_page": 110,
                "end_page": 112,
                "text": cache["bio10_10_1"].strip()
            }

            updated_topics = [new_t10_1]
            for t in existing_topics:
                if "10.2" in t["title"]:
                    t["title"] = "10.2 Theory of Evolution by Natural Selection"
                elif "10.3" in t["title"]:
                    t["title"] = "10.3 Species and Speciation"
                elif "10.4" in t["title"]:
                    t["title"] = "10.4 Sources of Variation"
                elif "10.5" in t["title"]:
                    t["title"] = "10.5 Evidences of Evolution"
                updated_topics.append(t)

            for idx, t in enumerate(updated_topics, 1):
                t["order_index"] = idx

            ch["topics"] = updated_topics

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully updated {json_path}")


# ==============================================================================
# 2. UPDATE 10 CHEMISTRY
# ==============================================================================
def update_10_chemistry(cache):
    print("\n" + "=" * 70)
    print("APPLYING UPDATES TO CLASS 10 CHEMISTRY...")
    print("=" * 70)

    json_path = os.path.join(PROJECT_ROOT, "data", "10_chemistry_en.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ch in data["chapters"]:
        c_num = ch["number"]

        if c_num == 9:
            existing = {t["title"]: t for t in ch["topics"]}
            t_9_2 = existing.get("9.2 LAW OF MASS ACTION")
            t_9_4 = existing.get("9.4 IMPORTANCE OF EQUILIBRIUM CONSTANT")

            t_9_1 = {
                "title": "9.1 Reversible Reactions and Dynamic Equilibrium",
                "order_index": 1,
                "start_page": 1,
                "end_page": 7,
                "text": cache["chem10_9_1"]
            }
            if t_9_2:
                t_9_2["title"] = "9.2 Law of Mass Action"
                t_9_2["order_index"] = 2
                t_9_2["start_page"] = 8
                t_9_2["end_page"] = 11

            t_9_3 = {
                "title": "9.3 Equilibrium Constant and Its Units",
                "order_index": 3,
                "start_page": 11,
                "end_page": 13,
                "text": cache["chem10_9_3"]
            }
            if t_9_4:
                t_9_4["title"] = "9.4 Importance of Equilibrium Constant"
                t_9_4["order_index"] = 4
                t_9_4["start_page"] = 14
                t_9_4["end_page"] = 23

            ch["topics"] = [t_9_1, t_9_2, t_9_3, t_9_4]

        elif c_num == 10:
            existing = {t["title"]: t for t in ch["topics"]}
            t_10_1 = existing.get("10.1 CONCEPTS OF ACIDS AND BASES")
            t_10_2 = existing.get("10.2 pH SCALE")

            if t_10_1:
                t_10_1["title"] = "10.1 Concepts of Acids and Bases"
                t_10_1["order_index"] = 1
                t_10_1["start_page"] = 20
                t_10_1["end_page"] = 33

            if t_10_2:
                t_10_2["title"] = "10.2 pH Scale"
                t_10_2["order_index"] = 2
                t_10_2["start_page"] = 34
                t_10_2["end_page"] = 36

            t_10_3 = {
                "title": "10.3 Indicators",
                "order_index": 3,
                "start_page": 37,
                "end_page": 39,
                "text": cache["chem10_10_3"]
            }
            t_10_4 = {
                "title": "10.4 Salts and Methods of Preparation",
                "order_index": 4,
                "start_page": 40,
                "end_page": 50,
                "text": cache["chem10_10_4"]
            }
            ch["topics"] = [t_10_1, t_10_2, t_10_3, t_10_4]

        elif c_num == 11:
            t_11_1 = {
                "title": "11.1 Classification and Characteristics of Organic Compounds",
                "order_index": 1,
                "start_page": 51,
                "end_page": 61,
                "text": cache["chem10_11_1"]
            }
            new_topics = [t_11_1]
            for t in ch["topics"]:
                if "11.2" in t["title"]:
                    t["title"] = "11.2 Sources of Organic Compounds"
                elif "11.3" in t["title"]:
                    t["title"] = "11.3 Uses of Organic Compounds"
                elif "11.4" in t["title"]:
                    t["title"] = "11.4 Alkanes and Alkyl Radicals"
                elif "11.5" in t["title"]:
                    t["title"] = "11.5 Functional Groups"
                elif "11.6" in t["title"]:
                    t["title"] = "11.6 Tests of Functional Groups"
                new_topics.append(t)

            for idx, t in enumerate(new_topics, 1):
                t["order_index"] = idx
            ch["topics"] = new_topics

        elif c_num == 12:
            existing = {t["title"]: t for t in ch["topics"]}
            t_12_3 = existing.get("12.3 ALKYNES")
            if t_12_3:
                t_12_3["title"] = "12.3 Alkynes"
                t_12_3["order_index"] = 3
                t_12_3["start_page"] = 93
                t_12_3["end_page"] = 100

            t_12_1 = {
                "title": "12.1 Alkanes and Preparation Methods",
                "order_index": 1,
                "start_page": 80,
                "end_page": 88,
                "text": cache["chem10_12_1"]
            }
            t_12_2 = {
                "title": "12.2 Alkenes and Preparation Methods",
                "order_index": 2,
                "start_page": 89,
                "end_page": 93,
                "text": cache["chem10_12_2"]
            }
            ch["topics"] = [t_12_1, t_12_2, t_12_3]

        elif c_num == 14:
            existing = {t["title"]: t for t in ch["topics"]}
            t_14_5 = existing.get("14.5 OZONE DEPLETION AND ITS EFFECTS")
            if t_14_5:
                t_14_5["title"] = "14.5 Ozone Depletion and Its Effects"
                t_14_5["order_index"] = 4
                t_14_5["start_page"] = 131
                t_14_5["end_page"] = 136

            t_14_1_2 = {
                "title": "14.1 Composition and Layers of Atmosphere",
                "order_index": 1,
                "start_page": 117,
                "end_page": 123,
                "text": cache["chem10_14_1_2"]
            }
            t_14_3_new = {
                "title": "14.3 Air Pollutants and Sources",
                "order_index": 2,
                "start_page": 124,
                "end_page": 127,
                "text": cache["chem10_14_3"]
            }
            t_14_4_new = {
                "title": "14.4 Acid Rain and Its Effects",
                "order_index": 3,
                "start_page": 128,
                "end_page": 130,
                "text": cache["chem10_14_4"]
            }
            ch["topics"] = [t_14_1_2, t_14_3_new, t_14_4_new, t_14_5]

        elif c_num == 15:
            new_topics = []
            for t in ch["topics"]:
                if "15.1" in t["title"]:
                    t["title"] = "15.1 Properties of Water"
                    new_topics.append(t)
                elif "15.2" in t["title"]:
                    t["title"] = "15.2 Water as a Solvent"
                    new_topics.append(t)
                    t_15_3_new = {
                        "title": "15.3 Soft and Hard Water & Methods of Removing Hardness",
                        "order_index": 3,
                        "start_page": 143,
                        "end_page": 146,
                        "text": cache["chem10_15_3"]
                    }
                    new_topics.append(t_15_3_new)
                elif "15.4" in t["title"]:
                    t["title"] = "15.4 Water Pollution"
                    new_topics.append(t)
                elif "15.5" in t["title"]:
                    t["title"] = "15.5 Waterborne Infectious Diseases"
                    new_topics.append(t)

            for idx, t in enumerate(new_topics, 1):
                t["order_index"] = idx
            ch["topics"] = new_topics

        elif c_num == 16:
            for t in ch["topics"]:
                if "16.1" in t["title"]:
                    t["title"] = "16.1 Basic Metallurgical Operations"
                elif "16.2" in t["title"]:
                    t["title"] = "16.2 Manufacture of Sodium Carbonate by Solvay's Process"
                elif "16.3" in t["title"]:
                    t["title"] = "16.3 Manufacture of Urea"
                elif "16.4" in t["title"]:
                    t["title"] = "16.4 Petroleum Industry"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully updated {json_path}")


# ==============================================================================
# 3. UPDATE 9 BIOLOGY (PARALLEL OCR FOR ALL 56 TOPICS)
# ==============================================================================
CURRICULUM_9_BIO = [
    {
        "number": 1,
        "title": "Chapter 1: The Science of Biology",
        "start_page": 5,
        "topics": [
            ("1.1 Biology and Its Branches", 5, 8),
            ("1.2 Relation of Biology with Other Sciences", 9, 10),
            ("1.3 Careers in Biology", 11, 12),
            ("1.4 Quranic Instructions to Reveal the Study of Life", 13, 13),
            ("1.5 Science as a Collaborative Field", 14, 14),
            ("1.6 Scientific Method", 15, 16),
            ("1.7 Theory and Law/Principle", 17, 17),
            ("1.8 Malaria - An Example of Biological Method", 18, 24)
        ]
    },
    {
        "number": 2,
        "title": "Chapter 2: Biodiversity",
        "start_page": 25,
        "topics": [
            ("2.1 Biodiversity", 25, 26),
            ("2.2 Classification", 27, 27),
            ("2.3 Taxonomic Ranks", 28, 28),
            ("2.4 History of Classification", 29, 30),
            ("2.5 Domains of Living Organisms", 31, 32),
            ("2.6 Classification of Domain Eukarya", 33, 34),
            ("2.7 Status of Virus in Classification", 35, 35),
            ("2.8 Binomial Nomenclature", 36, 40)
        ]
    },
    {
        "number": 3,
        "title": "Chapter 3: The Cell",
        "start_page": 41,
        "topics": [
            ("3.1 Cell as the Basic Unit of Life", 41, 41),
            ("3.2 Structure of Cell and Organelles", 42, 52),
            ("3.3 Plant and Animal Cells Comparison", 53, 56),
            ("3.4 Cell Specialization and Division of Labour", 57, 62)
        ]
    },
    {
        "number": 4,
        "title": "Chapter 4: Cell Cycle",
        "start_page": 63,
        "topics": [
            ("4.1 Cell Cycle", 63, 64),
            ("4.2 Mitosis and Its Phases", 65, 68),
            ("4.3 Meiosis and Its Phases", 69, 73),
            ("4.4 Comparison and Significance of Mitosis and Meiosis", 74, 79)
        ]
    },
    {
        "number": 5,
        "title": "Chapter 5: Tissues, Organs and Organ Systems",
        "start_page": 80,
        "topics": [
            ("5.1 Levels of Organization", 80, 82),
            ("5.2 Organs and Organ Systems in Plants", 83, 84),
            ("5.3 Organs and Organ Systems in Humans", 85, 87),
            ("5.4 Homeostasis", 88, 92)
        ]
    },
    {
        "number": 6,
        "title": "Chapter 6: Biomolecules",
        "start_page": 93,
        "topics": [
            ("6.1 Biomolecules and Biochemistry", 93, 94),
            ("6.2 Carbohydrates", 95, 97),
            ("6.3 Proteins and Amino Acids", 98, 99),
            ("6.4 Lipids", 99, 101),
            ("6.5 Nucleic Acids (DNA and RNA)", 101, 103),
            ("6.6 The Working of DNA and RNA", 104, 107)
        ]
    },
    {
        "number": 7,
        "title": "Chapter 7: Enzymes",
        "start_page": 108,
        "topics": [
            ("7.1 Metabolism and Introduction to Enzymes", 108, 109),
            ("7.2 Characteristics of Enzymes", 110, 111),
            ("7.3 Mechanism of Enzyme Action", 112, 112),
            ("7.4 Factors that Affect the Activity of Enzymes", 113, 114),
            ("7.5 Enzyme Inhibition", 115, 118)
        ]
    },
    {
        "number": 8,
        "title": "Chapter 8: Bioenergetics",
        "start_page": 119,
        "topics": [
            ("8.1 ATP: The Cell's Energy Currency", 119, 121),
            ("8.2 Photosynthesis and Pigments", 121, 124),
            ("8.3 Cellular Respiration and Mechanism", 124, 132)
        ]
    },
    {
        "number": 9,
        "title": "Chapter 9: Plant Physiology",
        "start_page": 133,
        "topics": [
            ("9.1 Nutrition in Plants", 133, 135),
            ("9.2 Transport in Plants", 136, 137),
            ("9.3 Transpiration and Stomatal Regulation", 138, 140),
            ("9.4 Transport of Water and Salts in Plants", 140, 141),
            ("9.5 Translocation in Plants", 141, 142),
            ("9.6 Gaseous Exchange in Plants", 143, 144),
            ("9.7 Mechanisms for Excretion in Plants", 144, 146),
            ("9.8 Osmotic Adjustments in Plants", 146, 150)
        ]
    },
    {
        "number": 10,
        "title": "Chapter 10: Reproduction in Plants",
        "start_page": 151,
        "topics": [
            ("10.1 Types of Asexual Reproduction", 151, 155),
            ("10.2 Artificial Propagation", 156, 157),
            ("10.3 Sexual Reproduction in Plants", 158, 165)
        ]
    },
    {
        "number": 11,
        "title": "Chapter 11: Biostatistics",
        "start_page": 166,
        "topics": [
            ("11.1 Introduction of Biostatistics and Its Uses", 166, 168),
            ("11.2 Mean, Median, and Mode", 169, 171),
            ("11.3 Bar Chart and Data Representation", 171, 180)
        ]
    }
]

def update_9_biology():
    print("\n" + "=" * 70)
    print("EXTRACTING CLASS 9 BIOLOGY GRANULAR TOPICS (8 WORKERS PARALLEL)...")
    print("=" * 70)

    pdf_path = os.path.join(PROJECT_ROOT, "books", "9_biology_en.pdf")
    json_path = os.path.join(PROJECT_ROOT, "data", "9_biology_en.json")
    doc = fitz.open(pdf_path)

    # Pre-render pages to avoid thread conflicts in fitz
    images = {}
    print(f"Rendering {len(doc)} PDF pages...")
    for p in range(len(doc)):
        pix = doc[p].get_pixmap(dpi=150)
        images[p + 1] = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def ocr_page_img(p_num):
        img = images[p_num]
        txt = pytesseract.image_to_string(img)
        return p_num, txt.strip()

    print("Running parallel OCR across all textbook pages...")
    page_texts = {}
    total_pages = len(doc)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_page = {executor.submit(ocr_page_img, p): p for p in range(1, total_pages + 1)}
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_page):
            p_num, txt = future.result()
            page_texts[p_num] = txt
            done_count += 1
            if done_count % 30 == 0 or done_count == total_pages:
                print(f"   OCR Completed: {done_count}/{total_pages} pages")

    def slice_pages(start_p: int, end_p: int) -> str:
        return "\n\n".join([page_texts[p] for p in range(start_p, end_p + 1) if p in page_texts and page_texts[p]]).strip()

    new_chapters = []
    total_new_topics = 0

    for ch_info in CURRICULUM_9_BIO:
        c_num = ch_info["number"]
        c_title = ch_info["title"]
        c_start = ch_info["start_page"]

        ch_topics = []
        for order_idx, (t_title, t_start, t_end) in enumerate(ch_info["topics"], 1):
            topic_text = slice_pages(t_start, t_end)
            ch_topics.append({
                "title": t_title,
                "order_index": order_idx,
                "start_page": t_start,
                "end_page": t_end,
                "text": topic_text
            })
            total_new_topics += 1

        new_chapters.append({
            "number": c_num,
            "title": c_title,
            "start_page": c_start,
            "topics": ch_topics
        })

    with open(json_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)

    existing_data["chapters"] = new_chapters

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    print(f"🎉 Successfully reconstructed Class 9 Biology: 11 chapters, {total_new_topics} granular topics!")


def main():
    cache_path = os.path.join(PROJECT_ROOT, "scripts", "extracted_cache.json")
    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)

    update_10_biology(cache)
    update_10_chemistry(cache)
    update_9_biology()

    print("\n" + "=" * 70)
    print("ALL TARGET BOOKS UPDATED TO COMPLETE, CANONICAL TOPICS!")
    print("=" * 70)


if __name__ == "__main__":
    main()
