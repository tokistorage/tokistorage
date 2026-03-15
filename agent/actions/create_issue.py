import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']
title = payload.get('title', 'New Task')
body = payload.get('body', '')
labels = payload.get('labels', [])
repo = payload.get('repo', 'tokistorage/tokistorage')

def api(url, data, method='POST'):
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(),
        headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json'},
        method=method
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def gql(query, variables=None):
    body = {'query': query}
    if variables: body['variables'] = variables
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# Issue作成
issue_data = {'title': title, 'body': body}
if labels: issue_data['labels'] = labels
issue = api(f'https://api.github.com/repos/{repo}/issues', issue_data)
print(f"✅ Issue作成: #{issue['number']} {issue['title']}")

# Project #2 に追加
meta = gql('{ user(login: "tokistorage") { projectV2(number: 2) { id } } }')
if 'errors' in meta:
    raise Exception(f"Project取得エラー: {meta['errors']}")
project_id = meta['data']['user']['projectV2']['id']
result = gql('''mutation($p:ID!, $c:ID!) {
  addProjectV2ItemById(input: {projectId: $p, contentId: $c}) {
    item { id }
  }
}''', {'p': project_id, 'c': issue['node_id']})
if 'errors' in result:
    raise Exception(f"Project追加エラー: {result['errors']}")
item_id = result['data']['addProjectV2ItemById']['item']['id']
print(f"✅ Project追加: {item_id}")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'create_issue', 'issue_number': issue['number'], 'url': issue['html_url'], 'title': title, 'project_item_id': item_id}, f, ensure_ascii=False, indent=2)
