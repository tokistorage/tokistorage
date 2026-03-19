import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']

name = payload.get('name', 'new-repo')
description = payload.get('description', '')
private = payload.get('private', False)
auto_init = payload.get('auto_init', True)
org = payload.get('org', '')  # org指定があればorg配下に作成

if org:
    url = f'https://api.github.com/orgs/{org}/repos'
else:
    url = 'https://api.github.com/user/repos'

req = urllib.request.Request(
    url,
    data=json.dumps({
        'name': name,
        'description': description,
        'private': private,
        'auto_init': auto_init
    }).encode(),
    headers={
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
        print(f"✅ create_repo: {d['html_url']}")
        with open('/tmp/result.json', 'w') as f:
            json.dump({'action': 'create_repo', 'url': d['html_url'], 'name': d['full_name']}, f, ensure_ascii=False, indent=2)
except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    print(f"❌ create_repo failed: {body.get('message')}")
    with open('/tmp/result.json', 'w') as f:
        json.dump({'action': 'create_repo', 'error': body.get('message')}, f, ensure_ascii=False, indent=2)

private = payload.get('private', False)
auto_init = payload.get('auto_init', True)

req = urllib.request.Request(
    'https://api.github.com/user/repos',
    data=json.dumps({
        'name': name,
        'description': description,
        'private': private,
        'auto_init': auto_init
    }).encode(),
    headers={
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
        print(f"✅ create_repo: {d['html_url']}")
        with open('/tmp/result.json', 'w') as f:
            json.dump({'action': 'create_repo', 'url': d['html_url'], 'name': d['full_name']}, f, ensure_ascii=False, indent=2)
except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    print(f"❌ create_repo failed: {body.get('message')}")
    with open('/tmp/result.json', 'w') as f:
        json.dump({'action': 'create_repo', 'error': body.get('message')}, f, ensure_ascii=False, indent=2)
