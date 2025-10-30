# Koyebデプロイメントガイド

## 概要
このガイドでは、LINE Bot Applicationを Koyeb にデプロイする手順を説明します。

## 事前準備

### 1. 必要なAPIキー・トークンの取得
以下の情報を準備してください：

- **LINE Bot設定**
  - `LINE_CHANNEL_SECRET`: LINE Developersコンソールから取得
  - `LINE_ACCESS_TOKEN`: LINE Developersコンソールから取得

- **AI機能 (必須)**
  - `GEMINI_API_KEY`: Google AI Studioから取得

- **検索機能 (オプション)**
  - `GOOGLE_API_KEY`: Google Cloud Consoleから取得
  - `SEARCH_ENGINE_ID`: Custom Search Engineから取得

- **天気機能 (オプション)**
  - `WEATHER_API_KEY`: OpenWeatherMapから取得

### 2. リポジトリ準備
GitHubリポジトリが最新の状態になっていることを確認してください。

## Koyebデプロイ手順

### ステップ1: Koyebアカウント設定
1. [Koyeb](https://app.koyeb.com)にアクセスしてアカウントを作成
2. GitHubアカウントと連携

### ステップ2: アプリケーション作成
1. Koyebダッシュボードで「Create App」をクリック
2. 「Deploy from Git repository」を選択
3. GitHubリポジトリを選択: `takenoko888/sin_sin_linechat2`

### ステップ3: デプロイ設定

#### 基本設定
- **App name**: `line-bot-ai-assistant`
- **Service name**: `web`
- **Region**: `Frankfurt` (推奨)

#### ビルド設定
- **Build method**: `Dockerfile`
- **Dockerfile**: `Dockerfile`
- **Build context**: `/`

#### 実行設定
- **Port**: `5000`
- **Health check path**: `/`

#### 環境変数設定
以下の環境変数を設定してください：

```bash
# 必須設定
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_ACCESS_TOKEN=your_line_access_token
GEMINI_API_KEY=your_gemini_api_key

# システム設定
PORT=5000
PYTHONUNBUFFERED=1

# オプション設定（持っている場合のみ）
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id
WEATHER_API_KEY=your_weather_api_key

# 機能フラグ（必要に応じて調整）
NOTIFICATIONS_ENABLED=true
AUTO_TASKS_ENABLED=true
PERFORMANCE_MONITORING_ENABLED=true
```

#### リソース設定
- **Instance type**: `nano` (512MB RAM, 0.1 vCPU)
- **Scaling**: `Min: 1, Max: 2`

### ステップ4: デプロイ実行
1. 「Deploy」ボタンをクリック
2. ビルドログを確認
3. デプロイ完了を待機

### ステップ5: LINE Webhook設定
1. デプロイが完了したらKoyebアプリのURLを取得
2. LINE Developersコンソールでwebhook URLを設定：
   ```
   https://your-app-name-your-service.koyeb.app/callback
   ```
3. Webhook URLの検証を実行

## トラブルシューティング

### よくある問題と解決方法

#### 1. ビルドエラー
```
Error: Could not find requirements.txt
```
**解決方法**: リポジトリにrequirements.txtが存在することを確認

#### 2. 起動エラー
```
Application failed to start
```
**解決方法**: 
- 環境変数が正しく設定されているか確認
- ログでエラー詳細を確認
- Procfileの設定を確認

#### 3. LINE Webhook検証エラー
```
Webhook URL verification failed
```
**解決方法**:
- アプリが正常に起動しているか確認
- `/callback`エンドポイントが正常に応答するか確認
- LINE_CHANNEL_SECRETが正しく設定されているか確認

#### 4. メモリ不足エラー
**解決方法**:
- インスタンスタイプをより大きなものに変更
- Gunicornのワーカー数を削減

### デバッグ用コマンド

#### ログ確認
Koyebダッシュボードでアプリケーションのログを確認できます。

#### ヘルスチェック
```bash
curl https://your-app-name-your-service.koyeb.app/
```

#### LINE Webhook テスト
```bash
curl -X POST https://your-app-name-your-service.koyeb.app/callback \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

## 設定ファイル詳細

### Dockerfile最適化ポイント
- マルチステージビルドでイメージサイズ削減
- 非rootユーザーでセキュリティ向上
- ヘルスチェック機能付き

### Procfile設定詳細
```
web: gunicorn app:app --log-file=- --log-level=debug --workers=2 --threads=4 --timeout=60 --worker-class=gthread --max-requests=1000 --max-requests-jitter=50 --preload
```

**パラメータ説明**:
- `--workers=2`: ワーカープロセス数（nanoインスタンス用）
- `--threads=4`: スレッド数
- `--timeout=60`: タイムアウト設定
- `--max-requests=1000`: メモリリーク対策

## 本番運用の注意点

### 1. 監視
- Koyebの監視ダッシュボードを定期的に確認
- アプリケーションログを監視
- レスポンス時間とエラー率を確認

### 2. セキュリティ
- 環境変数にAPIキーを直接記載しない
- 定期的にAPIキーをローテーション
- LINE Webhookの署名検証を有効化

### 3. パフォーマンス
- 必要に応じてインスタンスタイプをアップグレード
- 定期的にアプリケーションを再起動（メモリリーク対策）

### 4. バックアップ
- 通知データの定期バックアップ
- 設定の文書化

## コスト最適化

### Koyeb料金
- nano instance: 月額約$5.5
- CPU使用量に基づく従量課金

### 節約方法
- 不要な機能を無効化
- スケーリング設定を最適化
- 定期的なリソース使用量確認

## サポート

### 問題が発生した場合
1. Koyebダッシュボードでログを確認
2. GitHub Issuesで報告
3. 環境変数設定を再確認

### 機能拡張
新機能を追加する場合は、以下の順序で実行：
1. ローカルでテスト
2. GitHubにプッシュ
3. Koyebで自動デプロイ

---

## 設定チェックリスト

- [ ] GitHubリポジトリが最新
- [ ] 必要なAPIキーを全て取得
- [ ] Koyebアカウント作成
- [ ] 環境変数設定完了
- [ ] デプロイ実行
- [ ] LINE Webhook設定
- [ ] 機能テスト実行
- [ ] 監視設定

このガイドに従ってデプロイを実行することで、安定したLINE Botの運用が可能になります。 