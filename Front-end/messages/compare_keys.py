import json
import os

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

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    
    missing = []
    for k in sorted(en_keys.keys()):
        if k not in lang_keys:
            val = en_keys[k]
            missing.append((k, val))
    
    if missing:
        print(f'=== {file} === ({len(missing)} missing keys)')
        for k, v in missing:
            if len(str(v)) > 80:
                v = str(v)[:77] + '...'
            print(f'  MISSING: {k} = "{v}"')
        print()

total_missing = 0
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    missing = [k for k in en_keys if k not in lang_keys]
    total_missing += len(missing)
print(f'TOTAL missing keys across all languages: {total_missing}')
print(f'Total en.json keys: {len(en_keys)}')
