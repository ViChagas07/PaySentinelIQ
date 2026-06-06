import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

fixes = {
    'pt-BR': {
        'auditLogs': {
            'status': 'Situação',
        },
    },
    'ja': {
        'reports': {
            'notAvailable': 'なし',
        },
    },
    'zh': {
        'reports': {
            'notAvailable': '无',
        },
    },
    'de': {
        'auditLogs': {
            'live': 'Echtzeit',
        },
        'reports': {
            'trend': 'Verlauf',
        },
    },
}

for code, namespaces in fixes.items():
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    changes = 0
    for ns, keys in namespaces.items():
        for key, new_val in keys.items():
            if ns in data and key in data[ns]:
                old_val = data[ns][key]
                if old_val != new_val:
                    data[ns][key] = new_val
                    print(f'  FIXED {code}: {ns}.{key}: "{old_val}" -> "{new_val}"')
                    changes += 1
    
    if changes > 0:
        with open(f'{code}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f'  -> Saved {code}.json ({changes} changes)')
    else:
        print(f'  {code}: No changes needed')
