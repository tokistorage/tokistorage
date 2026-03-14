import sys, re

with open(sys.argv[1]) as f:
    content = f.read()

lines = content.split('\n')
in_run_block = False
in_heredoc = False
heredoc_marker = None

for i, line in enumerate(lines, 1):
    # ヒアドキュメント開始検出
    if in_run_block and not in_heredoc:
        m = re.search(r"<<\s*['\"]?(\w+)['\"]?", line)
        if m:
            in_heredoc = True
            heredoc_marker = m.group(1)
            continue
    # ヒアドキュメント終了検出
    if in_heredoc and line.strip() == heredoc_marker:
        in_heredoc = False
        heredoc_marker = None
        continue
    if in_heredoc:
        continue
    if '        run: |' in line:
        in_run_block = True
    elif in_run_block and line and not line.startswith(' ') and not line.startswith('#'):
        print(f'⚠️  L{i}: インデントなし行を検出: {line[:60]}')
        sys.exit(1)
    elif in_run_block and line.startswith('      - '):
        in_run_block = False

print('✅ ワークフロー簡易チェック OK')
