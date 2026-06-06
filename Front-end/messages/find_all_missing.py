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
en_keys = set(en_flat.keys())

# Check each locale for missing keys in reports and auditLogs
target_ns = ['reports', 'auditLogs']

locales = ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']

print("=" * 80)
print("ALL MISSING KEYS IN reports AND auditLogs NAMESPACES")
print("=" * 80)

any_missing = False
for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_flat = flatten(data)
    loc_keys = set(loc_flat.keys())
    
    missing = sorted(en_keys - loc_keys)
    
    # Filter for reports and auditLogs only
    ns_missing = [k for k in missing if k.startswith('reports.') or k.startswith('auditLogs.')]
    
    if ns_missing:
        any_missing = True
        print(f"\n--- {code} ({len(ns_missing)} missing in reports/auditLogs) ---")
        for k in ns_missing:
            print(f"  MISSING: {k} = \"{en_flat[k][:80]}\"")

if not any_missing:
    print("\nNo missing keys in reports/auditLogs namespaces!")

print("\n" + "=" * 80)
print("ALL MISSING KEYS ACROSS ALL NAMESPACES (complete list)")
print("=" * 80)

any_all_missing = False
for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_flat = flatten(data)
    loc_keys = set(loc_flat.keys())
    
    missing = sorted(en_keys - loc_keys)
    
    if missing:
        any_all_missing = True
        print(f"\n--- {code} ({len(missing)} missing total) ---")
        for k in missing:
            ns = k.split('.')[0] if '.' in k else k
            print(f"  {k}")

if not any_all_missing:
    print("\n*** NO MISSING KEYS IN ANY LOCALE ***")
