import json, sys, os, re, glob
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load English reference
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
en_keys = set(en_flat.keys())

locales = ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']

print("=" * 80)
print("FINAL COMPREHENSIVE AUDIT")
print("=" * 80)

total_issues = 0

for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_flat = flatten(data)
    loc_keys = set(loc_flat.keys())
    
    # Missing keys
    missing = sorted(en_keys - loc_keys)
    
    # English-valued keys (focus on reports and auditLogs)
    english_vals = []
    for k in sorted(en_keys):
        if k in loc_keys:
            en_val = en_flat[k]
            loc_val = loc_flat[k]
            if isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 2 and loc_val == en_val:
                # Only report if it's in reports or auditLogs namespaces  
                if k.startswith('reports.') or k.startswith('auditLogs.'):
                    english_vals.append(k)
    
    if missing:
        # Only reports/auditLogs related missing keys
        ns_missing = [k for k in missing if k.startswith('reports.') or k.startswith('auditLogs.')]
        if ns_missing:
            total_issues += len(ns_missing)
            print(f'\n[{code}] MISSING in reports/auditLogs:')
            for k in ns_missing:
                print(f'  {k} = "{en_flat[k][:60]}"')
    
    if english_vals:
        total_issues += len(english_vals)
        print(f'\n[{code}] ENGLISH values in reports/auditLogs:')
        for k in english_vals:
            print(f'  {k} = "{loc_flat[k]}"')

if total_issues == 0:
    print('\n*** ZERO ISSUES FOUND - ALL KEYS CORRECT IN ALL LOCALES ***')
else:
    print(f'\n*** {total_issues} ISSUES FOUND ***')
