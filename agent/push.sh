#!/bin/bash
# agent/push.sh — Claudeがアクションを送信する際に使うヘルパー
# 使い方: PAT=xxx bash agent/push.sh
#
# やること:
#   1. agent/request.json に _t タイムスタンプを自動付与
#   2. .github/workflows/agent-dispatch.yml の構文チェック
#   3. 問題なければ push
#   4. 短いポーリング（3秒×10回）で完了を待機

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REQUEST="$REPO_ROOT/agent/request.json"
WORKFLOW="$REPO_ROOT/.github/workflows/agent-dispatch.yml"

# PAT チェック
if [ -z "$PAT" ]; then
  echo "❌ PAT が未設定です。PAT=xxx bash agent/push.sh で実行してください"
  exit 1
fi

# request.json チェック
if [ ! -f "$REQUEST" ]; then
  echo "❌ agent/request.json が見つかりません"
  exit 1
fi

# _t タイムスタンプを付与（既存の _t は上書き）
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
python3 - << PYEOF
import json, sys
with open('$REQUEST') as f:
    d = json.load(f)
d['_t'] = '$TIMESTAMP'
with open('$REQUEST', 'w') as f:
    json.dump(d, f, ensure_ascii=False)
print(f"✅ _t 付与: $TIMESTAMP")
PYEOF

# ワークフロー YAML チェック
python3 -c "
import sys
with open('$WORKFLOW') as f:
    content = f.read()
lines = content.split('\n')
in_run_block = False
for i, line in enumerate(lines, 1):
    if '        run: |' in line:
        in_run_block = True
    elif in_run_block and line and not line.startswith(' ') and not line.startswith('#'):
        print(f'⚠️  L{i}: インデントなし行を検出: {line[:60]}')
        sys.exit(1)
    elif in_run_block and line.startswith('      - '):
        in_run_block = False
print('✅ ワークフロー簡易チェック OK')
" || { echo "❌ ワークフローに問題があります。修正してから再実行してください"; exit 1; }

# git push
cd "$REPO_ROOT"
ACTION=$(python3 -c "import json; print(json.load(open('agent/request.json')).get('action','unknown'))")
git add -u
git add agent/request.json
git diff --cached --quiet && echo "⚠️  変更なし（すでにpush済み？）" || \
  git commit -m "agent: $ACTION"
git push https://${PAT}@github.com/tokistorage/tokistorage.git main

echo ""
echo "✅ push完了: $ACTION"
echo "⏳ 結果を待機中（3秒×10回）..."

BEFORE=$(cat /home/claude/tr/.agent/last_run.json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('last_run',''))" 2>/dev/null || echo "")
for i in $(seq 1 10); do
  sleep 3
  cd /home/claude/tr && git pull https://${PAT}@github.com/tokistorage/tr.git main -q 2>/dev/null
  AFTER=$(cat .agent/last_run.json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('last_run',''))" 2>/dev/null || echo "")
  if [ "$AFTER" != "$BEFORE" ] && [ -n "$AFTER" ]; then
    echo "✅ 完了 ($((i*3))秒)"
    cat .agent/last_run.json
    exit 0
  fi
  echo "  ($i/10)"
done
echo "⚠️  30秒以内に完了しませんでした。Actionsタブで確認してください"
