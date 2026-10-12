#!/usr/bin/env python3
"""
scripts/sync_all_to_supabase.py
Syncs all updated, cleaned curriculum JSON files into Supabase PostgreSQL.
- Idempotent upsert of subjects and chapters.
- Removes obsolete/spurious chapters from database.
- Completely refreshes topics for each chapter to eliminate corrupted/duplicate records.
"""

import os
import sys
import json
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
load_dotenv(override=False)

from supabase import create_client, Client

def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    return create_client(url, key)

BOOKS_TO_SYNC = [
    "data/9_physics_en.json",
    "data/9_chemistry_en.json",
    "data/9_biology_en.json",
    "data/10_physics_en.json",
    "data/10_chemistry_en.json",
    "data/10_biology_en.json"
]

def sync_book(client: Client, filepath: str):
    print("\n" + "="*70)
    print(f"SYNCING TO SUPABASE: {filepath}")
    print("="*70)
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    subject_name = data.get("subject")
    class_level = data.get("class")
    medium = data.get("medium", "en")
    book_version = data.get("book_version", "PCTB")
    chapters_data = data.get("chapters", [])
    
    print(f"Subject: {subject_name} | Class: {class_level} | Medium: {medium} | Chapters in file: {len(chapters_data)}")
    
    # 1. Upsert Subject
    sub_payload = {
        "name": subject_name,
        "class": class_level,
        "medium": medium,
        "book_version": book_version
    }
    client.table("subjects").upsert(sub_payload, on_conflict="name,class,medium").execute()
    
    sub_res = client.table("subjects").select("id").match({
        "name": subject_name,
        "class": class_level,
        "medium": medium
    }).execute()
    
    if not sub_res.data:
        print(f"❌ Failed to locate subject {subject_name} (Class {class_level})")
        return
        
    subject_id = sub_res.data[0]["id"]
    print(f"✅ Subject ID: {subject_id}")
    
    # 2. Clean up any obsolete chapters in DB that do not exist in the new JSON
    valid_chap_numbers = set(c["number"] for c in chapters_data)
    existing_db_chaps = client.table("chapters").select("id, number, title").eq("subject_id", subject_id).execute()
    
    for db_ch in existing_db_chaps.data:
        if db_ch["number"] not in valid_chap_numbers:
            print(f"🗑️ Deleting obsolete DB Chapter {db_ch['number']}: '{db_ch['title']}'...")
            client.table("chapters").delete().eq("id", db_ch["id"]).execute()
            
    # 3. Upsert Chapters and Refresh Topics
    total_topics = 0
    for ch in chapters_data:
        c_num = ch["number"]
        c_title = ch["title"]
        topics = ch.get("topics", [])
        
        chap_payload = {
            "subject_id": subject_id,
            "number": c_num,
            "title": c_title
        }
        
        client.table("chapters").upsert(chap_payload, on_conflict="subject_id,number").execute()
        
        ch_res = client.table("chapters").select("id").match({
            "subject_id": subject_id,
            "number": c_num
        }).execute()
        chapter_id = ch_res.data[0]["id"]
        
        # Clear existing topics for this chapter to ensure clean state
        client.table("topics").delete().eq("chapter_id", chapter_id).execute()
        
        # Insert topics in batches of 20
        batch = []
        for t in topics:
            top_payload = {
                "chapter_id": chapter_id,
                "title": t["title"],
                "order_index": t["order_index"],
                "start_page": t.get("start_page"),
                "end_page": t.get("end_page"),
                "text": t.get("text", "")
            }
            batch.append(top_payload)
            if len(batch) >= 20:
                client.table("topics").insert(batch).execute()
                batch = []
        if batch:
            client.table("topics").insert(batch).execute()
            
        total_topics += len(topics)
        print(f"   ✓ Ch {c_num}: '{c_title}' -> {len(topics)} topics synced")
        
    print(f"🎉 Successfully synced {subject_name} Class {class_level}: {len(chapters_data)} chapters, {total_topics} topics.")

def main():
    client = get_client()
    for book_file in BOOKS_TO_SYNC:
        if os.path.exists(book_file):
            sync_book(client, book_file)
        else:
            print(f"⚠️ File not found: {book_file}")
    print("\n" + "="*70)
    print("ALL CURRICULUM BOOKS SYNCED TO SUPABASE SUCCESSFULLY!")
    print("="*70)

if __name__ == "__main__":
    main()
