#!/bin/bash
set -e

PROJECT_ID="esa-summary"
REGION="asia-northeast1"
SERVICE_NAME="esa-summary"

echo "🔑 Secret Manager 設定スクリプト"
echo "----------------------------------------"
echo "各項目の値を入力してください。"
echo "（入力内容は画面には表示されませんが、記録されています）"
echo ""

# 関数: Secretを作成・更新する
create_secret() {
    local name=$1
    local prompt=$2
    
    echo ""
    read -s -p "${prompt}: " value
    echo ""
    
    if [ -z "$value" ]; then
        echo "⚠️  値が空のためスキップします"
        return
    fi

    # Secretが存在しない場合は作成
    if ! gcloud secrets describe "$name" --project="$PROJECT_ID" >/dev/null 2>&1; then
        gcloud secrets create "$name" --replication-policy=automatic --project="$PROJECT_ID"
    fi

    # 新しいバージョンを追加
    printf "%s" "$value" | gcloud secrets versions add "$name" --data-file=- --project="$PROJECT_ID" >/dev/null
    echo "✅ $name を更新しました"
}

# 各Secretの入力
create_secret "slack-bot-token" "Slack Bot Token (xoxb-...)"
create_secret "slack-app-token" "Slack App Token (xapp-...)"
create_secret "esa-access-token" "esa Access Token"
create_secret "esa-team-name" "esa Team Name"
create_secret "gemini-api-key" "Gemini API Key"
create_secret "esa-watch-channel-id" "監視するチャンネルID (例: C12345678)"
create_secret "esa-summary-channel-id" "要約を投稿するチャンネルID (例: C87654321)"

echo ""
echo "🚀 Cloud Run に設定を反映しています..."
echo "----------------------------------------"

gcloud run services update "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --update-secrets SLACK_BOT_TOKEN=slack-bot-token:latest,SLACK_APP_TOKEN=slack-app-token:latest,ESA_ACCESS_TOKEN=esa-access-token:latest,ESA_TEAM_NAME=esa-team-name:latest,GEMINI_API_KEY=gemini-api-key:latest,ESA_WATCH_CHANNEL_ID=esa-watch-channel-id:latest,ESA_SUMMARY_CHANNEL_ID=esa-summary-channel-id:latest \
  --update-env-vars LOG_LEVEL=INFO,GEMINI_MODEL=gemini-2.5-flash-lite

echo ""
echo "✅ 完了しました！"
