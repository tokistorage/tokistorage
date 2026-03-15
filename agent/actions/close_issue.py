import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']
issue_number = payload.get('issue_number')
repo = payload.get('repo', 'tokistorage/tokistorage.github.io')

if not issue_number:
    raise ValueError("issue_number is required")

req = urllib.request.Request(
    f'https://api.github.com/repos/{repo}/issues/{issue_number}',
    data=json.dumps({'state': 'closed'}).encode(),
    headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json'},
    method='PATCH'
)
with urllib.request.urlopen(req) as r:
    issue = json.loads(r.read())
print(f"✅ Issue #{issue_number} クローズ: {issue['state']}")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'close_issue', 'issue_number': issue_number, 'repo': repo, 'state': issue['state']}, f, ensure_ascii=False, indent=2)
