# 🛠️ 開発者ガイド

## 📋 目次
- [🏗️ アーキテクチャ概要](#️-アーキテクチャ概要)
- [⚙️ 環境セットアップ](#️-環境セットアップ)
- [🔧 コア技術スタック](#-コア技術スタック)
- [📊 データフロー](#-データフロー)
- [🧪 テスト戦略](#-テスト戦略)
- [🚀 デプロイメント](#-デプロイメント)
- [🔍 デバッグ・監視](#-デバッグ監視)
- [🤝 コントリビューション](#-コントリビューション)

---

## 🏗️ アーキテクチャ概要

### 🎯 システム設計思想
- **マイクロサービス指向**: 各機能を独立したサービスとして設計
- **AI中心アーキテクチャ**: Gemini AIを中核とした統一判定システム
- **プラグイン対応**: 新機能の容易な追加・削除
- **スケーラビリティ**: 負荷に応じた水平・垂直スケーリング対応

### 📐 レイヤー構造
```
┌─────────────────────────────────────┐
│          LINE Bot Interface         │ ← Webhook受信・応答送信
├─────────────────────────────────────┤
│         Message Handlers            │ ← メッセージルーティング・処理
├─────────────────────────────────────┤
│          AI Core System             │ ← Gemini AI統一判定・分析
├─────────────────────────────────────┤
│      Business Logic Services       │ ← 各機能サービス(通知/天気/検索等)
├─────────────────────────────────────┤
│        Infrastructure Layer        │ ← 設定管理・セキュリティ・監視
├─────────────────────────────────────┤
│         Data Persistence           │ ← ファイルベース永続化・キャッシュ
└─────────────────────────────────────┘
```

### 🔄 サービス間通信
```python
# 依存注入パターン
class MessageHandler:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.notification_service = NotificationService(
            gemini_service=self.gemini_service
        )
        self.auto_task_service = AutoTaskService(
            notification_service=self.notification_service,
            weather_service=self.weather_service
        )
```

---

## ⚙️ 環境セットアップ

### 🐍 Python環境
```bash
# Python 3.8+ 推奨
python --version  # 3.8.0+

# 仮想環境作成
python -m venv linebot_env
source linebot_env/bin/activate  # Unix
linebot_env\Scripts\activate     # Windows

# 依存パッケージインストール
pip install -r requirements.txt
```

### 🔑 環境変数設定
```bash
# .env ファイル作成
cat > .env << EOL
# 必須設定
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_ACCESS_TOKEN=your_line_access_token
GEMINI_API_KEY=your_gemini_api_key

# オプション設定
WEATHER_API_KEY=your_openweather_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# システム設定
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG
NOTIFICATION_CHECK_INTERVAL=5
EOL
```

### 🔧 IDE設定（VSCode推奨）
```json
// .vscode/settings.json
{
    "python.defaultInterpreter": "./linebot_env/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"]
}
```

---

## 🔧 コア技術スタック

### 📚 主要ライブラリ
```python
# requirements.txt 詳細
flask==2.3.3                    # Webフレームワーク
line-bot-sdk==3.5.0            # LINE Bot SDK
google-generativeai==0.3.1     # Gemini AI SDK
aiohttp==3.8.5                 # 非同期HTTP クライアント
requests==2.31.0               # HTTP クライアント
python-dotenv==1.0.0           # 環境変数管理
gunicorn==21.2.0               # WSGIサーバー
Werkzeug==2.3.7                # WSGI ユーティリティ
psutil==5.9.6                  # システム監視
pytz==2023.3                   # タイムゾーン
schedule==1.2.0                # タスクスケジューラー
```

### 🧠 AI・機械学習スタック
```python
# Gemini AI 設定
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

# 生成設定
generation_config = {
    'temperature': 0.3,         # 創造性 vs 一貫性
    'max_output_tokens': 1200,  # 最大出力トークン
    'top_p': 0.8,              # 核サンプリング
    'top_k': 40                # トップKサンプリング
}
```

### 🗄️ データ管理
```python
# ファイルベース永続化
storage_structure = {
    '/workspace/data/': {
        'notifications.json': 'ユーザー通知データ',
        'auto_tasks.json': '自動実行タスク',
        'auto_task_logs.json': 'タスク実行履歴',
        'conversation_memory/': 'ユーザー別対話履歴',
        'suggestions/': 'スマート提案データ',
        'performance_logs/': 'パフォーマンス監視ログ'
    }
}
```

---

## 📊 データフロー

### 🔄 メッセージ処理フロー
```
1. LINE Webhook → app.py
                    ↓
2. MessageHandler → handle_message()
                    ↓
3. GeminiService → analyze_text() [AI判定]
                    ↓
4. Intent routing → 各種サービス
                    ↓
5. Service execution → ビジネスロジック実行
                    ↓
6. Response generation → 応答メッセージ作成
                    ↓
7. LINE API → ユーザーに送信
```

### 🧠 AI判定システム
```python
def analyze_text(self, text: str, user_id: str) -> Dict[str, Any]:
    """統一AI判定システム"""
    
    # 1. 簡単パターン事前チェック（コスト最適化）
    simple_result = self._check_simple_patterns(text)
    if simple_result:
        return simple_result
    
    # 2. 対話履歴の取得
    conversation_context = self._get_conversation_context(user_id)
    
    # 3. Gemini AI による高度分析
    ai_result = self._unified_ai_analysis_with_context(text, user_id)
    
    # 4. 結果の後処理・検証
    validated_result = self._validate_and_format_result(ai_result)
    
    # 5. 行動記録（学習用）
    self._record_user_behavior(user_id, text, validated_result)
    
    return validated_result
```

### 📈 データ永続化フロー
```python
# 自動保存システム
class AutoSaveManager:
    def __init__(self, save_interval=30):
        self.save_interval = save_interval
        self.dirty_flags = {}
        self._start_auto_save_thread()
    
    def mark_dirty(self, service_name: str):
        """データ変更を記録"""
        self.dirty_flags[service_name] = True
    
    def auto_save_loop(self):
        """定期自動保存"""
        while True:
            for service_name, is_dirty in self.dirty_flags.items():
                if is_dirty:
                    self._save_service_data(service_name)
                    self.dirty_flags[service_name] = False
            time.sleep(self.save_interval)
```

---

## 🧪 テスト戦略

### 📋 テスト分類
```
1. Unit Tests (各サービス個別)
   ├── services/test_notification_service.py
   ├── services/test_auto_task_service.py
   ├── services/test_gemini_service.py
   └── handlers/test_message_handler.py

2. Integration Tests (サービス間連携)
   ├── test_ai_integration.py
   ├── test_notification_workflow.py
   └── test_auto_task_workflow.py

3. E2E Tests (エンドツーエンド)
   ├── test_complete_user_scenarios.py
   └── test_webhook_to_response.py

4. Performance Tests
   ├── test_response_time.py
   ├── test_memory_usage.py
   └── test_concurrent_users.py
```

### 🏃‍♂️ テスト実行
```bash
# 全テスト実行
python -m pytest tests/ -v

# 個別テスト
python test_auto_task_system.py
python test_enhanced_ai_system.py

# カバレッジ測定
pip install pytest-cov
python -m pytest --cov=services --cov=handlers

# パフォーマンステスト
python test_performance_load.py
```

### 🧪 テストデータ管理
```python
# テスト用フィクスチャ
@pytest.fixture
def mock_services():
    """テスト用サービスモック"""
    return {
        'gemini_service': Mock(),
        'notification_service': Mock(),
        'weather_service': Mock(),
        'search_service': Mock()
    }

@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータ"""
    return {
        'user_id': 'test_user_001',
        'notifications': [...],
        'conversation_history': [...]
    }
```

---

## 🚀 デプロイメント

### 🐳 Docker デプロイ
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  linebot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - LINE_ACCESS_TOKEN=${LINE_ACCESS_TOKEN}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/workspace/data
    restart: unless-stopped
```

### ☁️ Heroku デプロイ
```bash
# Heroku設定
heroku create your-linebot-app

# 環境変数設定
heroku config:set LINE_CHANNEL_SECRET=your_secret
heroku config:set LINE_ACCESS_TOKEN=your_token
heroku config:set GEMINI_API_KEY=your_key

# デプロイ
git push heroku main

# ログ確認
heroku logs --tail
```

### 🏗️ 本番環境設定
```python
# production.py
import os

class ProductionConfig:
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'
    
    # パフォーマンス設定
    GUNICORN_WORKERS = int(os.environ.get('WEB_CONCURRENCY', 2))
    GUNICORN_TIMEOUT = 120
    
    # セキュリティ設定
    RATE_LIMIT_ENABLED = True
    MAX_REQUESTS_PER_MINUTE = 10
    
    # データベース（将来用）
    DATABASE_URL = os.environ.get('DATABASE_URL')
```

---

## 🔍 デバッグ・監視

### 📊 ロギング設定
```python
# logging_config.py
import logging
import logging.handlers

def setup_logging(log_level='INFO'):
    """ログ設定"""
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ファイルハンドラー（ローテーション）
    file_handler = logging.handlers.RotatingFileHandler(
        'app.log', maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

### 📈 パフォーマンス監視
```python
# performance_monitoring.py
import time
import psutil
from collections import defaultdict

class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.active_timers = {}
    
    def start_timer(self, operation: str) -> str:
        """処理時間測定開始"""
        timer_id = f"{operation}_{int(time.time() * 1000000)}"
        self.active_timers[timer_id] = {
            'operation': operation,
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss
        }
        return timer_id
    
    def end_timer(self, operation: str, timer_id: str):
        """処理時間測定終了"""
        if timer_id in self.active_timers:
            timer_data = self.active_timers.pop(timer_id)
            duration = time.time() - timer_data['start_time']
            memory_delta = psutil.Process().memory_info().rss - timer_data['start_memory']
            
            self.metrics[operation].append({
                'duration': duration,
                'memory_delta': memory_delta,
                'timestamp': time.time()
            })
```

### 🚨 エラー監視・アラート
```python
# error_monitoring.py
import logging
import smtplib
from email.message import EmailMessage

class ErrorAlert:
    def __init__(self, alert_email=None):
        self.alert_email = alert_email
        self.error_count = defaultdict(int)
        self.last_alert_time = defaultdict(float)
    
    def log_error(self, error: Exception, context: dict = None):
        """エラーログ記録とアラート"""
        error_type = type(error).__name__
        self.error_count[error_type] += 1
        
        # 重大エラーの即座アラート
        if self._is_critical_error(error):
            self._send_alert(error, context)
        
        # ログ記録
        logging.error(f"{error_type}: {str(error)}", extra=context)
    
    def _is_critical_error(self, error: Exception) -> bool:
        """重大エラーの判定"""
        critical_errors = [
            'ConnectionError',
            'TimeoutError', 
            'DatabaseError',
            'ConfigurationError'
        ]
        return type(error).__name__ in critical_errors
```

---

## 🤝 コントリビューション

### 🔄 開発ワークフロー
```bash
# 1. フォーク・クローン
git clone https://github.com/your-username/linebot-project.git
cd linebot-project

# 2. 開発ブランチ作成
git checkout -b feature/new-ai-feature

# 3. 開発・テスト
# ... コード実装 ...
python -m pytest tests/

# 4. コミット
git add .
git commit -m "feat: Add new AI feature for document analysis"

# 5. プッシュ・プルリクエスト
git push origin feature/new-ai-feature
# GitHubでPR作成
```

### 📝 コードスタイル
```python
# PEP 8 準拠 + プロジェクト固有ルール

# 1. インポート順序
import os                    # 標準ライブラリ
import logging

from typing import Dict      # サードパーティ
from flask import Flask

from services.gemini_service import GeminiService  # プロジェクト内

# 2. 型ヒント必須
def process_message(text: str, user_id: str) -> Dict[str, Any]:
    """関数には必ず型ヒントとDocstring"""
    pass

# 3. クラス設計
class ServiceBase:
    """すべてのサービスは共通基底クラスを継承"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_input(self, data: Any) -> bool:
        """入力検証は必須実装"""
        raise NotImplementedError
```

### 🧪 テスト要件
```python
# テスト作成ガイドライン

class TestNewFeature:
    """新機能テストクラス"""
    
    def test_basic_functionality(self):
        """基本機能テスト（必須）"""
        pass
    
    def test_edge_cases(self):
        """境界値・エラーケース（必須）"""
        pass
    
    def test_integration(self):
        """他サービスとの連携（推奨）"""
        pass
    
    def test_performance(self):
        """パフォーマンス（重要機能は必須）"""
        pass
```

### 📋 PR チェックリスト
- [ ] 🧪 **テスト**: 新機能のテストが追加されている
- [ ] 📝 **ドキュメント**: README/機能ガイドが更新されている  
- [ ] 🎨 **コードスタイル**: PEP 8準拠・型ヒント付き
- [ ] 🔧 **後方互換性**: 既存機能に影響がない
- [ ] 🚀 **パフォーマンス**: 性能劣化がない
- [ ] 🛡️ **セキュリティ**: セキュリティリスクがない
- [ ] 📊 **ログ**: 適切なログ出力が追加されている

### 🎯 新機能開発ガイド
```python
# 新サービス追加のテンプレート

class NewFeatureService:
    """新機能サービステンプレート"""
    
    def __init__(self, gemini_service=None):
        self.logger = logging.getLogger(__name__)
        self.gemini_service = gemini_service
        
    def initialize(self) -> bool:
        """サービス初期化"""
        try:
            # 初期化処理
            self.logger.info("NewFeatureService initialized")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def process_request(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """メインの処理メソッド"""
        try:
            # 入力検証
            if not self._validate_input(user_input):
                return {'error': 'Invalid input'}
            
            # ビジネスロジック実行
            result = self._execute_business_logic(user_input, user_id)
            
            # 結果の整形
            formatted_result = self._format_result(result)
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Process request failed: {e}")
            return {'error': 'Internal error'}
    
    def _validate_input(self, user_input: str) -> bool:
        """入力検証（必須実装）"""
        return bool(user_input and user_input.strip())
    
    def _execute_business_logic(self, user_input: str, user_id: str) -> Any:
        """ビジネスロジック（サービス固有）"""
        raise NotImplementedError
    
    def _format_result(self, result: Any) -> Dict[str, Any]:
        """結果整形（必須実装）"""
        return {'result': result}
```

---

## 🎯 まとめ

この開発者ガイドは、高機能LINEチャットボットの技術的詳細と開発プロセスを包括的にカバーしています。新しい開発者がプロジェクトに参加する際や、既存機能を拡張する際の参考としてご活用ください。

質問や提案がある場合は、GitHubのIssueやプルリクエストでお気軽にお声がけください！🚀 