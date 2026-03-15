import json, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
path = payload.get('path', '')
content = payload.get('content', '')
mode = payload.get('mode', 'overwrite')

if not path:
    raise ValueError("path is required")

os.makedirs('/tmp/tr_relations', exist_ok=True)
with open('/tmp/tr_relations/path.txt', 'w') as f:
    f.write(path)
with open('/tmp/tr_relations/content.txt', 'w') as f:
    f.write(content)
with open('/tmp/tr_relations/mode.txt', 'w') as f:
    f.write(mode)
with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'write_relations', 'path': f'memory/relations/{path}', 'mode': mode, 'size': len(content)}, f, ensure_ascii=False, indent=2)
print(f"✅ write_relations: memory/relations/{path} ({mode}, {len(content)} chars)")
