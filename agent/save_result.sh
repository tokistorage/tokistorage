#!/bin/bash
# agent/save_result.sh — アクション結果を private repo (tr) に保存する

set -e

git clone https://x-access-token:$PAT_TOKEN@github.com/tokistorage/tr.git /tmp/tr
cd /tmp/tr

case "$ACTION" in
  fetch_project)
    python3 $GITHUB_WORKSPACE/agent/actions/save_fetch_project.py
    ;;
  update_task)
    mkdir -p project/updates
    cp /tmp/result.json project/updates/latest.json
    echo "✅ update結果 → project/updates/latest.json"
    ;;
  create_issue)
    mkdir -p outbox
    cp /tmp/result.json outbox/created_issue.json
    echo "✅ issue作成結果 → outbox/created_issue.json"
    ;;
  write_file)
    WPATH=$(python3 -c "import json; print(json.load(open('/tmp/result.json'))['path'])")
    mkdir -p "$(dirname /tmp/tr/$WPATH)"
    cp /tmp/tr_write_content.txt "/tmp/tr/$WPATH"
    echo "✅ ファイル書き込み → $WPATH"
    ;;
  write_memory)
    MPATH=$(cat /tmp/tr_memory/path.txt)
    MODE=$(cat /tmp/tr_memory/mode.txt)
    mkdir -p "$(dirname /tmp/tr/memory/$MPATH)"
    if [ "$MODE" = "append" ] && [ -f "/tmp/tr/memory/$MPATH" ]; then
      cat /tmp/tr_memory/content.txt >> "/tmp/tr/memory/$MPATH"
    else
      cp /tmp/tr_memory/content.txt "/tmp/tr/memory/$MPATH"
    fi
    echo "✅ write_memory → memory/$MPATH ($MODE)"
    ;;
  publish_essay)
    FNAME=$(cat /tmp/tr_essay/filename.txt)
    mkdir -p outbox/essays
    cp /tmp/tr_essay/content.txt "outbox/essays/$FNAME"
    echo "✅ publish_essay → outbox/essays/$FNAME"
    ;;
  reorder_tasks)
    mkdir -p outbox
    cp /tmp/result.json outbox/reorder_result.json
    echo "✅ 並び替え結果 → outbox/reorder_result.json"
    ;;
  close_issue)
    mkdir -p outbox
    cp /tmp/result.json outbox/close_issue_result.json
    echo "✅ クローズ結果 → outbox/close_issue_result.json"
    ;;
  add_comment)
    mkdir -p outbox
    cp /tmp/result.json outbox/comment_result.json
    echo "✅ コメント結果 → outbox/comment_result.json"
    ;;
  run_skill)
    mkdir -p outbox
    cp /tmp/result.json outbox/skill_queue.json
    echo "✅ スキルキュー → outbox/skill_queue.json"
    ;;
  fetch_inbox)
    DATE=$(python3 -c "import json; print(json.load(open('/tmp/result.json'))['date'])")
    mkdir -p memory/inbox
    cp /tmp/result.json "memory/inbox/${DATE}.json"
    echo "✅ fetch_inbox → memory/inbox/${DATE}.json"
    ;;
  send_email)
    mkdir -p outbox
    cp /tmp/result.json outbox/send_email_result.json
    echo "✅ send_email結果 → outbox/send_email_result.json"
    ;;
  write_inbox)
    FNAME=$(cat /tmp/tr_inbox/filename.txt)
    mkdir -p memory/inbox
    cp /tmp/tr_inbox/content.txt "memory/inbox/$FNAME"
    echo "✅ write_inbox → memory/inbox/$FNAME"
    ;;
  archive_inbox)
    FILES=$(python3 -c "import json; print(chr(10).join(json.load(open('/tmp/result.json'))['files']))")
    mkdir -p memory/inbox/archive
    echo "$FILES" | while IFS= read -r FNAME; do
      [ -z "$FNAME" ] && continue
      if [ -f "memory/inbox/$FNAME" ]; then
        mv "memory/inbox/$FNAME" "memory/inbox/archive/$FNAME"
        echo "✅ アーカイブ: $FNAME"
      else
        echo "⚠️ 見つからず: $FNAME"
      fi
    done
    ;;
  write_relations)
    RPATH=$(cat /tmp/tr_relations/path.txt)
    RMODE=$(cat /tmp/tr_relations/mode.txt)
    mkdir -p "$(dirname memory/relations/$RPATH)"
    if [ "$RMODE" = "append" ] && [ -f "memory/relations/$RPATH" ]; then
      cat /tmp/tr_relations/content.txt >> "memory/relations/$RPATH"
    else
      cp /tmp/tr_relations/content.txt "memory/relations/$RPATH"
    fi
    echo "✅ write_relations → memory/relations/$RPATH ($RMODE)"
    ;;
  morning_briefing)
    DATE=$(python3 -c "import json; print(json.load(open('/tmp/result.json'))['date'])")
    mkdir -p memory/daily memory/briefings
    python3 $GITHUB_WORKSPACE/agent/save_briefing.py
    cp /tmp/result.json "memory/briefings/${DATE}.json"
    echo "✅ morning_briefing → memory/briefings/${DATE}.json"
    ;;
  delete_project_items)
    mkdir -p outbox
    cp /tmp/result.json outbox/delete_items_result.json
    echo "✅ delete結果 → outbox/delete_items_result.json"
    ;;
esac

# ハンドシェイク: .agent/last_run.json を更新
mkdir -p .agent
python3 -c "
import json, datetime
info = {'last_run': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'action': '${ACTION}', 'status': 'ok'}
open('.agent/last_run.json','w').write(json.dumps(info, indent=2))
"

git config user.name "github-actions"
git config user.email "actions@github.com"
git add -A
git diff --cached --quiet || git commit -m "agent[${ACTION}]: $(date '+%Y-%m-%dT%H:%M:%S') [skip ci]"
git push
echo "✅ private repo push完了"
