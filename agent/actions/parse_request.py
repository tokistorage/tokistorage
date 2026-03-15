import os, json, sys

github_output = os.environ.get('GITHUB_OUTPUT', '/dev/stdout')

inbox_text = os.environ.get('INBOX_TEXT', '').strip()
action_input = os.environ.get('ACTION_INPUT', '').strip()

if inbox_text:
    action = 'write_inbox'
    payload = json.dumps({
        'text': inbox_text,
        'place': os.environ.get('PLACE', ''),
        'lat': os.environ.get('LAT', ''),
        'lng': os.environ.get('LNG', ''),
        'weather': os.environ.get('WEATHER', ''),
        'date': os.environ.get('DATE_INPUT', ''),
        'time': os.environ.get('TIME_INPUT', ''),
    })
elif os.path.exists('agent/request.json'):
    d = json.load(open('agent/request.json'))
    action = d.get('action', 'fetch_project')
    payload = json.dumps(d.get('payload', {}))
else:
    action = action_input or 'fetch_project'
    payload = '{}'

print(f"▶ action={action}")

with open(github_output, 'a') as f:
    f.write(f"action={action}\n")
    f.write(f"payload={payload}\n")
