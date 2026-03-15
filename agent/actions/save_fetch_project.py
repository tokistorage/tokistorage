import json, datetime

with open('/tmp/result.json') as f:
    raw = json.load(f)

nodes = raw['data']['user']['projectV2']['items']['nodes']
tasks = []
for n in nodes:
    c = n.get('content') or {}
    status = ''
    for fv in (n.get('fieldValues') or {}).get('nodes', []):
        if fv and fv.get('field', {}).get('name') == 'Status':
            status = fv.get('name', '')
    tasks.append({
        'id': n['id'],
        'title': c.get('title', '(draft)'),
        'state': c.get('state', ''),
        'status': status,
        'number': c.get('number'),
        'url': c.get('url'),
    })

result = {
    'project': raw['data']['user']['projectV2']['title'],
    'fetched_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'total': len(tasks),
    'tasks': tasks,
}

with open('/tmp/tr/project/cache/project.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"✅ {len(tasks)}件 → project/cache/project.json")
