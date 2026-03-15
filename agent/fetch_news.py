"""
トキストレージ目線のニューストピック収集
RSS経由で取得してgpt-4o-miniで要約・フィルタリング
"""
import json, os, urllib.request, urllib.parse, datetime, xml.etree.ElementTree as ET

token = os.environ['PAT_TOKEN']
today = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')

# 収集するRSSフィード（無料・認証不要）
FEEDS = [
    # 記憶・保存・アーカイブ
    {'label': '記憶・保存技術', 'url': 'https://feeds.feedburner.com/TechCrunch'},
    # AI・エージェント動向
    {'label': 'AI動向', 'url': 'https://hnrss.org/frontpage?q=AI+agent+model&count=10'},
    # 日本語ニュース（地方・移住・BCP）
    {'label': '国内動向', 'url': 'https://www3.nhk.or.jp/rss/news/cat0.xml'},
    # デジタル遺産・長期保存
    {'label': 'デジタルアーカイブ', 'url': 'https://hnrss.org/frontpage?q=archive+preservation+memory&count=10'},
    # 災害・BCP
    {'label': '災害・BCP', 'url': 'https://hnrss.org/frontpage?q=disaster+resilience+offline&count=5'},
]

def fetch_rss(url, max_items=5, timeout=8):
    items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TokiStorage-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        root = ET.fromstring(raw)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        # RSS 2.0
        for item in root.findall('.//item')[:max_items]:
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            desc = item.findtext('description', '').strip()[:200]
            if title:
                items.append({'title': title, 'link': link, 'desc': desc})
        # Atom
        if not items:
            for entry in root.findall('.//atom:entry', ns)[:max_items]:
                title = entry.findtext('atom:title', '', ns).strip()
                link_el = entry.find('atom:link', ns)
                link = link_el.get('href', '') if link_el is not None else ''
                if title:
                    items.append({'title': title, 'link': link, 'desc': ''})
    except Exception as e:
        print(f'  RSS取得エラー: {url[:50]} → {e}')
    return items

# 全フィード収集
all_items = []
for feed in FEEDS:
    items = fetch_rss(feed['url'])
    for item in items:
        item['feed_label'] = feed['label']
    all_items.extend(items)
    print(f"  {feed['label']}: {len(items)}件取得")

if not all_items:
    print("⚠️ ニュース取得0件")
    result = {'date': today, 'news_digest': '（ニュース取得なし）', 'raw_count': 0}
    with open('/tmp/news_result.json', 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    exit(0)

# gpt-4o-miniでフィルタリング・要約
items_text = '\n'.join([
    f"[{i['feed_label']}] {i['title']} — {i['desc'][:100]}"
    for i in all_items
])

prompt = f"""以下はRSSフィードから収集したニュースの一覧です。
今日は{today}です。

あなたはtokistorageというプロジェクトの専属エージェントです。
tokistorageの関心軸:
1. 記憶・保存技術（DNA保存・石英ガラス・長期アーカイブ・デジタル遺産）
2. AI・エージェント動向（モデル変更・無料枠・新サービス・オープンソース）
3. 存在証明・デジタルアイデンティティ（法制度・相続・データ主権）
4. 災害・BCP・オフグリッド（インフラ停止・自給自足・レジリエンス）
5. 移住・地方創生（地方移住政策・コミュニティ・三重・伊賀）
6. 国際・文化保存（ユネスコ・移民・納骨・礼拝文化・多文化共生）

以下のニュースから、上記の関心軸に関連するものだけを選び、
以下のフォーマットで出力してください（関連なければ「関連ニュースなし」）:

🌍 **トキストレージ目線のニュース（{today}）**

🗄️ [記憶・保存] あれば
🤖 [AI動向] あれば
🏛️ [存在証明・制度] あれば
🆘 [災害・BCP] あれば
🏘️ [移住・地方] あれば
🌏 [国際・文化] あれば

各項目は1〜2行で簡潔に。関連性が低いものは省く。

--- ニュース一覧 ---
{items_text[:4000]}
"""

body = json.dumps({
    'model': 'openai/gpt-4o-mini',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 800
}).encode()

req = urllib.request.Request(
    'https://models.github.ai/inference/chat/completions',
    data=body,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as r:
    api_result = json.loads(r.read())

news_digest = api_result['choices'][0]['message']['content']
print('✅ ニュースダイジェスト生成完了')
print(news_digest[:300])

result = {
    'date': today,
    'news_digest': news_digest,
    'raw_count': len(all_items),
    'generated_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
}
with open('/tmp/news_result.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
