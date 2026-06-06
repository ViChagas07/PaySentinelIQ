import json, sys
sys.stdout.reconfigure(encoding='utf-8')

locales = ['en', 'pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']
keys = ['badgeAI', 'new']

all_ok = True
for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    nav = data.get('nav', {})
    for key in keys:
        if key not in nav:
            print(f'MISSING [{code}]: nav.{key}')
            all_ok = False
        elif not isinstance(nav[key], str):
            print(f'NOT STRING [{code}]: nav.{key} = {type(nav[key])}')
            all_ok = False

if all_ok:
    print('All badge keys exist in all locales!')
    for code in locales:
        with open(f'{code}.json', 'rb') as f:
            data = json.load(f)
        nav = data['nav']
        vals = ' | '.join([f'{k}="{nav[k]}"' for k in keys])
        print(f'  [{code}] {vals}')
