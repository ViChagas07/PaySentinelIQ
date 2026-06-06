import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('en.json', 'rb') as f:
    en = json.load(f)

print("=== reports namespace (English) ===")
for k, v in sorted(en.get('reports', {}).items()):
    if isinstance(v, dict):
        for sk, sv in sorted(v.items()):
            print(f"  reports.{k}.{sk} = \"{sv}\"")
    else:
        print(f"  reports.{k} = \"{v}\"")

print("\n=== auditLogs namespace (English) ===")
for k, v in sorted(en.get('auditLogs', {}).items()):
    if isinstance(v, dict):
        for sk, sv in sorted(v.items()):
            print(f"  auditLogs.{k}.{sk} = \"{sv}\"")
    else:
        print(f"  auditLogs.{k} = \"{v}\"")

# Now show current values in each locale for the keys with issues
print("\n=== CURRENT VALUES FOR PROBLEMATIC KEYS ===")
problematics = {
    'reports': ['cause', 'occurrences', 'trend'],
    'auditLogs': ['status', 'document', 'live'],
}

for ns, keys in problematics.items():
    for k in keys:
        print(f"\n  [{ns}.{k}]")
        print(f"    en: \"{en[ns][k]}\"")
        for code in ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']:
            with open(f'{code}.json', 'rb') as f:
                data = json.load(f)
            val = data.get(ns, {}).get(k, '')
            print(f"    {code}: \"{val}\"")
