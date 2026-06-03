#!/usr/bin/env python3
"""Final verification of all translation fixes."""
import json, os

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
lang_names = {'pt-BR': 'Português (Brasil)', 'es': 'Español', 'fr': 'Français',
              'de': 'Deutsch', 'ru': 'Русский', 'ja': '日本語', 'zh': '中文', 'ar': 'العربية'}

print("=" * 80)
print("FINAL VERIFICATION REPORT - ALL TRANSLATIONS")
print("=" * 80)

total_missing = 0
total_english = 0

for file in files:
    lang = file.replace('.json', '')
    name = lang_names.get(lang, lang)
    
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys = get_keys(data)
    
    # Check missing keys
    missing = [k for k in en_keys if k not in lang_keys]
    
    # Check English-valued keys (excluding proper names like Google, brand names, etc.)
    skip_keys = {'common.appName', 'settings.language.availableLanguages.en', 
                 'settings.language.availableLanguages.pt-BR',
                 'settings.language.availableLanguages.ja',
                 'settings.language.availableLanguages.zh',
                 'settings.language.availableLanguages.ar',
                 'settings.language.availableLanguages.es',
                 'settings.language.availableLanguages.fr',
                 'settings.language.availableLanguages.ru',
                 'settings.language.availableLanguages.de'}
    
    english_vals = []
    for k, en_val in sorted(en_keys.items()):
        if k in lang_keys and k not in skip_keys:
            lang_val = lang_keys[k]
            if isinstance(lang_val, str) and len(lang_val) > 3 and lang_val == en_val:
                # Check if it's a proper name or should stay same
                if not any(proper in k for proper in ['Google', 'Drive', 'Photos', 'FEBRABAN', 'CrewAI', 'LangChain', 'PaySentinelIQ', 'SOC', 'PIX', 'OCR', 'FORGE']):
                    if not k.startswith('timezones.') and not k.startswith('settings.language.availableLanguages.'):
                        english_vals.append(k)
    
    status = "OK" if (not missing and not english_vals) else "ISSUES"
    print(f"\n{name:<25} | Missing: {len(missing):<3} | English vals: {len(english_vals):<3} | {status}")
    
    total_missing += len(missing)
    total_english += len(english_vals)
    
    if missing:
        print(f"  Missing keys: {missing}")
    if english_vals:
        print(f"  English-valued keys: {english_vals[:20]}", end="")
        if len(english_vals) > 20:
            print(f" ... and {len(english_vals)-20} more")
        else:
            print()

print("\n" + "=" * 80)
print(f"GRAND TOTAL: {total_missing} missing keys, {total_english} English-valued keys across all languages")
if total_missing == 0 and total_english == 0:
    print("ALL CLEAN! All translations are complete.")
else:
    print("Some issues remain.")
print("=" * 80)
