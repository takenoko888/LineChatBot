# 🤖 高機能LINEチャットボット with Gemini AI

## 📋 プロジェクト概要

Google Gemini AIを活用した高機能LINEチャットボットアプリケーションです。自然言語処理、自動実行タスク、高度な通知管理、天気情報、検索機能など、豊富なAI機能を提供します。

- **提供価値**
  - 顧客体験向上: 対話的UIと通知自動化で継続利用を促進
  - 業務効率化: 予約・リマインド・FAQの自動化による工数削減
  - 拡張性: 天気・検索・外部API連携をモジュール追加で迅速拡張

- **セキュリティ/運用**
  - シークレットは `.env`/環境変数管理。リポジトリに機密は含めません
  - 署名検証、入力サニタイズ、レート制限、例外の安全処理を実装
  - `GET /health`, `GET /metrics` で稼働/性能を可視化し、運用を標準化

- **最近のAI活用（コード編集の自動化/半自動化）**
  - 最近では、コード編集をAIに任せ、開発者は設計・レビューと最終判断に注力しています
  - プロセス: 要件定義 → TODO化 → 自動編集 → 静的解析/フォーマット → テスト → PR → レビュー/承認 → デプロイ
  - ガードレール: 変更範囲の限定、型/リンタ準拠、コミット規約、CIテスト、差分レビュー、ロールバック手順を徹底
  - 成果: 修正リードタイム短縮、欠陥密度低下、レビューに注力可能な体制を実現

- **導入パターン**
  - 最小導入: 通知/検索/天気の有効化と運用監視
  - 標準導入: LINE公式アカウント運用＋業務タスクの自動化
  - 拡張導入: DB/RAG連携やワークフローDAGによる業務プロセス自動化

## 🌟 主要機能

### 🔔 **高度な通知・リマインダー機能**
- **自然言語による通知設定**: 「毎日7時に起きる」「明日の15時に会議」
- **文脈を考慮したリマインダー最適化**: AIが最適なタイミングを提案
- **類似通知パターンの自動分析**: 重複防止・効率化提案
- **優先度管理**: 高・中・低の優先度設定
- **繰り返し通知**: 毎日・毎週・毎月の定期通知

### 🤖 **自動実行・モニタリング機能**
- **天気配信**: 毎日指定時刻に天気情報を自動配信
- **ニュース配信**: キーワードベースのニュース自動配信
- **キーワードモニタリング**: 特定キーワードの監視・アラート
- **使用レポート**: 定期的な使用統計レポート
- **スケジュール管理**: daily/weekly/hourly パターンサポート

### 🧠 **AI学習・提案機能**
- **スマート提案**: 使用パターンからの最適化提案
- **対話履歴**: 会話を記憶して文脈を考慮した応答
- **行動パターン学習**: ユーザーの習慣を学習して改善提案
- **コンテキスト提案**: 現在の会話に基づく関連提案

### 🌤️ **天気情報機能**
- **現在の天気**: リアルタイム天気情報
- **天気予報**: 詳細な予報データ
- **天気に基づくアドバイス**: AIによる服装・行動提案
- **定期天気通知**: 指定時刻での自動配信

### 🔍 **検索機能**
- **ウェブ検索**: Google検索統合
- **ニュース検索**: 最新ニュース取得
- **AI要約**: 検索結果の自動要約
- **URL表示改善**: クリッカブルリンクとドメイン名表示

### ⚡ **AI駆動動的機能生成システム**
- **自然言語からの自動機能生成**: ユーザーの要求をAIが解析して機能を自動生成
- **リアルタイム機能実装**: 要求された機能を即座に作成・実行
- **曖昧性解消**: ユーザーの曖昧な表現を検出して明確化
- **コンテキスト追跡**: 会話の文脈を理解して最適な機能を提供
- **機能管理**: 生成された機能の登録・管理・バージョン制御
- **安全実行**: サンドボックス環境での安全な機能実行

### 📊 **高度なコンテキスト管理**
- **会話記憶**: 過去の会話履歴を記憶して文脈考慮
- **ユーザー行動パターン学習**: 個人の使用パターンを学習
- **インテント予測**: ユーザーの意図を事前予測
- **文脈適応**: 状況に応じた最適な応答生成

## 🏗️ プロジェクト構造

```
LineChatBot/
├── 📱 app.py                           # アプリケーションエントリーポイント
├── 📊 requirements.txt                 # 依存パッケージ
├── 🐳 docker-compose.yml / Dockerfile  # Docker設定
├── 📚 README.md                        # プロジェクト概要
├── 📚 docs/design/dynamic_feature_system_design.md  # 動的機能システム設計
│
├── 🧠 core/                           # コアシステム
│   ├── line_bot_base.py               # LINE Bot基盤機能
│   ├── config_manager.py              # 設定管理システム
│   ├── security_utils.py              # セキュリティユーティリティ
│   ├── function_call_loop.py          # 関数呼び出しループ
│   ├── function_dispatcher.py         # 関数ディスパッチャー
│   ├── function_registry.py           # 関数レジストリ
│   └── register_default_functions.py  # デフォルト関数登録
│
├── 🎯 handlers/                       # メッセージ処理
│   ├── message_handler.py             # メインメッセージ処理
│   └── admin_handler.py               # 管理者機能処理
│
├── 🚀 services/                       # 主要サービス
│   ├── 🤖 gemini_service.py           # Gemini AI統合サービス
│   ├── 🔔 notification_service.py     # 高度な通知管理
│   ├── ⏰ auto_task_service.py        # 自動実行・モニタリング
│   ├── 🧠 smart_suggestion_service.py # スマート提案システム
│   ├── 💭 conversation_memory_service.py # 対話履歴管理
│   ├── 🌤️ weather_service.py          # 天気情報サービス
│   ├── 🔍 search_service.py           # 検索機能サービス
│   ├── 🎯 dynamic_feature_service.py  # 動的機能生成サービス
│   ├── ⚡ enhanced_dynamic_feature_service.py # 強化動的機能サービス
│   ├── 🧠 enhanced_semantic_service.py # 強化意味解析サービス
│   ├── 🔍 ambiguity_resolution_service.py # 曖昧性解決サービス
│   ├── 📊 context_tracking_service.py # コンテキスト追跡サービス
│   ├── 💾 persistent_storage_service.py # 永続ストレージサービス
│   ├── 📈 activity_service.py         # 活動監視サービス
│   ├── 🔄 keepalive_service.py        # キープアライブサービス
│   └── 📁 notification/               # 通知関連サービス
│       ├── notification_model.py      # 通知データモデル
│       └── notification_service_base.py # 通知サービス基盤
│
└── 🛠️ utils/                          # ユーティリティ
    ├── date_utils.py                  # 日付処理
    ├── command_utils.py               # コマンド解析
    ├── context_utils.py               # コンテキスト管理
    └── performance_monitor.py         # パフォーマンス監視
```

## 🎮 使用例

### 📝 通知・リマインダー
```
👤 「毎日7時に起きる」
🤖 「✅ 通知を設定しました: 毎日7時に起床リマインダー」

👤 「明日の15時に病院予約」
🤖 「✅ 通知を設定しました: 2024-05-24 15:00 病院予約」

👤 「通知一覧」
🤖 「📋 設定済み通知一覧...」
```

### 🤖 自動実行タスク
```
👤 「毎日7時に天気を配信して」
🤖 「✅ 自動実行タスクを作成しました
     📋 毎日の天気配信
     ⏰ スケジュール: daily 07:00」

👤 「毎朝AIニュースを送って」
🤖 「✅ ニュース配信タスクを設定しました」
```

### ⚡ AI駆動動的機能生成
```
👤 「毎日の天気予報を自動で通知する機能を作って」
🤖 「✅ 新しい機能を生成しました
     🎯 機能名: daily_weather_notification
     📝 説明: 毎日指定時刻に天気情報を通知
     ⏰ 実行: 毎日 07:00」

👤 「曖昧な表現だけど、なんか便利な機能を作って」
🤖 「❓ もう少し具体的に教えてください
     💡 提案: 以下のような機能が考えられます
     ・自動翻訳機能
     ・スケジュール管理機能
     ・リマインダー最適化機能
     どれにしますか？」

👤 「今日のニュースをまとめて」
🤖 「✅ カスタム機能を生成中...
     🎯 機能名: daily_news_summary
     📝 説明: 今日の主要ニュースを自動収集・要約
     🔧 実行環境: 安全に構築中...」
```

### 🌤️ 天気・検索
```
👤 「東京の天気」
🤖 「🌤️ 東京: 25°C 晴れ
     今日は過ごしやすい天気です！」

👤 「最新のAIニュース」
🤖 「🔍 検索結果: "AI ニュース"
     📰 [最新記事一覧と要約]」
```

## ⚙️ セットアップ・環境構築

### 🔑 必要な環境変数
```env
# LINE設定（必須）
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_ACCESS_TOKEN=your_line_access_token

# AI設定（必須）
GEMINI_API_KEY=your_gemini_api_key

# オプション設定
WEATHER_API_KEY=your_openweather_api_key
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id  # ← 環境変数名に注意
NGROK_AUTHTOKEN=your_ngrok_token        # 開発時トンネリングに使用（任意）

# ストレージ設定（Dockerでの永続化推奨）
NOTIFICATION_STORAGE_PATH=/workspace/data/notifications.json

# システム設定
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### 🚀 インストール手順

#### 1. **標準インストール**
```bash
# リポジトリクローン
git clone https://github.com/takenoko888/LineChatBot.git
cd LineChatBot

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
# .envファイルを作成して必要な変数を設定

# アプリケーション起動
python app.py
```

#### 2. **Docker実行**
```bash
# Docker Composeで起動
docker-compose up --build

# または単体でDockerビルド
docker build -t linebot .
docker run -p 8000:8000 --env-file .env linebot
```

補足: 通知データを永続化するには、`.env` または `docker-compose.yml` で
`NOTIFICATION_STORAGE_PATH=/workspace/data/notifications.json` を設定し、
ホストボリュームを `./data:/workspace/data` のようにマウントしてください。

#### 3. **Herokuデプロイ**
```bash
# Heroku CLI設定
heroku create your-app-name

# 環境変数設定
heroku config:set LINE_CHANNEL_SECRET=your_secret
heroku config:set LINE_ACCESS_TOKEN=your_token
heroku config:set GEMINI_API_KEY=your_key

# デプロイ
git push heroku main
```

## 🔧 設定カスタマイズ

### 🎛️ 機能ON/OFF設定
```python
# core/config_manager.py または config.json で設定
features = {
    'weather': True,                    # 天気機能
    'search': True,                     # 検索機能
    'notifications': True,              # 通知機能
    'auto_tasks': True,                 # 自動実行機能
    'quick_reply': True,                # クイックリプライ
    'performance_monitoring': True      # パフォーマンス監視
}
```

### 📊 パフォーマンス設定
```env
# チェック間隔・制限設定
NOTIFICATION_CHECK_INTERVAL=5    # 通知チェック間隔（秒）
MAX_NOTIFICATIONS_PER_USER=100  # ユーザー当たり最大通知数
MAX_MESSAGE_LENGTH=5000         # 最大メッセージ長
MAX_REQUESTS_PER_MINUTE=10      # レート制限
```

## 🧪 テスト・品質管理

### 🏃‍♂️ テスト実行
```bash
# すべてのテストを実行（推奨）
pytest -q

# 例: 特定のディレクトリ/ファイル
tests/active -q
tests/specific/test_auto_task_system.py -q

# 新機能テスト
python scripts/integration_test.py
python scripts/test_dynamic_feature_system.py
python scripts/test_enhanced_system.py
python scripts/real_api_test.py

# 包括的システムテスト
python scripts/ultimate_system_test.py

# 動的機能システム専用テスト
python scripts/simple_test_dynamic_system.py
python scripts/standalone_test.py
```

### 🧪 テスト構成
- **active/**: 現在アクティブな包括的テストスイート
- **legacy/**: 過去バージョンのテスト（参照用）
- **integration/**: 統合テスト
- **specific/**: 特定機能に特化したテスト
- **results/**: テスト実行結果の記録

### 📊 テスト対象機能
- **動的機能生成システム**: AIによる自動機能生成テスト
- **曖昧性解決**: ユーザーの曖昧表現解消テスト
- **コンテキスト追跡**: 会話文脈管理テスト
- **拡張セマンティック解析**: 高度な意味解析テスト
- **統合システム**: 全機能連携テスト

## 📚 技術仕様・API詳細

### 🧠 AI判定システム
- **統一AI判定**: 全入力をGemini AIが解析
- **意図認識**: 15種類の機能意図を自動判定
- **信頼度スコア**: 判定の確実性を数値化
- **コンテキスト考慮**: 過去の会話を踏まえた判定

### 🔄 データ管理
- **JSON永続化**: 既定はファイルベース（`NOTIFICATION_STORAGE_PATH` で変更可）
- **メモリ管理**: 効率的なデータキャッシュ
- **バックアップ**: 必要に応じてボリュームへ永続化
- **将来拡張**: DB統合（PostgreSQL）を想定

### 🛡️ セキュリティ
- **入力サニタイズ**: XSS攻撃防止
- **レート制限**: API濫用防止
- **署名検証**: Webhook改ざん防止
- **エラーハンドリング**: 安全なエラー処理

## 📊 パフォーマンス最適化

### ⚡ 高速化施策
- **AI判定最適化**: 簡単パターンの事前チェック
- **キャッシュ機能**: 頻繁なデータの一時保存
- **非同期処理**: バックグラウンドタスク実行
- **リソース管理**: メモリ・CPU使用量最適化

### 📈 監視・分析
- **リアルタイム監視**: 応答時間・エラー率追跡
- **使用統計**: 機能利用パターン分析
- **アラート機能**: 異常検知時の自動通知

### 🧑‍💻 運用エンドポイント
- `GET /health`: ヘルスチェック
- `GET /metrics`: 簡易メトリクス（処理時間等）
- `GET /keepalive`: KeepAlive 状態
- `GET /keepalive/stats`: KeepAlive 統計
- `POST /keepalive/ping`: KeepAlive 手動実行
- `GET /activity/stats`: Activity サービス統計

## 🤝 開発・貢献

### 🔄 開発ワークフロー
1. **Issue作成**: 機能追加・バグ報告
2. **ブランチ作成**: `feature/機能名` または `fix/修正内容`
3. **実装・テスト**: コード実装とテスト追加
4. **プルリクエスト**: レビュー依頼
5. **マージ**: レビュー後の統合

### 📝 コミット規約
```
feat: 新機能追加
fix: バグ修正
refactor: リファクタリング
docs: ドキュメント更新
test: テスト追加・修正
perf: パフォーマンス改善
```

### 🧪 品質基準
- **テストカバレッジ**: 80%以上維持
- **コードレビュー**: 必須
- **ドキュメント更新**: 機能変更時は必須
- **パフォーマンステスト**: 重要機能は必須

## 📈 ロードマップ（実装状況）

### ✅ **実装済み機能**

#### 1) AI駆動動的機能生成システム
- ✅ **自然言語からの自動機能生成**: ユーザーの要求をAIが解析して機能を自動生成
- ✅ **リアルタイム機能実装**: 要求された機能を即座に作成・実行
- ✅ **曖昧性解消**: ユーザーの曖昧な表現を検出して明確化
- ✅ **コンテキスト追跡**: 会話の文脈を理解して最適な機能を提供
- ✅ **機能管理**: 生成された機能の登録・管理・バージョン制御
- ✅ **安全実行**: サンドボックス環境での安全な機能実行

#### 2) 高度なコンテキスト管理
- ✅ **会話記憶**: 過去の会話履歴を記憶して文脈考慮
- ✅ **ユーザー行動パターン学習**: 個人の使用パターンを学習
- ✅ **インテント予測**: ユーザーの意図を事前予測
- ✅ **文脈適応**: 状況に応じた最適な応答生成

#### 3) システム基盤強化
- ✅ **永続ストレージ**: JSONベースのデータ永続化
- ✅ **拡張サービスアーキテクチャ**: モジュール化されたサービス設計
- ✅ **包括的テストスイート**: 統合テスト・単体テストの整備

### 🔄 **進行中の拡張**

#### 1) データベース統合
- 🔄 JSON永続化からDB（PostgreSQL）へ移行検討中
- 🔄 通知/自動タスクのジョブキュー（Celery/Redis）実装準備中
- 効果: 可用性・スケール・リトライ耐性の向上

#### 2) RAGナレッジベース
- 🔄 PDF/URL/Drive/Notion等の外部文書取り込み準備中
- 🔄 ベクトル検索＋Gemini統合による根拠付き回答システム開発中
- 効果: 精度・一貫性の向上、出典提示

#### 3) ワークフローDAG
- 🔄 「検索→要約→翻訳→通知」等のワークフロー定義準備中
- 🔄 可視化・スケジュール実行システム設計中
- 効果: 定型業務の自動化と運用の見える化

## 🚀 今後の拡張予定

### 💡 追加可能な機能
- 📖 **ドキュメント解析**: PDF・Word文書のAI解析
- 🎨 **画像認識**: 画像内容認識・OCR・物体検出
- 📊 **データ分析**: CSV・Excel自動分析・可視化
- 🌐 **多言語翻訳**: リアルタイム翻訳・言語検出
- 🎯 **意思決定サポート**: AI による選択肢比較・推奨

### 🔧 システム改善
- **データベース統合**: PostgreSQL・MongoDB対応
- **マイクロサービス化**: 機能別サービス分離
- **API公開**: REST API・GraphQL エンドポイント
- **UI拡張**: Web管理画面・ダッシュボード

## 📞 サポート・連絡先

### 🆘 トラブルシューティング
- **ログ確認**: アプリケーションログの確認方法
- **環境変数**: 設定値の確認・更新手順
- **API制限**: 各種APIの利用制限と対処法

### 🔗 関連リンク
- **Gemini AI ドキュメント**: [Google AI Studio](https://ai.google.dev/)
- **LINE Developers**: [LINE Bot SDK](https://developers.line.biz/)
- **OpenWeather API**: [天気API](https://openweathermap.org/api)

---

## 📄 ライセンス

MIT License（本リポジトリに LICENSE を同梱）

---

## 🎉 開発完了

✅ **全主要機能実装完了**  
✅ **包括的テスト実施完了**  
✅ **ドキュメント整備完了**  
✅ **本番環境対応完了**  

高機能AIチャットボットとして、即座に利用開始できる状態です！🚀
