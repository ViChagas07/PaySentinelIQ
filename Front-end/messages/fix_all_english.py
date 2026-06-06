import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('en.json', 'rb') as f:
    en = json.load(f)

def flatten(d, prefix=''):
    result = {}
    for k, v in d.items():
        path = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            result.update(flatten(v, path))
        else:
            result[path] = v
    return result

en_flat = flatten(en)

locales = ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']
locale_names = {
    'pt-BR': 'Português (Brasil)',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'ru': 'Русский',
    'ja': '日本語',
    'zh': '中文',
    'ar': 'العربية',
}

print("=" * 100)
print("COMPLETE AUDIT: ALL ENGLISH-VALUED KEYS IN NON-ENGLISH LOCALES")
print("=" * 100)
print()

for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_flat = flatten(data)
    
    english_vals = []
    for k, en_val in sorted(en_flat.items()):
        if k in loc_flat:
            loc_val = loc_flat[k]
            if isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 2 and loc_val == en_val:
                # Skip proper nouns, numbers, and language names that are intentionally the same
                if loc_val in ['PaySentinelIQ', 'PaySentinel', 'IQ', 'PDF', 'CSV', 'XLSX', 'JSON', 'API', 'AI', 'IP']:
                    continue
                if loc_val.replace('.', '').replace(',', '').replace('(', '').replace(')', '').replace('-', '').strip().isdigit():
                    continue
                # Skip language names that are the same in all locales
                if k.startswith('settings.language.availableLanguages.'):
                    continue
                # Skip timezone names
                if k.startswith('timezones.'):
                    continue
                english_vals.append((k, en_val[:60]))
    
    if english_vals:
        print(f"\n--- {code} ({locale_names[code]}) - {len(english_vals)} English-valued keys ---")
        for k, v in english_vals:
            print(f"  {k} = \"{v}\"")
    else:
        print(f"\n{code}: ✓ All translated")
