# SETUP.md — 初回セットアップガイド

このシステムを新しい環境で使い始めるための手順書。

---

## Step 1: Gmail アカウント

1. Gmail アカウントを作成（または既存のものを使用）
2. **PC版 Gmail** を開く
3. 設定（歯車アイコン）→「すべての設定を表示」
4. 「機能」タブ → **「ネットワーク外部通信を許可」** をオン

> これにより Claude が Gmail 経由で外部と通信できるようになります（将来の通知機能用）。

---

## Step 2: GitHub Personal Access Token (PAT) 生成

1. GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)**
2. 「Generate new token (classic)」
3. 以下のスコープにチェック:
   - `repo` (全て)
   - `project` (read:project + write:project)
   - `workflow`
4. Expiration: 必要に応じて設定（推奨: No expiration または1年）
5. **生成されたトークンをコピーして安全な場所に保存**

---

## Step 3: GitHub Actions シークレット設定

以下の2つのリポジトリにシークレットを設定する。

### tokistorage/tokistorage（Actionsエンジン）
1. https://github.com/tokistorage/tokistorage/settings/secrets/actions
2. 「New repository secret」
3. Name: `PAT_TOKEN` / Value: 生成したPAT

### tokistorage/tr（確認用、不要な場合はスキップ）
- 基本的に Actions は tokistorage/tokistorage 側で動くので不要

---

## Step 4: Claude Project 設定

### 4-1. プロジェクト作成
1. claude.ai → Projects → 「New project」
2. プロジェクト名: 例「tokistorage agent」

### 4-2. ファイル追加
プロジェクトに以下のファイルを追加する。

**`token.txt`** — GitHub PAT
```
ghp_xxxxxxxxxxxxxxxxxxxxx
```

**`repos.txt`** — リポジトリ一覧
```
# 公開リポジトリ
https://github.com/tokistorage/tokistorage.git
https://github.com/tokistorage/tokistorage.github.io.git
https://github.com/tokistorage/lp.git
https://github.com/tokistorage/qr.git

# 非公開リポジトリ
https://github.com/tokistorage/tr.git
```

### 4-3. プロジェクト指示（Project instructions）
以下をプロジェクト設定の「Instructions」に貼り付ける:

```
あなたは tokistorage の専属エージェントです。

## 起動手順
ユーザーから最初のリクエストを受けたら、必ず以下を実行してから応答してください:

1. PAT（token.txt）を読み込む
2. git clone https://{PAT}@github.com/tokistorage/tokistorage.git でリポジトリをクローン
3. CLAUDE.md を読んでポリシーと全体構造を確認する
4. git clone https://{PAT}@github.com/tokistorage/tr.git で記憶リポジトリをクローン
5. tr/memory/context/claude-flow.md と tr/memory/daily/[今日の日付].md を読む
6. tr/project/cache/project.json でプロジェクト状況を確認する
7. ユーザーのリクエストに応答する

## 基本姿勢
- 記憶を活かす: 毎回 tr/memory/ を確認する
- 作業後は write_memory アクションで日次ログを更新する
- 日本語で応答する
```

---

## Step 5: 動作確認

プロジェクトを開いて「おはよう」と入力する。

Claude が以下の順に動くはず:
1. token.txt を読む
2. tokistorage/tokistorage をクローンして CLAUDE.md を読む
3. tokistorage/tr をクローンして記憶を読む
4. 短期計画のサマリーを表示する

---

## トラブルシューティング

### Actions が動かない
- PAT_TOKEN シークレットが設定されているか確認
- PAT のスコープに `repo` と `project` が含まれているか確認
- Actions が有効になっているか確認: リポジトリ → Settings → Actions → Allow all actions

### git clone が失敗する
- PAT が正しいか確認
- PAT の有効期限が切れていないか確認

### tr リポジトリが見えない
- PAT に `repo` スコープが含まれているか確認（private repo へのアクセスに必要）

