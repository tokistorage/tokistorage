import json, urllib.request, os, sys

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

meta = gql('{ user(login: "tokistorage") { projectV2(number: 2) { id fields(first:20){ nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }')
project_id = meta['data']['user']['projectV2']['id']
status_field = next((f for f in meta['data']['user']['projectV2']['fields']['nodes'] if f and f.get('name') == 'Status'), None)
options = {o['name']: o['id'] for o in status_field['options']}

updates = payload.get('updates', [])
results = []
for u in updates:
    option_id = options.get(u['new_status'])
    if not option_id:
        results.append({'task_id': u['task_id'], 'error': f"不明: {u['new_status']}", 'available': list(options.keys())})
        continue
    r = gql('''mutation($i:ID!,$p:ID!,$f:ID!,$o:String!){
      updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}
    }''', {'i': u['task_id'], 'p': project_id, 'f': status_field['id'], 'o': option_id})
    ok = 'errors' not in r
    results.append({'task_id': u['task_id'], 'ok': ok, 'new_status': u['new_status']})
    print(f"{'✅' if ok else '❌'} {u['task_id']} → {u['new_status']}")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'update_task', 'results': results}, f, ensure_ascii=False, indent=2)
