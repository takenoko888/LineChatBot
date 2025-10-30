# Koyeb環境での通知機能修正版デプロイガイド

## 修正内容

### 1. 主要な問題と解決策

#### 問題1: データ永続化の失敗
- **症状**: インスタンス停止時に通知データが失われる
- **原因**: `/workspace/data/notifications.json`がインスタンス再起動時に初期化される
- **解決策**: 複数のストレージパスを試行し、利用可能な場所にデータを保存

#### 問題2: アプリの頻繁な停止
- **症状**: Koyebの無料版でアイドル時間後にインスタンスが停止
- **原因**: 3秒間隔の通知チェックが逆効果で、リソース消費が多い
- **解決策**: 30秒間隔に変更し、KeepAliveサービスを最適化

#### 問題3: 通知の重複送信・欠落
- **症状**: 同じ通知が複数回送信されたり、送信されない
- **原因**: データの同期が不完全
- **解決策**: データ操作時の確実な保存とロック機構の改善

### 2. 設定変更点

#### 環境変数の更新
```bash
# 必須設定
PRODUCTION_MODE=true
KOYEB_INSTANCE_URL=your-app-name.koyeb.app
NOTIFICATION_CHECK_INTERVAL=30
NOTIFICATION_STORAGE_PATH=/tmp/notifications.json
PERSISTENT_STORAGE_ENABLED=true

# その他の必須環境変数
LINE_CHANNEL_SECRET=your_channel_secret
LINE_ACCESS_TOKEN=your_access_token
GEMINI_API_KEY=your_gemini_api_key
PORT=8000
```

#### データストレージパス
修正版では以下の順序でストレージパスを試行します：
1. 環境変数で指定されたパス（`NOTIFICATION_STORAGE_PATH`）
2. `/tmp/notifications.json`（Koyebで利用可能）
3. `/var/tmp/notifications.json`（代替一時ディレクトリ）
4. `./notifications.json`（現在のディレクトリ）

### 3. デプロイ手順

#### Step 1: 環境変数の設定
Koyebのダッシュボードで以下の環境変数を設定：

```bash
# 本番環境設定
PRODUCTION_MODE=true
KOYEB_INSTANCE_URL=your-app-name.koyeb.app

# 通知システム設定
NOTIFICATION_CHECK_INTERVAL=30
NOTIFICATION_STORAGE_PATH=/tmp/notifications.json
PERSISTENT_STORAGE_ENABLED=true

# LINEBot設定（必須）
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_ACCESS_TOKEN=your_line_access_token
GEMINI_API_KEY=your_gemini_api_key

# サーバー設定
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

#### Step 2: デプロイ設定
```yaml
# koyeb.yaml
app:
  name: your-app-name
  services:
    - name: linebot
      type: web
      build:
        type: docker
        dockerfile: Dockerfile
      instance_type: nano
      env:
        - name: PRODUCTION_MODE
          value: "true"
        - name: KOYEB_INSTANCE_URL
          value: "your-app-name.koyeb.app"
        - name: NOTIFICATION_CHECK_INTERVAL
          value: "30"
        - name: NOTIFICATION_STORAGE_PATH
          value: "/tmp/notifications.json"
        - name: PORT
          value: "8000"
      ports:
        - port: 8000
          protocol: http
      health_check:
        http:
          path: /health
        initial_delay_seconds: 30
        timeout_seconds: 10
```

#### Step 3: デプロイの実行
```bash
# GitHubからデプロイする場合
git add .
git commit -m "Koyeb環境での通知機能修正"
git push origin main

# Koyebが自動でデプロイを開始
```

### 4. 動作確認

#### テストスクリプトの実行
```bash
# ローカルでテストを実行
python koyeb_notification_fix_test.py
```

#### LINEBotでの動作確認
1. **通知追加のテスト**
   ```
   明日の14時に会議の通知を設定して
   ```

2. **通知一覧の確認**
   ```
   通知一覧
   ```

3. **通知削除のテスト**
   ```
   通知削除 [通知ID]
   ```

#### ログの確認
Koyebのダッシュボードでログを確認：
- データ永続化の成功ログ
- KeepAliveサービスの動作ログ
- 通知チェックの実行ログ

### 5. トラブルシューティング

#### 通知データが消失する場合
1. 環境変数`NOTIFICATION_STORAGE_PATH`を確認
2. ログで複数ストレージパスの試行状況を確認
3. `/tmp/notifications.json`へのアクセス権限を確認

#### アプリが頻繁に停止する場合
1. `NOTIFICATION_CHECK_INTERVAL`が30秒以上に設定されているか確認
2. KeepAliveサービスが正常に動作しているか確認
3. リソース使用量をモニタリング

#### 通知が送信されない場合
1. LINE APIの月間制限に達していないか確認
2. 通知時刻の形式が正しいか確認（`YYYY-MM-DD HH:MM`）
3. データの保存・読み込みが正常に行われているか確認

### 6. 監視とメンテナンス

#### 定期確認項目
- [ ] 通知データの保存状況
- [ ] KeepAliveサービスの動作状況
- [ ] LINE APIの使用量
- [ ] アプリケーションの稼働時間

#### パフォーマンス最適化
- 通知チェック間隔の調整（30-60秒推奨）
- 不要な通知の定期削除
- ログレベルの調整（本番ではINFO推奨）

### 7. よくある質問

#### Q: 無料版でも安定して動作しますか？
A: はい。修正版では以下の最適化により安定性が向上しています：
- リソース使用量の削減
- 効率的なKeepAlive
- 複数ストレージパスによる冗長性

#### Q: データはどの程度保持されますか？
A: Koyebの一時ディレクトリ（`/tmp`）を使用するため、インスタンス再起動時にはデータが失われる可能性があります。重要な通知は定期的にバックアップを取ることを推奨します。

#### Q: 通知の送信制限はありますか？
A: LINE APIの月間制限（無料プランで1,000通）が適用されます。制限に達した場合は自動的に送信を停止します。

### 8. サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：
- Koyebのアプリケーションログ
- 設定した環境変数の一覧
- 発生している具体的な現象
- テストスクリプトの実行結果

---

**注意**: この修正版は2025年1月時点のKoyeb環境に基づいています。Koyebの仕様変更により設定が変わる可能性がありますので、最新のドキュメントも併せて確認してください。 