import json, os, datetime, urllib.request, subprocess

token = os.environ['PAT_TOKEN']
now_jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
today = now_jst.strftime('%Y-%m-%d')

# 検索トピック定義（tokistorage目線）
TOPICS = [
    {'id': 'memory_storage',  'label': '記憶・保存技術',  'query': 'DNA storage quartz glass long-term archival technology 2026'},
    {'id': 'ai_models',       'label': 'AI・モデル動向',  'query': 'AI model free tier pricing changes Claude GPT Llama 2026'},
    {'id': 'digital_legacy',  'label': '存在証明・デジタル遺産', 'query': 'digital legacy identity proof existence inheritance law 2026'},
    {'id': 'disaster_bcp',    'label': '災害・BCP',       'query': '災害 インフラ停止 オフグリッド BCP 2026'},
    {'id': 'migration',       'label': '移住・地方創生',  'query': '地方移住 三重 伊賀 地域創生 2026'},
    {'id': 'culture_preserve','label': '文化・国際保存',  'query': 'UNESCO cultural preservation digital archive 2026'},
]

def call_model(messages, use_search=True):
    payload = {
        'model': 'openai/gpt-4o',
        'messages': messages,
        'max_tokens': 800,
    }
    if use_search:
        payload['tools'] = [{'type': 'web_search_preview'}]

    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        'https://models.github.ai/inference/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

# 全トピックをまとめて1回のAPI呼び出しで処理（トークン節約）
topics_text = '\n'.join([f"- {t['label']}: {t['query']}" for t in TOPICS])

prompt = f"""今日（{today}）の以下のトピックについて、tokistorage（1000年保存サービス）の視点で関連する最新ニュース・動向を検索してください。

## 検索トピック
{topics_text}

## 出力フォーマット（厳守）
各トピックについて以下の形式で出力してください：

### [絵文字] トピック名
- 📰 **タイトル**: 概要（1〜2文）
- 📰 **タイトル**: 概要（1〜2文）
（1トピックあたり最大2件。情報がなければ「特になし」）

トキストレージへの示唆があれば末尾に一言添えてください。"""

print(f"🔍 ニュース取得中... ({today})")

try:
    result = call_model([{'role': 'user', 'content': prompt}], use_search=True)

    # レスポンス組み立て（tool_use含む可能性あり）
    content_blocks = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    if isinstance(content_blocks, list):
        news_text = ' '.join(b.get('text', '') for b in content_blocks if b.get('type') == 'text')
    else:
        news_text = content_blocks or ''

    if not news_text.strip():
        news_text = '（ニュース取得結果が空でした）'

    print('✅ ニュース取得完了')
    print(news_text[:300])

except Exception as e:
    print(f"⚠️ web search失敗、フォールバック: {e}")
    # web searchなしでフォールバック
    try:
        result = call_model([{'role': 'user', 'content': prompt}], use_search=False)
        news_text = result['choices'][0]['message']['content']
        news_text = '⚠️ リアルタイム検索なし（学習データベース）\n\n' + news_text
    except Exception as e2:
        news_text = f'ニュース取得エラー: {e2}'

output = {
    'action': 'fetch_news',
    'date': today,
    'fetched_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'news': news_text,
}
with open('/tmp/result.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
