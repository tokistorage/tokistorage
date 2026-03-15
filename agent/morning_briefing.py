import json, os, datetime, urllib.request, glob, subprocess, re

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

# relations 読み込み（フォローアップ判定）
FOLLOWUP_DAYS = 30
relations_alert = []
relations_all = []

for path in sorted(glob.glob('/tmp/tr_briefing/memory/relations/**/*.md', recursive=True)):
    if '_template' in path:
        continue
    try:
        raw = open(path).read()
        name = raw.split('\n')[0].lstrip('# ').strip()

        # 最終接触日を抽出
        last_contact = None
        m = re.search(r'最終接触[:：]\s*(\d{4}-\d{2}-\d{2})', raw)
        if m:
            last_contact = datetime.date.fromisoformat(m.group(1))

        # 次のアクション日を抽出
        next_action = None
        m2 = re.search(r'次のアクション[:：].*?(\d{4}-\d{2}-\d{2})', raw)
        if m2:
            next_action = datetime.date.fromisoformat(m2.group(1))

        today_date = now_jst.date()
        entry = {'name': name, 'path': path, 'last_contact': last_contact, 'next_action': next_action}
        relations_all.append(entry)

        # アラート判定: 次のアクション期限が今日以前 or 最終接触から30日超
        if next_action and next_action <= today_date:
            entry['alert'] = f'期限: {next_action}'
            relations_alert.append(entry)
        elif last_contact and (today_date - last_contact).days >= FOLLOWUP_DAYS:
            entry['alert'] = f'最終接触から{(today_date - last_contact).days}日経過'
            relations_alert.append(entry)
        elif not last_contact and not next_action:
            pass  # 未記録はアラートしない

    except Exception:
        pass

# relations サマリー文字列生成
relations_summary = f"登録済み: {len(relations_all)}件\n"
if relations_alert:
    relations_summary += "\nフォローアップ推奨:\n"
    for r in relations_alert:
        relations_summary += f"- {r['name']}（{r['alert']}）\n"
else:
    relations_summary += "フォローアップ必要なし\n"

# ニュース取得（fetch_news.py を実行）
news_digest = ''
try:
    workspace = os.environ.get('GITHUB_WORKSPACE', os.path.dirname(os.path.abspath(__file__)) + '/..')
    fetch_news_path = os.path.join(workspace, 'agent', 'fetch_news.py')
    r = subprocess.run(['python3', fetch_news_path],
               capture_output=True, text=True, timeout=60,
               env={**os.environ, 'PAT_TOKEN': token})
    print(r.stdout[-500:] if r.stdout else '')
    if os.path.exists('/tmp/news_result.json'):
        nd = json.load(open('/tmp/news_result.json'))
        news_digest = nd.get('news_digest', '')
        print(f'✅ ニュース取得完了: {nd.get("raw_count",0)}件')
    else:
        print(f'⚠️ ニュース結果ファイルなし: {r.stderr[:200]}')
except Exception as e:
    print(f'⚠️ ニュース取得エラー: {e}')

# ニュース取得（web search）
news_text = ''
try:
    news_topics = (
        "以下のトピックについて今日の最新動向を簡潔に教えてください（各1〜2件）:\n"
        "1. 記憶・保存技術（DNA保存、石英ガラス、長期アーカイブ）\n"
        "2. AI・モデル動向（無料枠変更、新モデル、エージェント）\n"
        "3. 存在証明・デジタル遺産（法制度、相続、デジタルID）\n"
        "4. 災害・BCP（インフラ停止、オフグリッド）\n"
        "5. 移住・地方創生（三重・伊賀、地域政策）\n"
        "情報がなければ「特になし」と書いてください。"
    )
    news_body = json.dumps({
        'model': 'openai/gpt-4o',
        'messages': [{'role': 'user', 'content': news_topics}],
        'max_tokens': 600,
        'tools': [{'type': 'web_search_preview'}]
    }).encode()
    news_req = urllib.request.Request(
        'https://models.github.ai/inference/chat/completions',
        data=news_body,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(news_req, timeout=30) as r:
        news_result = json.loads(r.read())
    raw = news_result['choices'][0]['message']['content']
    news_text = raw if isinstance(raw, str) else ' '.join(b.get('text','') for b in raw if isinstance(b, dict))
    print('✅ ニュース取得完了')
except Exception as e:
    news_text = f'（取得エラー: {e}）'
    print(f'⚠️ ニュース取得失敗: {e}')

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
    "🤝 **リレーション フォローアップ**\n"
    "（次のアクション期限が来ている、または長期間連絡のない関係先。なければ「なし」）\n\n"
    "---\n\n"
    "---\n\n"
    "🌍 **トキストレージ目線のニュース**\n"
    "（社会動向ニュースから関連トピックを1〜3件。なければ省略）\n\n"
    "---\n\n"
    "💬 今日は何から始めますか？"
)

prompt = (
    "あなたはtokistorageの専属エージェントです。\n\n"
    "# プロジェクトタスク\n" + tasks_json + "\n\n"
    "# インボックス（声メモ・メール）\n" + inbox_content[:4000] + "\n\n"
    "# リレーション情報\n" + relations_summary + "\n\n"
    "# 指示\n" + format_instructions + "\n\n"
    "# 社会動向ニュース（参考）\n" + (news_digest or "（取得なし）")
)

body = json.dumps({
    'model': 'openai/gpt-4o-mini',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 2000
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
    'inbox_files': [os.path.basename(f) for f in inbox_files],
    'relations_alert_count': len(relations_alert)
}
with open('/tmp/result.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
