# Cloud Run デプロイ手順（Slack Socket Mode 常駐）

## 0. 初期設定
- Cloud SDK インストール: https://cloud.google.com/sdk/docs/install
- ログイン＆プロジェクト/リージョン設定
  ```bash
  gcloud auth login
  gcloud config set project <PROJECT_ID>
  gcloud config set compute/region asia-northeast1   # 任意リージョン
  ```
- API 有効化
  ```bash
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
  ```

## 1. Secret Manager に機密値を登録
`.env` の値を Secret として作成（例）。値は都度入力。
```bash
gcloud secrets create slack-bot-token --replication-policy=automatic
printf "<SLACK_BOT_TOKEN>\n" | gcloud secrets versions add slack-bot-token --data-file=-

gcloud secrets create slack-app-token --replication-policy=automatic
printf "<SLACK_APP_TOKEN>\n" | gcloud secrets versions add slack-app-token --data-file=-

gcloud secrets create esa-access-token --replication-policy=automatic
printf "<ESA_ACCESS_TOKEN>\n" | gcloud secrets versions add esa-access-token --data-file=-

gcloud secrets create esa-team-name --replication-policy=automatic
printf "<ESA_TEAM_NAME>\n" | gcloud secrets versions add esa-team-name --data-file=-

gcloud secrets create gemini-api-key --replication-policy=automatic
printf "<GEMINI_API_KEY>\n" | gcloud secrets versions add gemini-api-key --data-file=-

# チャンネルIDも Secret 化
gcloud secrets create esa-watch-channel-id --replication-policy=automatic
printf "<ESA_WATCH_CHANNEL_ID>\n" | gcloud secrets versions add esa-watch-channel-id --data-file=-

gcloud secrets create esa-summary-channel-id --replication-policy=automatic
printf "<ESA_SUMMARY_CHANNEL_IDs_COMMA_SEPARATED>\n" | gcloud secrets versions add esa-summary-channel-id --data-file=-
```

## 2. Artifact Registry リポジトリを作成（初回のみ）
```bash
gcloud artifacts repositories create esa-summarizer-repo \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="esa summarizer images"
```

## 3. Cloud Build でビルド & プッシュ
リポジトリ直下で実行。
```bash
IMAGE="asia-northeast1-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/esa-summarizer-repo/esa-summarizer:latest"
gcloud builds submit --tag "$IMAGE"
```

## 4. Cloud Run にデプロイ
Socket Mode 用にスケールゼロを防ぐ設定を推奨。
```bash
gcloud run deploy esa-summarizer \
  --image "$IMAGE" \
  --region asia-northeast1 \
  --platform managed \
  --port 8080 \
  --min-instances 1 \
  --cpu-throttling=never \
  --allow-unauthenticated
```
※ 外部公開不要なら `--ingress internal` を検討。

## 5. Secrets/環境変数を反映
```bash
gcloud run services update esa-summarizer \
  --region asia-northeast1 \
  --update-secrets \
    SLACK_BOT_TOKEN=slack-bot-token:latest,\
    SLACK_APP_TOKEN=slack-app-token:latest,\
    ESA_ACCESS_TOKEN=esa-access-token:latest,\
    ESA_TEAM_NAME=esa-team-name:latest,\
    GEMINI_API_KEY=gemini-api-key:latest,\
    ESA_WATCH_CHANNEL_ID=esa-watch-channel-id:latest,\
    ESA_SUMMARY_CHANNEL_ID=esa-summary-channel-id:latest \
  --update-env-vars LOG_LEVEL=INFO,DEBUG_VERBOSE=false,PORT=8080
```

## 6. Secret Manager へのアクセス権付与
Cloud Run 実行サービスアカウントに Secret 参照権限を付与。
```bash
SA="$(gcloud run services describe esa-summarizer --region asia-northeast1 --format='value(spec.template.spec.serviceAccount)')"
gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" \
  --member="serviceAccount:${SA}" \
  --role="roles/secretmanager.secretAccessor"
```

## 7. 動作確認
- Cloud Run のログで `⚡️ Bolt app is running!` などが出ているか確認。
- Slack 側で Bot がチャンネル参加済み／Socket Mode 有効か確認。
- `curl https://<cloud-run-url>/` でヘルス応答が返ることを確認。
