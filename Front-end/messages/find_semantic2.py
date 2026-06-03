import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8
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

with open('en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)
en_keys = get_keys(en)

files = ['pt-BR.json', 'es.json', 'fr.json', 'de.json', 'ru.json', 'ja.json', 'zh.json', 'ar.json']

print("=" * 80)
print("ANALYSIS OF KEYS WITH ENGLISH VALUES IN NON-ENGLISH FILES")
print("=" * 80)

for file in files:
    lang = file.replace('.json', '')
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    
    english_semantic = []
    for k, en_val in sorted(en_keys.items()):
        if k in lang_keys:
            lang_val = lang_keys[k]
            if isinstance(lang_val, str) and len(lang_val) > 3 and lang_val == en_val:
                if k not in ['common.appName', 'common.and']:
                    english_semantic.append(k)
    
    if english_semantic:
        print(f'\n--- {file} ({len(english_semantic)} English-valued keys) ---')
        for k in english_semantic:
            print(f'  {k}')

print()
print("=" * 80)
print("ANALYSIS OF MISSING KEYS")
print("=" * 80)

for file in files:
    lang = file.replace('.json', '')
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    
    missing = []
    for k in sorted(en_keys.keys()):
        if k not in lang_keys:
            missing.append(k)
    
    if missing:
        print(f'\n--- {file} ({len(missing)} missing keys) ---')
        for k in missing[:30]:
            print(f'  {k}')
        if len(missing) > 30:
            print(f'  ... and {len(missing) - 30} more')
