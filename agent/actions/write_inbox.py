import json, os, datetime

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
text = payload.get('text', '').strip()
place = payload.get('place', '').strip()
lat = payload.get('lat', '').strip()
lng = payload.get('lng', '').strip()
weather = payload.get('weather', '').strip()
date_str = payload.get('date', '').strip()
time_str = payload.get('time', '').strip()

if not text:
    raise ValueError("text is required")

now = datetime.datetime.utcnow()
jst = now + datetime.timedelta(hours=9)

# ショートカットから日時が渡された場合はそちらを優先（オフライン記録の場合）
if date_str and time_str:
    timestamp = f"{date_str} {time_str}"
    # ファイル名用にdatetimeをパース試みる（失敗したらサーバー時刻）
    try:
        import re
        # "2026/03/14 19:20" or "2026/03/14 19:20:36 GMT+9:18:59" などに対応
        m = re.match(r'(\d{4})[/\-](\d{2})[/\-](\d{2})\s+(\d{2}):(\d{2})', f"{date_str} {time_str}")
        if m:
            y,mo,d,h,mi = m.groups()
            filename = f"{y}-{mo}-{d}-{h}-{mi}.md"
            display_time = f"{y}-{mo}-{d} {h}:{mi} (現地時刻)"
        else:
            raise ValueError("parse failed")
    except:
        filename = jst.strftime('%Y-%m-%d-%H-%M') + '.md'
        display_time = jst.strftime('%Y-%m-%d %H:%M') + ' JST'
else:
    filename = jst.strftime('%Y-%m-%d-%H-%M') + '.md'
    display_time = jst.strftime('%Y-%m-%d %H:%M') + ' JST'

lines = [f"# {display_time}", "", text, ""]
if weather:
    lines.append(f"🌤 {weather}")
    lines.append("")
if place or (lat and lng):
    lines.append("## 位置情報")
    if place:
        lines.append(f"- 住所: {place}")
    if lat and lng:
        lines.append(f"- 座標: {lat}, {lng}")
        lines.append(f"- マップ: https://maps.google.com/maps?q={lat},{lng}")
    lines.append("")
content = "\n".join(lines)

os.makedirs('/tmp/tr_inbox', exist_ok=True)
with open('/tmp/tr_inbox/filename.txt', 'w') as f:
    f.write(filename)
with open('/tmp/tr_inbox/content.txt', 'w') as f:
    f.write(content)
with open('/tmp/result.json', 'w') as f:
    json.dump({'action': 'write_inbox', 'filename': filename, 'size': len(text), 'has_location': bool(place or lat)}, f, ensure_ascii=False, indent=2)
print(f"✅ write_inbox: inbox/{filename} ({len(text)} chars, location={'yes' if place or lat else 'no'})")
