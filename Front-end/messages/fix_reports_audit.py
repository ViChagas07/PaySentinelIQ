import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load English as reference
with open('en.json', 'rb') as f:
    en = json.load(f)

locales = ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']
all_ok = True

# ============================================================
# STEP 1: Check 'reports' namespace
# ============================================================
print("=" * 70)
print("REPORTS NAMESPACE AUDIT")
print("=" * 70)

en_reports = en.get('reports', {})
en_reports_keys = set(en_reports.keys())

for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_reports = data.get('reports', {})
    loc_reports_keys = set(loc_reports.keys())
    
    # Missing keys
    missing = en_reports_keys - loc_reports_keys
    if missing:
        all_ok = False
        print(f"\n[REPORTS] {code}: MISSING {len(missing)} keys:")
        for k in sorted(missing):
            print(f"  - {k} (en: \"{en_reports[k]}\")")
    
    # Keys still in English
    for k in sorted(en_reports_keys):
        if k in loc_reports:
            en_val = en_reports[k]
            loc_val = loc_reports[k]
            if isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 2 and loc_val == en_val:
                # Check if it's a proper noun or number that should stay the same
                if not loc_val.replace('.', '').replace(',', '').isdigit() and loc_val not in ['PDF', 'CSV', 'XLSX']:
                    all_ok = False
                    print(f"\n[REPORTS] {code}: ENGLISH VALUE nav.{k} = \"{loc_val}\"")

# ============================================================
# STEP 2: Check 'auditLogs' namespace
# ============================================================
print("\n" + "=" * 70)
print("AUDIT LOGS NAMESPACE AUDIT")
print("=" * 70)

en_audit = en.get('auditLogs', {})
en_audit_keys = set(en_audit.keys())

for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    loc_audit = data.get('auditLogs', {})
    loc_audit_keys = set(loc_audit.keys())
    
    # Missing keys
    missing = en_audit_keys - loc_audit_keys
    if missing:
        all_ok = False
        print(f"\n[AUDIT LOGS] {code}: MISSING {len(missing)} keys:")
        for k in sorted(missing):
            print(f"  - {k} (en: \"{en_audit[k]}\")")
    
    # Keys still in English
    for k in sorted(en_audit_keys):
        if k in loc_audit:
            en_val = en_audit[k]
            loc_val = loc_audit[k]
            if isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 2 and loc_val == en_val:
                all_ok = False
                print(f"\n[AUDIT LOGS] {code}: ENGLISH VALUE {k} = \"{loc_val}\"")

# ============================================================
# STEP 3: Also check ALL other namespaces for completeness
# ============================================================
print("\n" + "=" * 70)
print("ADDITIONAL ISSUES IN NAV/AUTH/COMMON RELATED TO REPORTS/AUDIT")
print("=" * 70)

# Check nav keys related to reports/audit
for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    # nav.reports and nav.auditLogs
    for nav_key in ['reports', 'auditLogs']:
        en_val = en.get('nav', {}).get(nav_key, '')
        loc_val = data.get('nav', {}).get(nav_key, '')
        if loc_val and en_val and isinstance(loc_val, str) and loc_val == en_val and len(loc_val) > 2:
            all_ok = False
            print(f"[NAV] {code}: nav.{nav_key} = \"{loc_val}\" (English)")

if all_ok:
    print("\n*** ALL CHECKS PASSED - No issues found ***")
else:
    print("\n*** ISSUES FOUND - See above ***")
