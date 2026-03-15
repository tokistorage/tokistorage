import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']
issue_number = payload.get('issue_number')
body = payload.get('body', '')
repo = payload.get('repo', 'tokistorage/tokistorage')

if not issue_number:
    raise ValueError("issue_number is required")

req = urllib.request.Request(
    f'https://api.github.com/repos/{repo}/issues/{issue_number}/comments',
    data=json.dumps({'body': body}).encode(),
    headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json'}
)
with urllib.request.urlopen(req) as r:
    comment = json.loads(r.read())
print(f"✅ コメント追加: Issue #{issue_number} → comment #{comment['id']}")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'add_comment', 'issue_number': issue_number, 'comment_id': comment['id'], 'url': comment['html_url']}, f, ensure_ascii=False, indent=2)
