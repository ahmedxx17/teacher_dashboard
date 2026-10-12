#!/usr/bin/env python3
"""
scripts/clean_book_json.py
Cleans and standardizes chapters and topics in data/9_physics_en_full.json:
- Assigns official chapter titles from PCTB textbook.
- Separates actual teaching topics from end-of-chapter exercises (MCQs, conceptual questions).
- Groups exercises into a dedicated "Chapter Review & Exercises" topic at the end of each chapter.
- Fixes OCR artifacts in topic titles.
- Sequentially numbers topics (e.g. 1.1, 1.2, 1.3... or C.1, C.2, C.3...) and assigns order_index 1..N.
"""

import json
import re

OFFICIAL_CHAPTERS = {
    1: "Physical Quantities and Measurements",
    2: "Kinematics",
    3: "Dynamics",
    4: "Turning Effects of Force",
    5: "Work, Energy and Power",
    6: "Mechanical Properties of Matter",
    7: "Thermal Properties of Matter",
    8: "Magnetism",
    9: "Nature of Science"
}

# Page where the end-of-chapter exercise section begins in each chapter
EXERCISE_START_PAGES = {
    1: 24,
    2: 48,
    3: 76,
    4: 100,
    5: 123,
    6: 143,
    7: 158,
    8: 177,
    9: 193
}

def clean_topic_title(raw_title: str) -> str:
    # Take first line only
    title = raw_title.split('\n')[0].strip()
    title = re.sub(r'\s+', ' ', title)
    
    # Remove leading section numbers like "1.2 ", "3.10 "
    title = re.sub(r'^\d+\.\d+\.?\s*', '', title)
    
    # Specific known OCR fixes
    title = re.sub(r'\bEar Nouriinformaticn\b', '', title, flags=re.I)
    title = re.sub(r'\boT\b', '', title)
    title = re.sub(r'\bOh\b', '', title)
    title = re.sub(r'\b\s+4$', '', title)
    if "Determination of a Force from its" in title:
        title = "Determination of a Force from its Perpendicular Components"
    if "Conditions of Equilibrium A paratrooper" in title:
        title = "Conditions of Equilibrium"
    if "Free- Body" in title:
        title = title.replace("Free- Body", "Free-Body")
    if "Advantages and Disadvantages" in title:
        title = "Advantages and Disadvantages of Energy Production Methods"
        
    return title.strip(' ,.-_')

def process_book_json(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for ch in data['chapters']:
        c_num = ch['number']
        ch_name = OFFICIAL_CHAPTERS.get(c_num, f"Chapter {c_num}")
        ch['title'] = f"Chapter {c_num}: {ch_name}"
        
        ex_start = EXERCISE_START_PAGES.get(c_num, 999)
        
        content_topics = []
        exercise_texts = []
        ex_page_start = 999
        ex_page_end = 0
        
        for t in ch['topics']:
            start_p = t.get('start_page', 0)
            end_p = t.get('end_page', 0)
            
            if start_p >= ex_start:
                # This is an exercise question that was wrongly classified as a topic
                exercise_texts.append(t['text'])
                ex_page_start = min(ex_page_start, start_p)
                ex_page_end = max(ex_page_end, end_p)
            else:
                cleaned = clean_topic_title(t['title'])
                content_topics.append({
                    "title": cleaned,
                    "start_page": start_p,
                    "end_page": end_p,
                    "text": t['text']
                })
                
        # Append exercise topic if there were any exercise sections
        if exercise_texts:
            content_topics.append({
                "title": "Review Questions, MCQs & Exercises",
                "start_page": ex_page_start,
                "end_page": ex_page_end,
                "text": "\n\n".join(exercise_texts)
            })
            
        # Re-number and format titles with sequential topic numbers:
        # e.g., "1.1 Base and Derived Physical Quantities", "1.2 Uncertainty in a Measurement", ...
        formatted_topics = []
        for idx, t in enumerate(content_topics, start=1):
            if "Review Questions" in t['title']:
                full_title = f"{c_num}.Review {t['title']}"
            else:
                full_title = f"{c_num}.{idx} {t['title']}"
                
            formatted_topics.append({
                "title": full_title,
                "order_index": idx,
                "start_page": t['start_page'],
                "end_page": t['end_page'],
                "text": t['text']
            })
            
        ch['topics'] = formatted_topics

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Successfully cleaned and saved: {output_path}")

if __name__ == '__main__':
    process_book_json('data/9_physics_en_full.json', 'data/9_physics_en_full.json')
