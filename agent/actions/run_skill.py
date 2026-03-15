import json, os

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
skill = payload.get('skill', '')
args = payload.get('args', {})

with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'run_skill', 'skill': skill, 'args': args, 'status': 'queued'}, f, ensure_ascii=False, indent=2)
print(f"✅ run_skill: {skill} キューへ追加")
