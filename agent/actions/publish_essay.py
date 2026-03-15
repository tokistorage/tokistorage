import json, os, datetime

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
slug = payload.get('slug', f"essay-{datetime.date.today().isoformat()}")
title = payload.get('title', 'Untitled')
content = payload.get('content', '')  # HTML or Markdown
lang = payload.get('lang', 'ja')  # ja | en

filename = f"{slug}.html" if not slug.endswith('.html') else slug

os.makedirs('/tmp/tr_essay', exist_ok=True)
with open('/tmp/tr_essay/filename.txt', 'w') as f:
    f.write(filename)
with open('/tmp/tr_essay/content.txt', 'w') as f:
    f.write(content)
with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'publish_essay', 'filename': filename, 'title': title, 'lang': lang}, f, ensure_ascii=False, indent=2)
print(f"✅ publish_essay: {filename}")
