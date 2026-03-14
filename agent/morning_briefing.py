import json, os, datetime, urllib.request, glob, subprocess

token = os.environ['PAT_TOKEN']
now_jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
today = now_jst.strftime('%Y-%m-%d')
yesterday = (now_jst - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# tr をクローン
subprocess.run(
    ['git', 'clone', f'https://x-access-token:{token}@github.com/tokistorage/tr.git', '/tmp/tr_briefing'],
    check=True, capture_output=True
)

# project.json 読み込み
with open('/tmp/tr_briefing/project/cache/project.json') as f:
    project = json.load(f)

tasks = project['tasks']
todo_count = sum(1 for t in tasks if t['status'] == 'Todo')
wip_count = sum(1 for t in tasks if t['status'] == 'In Progress')

# inbox ファイル読み込み（直近2日分、archive除く）
inbox_files = sorted(
    glob.glob(f'/tmp/tr_briefing/memory/inbox/{today}*.md') +
    glob.glob(f'/tmp/tr_briefing/memory/inbox/{yesterday}*.md') +
    glob.glob(f'/tmp/tr_briefing/memory/inbox/{today}*.json') +
    glob.glob(f'/tmp/tr_briefing/memory/inbox/{yesterday}*.json')
)

inbox_content = ''
for path in inbox_files:
    inbox_content += f'\n--- {os.path.basename(path)} ---\n'
    try:
        raw = open(path).read()
        if path.endswith('.json'):
            data = json.loads(raw)
            msgs = data.get('messages', [])
            for m in msgs:
                inbox_content += f"[{m.get('account','')}] {m.get('subject','')}\n"
                inbox_content += m.get('body', '')[:150] + '\n'
        else:
            inbox_content += raw
    except Exception:
        pass

tasks_json = json.dumps(tasks, ensure_ascii=False)
format_instructions = (
    "以下のフォーマットで出力してください:\n\n"
    "☀️ おはようございます、卓也さん！\n\n"
    f"📋 **短期計画 — {today}**\n"
    f"全{project['total']}件 | Todo: {todo_count}件 | In Progress: {wip_count}件\n\n"
    "---\n\n"
    "⚡ **今日フォーカスすべき上位5件**\n"
    "（期限あり > In Progress > Todo の順）\n"
    "1. ...\n\n"
    "---\n\n"
    "📂 **カテゴリ別**\n"
    "- 財務・法務: X件\n- 不動産: X件\n- 事業整理・新規: X件\n"
    "- 地域・移住: X件\n- 国際・関係: X件\n- その他: X件\n\n"
    "---\n\n"
    "📥 **インボックス インサイト**\n\n"
    "🎙️ 声メモ\n（テスト・挨拶を除いた実質メモのみ）\n\n"
    "📬 メール\n（ニュースレター・GitHub通知を除く、要対応・重要情報のみ ⚠️付き）\n\n"
    "---\n\n"
    "💬 今日は何から始めますか？"
)

prompt = (
    "あなたはtokistorageの専属エージェントです。\n\n"
    "# プロジェクトタスク\n" + tasks_json + "\n\n"
    "# インボックス（声メモ・メール）\n" + inbox_content[:5000] + "\n\n"
    "# 指示\n" + format_instructions
)

body = json.dumps({
    'model': 'openai/gpt-4o-mini',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 1500
}).encode()

req = urllib.request.Request(
    'https://models.github.ai/inference/chat/completions',
    data=body,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())

briefing = result['choices'][0]['message']['content']
print('✅ ブリーフィング生成完了')
print(briefing[:300])

output = {
    'action': 'morning_briefing',
    'generated_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'date': today,
    'briefing': briefing,
    'model': 'openai/gpt-4o-mini',
    'inbox_files': [os.path.basename(f) for f in inbox_files]
}
with open('/tmp/result.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
