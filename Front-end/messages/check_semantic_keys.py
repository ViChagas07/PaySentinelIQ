import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
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

# Keys specifically used in Navbar and Sidebar components
focus_keys = [
    # nav namespace
    'nav.openMenu', 'nav.toggleSidebar', 'nav.searchPlaceholder', 'nav.globalSearch',
    'nav.aiAssistant', 'nav.notificationsAria', 'nav.userMenu', 'nav.unknownUser',
    'nav.profile', 'nav.settings', 'nav.sidebarLabel', 'nav.goToDashboard',
    'nav.tagline', 'nav.dashboard', 'nav.payroll', 'nav.verification',
    'nav.fraudIntelligence', 'nav.aiInsights', 'nav.analyzePayroll', 'nav.analyzeBankSlip',
    'nav.reports', 'nav.auditLogs', 'nav.notifications',
    'nav.sections.core', 'nav.sections.intelligence', 'nav.sections.analysis', 'nav.sections.system',
    'nav.collapse', 'nav.expand', 'nav.badgeAI',
    # common namespace
    'common.language', 'common.tagline', 'common.appName',
    # auth namespace
    'auth.guest', 'auth.loginToAccount', 'auth.signOutLabel',
]

locales = ['pt-BR.json', 'es.json', 'fr.json', 'de.json', 'ru.json', 'ja.json', 'zh.json', 'ar.json']

print("=" * 80)
print("SEMANTIC KEY CHECK FOR NAVBAR + SIDEBAR COMPONENTS")
print("=" * 80)

found_issues = False

for filename in locales:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    loc_keys = get_keys(data)
    
    issues = []
    for k in focus_keys:
        en_val = en_keys.get(k, '')
        loc_val = loc_keys.get(k, None)
        
        if loc_val is None:
            issues.append(f'  MISSING: {k}')
        elif isinstance(loc_val, str) and len(loc_val) > 3 and loc_val == en_val:
            # Skip keys that are intentionally the same across languages
            if k not in ['common.appName']:
                issues.append(f'  ENGLISH VALUE: {k} = "{loc_val[:80]}"')
        elif isinstance(loc_val, dict):
            issues.append(f'  NOT A STRING: {k} is an object')
    
    if issues:
        found_issues = True
        lang_name = filename.replace('.json', '')
        print(f'\n--- {lang_name} ({len(issues)} issues) ---')
        for issue in issues:
            print(issue)

if not found_issues:
    print("\nNo semantic key issues found in focus keys across all locales.")

print()
print("=" * 80)
print("CHECKING FOR REMAINING ENGLISH VALUES IN ALL LOCALES")
print("=" * 80)

for filename in locales:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    loc_keys = get_keys(data)
    
    english_vals = []
    for k, en_val in sorted(en_keys.items()):
        if k in loc_keys:
            loc_val = loc_keys[k]
            if isinstance(loc_val, str) and len(loc_val) > 3 and loc_val == en_val:
                if k not in ['common.appName', 'common.and', 'common.or']:
                    english_vals.append(k)
    
    if english_vals:
        lang_name = filename.replace('.json', '')
        print(f'\n--- {lang_name} ({len(english_vals)} English-valued keys) ---')
        for k in english_vals[:20]:
            print(f'  {k}: "{en_keys[k][:60]}"')
        if len(english_vals) > 20:
            print(f'  ... and {len(english_vals) - 20} more')

print("\nDone.")
