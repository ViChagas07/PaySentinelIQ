import json
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

# Detect English values in non-English files (potential semantic keys)
for file in files:
    lang = file.replace('.json', '')
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    
    english_semantic = []
    for k, en_val in sorted(en_keys.items()):
        if k in lang_keys:
            lang_val = lang_keys[k]
            # Check if value is still English text (only for longer text, not placeholders/patterns)
            if isinstance(lang_val, str) and len(lang_val) > 5 and lang_val == en_val:
                # This is exactly the same as English - might be intentionally same (like appName)
                # Skip keys that are meant to be the same across languages
                if k not in ['common.appName']:
                    english_semantic.append((k, lang_val[:100]))
    
    if english_semantic:
        print(f'=== {file} === ({len(english_semantic)} keys with English values)')
        for k, v in english_semantic:
            print(f'  ENGLISH: {k} = "{v}"')
        print()

total = 0
lang_names = {'pt-BR': 'Português (Brasil)', 'es': 'Español', 'fr': 'Français', 
              'de': 'Deutsch', 'ru': 'Русский', 'ja': '日本語', 'zh': '中文', 'ar': 'العربية'}

print("\n=== SUMMARY OF ALL ISSUES ===")
print(f"{'Language':<25} {'Missing Keys':<15} {'English Values':<15}")
print("-" * 55)

for file in files:
    lang = file.replace('.json', '')
    name = lang_names.get(lang, lang)
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    
    missing = [k for k in en_keys if k not in lang_keys]
    
    english_vals = []
    for k, en_val in sorted(en_keys.items()):
        if k in lang_keys:
            lang_val = lang_keys[k]
            if isinstance(lang_val, str) and len(lang_val) > 5 and lang_val == en_val and k != 'common.appName':
                english_vals.append(k)
    
    print(f"{name:<25} {str(len(missing)):<15} {str(len(english_vals)):<15}")
