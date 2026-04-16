# Cloud Run デプロイ自動化 トラブルシューティングレポート

このドキュメントでは、`esa-summarizer` プロジェクトの Cloud Run デプロイ自動化構築中に発生した問題とその解決策を詳細に記録します。

## 1. Artifact Registry リポジトリの未作成

### 発生した問題
Docker イメージのプッシュに失敗し、デプロイが開始されませんでした。
**エラー:** `denied: Unauthenticated request`（またはターゲットが見つからない旨のエラー）

### 原因
`setup_automation.sh` スクリプトで Artifact Registry API の有効化は行っていましたが、実際にイメージを保存する「リポジトリ（`esa-summarizer-repo`）」を作成する手順が抜けていました。

### 解決策
`gcloud` コマンドを使用して手動でリポジトリを作成しました。
```bash
gcloud artifacts repositories create esa-summarizer-repo \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="Docker repository for esa-summarizer" \
  --project=esa-summary
```

---

## 2. サービスアカウント作成の反映待ち

### 発生した問題
`setup_automation.sh` 実行時、サービスアカウント作成直後に「サービスアカウントが存在しない」というエラーで停止しました。
**エラー:** `INVALID_ARGUMENT: Service account ... does not exist.`

### 原因
Google Cloud 側でサービスアカウントが作成されてから、IAM ポリシーの設定が可能になるまでにわずかなタイムラグ（反映待ち時間）があるため、スクリプトの処理が早すぎて失敗しました。

### 解決策
スクリプトに `sleep 10` コマンドを追加し、作成後 10 秒間待機してから権限付与を行うように修正しました。

---

## 3. Workload Identity Federation: 属性条件と認証エラー

### 発生した問題
GitHub Actions が Google Cloud への認証に失敗しました。
**エラー:** `{"error":"unauthorized_client","error_description":"The given credential is rejected by the attribute condition."}`

### 原因
Workload Identity Provider に設定されていた属性条件（セキュリティチェック）が、GitHub Actions から送られてくる情報（クレーム）と一致しませんでした。特に `repository_owner` のチェックがうまくいっていませんでした。

### 解決策
1.  **属性条件の変更:** OIDC の標準的な識別子である `sub`（サブジェクト）クレームをチェックするように変更しました。
2.  **デバッグ:** 一時的に発行元（`iss`）のみをチェックするように条件を緩めて接続確認を行いました。
3.  **最終設定:** プロバイダ側では GitHub Actions からのトークンを信頼し、具体的なアクセス制御は後述の IAM バインディングで行う構成にしました。

---

## 4. サービスアカウントへのなりすまし（IAM バインディング）

### 発生した問題
認証自体は成功しましたが、その後の「サービスアカウントとして振る舞う（なりすまし）」処理で権限エラーが発生しました。
**エラー:** `Permission 'iam.serviceAccounts.getAccessToken' denied on resource`

### 原因
サービスアカウントの IAM ポリシー設定において、GitHub Actions の ID を許可する記述（バインディング）が正しくマッチしていませんでした。当初の `principalSet://.../attribute.repository/...` という記述では正しく権限が渡っていませんでした。

### 解決策
特定の GitHub Actions（`uhey77/esa-summarizer` リポジトリの `main` ブランチ）を直接指名する `principal://` 形式のバインディングを追加しました。
```bash
gcloud iam service-accounts add-iam-policy-binding "github-actions-deployer@..." \
  --role="roles/iam.workloadIdentityUser" \
  --member="principal://iam.googleapis.com/.../subject/repo:uhey77/esa-summarizer:ref:refs/heads/main"
```

---

## 5. Cloud Run からの Secret Manager アクセス権限不足

### 発生した問題
デプロイの最終段階、Cloud Run サービスが起動しようとした際にエラーが発生しました。
**エラー:** `Permission denied on secret: ... The service account used must be granted the 'Secret Manager Secret Accessor' role`

### 原因
Cloud Run の実行用サービスアカウント（`github-actions-deployer`）に、Secret Manager から機密情報を読み取る権限が付与されていませんでした。デプロイ権限（`run.admin`）はありましたが、実行時のシークレット参照権限（`secretmanager.secretAccessor`）が不足していました。

### 解決策
サービスアカウントに `roles/secretmanager.secretAccessor` ロールを追加付与しました。
```bash
gcloud projects add-iam-policy-binding esa-summary \
  --member="serviceAccount:github-actions-deployer@..." \
  --role="roles/secretmanager.secretAccessor"
```

## 現状のまとめ
- **Artifact Registry:** 作成済み、正常稼働。
- **認証 (Authentication):** Workload Identity Federation が正しく設定されています。
- **認可 (Authorization):** GitHub Actions がサービスアカウントになりすます設定が完了しています。
- **実行時権限:** サービスアカウントに必要な権限（Cloud Run 管理、Secret 参照など）がすべて付与されています。

これにより、デプロイパイプラインは完全に動作する状態となりました。