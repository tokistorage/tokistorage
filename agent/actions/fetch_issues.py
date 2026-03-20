import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']
repo = payload.get('repo', 'tokistorage/tr')
labels = payload.get('labels', 'contact')
state = payload.get('state', 'open')

def api(url):
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'tokistorage-agent',
        }
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

url = f'https://api.github.com/repos/{repo}/issues?labels={labels}&state={state}&per_page=20'
issues = api(url)

result = []
for i in issues:
    result.append({
        'number': i['number'],
        'title': i['title'],
        'body': i['body'],
        'state': i['state'],
        'created_at': i['created_at'],
        'url': i['html_url'],
    })

print(f'✅ {len(result)}件取得')
for i in result:
    print(f"  #{i['number']} {i['title']} ({i['created_at'][:10]})")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'fetch_issues', 'repo': repo, 'count': len(result), 'issues': result}, f, ensure_ascii=False, indent=2)
