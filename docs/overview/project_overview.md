# プロジェクト概要

## 全体構造

このプロジェクトは、LINE Botアプリケーションを構築するためのものです。主な機能は、Gemini AIによる自然言語処理、高度な通知管理、天気情報提供、および検索機能です。

```
sin_line_chat_7/
├── .gitignore
├── app.py                  # アプリケーションのエントリーポイント
├── docker-compose.yml    # Docker Compose設定ファイル
├── Dockerfile             # Dockerビルドファイル
├── Procfile               # Herokuデプロイ用設定ファイル
├── README.md              # プロジェクトの概要と説明
├── requirements.txt       # 依存パッケージリスト
├── config/                # 設定ファイル（将来用）
├── core/                  # コア機能モジュール
│   ├── __init__.py
│   └── line_bot_base.py   # LINE Botの基本機能を提供するベースクラス
├── handlers/              # メッセージハンドラー
│   ├── __init__.py
│   └── message_handler.py # メッセージ処理ロジック
├── services/              # 各種サービスモジュール
│   ├── __init__.py
│   ├── gemini_service.py   # Gemini AIサービス
│   ├── notification_service.py # 通知管理サービス
│   ├── search_service.py   # 検索サービス
│   └── weather_service.py  # 天気情報サービス
├── static/                # 静的ファイル（将来用）
│   └── robots.txt
├── templates/             # HTMLテンプレート（将来用）
│   └── index.html
└── utils/                 # ユーティリティモジュール
    ├── __init__.py
    ├── command_utils.py    # コマンド解析ユーティリティ
    ├── context_utils.py    # コンテキスト管理ユーティリティ
    └── date_utils.py      # 日付処理ユーティリティ
```

## 各モジュールの詳細

### `app.py`

アプリケーションのエントリーポイント。Flaskアプリケーションを初期化し、LINE BotのWebhookエンドポイントを設定します。

- **主要クラス**: `LineBot`
  - `__init__`: 各種サービスとユーティリティを初期化
  - `handle_message_event`: メッセージイベントを処理し、適切なサービスにディスパッチ
  - `_check_required_env`: 必須の環境変数が設定されているか確認
  - `_initialize_services`: 各種サービス（通知、天気、検索）を初期化
  - `_setup_message_handler`: メッセージハンドラーを設定

### `core/`

#### `line_bot_base.py`

LINE Botの基本機能を提供するベースクラス。

- **主要クラス**: `LineBotBase`
  - `__init__`: LINE Bot APIの初期化
  - `send_message`: ユーザーにメッセージを送信
  - `reply_message`: メッセージに返信
  - `get_quick_reply_items`: クイックリプライ項目を生成
  - `handle_webhook`: Webhookリクエストを処理
  - `validate_signature`: 署名を検証

### `handlers/`

#### `message_handler.py`

メッセージ処理ロジックを実装。

- **主要クラス**: `MessageHandler`
  - `handle_message`: メッセージイベントを処理し、適切なサービスにディスパッチ
  - `_generate_help_message`: ヘルプメッセージを生成
  - `format_error_message`: エラーメッセージを生成

### `services/`

#### `gemini_service.py`

Gemini AIサービスとの連携を実装。

- **主要クラス**: `GeminiService`
  - `__init__`: Gemini AIモデルを初期化
  - `parse_notification_request`: 通知リクエストを解析
  - `suggest_notification_format`: エラー時にユーザーへの提案を生成
  - `validate_notification_time`: 通知時刻の妥当性を検証
  - `analyze_text`: テキストを解析してコンテキストを抽出
  - `enhance_natural_language_processing`: 自然言語処理を拡張

#### `notification_service.py`

高度な通知管理機能を実装。
- **高度な通知機能:**
  - 文脈を考慮したリマインダー最適化
  - 自然言語による柔軟なリマインダー設定
  - 類似通知パターンの自動分析・提案
- **主要クラス**: `NotificationService`
  - `__init__`: 通知データを初期化
  - `add_notification_from_text`: テキストから通知を追加
  - `_load_notifications`: 保存された通知データを読み込む
  - `_save_notifications`: 通知データを保存
  - `add_notification`: 新しい通知を追加
  - `get_notification`: 指定された通知を取得
  - `update_notification`: 通知を更新
  - `delete_notification`: 通知を削除
  - `get_notifications`: 通知を検索して取得
  - `format_notification_list`: 通知リストを整形
  - `process_natural_language_input`: 自然言語入力を処理し、最適化された通知内容を取得
  - `analyze_notification_patterns`: 類似通知パターンを分析
  - `optimize_reminder_based_on_context`: 文脈に基づいてリマインダーを最適化

#### `search_service.py`

検索機能を実装。

- **主要クラス**: `SearchService`
  - `__init__`: 検索サービスを初期化
  - `search`: 検索を実行
  - `format_search_results`: 検索結果を整形
  - `get_enhanced_results`: 拡張検索結果を取得
  - `format_enhanced_results`: 拡張検索結果を整形
  - `close`: リソースをクリーンアップ

#### `weather_service.py`

天気情報機能を提供。

- **主要クラス**: `WeatherService`
  - `__init__`: 天気サービスを初期化
  - `get_current_weather`: 現在の天気を取得
  - `get_weather_forecast`: 天気予報を取得
  - `format_weather_message`: 天気情報を整形
  - `format_forecast_message`: 天気予報を整形
  - `_get_weather_emoji`: 天気に対応する絵文字を取得
  - `_get_temperature_emoji`: 気温に対応する絵文字を取得

### `utils/`

#### `command_utils.py`

コマンド解析ユーティリティ。

- **主要クラス**: `CommandUtils`
  - `parse_command`: テキストからコマンドとパラメータを抽出
  - `_determine_command_type`: コマンドタイプを判定
  - `_extract_parameters`: テキストからパラメータを抽出
  - `_parse_search_options`: 検索オプションをパース
  - `_parse_edit_options`: 編集オプションをパース
  - `_parse_notification_options`: 通知オプションをパース
  - `_parse_weather_options`: 天気オプションをパース
  - `_parse_search_query`: 検索クエリをパース
  - `format_command_help`: コマンドのヘルプメッセージを生成

#### `context_utils.py`

コンテキスト管理ユーティリティ。

- **主要クラス**: `ContextUtils`
  - `add_context`: コンテキストを追加
  - `get_recent_contexts`: 最近のコンテキストを取得
  - `clear_contexts`: コンテキストをクリア
  - `get_context_summary`: コンテキストのサマリーを生成
  - `analyze_context`: コンテキストを分析
  - `save_contexts`: コンテキストをファイルに保存
  - `load_contexts`: コンテキストをファイルから読み込み
  - `get_conversation_state`: 会話の状態を取得
  - `analyze_conversation_context`: 会話の流れからユーザーの意図を推定
  - `extract_user_preferences`: 会話履歴からユーザーの好みや設定を抽出

#### `date_utils.py`

日付処理ユーティリティ。

- **主要クラス**: `DateUtils`
  - `parse_natural_datetime`: 自然言語の日時表現を解析
  - `format_datetime`: 日時を指定された形式で整形
  - `get_next_occurrence`: 次回の発生日時を計算
  - `is_valid_datetime`: 日時が有効か検証
  - `get_relative_time_description`: 相対的な時間表現を生成

## 今後の開発のための推奨事項

1. **エラーハンドリングの強化**: 各モジュールで発生する可能性のある例外をより詳細に処理し、ユーザーに適切なフィードバックを提供できるようにする。
2. **ログ記録の改善**: 重要なイベントやエラーについて、より詳細なログを記録する。
3. **テストの拡充**: 各モジュールのユニットテストと統合テストを追加し、コードの品質を向上させる。
4. **機能拡張**: ユーザーからのフィードバックに基づいて、新しい機能を追加する。例えば、TODO管理機能や、より高度な自然言語処理機能など。
5. **パフォーマンスの最適化**: 大量のデータを扱う場合や、高頻度のリクエストが発生する場合に備えて、パフォーマンスのボトルネックを特定し、最適化を行う。
6. **セキュリティ対策**: ユーザーデータの保護や、不正アクセスの防止など、セキュリティ対策を強化する。
7. **ドキュメントの充実**: コードの変更に合わせて、READMEや内部ドキュメントを常に最新の状態に保つ。

## 注意点

- **APIキーの管理**: 各種APIキー（LINE, Gemini, OpenWeather, Google）は環境変数で管理されています。これらのキーを安全に保管し、外部に漏らさないように注意してください。
- **依存パッケージの更新**: `requirements.txt`に記載されているパッケージは定期的に更新し、セキュリティパッチや新機能の恩恵を受けられるようにしてください。
- **Herokuデプロイ**: Herokuへのデプロイ手順はREADMEに記載されていますが、変更があった場合は適宜更新してください。
- **データ永続化**: 現在、通知データはファイルに保存されています。より堅牢なデータストレージ（データベースなど）への移行を検討してください。

## 高度な通知機能について
このプロジェクトでは、以下の高度な通知機能が実装されています。
- **文脈を考慮したリマインダー最適化:** 会話履歴やユーザーの行動パターンに基づいて、通知のタイミングや優先度を自動的に調整します。
- **自然言語による柔軟なリマインダー設定:** 自然な言葉で通知を設定できます。例えば、「明日の朝7時に会議の通知」や「3時間後に会議」のように指定できます。
- **類似通知パターンの自動分析・提案:** 過去の通知履歴から類似パターンを検出し、重複通知を避けたり、より適切な通知タイミングを提案します。

これらの機能は、以下のモジュールで実装されています。
- `services/notification_service.py`
- `utils/context_utils.py`
- `services/gemini_service.py`

## テストについて
統合テストは`app.py`に追加されており、以下のテストケースが含まれています。
- 「明日の朝7時に会議の通知」
- 「毎日18時に夕食の準備」
- 「来週の月曜日に病院の予約」
- 「3時間後に会議」
- 「会議の時間を1時間遅らせて」
- 「この通知は重要」
- 「明日の朝7時に打ち合わせの通知」

## データモデル拡張について
`services/notification/notification_model.py`に`context_metadata`フィールドと`add_optimization_record`メソッドが追加されました。