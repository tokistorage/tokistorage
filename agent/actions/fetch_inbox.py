import imaplib, email, json, os, datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime

payload = json.loads(os.environ.get('PAYLOAD', '{}'))
max_count = payload.get('max', 20)

# 取得対象アカウント一覧
accounts = [
    {
        'account': 'tokistorage',
        'address': os.environ['GMAIL_ADDRESS'],
        'password': os.environ['GMAIL_APP_PASSWORD'],
        'host': 'imap.gmail.com',
    },
    {
        'account': 'business',
        'address': os.environ['BUSINESS_EMAIL'],
        'password': os.environ['BUSINESS_APP_PASSWORD'],
        'host': 'imap.gmail.com',
    },
]

def decode_str(s):
    if s is None:
        return ''
    parts = decode_header(s)
    result = ''
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or 'utf-8', errors='replace')
        else:
            result += part
    return result

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in cd:
                payload_bytes = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                return payload_bytes.decode(charset, errors='replace')
    else:
        payload_bytes = msg.get_payload(decode=True)
        if payload_bytes:
            charset = msg.get_content_charset() or 'utf-8'
            return payload_bytes.decode(charset, errors='replace')
    return ''

def fetch_account(acct):
    print(f"\n📬 [{acct['account']}] {acct['address']}")
    mail = imaplib.IMAP4_SSL(acct['host'])
    mail.login(acct['address'], acct['password'])
    mail.select('inbox')
    status, data = mail.search(None, 'UNSEEN')
    uids = data[0].split()
    print(f"  未読: {len(uids)}件")
    messages = []
    for uid in uids[-max_count:]:
        status, msg_data = mail.fetch(uid, '(RFC822)')
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        date_str = msg.get('Date', '')
        try:
            dt = parsedate_to_datetime(date_str).isoformat()
        except:
            dt = date_str
        messages.append({
            'uid': uid.decode(),
            'account': acct['account'],
            'subject': decode_str(msg.get('Subject', '')),
            'from': decode_str(msg.get('From', '')),
            'to': decode_str(msg.get('To', '')),
            'date': dt,
            'body': get_body(msg)[:2000],
        })
        print(f"  - [{dt[:10]}] {decode_str(msg.get('Subject',''))}")
    mail.logout()
    return {'unread_count': len(uids), 'messages': messages}

all_messages = []
summary = {}
for acct in accounts:
    try:
        result = fetch_account(acct)
        summary[acct['account']] = result['unread_count']
        all_messages.extend(result['messages'])
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        summary[acct['account']] = f'error: {e}'

today = datetime.date.today().isoformat()
result = {
    'action': 'fetch_inbox',
    'fetched_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'date': today,
    'summary': summary,
    'total_unread': sum(v for v in summary.values() if isinstance(v, int)),
    'fetched_count': len(all_messages),
    'messages': all_messages,
}
with open('/tmp/result.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n✅ fetch_inbox 完了: 合計{len(all_messages)}件取得")
