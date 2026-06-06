import json, sys
sys.stdout.reconfigure(encoding='utf-8')

locales = ['en', 'pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']

keys_of_interest = [
    'dashboard','payroll','verification','fraudIntelligence','aiInsights',
    'analyzePayroll','analyzeBankSlip','reports','auditLogs','notifications','settings',
    'goToDashboard','sidebarLabel','tagline','openMenu','toggleSidebar',
    'searchPlaceholder','globalSearch','aiAssistant','notificationsAria','userMenu',
    'unknownUser','profile','help','badgeAI','adminOnly','apiDocs','selectCompany',
    'switchCompany','collapse','expand','tenant','switchTenant','new',
    'compliance','documentAnalysis','employees','companies',
]

section_subkeys = ['core', 'intelligence', 'analysis', 'system', 'data']

data = {}
for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data[code] = json.load(f)

nav = data['en'].get('nav', {})

# Check nav keys
print("=" * 80)
print("NAV KEYS THAT ARE STILL IN ENGLISH IN NON-ENGLISH LOCALES")
print("=" * 80)

for key in keys_of_interest:
    en_val = data['en']['nav'].get(key, '')
    
    for code in locales[1:]:
        loc_val = data[code]['nav'].get(key, None)
        if loc_val is None:
            print(f"MISSING [{code}]: nav.{key}")
        elif isinstance(loc_val, str) and loc_val == en_val and len(loc_val) > 2:
            if key == 'badgeAI' and loc_val == 'AI':
                continue  # AI is universal
            print(f"ENGLISH [{code}]: nav.{key} = \"{loc_val}\"")

# Check sections
for sk in section_subkeys:
    en_val = data['en']['nav'].get('sections', {}).get(sk, '')
    for code in locales[1:]:
        loc_val = data[code]['nav'].get('sections', {}).get(sk, None)
        if loc_val is None:
            print(f"MISSING [{code}]: nav.sections.{sk}")
        elif isinstance(loc_val, str) and loc_val == en_val and len(loc_val) > 2:
            print(f"ENGLISH [{code}]: nav.sections.{sk} = \"{loc_val}\"")

print()
print("=" * 80)
print("CHECKING AUTH KEYS")
print("=" * 80)

auth_keys = ['guest', 'loginToAccount', 'signOutLabel']
for key in auth_keys:
    en_val = data['en']['auth'].get(key, '')
    for code in locales[1:]:
        loc_val = data[code]['auth'].get(key, None)
        if loc_val is None:
            print(f"MISSING [{code}]: auth.{key}")
        elif isinstance(loc_val, str) and loc_val == en_val and len(loc_val) > 2:
            print(f"ENGLISH [{code}]: auth.{key} = \"{loc_val}\"")

print()
print("=" * 80)
print("CHECKING COMMON KEYS")
print("=" * 80)

common_keys = ['language', 'tagline']
for key in common_keys:
    en_val = data['en']['common'].get(key, '')
    for code in locales[1:]:
        loc_val = data[code]['common'].get(key, None)
        if loc_val is None:
            print(f"MISSING [{code}]: common.{key}")
        elif isinstance(loc_val, str) and loc_val == en_val and len(loc_val) > 2:
            print(f"ENGLISH [{code}]: common.{key} = \"{loc_val}\"")

print()
print("Done.")
