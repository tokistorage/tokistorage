import json, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
files = payload.get('files', [])  # 移動するファイル名リスト (例: ["2026-03-14-17-19.md"])

if not files:
    raise ValueError("files is required")

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'archive_inbox', 'files': files, 'count': len(files)}, f, ensure_ascii=False, indent=2)
print(f"✅ archive_inbox: {len(files)}件をアーカイブ予定")
