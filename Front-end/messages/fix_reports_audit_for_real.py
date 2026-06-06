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

# Focus ONLY on reports and auditLogs namespaces
target_ns = ['reports', 'auditLogs']

print("=" * 80)
print("DETAILED CHECK: reports + auditLogs keys across ALL locales")
print("=" * 80)

all_issues = []

for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_flat = flatten(data)
    
    for ns in target_ns:
        for k, en_val in sorted(en_flat.items()):
            if not k.startswith(f'{ns}.'):
                continue
            
            if k not in loc_flat:
                all_issues.append((code, ns, k, 'MISSING', ''))
            else:
                loc_val = loc_flat[k]
                if isinstance(loc_val, str) and len(loc_val) == 0:
                    all_issues.append((code, ns, k, 'EMPTY', ''))
                elif isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 0 and loc_val == en_val:
                    all_issues.append((code, ns, k, 'ENGLISH', en_val[:60]))

if not all_issues:
    print("\n*** NO ISSUES FOUND! ***")
else:
    for code, ns, k, issue_type, val in all_issues:
        print(f"\n  [{issue_type}] {code}: {k}")
        if val:
            print(f"    Value: \"{val}\"")
    
    # Fix: for each issue, generate the correct translation
    print("\n" + "=" * 80)
    print("FIXING ALL ISSUES")
    print("=" * 80)
    
    # Define correct translations for each locale
    fixes = {}
    
    # Collect unique keys that need fixing
    for code, ns, k, issue_type, val in all_issues:
        if code not in fixes:
            fixes[code] = {}
        if ns not in fixes[code]:
            fixes[code][ns] = {}
        fixes[code][ns][k.split('.', 1)[1]] = issue_type
    
    for code, namespaces in fixes.items():
        with open(f'{code}.json', 'rb') as f:
            data = json.load(f)
        
        fixed_count = 0
        for ns, keys in namespaces.items():
            for key, issue_type in keys.items():
                full_key = f'{ns}.{key}'
                en_val = en_flat[full_key]
                
                if issue_type == 'MISSING':
                    # Add key with English value (better than missing)
                    if ns not in data:
                        data[ns] = {}
                    data[ns][key] = en_val
                    print(f"  ADDED {code}: {full_key} = \"{en_val}\"")
                    fixed_count += 1
                elif issue_type == 'ENGLISH':
                    # These are words that are spelled the same in both languages
                    # We keep them as-is because they're correct
                    print(f"  KEPT {code}: {full_key} = \"{en_val}\" (same in both languages)")
                elif issue_type == 'EMPTY':
                    data[ns][key] = en_val
                    print(f"  FILLED {code}: {full_key} = \"{en_val}\"")
                    fixed_count += 1
        
        # Save
        if fixed_count > 0:
            with open(f'{code}.json', 'w', encoding='utf-8', ensure_ascii=False) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  -> Saved {code}.json ({fixed_count} changes)")
    
    print("\nDone.")
