#!/usr/bin/env python3
"""Fix remaining languages (ja, zh, ar) after fixing ru."""
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

def get_keys(obj, prefix=''):
    keys = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f'{prefix}.{k}' if prefix else k
            if isinstance(v, dict):
                keys.update(get_keys(v, key))
            else:
                keys[key] = v
    return keys

def set_nested(obj, key_path, value):
    parts = key_path.split('.')
    current = obj
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

def get_nested(obj, key_path):
    parts = key_path.split('.')
    current = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current

with open('en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)
en_keys = get_keys(en)

# Import translations from main script
exec(open('fix_all_translations.py', 'r', encoding='utf-8').read())

# Run remaining files
remaining = {
    "ja.json": (TR_JA_MISSING, TR_JA_ENGLISH),
    "zh.json": (TR_ZH_MISSING, TR_ZH_ENGLISH),
    "ar.json": (TR_AR_MISSING, TR_AR_ENGLISH),
}

with open('fix_report.txt', 'w', encoding='utf-8') as report:
    for filename, (missing_tr, english_tr) in remaining.items():
        print(f"\n--- {filename} ---")
        report.write(f"\n--- {filename} ---\n")
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        lang_keys = get_keys(data)
        
        added = 0
        fixed = 0
        
        # Add missing keys
        for key, translation in missing_tr.items():
            existing = get_nested(data, key)
            if existing is None:
                set_nested(data, key, translation)
                added += 1
                msg = f"  ADDED: {key}"
                print(msg)
                report.write(msg + "\n")
        
        # Fix English-valued keys
        for key, translation in english_tr.items():
            existing = get_nested(data, key)
            if existing is not None:
                en_val = en_keys.get(key)
                if existing == en_val:
                    set_nested(data, key, translation)
                    fixed += 1
                    msg = f"  FIXED: {key}"
                    print(msg)
                    report.write(msg + "\n")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        result = f"  => {added} added, {fixed} fixed"
        print(result)
        report.write(result + "\n")

print("\nDone! Report saved to fix_report.txt")
