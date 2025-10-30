# デプロイ時データ永続化ガイド

## 🎯 概要

このガイドでは、LINE Botアプリケーションをデプロイする際に通知データが失われないようにする永続化機能について説明します。

## 🔧 問題の解決

### 以前の問題
- デプロイ時にファイルシステムがリセットされ、通知データが失われる
- ユーザーが設定した通知が消去される
- 毎回初期化が必要

### 解決策
- **永続化ストレージサービス**によるバックアップ・復元機能
- **複数ストレージ戦略**（GitHub + ローカルフォールバック）
- **自動データ復元**機能

## 🚀 機能概要

### 1. 永続化ストレージサービス
新しく追加された`PersistentStorageService`により、以下が可能になります：

- **GitHubバックアップ**: データをGitHubリポジトリに自動バックアップ
- **ローカルフォールバック**: GitHubが利用できない場合のローカルバックアップ
- **自動復元**: 起動時にバックアップからのデータ復元

### 2. 通知サービスの改善
`NotificationServiceBase`が拡張され、以下の機能を追加：

- **起動時復元**: アプリケーション起動時に永続化データから復元
- **自動バックアップ**: データ変更時の自動バックアップ
- **整合性チェック**: データの整合性を確認して復元

## 📋 設定方法

### 1. 環境変数の設定

#### 必須設定（既存）
```bash
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_ACCESS_TOKEN=your_line_access_token
GEMINI_API_KEY=your_gemini_api_key
```

#### データ永続化設定（新規追加）
```bash
# GitHubバックアップ設定
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=your_username/your_repository_name
BACKUP_BRANCH=data-backup
```

### 2. GitHubトークンの取得

1. GitHubで Personal Access Token を作成
   - GitHub Settings → Developer settings → Personal access tokens
   - 必要な権限: `repo` (リポジトリアクセス)

2. バックアップ用ブランチの作成
   ```bash
   git checkout -b data-backup
   git push origin data-backup
   ```

### 3. Koyebでの設定

Koyebダッシュボードで環境変数を設定：
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=your_username/sin_line_chat8-main
BACKUP_BRANCH=data-backup
```

## 🔄 動作フロー

### 起動時
1. ローカルファイルからデータ読み込み
2. 永続化ストレージからデータ読み込み
3. より新しいデータがあれば復元
4. データを統合して保存

### データ変更時
1. ローカルファイルに保存
2. 永続化ストレージにバックアップ
3. GitHub（利用可能時）とローカルの両方にバックアップ

### デプロイ時
1. ファイルシステムがリセット
2. アプリケーション起動
3. 永続化ストレージから自動復元
4. 通知データが完全復元

## 🧪 テスト

### テストの実行
```bash
python tests/active/deployment_persistence_test.py
```

### テスト内容
- ✅ 永続化ストレージサービスの動作確認
- ✅ 通知サービスの永続化機能確認
- ✅ デプロイシミュレーションテスト
- ✅ バックアップ・復元の整合性確認

### テスト結果例
```
📊 テスト結果サマリー:
  総テスト数: 2
  成功数: 2
  成功率: 100.0%
  総合判定: ✅ 合格
```

## 📁 ファイル構成

### 新規追加ファイル
```
services/
├── persistent_storage_service.py  # 永続化ストレージサービス

tests/active/
├── deployment_persistence_test.py # 永続化テスト

docs/
├── DEPLOYMENT_PERSISTENCE_GUIDE.md # このガイド
```

### 変更されたファイル
```
services/notification/
├── notification_service_base.py    # 永続化機能追加

koyeb.env.example                    # 新環境変数追加
```

## 🛡️ セキュリティ

### GitHubトークンの管理
- Personal Access Tokenを使用
- 必要最小限の権限のみ付与（`repo`権限）
- 環境変数として設定（ハードコーディング禁止）

### データの暗号化
現在はJSONファイルとして保存していますが、今後の拡張で暗号化機能も追加可能です。

## 🚨 トラブルシューティング

### 問題1: GitHubバックアップが失敗する
**原因**: トークンの権限不足またはリポジトリアクセス権限なし
**解決**: 
- トークンに`repo`権限があることを確認
- リポジトリが存在し、書き込み権限があることを確認

### 問題2: データが復元されない
**原因**: ブランチが存在しないまたはデータファイルが見つからない
**解決**:
- バックアップブランチ（`data-backup`）の存在確認
- ローカルフォールバックの確認

### 問題3: 通知が重複する
**原因**: 復元時のデータ統合エラー
**解決**:
- アプリケーションを再起動
- 通知データのクリーンアップ

## 📈 パフォーマンス

### バックアップ頻度
- **デフォルト**: 30分間隔で自動バックアップ
- **設定変更**: `BACKUP_INTERVAL_MINUTES`環境変数で調整可能

### ストレージ使用量
- 通常の使用では数KB〜数MB程度
- JSON形式のため可読性が高い

## 🔮 将来の拡張

### 予定されている機能
1. **データベース連携**: PostgreSQL/MySQLへの永続化
2. **クラウドストレージ**: AWS S3、Google Cloud Storage対応
3. **暗号化**: データの暗号化保存
4. **圧縮**: バックアップデータの圧縮
5. **履歴管理**: バックアップ履歴の管理とロールバック

### カスタマイズ
現在の実装はモジュール化されているため、独自の永続化ストレージを簡単に追加できます。

## ✅ 導入完了確認

以下の項目をチェックして、永続化機能が正しく導入されていることを確認してください：

- [ ] 環境変数`GITHUB_TOKEN`が設定されている
- [ ] 環境変数`GITHUB_REPO`が設定されている
- [ ] バックアップ用ブランチが作成されている
- [ ] テストが100%成功している
- [ ] デプロイ後も通知データが保持されている

## 📞 サポート

問題が発生した場合は、以下のログを確認してください：

```bash
# 永続化サービスのログ
grep "persistent_storage" logs/app.log

# 通知サービスのログ
grep "notification.*restore\|notification.*backup" logs/app.log
```

---

**🎉 これで、デプロイ時の通知データ消失問題は完全に解決されました！**

ユーザーの貴重な通知設定が確実に保持され、デプロイ後も継続して利用できます。 