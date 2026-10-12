import json
import glob
import re

def audit_file(filepath):
    print(f"\n{'='*80}\nAUDIT: {filepath}\n{'='*80}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    errors = []
    warnings = []
    
    # Check top-level
    for key in ['subject', 'class', 'medium', 'chapters']:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")
            
    chapters = data.get('chapters', [])
    if not isinstance(chapters, list):
        errors.append("Chapters is not a list")
        return
        
    chap_numbers = []
    for c_idx, c in enumerate(chapters):
        c_num = c.get('number')
        c_title = c.get('title', '')
        topics = c.get('topics', [])
        
        if c_num is None:
            errors.append(f"Chapter at index {c_idx} missing 'number'")
        else:
            chap_numbers.append(c_num)
            
        if not c_title or not str(c_title).strip():
            errors.append(f"Chapter {c_num} has empty title")
        elif re.match(r'^Chapter\s+\d+$', str(c_title).strip()):
            warnings.append(f"Chapter {c_num} has generic title: '{c_title}'")
        elif '\n' in str(c_title):
            warnings.append(f"Chapter {c_num} title contains newline: {repr(c_title)}")
            
        if not isinstance(topics, list) or len(topics) == 0:
            warnings.append(f"Chapter {c_num} has no topics")
            
        topic_orders = []
        for t_idx, t in enumerate(topics):
            t_title = t.get('title', '')
            t_order = t.get('order_index')
            t_start = t.get('start_page')
            t_end = t.get('end_page')
            t_text = t.get('text', '')
            
            if t_order is None:
                errors.append(f"Ch {c_num} Topic {t_idx} missing order_index")
            else:
                topic_orders.append(t_order)
                
            if not t_title or not str(t_title).strip():
                errors.append(f"Ch {c_num} Topic {t_idx} empty title")
            elif '\n' in str(t_title):
                errors.append(f"Ch {c_num} Topic {t_idx} (order {t_order}) title contains newline: {repr(t_title[:50])}")
                
            if t_start is not None and t_end is not None:
                if t_end < t_start:
                    errors.append(f"Ch {c_num} Topic {t_idx} (order {t_order}) invalid pages: start {t_start} > end {t_end}")
                    
            if not t_text or len(str(t_text).strip()) == 0:
                errors.append(f"Ch {c_num} Topic {t_idx} (order {t_order}) empty text")
                
        # Check duplicate orders
        if len(topic_orders) != len(set(topic_orders)):
            errors.append(f"Ch {c_num} has duplicate topic order_indices: {topic_orders}")
            
    if len(chap_numbers) != len(set(chap_numbers)):
        errors.append(f"Duplicate chapter numbers: {chap_numbers}")
        
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  ❌ {e}")
    print(f"WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  ⚠️  {w}")

if __name__ == '__main__':
    for f in sorted(glob.glob('data/*.json')):
        audit_file(f)
