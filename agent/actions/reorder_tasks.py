import json, urllib.request, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
token = os.environ['PAT_TOKEN']

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

# ordered_ids: 上から順に並べたいitem IDのリスト
ordered_ids = payload.get('ordered_ids', [])
results = []
prev_id = None
for item_id in ordered_ids:
    variables = {'projectId': project_id, 'itemId': item_id}
    if prev_id:
        variables['afterId'] = prev_id
    r = gql('''mutation($projectId:ID!,$itemId:ID!,$afterId:ID){
      updateProjectV2ItemPosition(input:{projectId:$projectId,itemId:$itemId,afterId:$afterId}){
        items { totalCount }
      }
    }''', variables)
    ok = 'errors' not in r
    results.append({'item_id': item_id, 'ok': ok})
    print(f"{'✅' if ok else '❌'} {item_id}")
    prev_id = item_id

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'reorder_tasks', 'results': results}, f, ensure_ascii=False, indent=2)
