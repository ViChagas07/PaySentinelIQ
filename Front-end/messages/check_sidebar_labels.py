import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check specifically the sidebar nav item labels + badge values
# in pt-BR which is the user's language

with open('en.json', 'rb') as f:
    en = json.load(f)
with open('pt-BR.json', 'rb') as f:
    pt = json.load(f)

nav_keys = [
    'dashboard', 'payroll', 'verification', 'fraudIntelligence', 'aiInsights',
    'analyzePayroll', 'analyzeBankSlip', 'reports', 'auditLogs', 'notifications', 'settings',
    'goToDashboard', 'sidebarLabel', 'tagline', 'openMenu', 'toggleSidebar',
    'searchPlaceholder', 'globalSearch', 'aiAssistant', 'notificationsAria',
    'userMenu', 'unknownUser', 'profile', 'help', 'badgeAI', 'adminOnly',
    'collapse', 'expand', 'tenant', 'switchTenant', 'new',
    'compliance', 'documentAnalysis', 'employees', 'companies', 'apiDocs',
]

sections = ['core', 'intelligence', 'analysis', 'system', 'data']

print("=== SIDEBAR NAV ITEM LABELS: en vs pt-BR ===")
print()
for key in nav_keys:
    en_val = en['nav'].get(key, '')
    pt_val = pt['nav'].get(key, '')
    status = 'OK' if en_val == pt_val else 'TRANSLATED'
    short_en = en_val[:50]
    short_pt = pt_val[:50]
    if en_val != pt_val:
        print(f"[{status}] nav.{key}")
        print(f"  en: '{en_val}'")
        print(f"  pt: '{pt_val}'")
        print()

print()
print("=== SECTIONS: en vs pt-BR ===")
for sk in sections:
    en_val = en['nav'].get('sections', {}).get(sk, '')
    pt_val = pt['nav'].get('sections', {}).get(sk, '')
    if en_val != pt_val:
        print(f"[TRANSLATED] nav.sections.{sk}: '{en_val}' -> '{pt_val}'")
    elif en_val:
        print(f"[SAME] nav.sections.{sk}: '{en_val}'")

print()
print("=== AUTH KEYS: en vs pt-BR ===")
for key in ['guest', 'loginToAccount', 'signOutLabel']:
    en_val = en['auth'].get(key, '')
    pt_val = pt['auth'].get(key, '')
    if en_val != pt_val:
        print(f"[TRANSLATED] auth.{key}: '{en_val}' -> '{pt_val}'")
    elif en_val:
        print(f"[SAME] auth.{key}: '{en_val}'")

print()
print("=== COMMON KEYS: en vs pt-BR ===")
for key in ['language', 'tagline', 'appName']:
    en_val = en['common'].get(key, '')
    pt_val = pt['common'].get(key, '')
    if en_val != pt_val:
        print(f"[TRANSLATED] common.{key}: '{en_val}' -> '{pt_val}'")
    elif en_val:
        print(f"[SAME] common.{key}: '{en_val}'")

# Also check ALL keys that are the same between en and pt-BR
print()
print("=== ALL PT-BR KEYS STILL IN ENGLISH (len>3) ===")
def get_all_keys(d, prefix=''):
    result = {}
    for k, v in d.items():
        path = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            result.update(get_all_keys(v, path))
        else:
            result[path] = v
    return result

en_all = get_all_keys(en)
pt_all = get_all_keys(pt)

count = 0
for k in sorted(en_all.keys()):
    if k not in pt_all:
        print(f"[MISSING] {k}")
        count += 1
    elif isinstance(en_all[k], str) and isinstance(pt_all[k], str) and len(en_all[k]) > 3 and en_all[k] == pt_all[k]:
        if k not in ['common.appName', 'common.and']:
            print(f"[ENGLISH] {k} = '{en_all[k]}'")
            count += 1

if count == 0:
    print("All keys are properly translated!")
