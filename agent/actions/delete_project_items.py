import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']
item_ids = payload.get('item_ids', [])

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

meta = gql('{ user(login: "tokistorage") { projectV2(number: 2) { id } } }')
project_id = meta['data']['user']['projectV2']['id']

results = []
for item_id in item_ids:
    result = gql('''mutation($p:ID!, $i:ID!) {
      deleteProjectV2Item(input: {projectId: $p, itemId: $i}) {
        deletedItemId
      }
    }''', {'p': project_id, 'i': item_id})
    if 'errors' in result:
        results.append({'id': item_id, 'status': 'error', 'error': str(result['errors'])})
        print(f"❌ {item_id}: {result['errors']}")
    else:
        results.append({'id': item_id, 'status': 'deleted'})
        print(f"✅ 削除: {item_id}")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'delete_project_items', 'deleted': len([r for r in results if r['status']=='deleted']), 'results': results}, f, ensure_ascii=False, indent=2)
print(f"✅ 完了: {len([r for r in results if r['status']=='deleted'])}/{len(item_ids)}件削除")
