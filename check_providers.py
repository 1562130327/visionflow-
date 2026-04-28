import json
d = json.load(open(r'C:\Users\Administrator\.openclaw\agents\main\agent\models.json', encoding='utf-8'))
for pk, pv in d.get('providers', {}).items():
    if isinstance(pv, dict) and 'models' in pv:
        models = pv['models']
        base = pv.get('baseUrl', '')
        if isinstance(models, list):
            for m in models:
                mid = m.get('id', '?')
                print(f'{pk:30s} -> {mid:20s}  base={base}')
        else:
            print(f'{pk:30s} -> (dict) base={base}')
    else:
        print(f'{pk:30s} -> {str(pv)[:80]}')
