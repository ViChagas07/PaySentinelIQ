import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check and fix nav keys that are still in English in non-English locales

with open('en.json', 'rb') as f:
    en = json.load(f)

locales_to_check = {
    'fr': {
        'notifications': 'Notifications',
        'sections.intelligence': 'Renseignement',
    },
    'de': {
        'dashboard': 'Dashboard',  # This is standard in German, skip
        'sections.intelligence': 'Nachrichtendienst',
        'sections.system': 'System',  # This is standard in German, skip
    },
}

print("=== Checking nav keys that are still English ===")

all_keys = ['dashboard', 'payroll', 'verification', 'fraudIntelligence', 'aiInsights',
            'notifications', 'settings', 'profile', 'help', 'tagline',
            'badgeAI', 'new', 'openMenu', 'toggleSidebar', 'searchPlaceholder',
            'globalSearch', 'aiAssistant', 'notificationsAria', 'userMenu',
            'unknownUser', 'goToDashboard', 'sidebarLabel', 'collapse', 'expand',
            'tenant', 'switchTenant', 'adminOnly', 'apiDocs', 'selectCompany',
            'switchCompany', 'compliance', 'documentAnalysis', 'employees', 'companies']

section_keys = ['core', 'intelligence', 'analysis', 'system', 'data']

for code in ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    issues = []
    
    for key in all_keys:
        en_val = en['nav'].get(key, '')
        loc_val = data['nav'].get(key, '')
        if isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 2 and loc_val == en_val:
            issues.append(f'  nav.{key} = "{loc_val}"')
    
    for sk in section_keys:
        en_val = en['nav'].get('sections', {}).get(sk, '')
        loc_val = data['nav'].get('sections', {}).get(sk, '')
        if isinstance(loc_val, str) and isinstance(en_val, str) and len(loc_val) > 2 and loc_val == en_val:
            issues.append(f'  nav.sections.{sk} = "{loc_val}"')
    
    if issues:
        print(f'\n--- {code} ({len(issues)} English nav values) ---')
        for i in issues:
            print(i)

print()
print("Done.")
