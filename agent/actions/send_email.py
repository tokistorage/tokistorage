import smtplib, json, os, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

gmail_address = os.environ['GMAIL_ADDRESS']
app_password = os.environ['GMAIL_APP_PASSWORD']
payload = json.loads(os.environ.get('PAYLOAD', '{}'))

to = payload.get('to', '')
subject = payload.get('subject', '')
body = payload.get('body', '')
from_name = payload.get('from_name', 'Takuya Sato / TokiStorage')

if not to or not subject or not body:
    raise ValueError("to / subject / body は必須です")

msg = MIMEMultipart()
msg['From'] = f'{from_name} <{gmail_address}>'
msg['To'] = to
msg['Subject'] = Header(subject, 'utf-8')
msg.attach(MIMEText(body, 'plain', 'utf-8'))

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
    server.login(gmail_address, app_password)
    server.sendmail(gmail_address, to, msg.as_string())

print(f"✅ 送信完了: {to} / {subject}")

result = {
    'action': 'send_email',
    'sent_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'to': to,
    'subject': subject,
    'status': 'sent',
}
with open('/tmp/result.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
