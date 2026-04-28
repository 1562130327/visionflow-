import json
d = json.load(open(r'C:\Users\Administrator\.openclaw\openclaw.json', encoding='utf-8'))
models = d.get('models', {}).get('models', {})
if isinstance(models, dict):
    print('=== Model aliases ===')
    for alias, cfg in models.items():
        prov = cfg.get('provider', '?')
        model = cfg.get('model', '?')
        print(f'{alias:40s} provider={prov:30s} model={model}')
else:
    print('models not a dict, type:', type(models))
    print('models:', json.dumps(models, indent=2, ensure_ascii=False)[:500])
