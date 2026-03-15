import json, os, base64

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
path = payload.get('path', 'outbox/output.md')
content = payload.get('content', '')
os.makedirs('/tmp/tr_write', exist_ok=True)
with open('/tmp/tr_write_content.txt', 'w') as f:
    f.write(content)
with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'write_file', 'path': path, 'size': len(content)}, f, ensure_ascii=False, indent=2)
print(f"✅ write_file: {path} ({len(content)} chars)")
