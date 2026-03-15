import json, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
# path例: "daily/2026-03-12.md" or "context/project-notes.md"
path = payload.get('path', '')
content = payload.get('content', '')
mode = payload.get('mode', 'overwrite')  # overwrite | append

if not path:
    raise ValueError("path is required")

os.makedirs('/tmp/tr_memory', exist_ok=True)
with open('/tmp/tr_memory/path.txt', 'w') as f:
    f.write(path)
with open('/tmp/tr_memory/content.txt', 'w') as f:
    f.write(content)
with open('/tmp/tr_memory/mode.txt', 'w') as f:
    f.write(mode)
with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'write_memory', 'path': f'memory/{path}', 'mode': mode, 'size': len(content)}, f, ensure_ascii=False, indent=2)
print(f"✅ write_memory: memory/{path} ({mode}, {len(content)} chars)")
