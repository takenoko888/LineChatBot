# 🎯 機能別詳細ガイド

## 📋 目次
- [🔔 通知・リマインダー機能](#-通知リマインダー機能)
- [🤖 自動実行・モニタリング機能](#-自動実行モニタリング機能)
- [🧠 AI学習・提案機能](#-ai学習提案機能)
- [💭 対話履歴管理](#-対話履歴管理)
- [🌤️ 天気情報機能](#️-天気情報機能)
- [🔍 検索機能](#-検索機能)
- [⚙️ システム管理機能](#️-システム管理機能)

---

## 🔔 通知・リマインダー機能

### 📍 ファイル場所
- **メインサービス**: `services/notification_service.py` (988行)
- **関連ユーティリティ**: `utils/date_utils.py`, `utils/context_utils.py`

### 🎯 主要機能

#### 🗣️ 自然言語による通知設定
```
入力例:
- 「毎日7時に起きる」
- 「明日の15時に会議」
- 「3時間後に薬を飲む」
- 「毎週月曜9時にミーティング」
- 「来月の1日に家賃支払い」

出力: 
✅ 通知を設定しました: [詳細]
```

#### 🧠 文脈を考慮したリマインダー最適化
- **過去の行動パターン分析**: ユーザーの通知履歴から最適なタイミングを提案
- **重複通知の検出**: 類似する通知の自動検出と統合提案
- **優先度の自動調整**: 文脈に基づく重要度判定

#### 📊 通知管理機能
```
コマンド例:
- 「通知一覧」→ 設定済み通知の表示
- 「重要な通知のみ」→ 高優先度通知のフィルター
- 「通知削除 n_123」→ 特定通知の削除
- 「全通知削除」→ 全通知の一括削除
```

### 🔧 技術仕様

#### データ構造
```python
class Notification:
    notification_id: str
    user_id: str
    title: str
    message: str
    datetime: datetime
    priority: str  # 'high', 'medium', 'low'
    repeat_pattern: str  # 'none', 'daily', 'weekly', 'monthly'
    is_active: bool
    context_metadata: Dict[str, Any]
```

#### 主要メソッド
- `add_notification_from_text()`: 自然言語からの通知作成
- `analyze_notification_patterns()`: パターン分析
- `optimize_reminder_based_on_context()`: 文脈最適化
- `process_natural_language_input()`: 自然言語処理

---

## 🤖 自動実行・モニタリング機能

### 📍 ファイル場所
- **メインサービス**: `services/auto_task_service.py` (497行)
- **依存関係**: `schedule` ライブラリ

### 🎯 主要機能

#### ⏰ 定期実行タスク
```
サポートするタスクタイプ:
1. 天気配信 (weather_daily): 毎日の天気情報配信
2. ニュース配信 (news_daily): キーワードベースニュース
3. キーワードモニタリング (keyword_monitor): 監視・アラート
4. 使用レポート (usage_report): 定期統計レポート
```

#### 📅 スケジュールパターン
- **daily**: 毎日指定時刻 (例: 07:00)
- **weekly**: 毎週月曜日指定時刻
- **hourly**: 毎時実行

#### 🎮 使用例
```
👤 「毎日7時に天気を配信して」
🤖 ✅ 自動実行タスクを作成しました
   📋 毎日の天気配信
   ⏰ スケジュール: daily 07:00
   🆔 タスクID: task_user123_20240523_070000

👤 「自動実行一覧」
🤖 🤖 自動実行タスク一覧
   1. 毎日の天気配信
      📊 実行回数: 15回
      🔄 状態: ✅ 有効
```

### 🔧 技術仕様

#### データ構造
```python
@dataclass
class AutoTask:
    task_id: str
    user_id: str
    task_type: str
    title: str
    description: str
    schedule_pattern: str
    schedule_time: str
    parameters: Dict[str, Any]
    is_active: bool = True
    execution_count: int = 0
```

#### 主要メソッド
- `create_auto_task()`: タスク作成
- `_execute_task()`: タスク実行
- `start_scheduler()`: スケジューラー開始
- `_schedule_task()`: タスクのスケジュール登録

---

## 🧠 AI学習・提案機能

### 📍 ファイル場所
- **メインサービス**: `services/smart_suggestion_service.py` (543行)
- **統合サービス**: `services/gemini_service.py`

### 🎯 主要機能

#### 💡 スマート提案
```
提案タイプ:
1. タイミング最適化: 通知時刻の改善提案
2. グループ化: 関連タスクの統合提案  
3. スケジュール最適化: 効率的なスケジュール
4. 機能活用: 未使用機能の提案
```

#### 📊 行動パターン学習
- **使用頻度分析**: よく使う機能の特定
- **時間帯分析**: アクティブな時間帯の把握
- **成功パターン**: 効果的な設定の学習

#### 🎮 使用例
```
👤 「おすすめは？」
🤖 🎯 あなたへのスマート提案

   🕐 タイミング最適化:
   ・朝の通知を6:30に変更すると効果的

   📋 グループ化提案:
   ・「会議」関連の通知を統合しませんか？

   ⚡ 新機能活用:
   ・自動天気配信を試してみませんか？
```

### 🔧 技術仕様

#### データ構造
```python
@dataclass 
class Suggestion:
    suggestion_id: str
    user_id: str
    suggestion_type: str
    title: str
    description: str
    confidence: float
    data: Dict[str, Any]
```

---

## 💭 対話履歴管理

### 📍 ファイル場所
- **メインサービス**: `services/conversation_memory_service.py` (475行)

### 🎯 主要機能

#### 🔄 会話の記憶・継続
- **対話履歴の保存**: ユーザーとの会話を長期記憶
- **文脈の理解**: 前の会話を踏まえた応答
- **ユーザープロファイル**: 好みや習慣の学習

#### 📊 利用パターン分析
```
分析項目:
- よく使う機能
- アクティブな時間帯
- コミュニケーションスタイル
- 好みのトピック
```

#### 🎮 使用例
```
👤 「前回何話した？」
🤖 📝 最近の会話履歴
   
   💬 昨日 14:30: 天気予報について
   💬 昨日 09:15: 会議の通知設定
   💬 一昨日 18:45: ニュース検索

👤 「利用パターン確認」  
🤖 📊 あなたの利用パターン
   - 総会話数: 127回
   - よく使う機能: 通知, 天気, 検索
   - よく使う時間: 9時, 18時
```

---

## 🌤️ 天気情報機能

### 📍 ファイル場所
- **メインサービス**: `services/weather_service.py` (376行)
- **API**: OpenWeather API

### 🎯 主要機能

#### 🌡️ 現在の天気
- **リアルタイム情報**: 気温、湿度、風速
- **体感温度**: AIによる体感予測
- **服装アドバイス**: 天気に基づく提案

#### 📅 天気予報
- **5日間予報**: 詳細な予報データ
- **時間別予報**: 3時間ごとの詳細
- **警報・注意報**: 気象警報の通知

#### 🎮 使用例
```
👤 「東京の天気」
🤖 🌤️ 東京の天気情報
   
   🌡️ 現在: 25°C 晴れ
   💨 風速: 3m/s
   💧 湿度: 60%
   
   👕 今日の服装: 半袖がおすすめ
   ☂️ 降水確率: 10%

👤 「明日の天気予報」
🤖 📅 明日の天気予報
   
   🌅 朝(6-12時): 22°C 曇り
   🌞 昼(12-18時): 28°C 晴れ  
   🌙 夜(18-24時): 24°C 曇り
```

---

## 🔍 検索機能

### 📍 ファイル場所
- **メインサービス**: `services/search_service.py` (421行)
- **API**: Google Custom Search API

### 🎯 主要機能

#### 🌐 ウェブ検索
- **一般検索**: Google検索との統合
- **ニュース検索**: 最新ニュース特化
- **画像検索**: 画像コンテンツ取得

#### 🤖 AI要約・分析
- **検索結果要約**: Gemini AIによる自動要約
- **重要ポイント抽出**: 必要な情報の抽出
- **関連情報提案**: 追加の検索提案

#### 🔗 表示改善
- **クリッカブルリンク**: タップでサイトアクセス
- **ドメイン名表示**: 信頼性の確認
- **スニペット**: 内容のプレビュー

#### 🎮 使用例
```
👤 「最新のAIニュース」
🤖 🔍 検索結果: "AI ニュース"

   📰 1. ChatGPT新機能リリース
   📝 OpenAIが新たなマルチモーダル機能を発表...
   🔗 https://openai.com/news (openai.com)

   📰 2. Google AI の最新動向  
   📝 Bard の機能拡張により、より自然な対話が...
   🔗 https://blog.google/ai (blog.google)

   🤖 AI要約:
   AI業界では新機能リリースが相次ぎ、
   特にマルチモーダル技術への注目が高まっている。
```

---

## ⚙️ システム管理機能

### 📍 ファイル場所
- **設定管理**: `core/config_manager.py` (286行)
- **セキュリティ**: `core/security_utils.py` (220行)
- **監視**: `utils/performance_monitor.py` (273行)
- **管理者**: `handlers/admin_handler.py` (331行)

### 🎯 主要機能

#### ⚙️ 設定管理
```python
# 機能のON/OFF
features = {
    'weather': True,
    'search': True, 
    'notifications': True,
    'auto_tasks': True,
    'performance_monitoring': True
}
```

#### 🛡️ セキュリティ
- **入力サニタイズ**: XSS攻撃防止
- **レート制限**: API濫用防止  
- **署名検証**: Webhook改ざん防止
- **エラーハンドリング**: 安全なエラー処理

#### 📊 パフォーマンス監視
```
監視項目:
- 応答時間
- エラー率
- メモリ使用量
- API呼び出し回数
```

#### 👨‍💼 管理者機能
```
管理者コマンド:
- 「system status」: システム状態確認
- 「performance report」: パフォーマンスレポート
- 「config show」: 設定表示
- 「logs recent」: 最近のログ確認
```

---

## 🔧 開発者向け情報

### 📋 各サービスの依存関係
```
app.py
├── handlers/
│   ├── message_handler.py
│   └── admin_handler.py
├── services/
│   ├── gemini_service.py (中核)
│   ├── notification_service.py
│   ├── auto_task_service.py
│   ├── smart_suggestion_service.py
│   ├── conversation_memory_service.py
│   ├── weather_service.py
│   └── search_service.py
└── core/
    ├── config_manager.py
    ├── security_utils.py
    └── line_bot_base.py
```

### 🧪 テスト対象
- **unit tests**: 各サービスの個別機能
- **integration tests**: サービス間連携
- **e2e tests**: エンドツーエンドシナリオ
- **performance tests**: 負荷・応答時間

### 📝 ログ・デバッグ
```python
# ログレベル設定
LOG_LEVEL=DEBUG  # DEBUG/INFO/WARNING/ERROR

# 主要ログ出力箇所
- services/*.py: 各機能の実行ログ
- handlers/*.py: メッセージ処理ログ  
- core/*.py: システムレベルログ
```

---

## 🎯 まとめ

この高機能LINEチャットボットは、7つの主要サービスが連携して動作する包括的なAIアシスタントシステムです。各機能は独立性を保ちながら、必要に応じて他のサービスと連携し、ユーザーに最適な体験を提供します。

詳細な実装については各ソースコードファイルをご確認ください。🚀 