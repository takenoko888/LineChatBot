"""
Configuration management system
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class AppConfig:
    """アプリケーション設定"""
    # LINE Bot設定
    line_channel_secret: str = ""
    line_access_token: str = ""
    
    # AI設定
    gemini_api_key: str = ""
    
    # オプションサービス設定
    weather_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    
    # システム設定
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    
    # 通知設定（プラットフォーム安全な既定パス: ./data/notifications.json）
    notification_storage_path: str = os.path.join(os.getcwd(), 'data', 'notifications.json')
    notification_check_interval: int = 30  # 30秒間隔に変更してリソース節約しつつアクティブ維持
    max_notifications_per_user: int = 100
    
    # Koyeb本番環境設定
    production_mode: bool = False
    koyeb_instance_url: Optional[str] = None
    persistent_storage_enabled: bool = True
    
    # パフォーマンス設定
    max_message_length: int = 5000
    request_timeout: int = 30
    max_retries: int = 3
    
    # セキュリティ設定
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 10
    
    # 機能フラグ
    features: Dict[str, bool] = field(default_factory=lambda: {
        'weather': True,
        'search': True,
        'notifications': True,
        'auto_tasks': True,
        'quick_reply': True,
        'performance_monitoring': True
    })

class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初期化
        
        Args:
            config_file (Optional[str]): 設定ファイルのパス
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file or os.getenv('CONFIG_FILE', 'config.json')
        self.config = AppConfig()
        
        # 設定を読み込み
        self._load_config()

    def _load_config(self) -> None:
        """設定を読み込み"""
        # 環境変数から設定を読み込み
        self._load_from_env()
        
        # 設定ファイルから読み込み（存在する場合）
        if os.path.exists(self.config_file):
            self._load_from_file()
        
        # 設定の検証
        self._validate_config()
        
        self.logger.info("設定の読み込みが完了しました")

    def _load_from_env(self) -> None:
        """環境変数から設定を読み込み"""
        # 必須設定
        self.config.line_channel_secret = os.getenv('LINE_CHANNEL_SECRET', '')
        self.config.line_access_token = os.getenv('LINE_ACCESS_TOKEN', '')
        self.config.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        
        # オプション設定
        self.config.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.config.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.config.google_search_engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        # システム設定
        self.config.port = int(os.getenv('PORT', '8000'))
        self.config.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.config.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # 通知設定（Windowsでも安全なデフォルト: ./data/notifications.json）
        default_data_dir = os.getenv('DATA_DIR', os.path.join(os.getcwd(), 'data'))
        try:
            os.makedirs(default_data_dir, exist_ok=True)
        except Exception:
            # 作成失敗時はユーザーディレクトリ配下にフォールバック
            from pathlib import Path
            default_data_dir = os.path.join(str(Path.home()), 'sin_line_chat8_data')
            os.makedirs(default_data_dir, exist_ok=True)

        self.config.notification_storage_path = os.getenv(
            'NOTIFICATION_STORAGE_PATH',
            os.path.join(default_data_dir, 'notifications.json')
        )
        self.config.notification_check_interval = int(os.getenv('NOTIFICATION_CHECK_INTERVAL', '30'))
        self.config.max_notifications_per_user = int(os.getenv('MAX_NOTIFICATIONS_PER_USER', '100'))
        
        # Koyeb本番環境設定
        self.config.production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
        self.config.koyeb_instance_url = os.getenv('KOYEB_INSTANCE_URL')
        self.config.persistent_storage_enabled = os.getenv('PERSISTENT_STORAGE_ENABLED', 'true').lower() == 'true'
        
        # パフォーマンス設定
        self.config.max_message_length = int(os.getenv('MAX_MESSAGE_LENGTH', '5000'))
        self.config.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.config.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        # セキュリティ設定
        self.config.rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        self.config.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '10'))

    def _load_from_file(self) -> None:
        """設定ファイルから読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # ファイルの設定で環境変数を上書き（機密情報は除く）
            for key, value in file_config.items():
                if key not in ['line_channel_secret', 'line_access_token', 'gemini_api_key']:
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            
            self.logger.info(f"設定ファイルを読み込みました: {self.config_file}")
            
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗: {str(e)}")

    def _validate_config(self) -> None:
        """設定の検証"""
        errors = []
        
        # 必須設定のチェック
        if not self.config.line_channel_secret:
            errors.append("LINE_CHANNEL_SECRET が設定されていません")
        if not self.config.line_access_token:
            errors.append("LINE_ACCESS_TOKEN が設定されていません")
        if not self.config.gemini_api_key:
            errors.append("GEMINI_API_KEY が設定されていません")
        
        # 数値設定の妥当性チェック
        if self.config.port < 1000 or self.config.port > 65535:
            errors.append("PORT は 1000-65535 の範囲で設定してください")
        if self.config.notification_check_interval < 1:
            errors.append("NOTIFICATION_CHECK_INTERVAL は 1 以上で設定してください")
        if self.config.max_notifications_per_user < 1:
            errors.append("MAX_NOTIFICATIONS_PER_USER は 1 以上で設定してください")
        
        # ログレベルの妥当性チェック
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.log_level not in valid_log_levels:
            errors.append(f"LOG_LEVEL は {valid_log_levels} のいずれかで設定してください")
        
        if errors:
            # 環境変数 SKIP_CONFIG_VALIDATION が true の場合は警告のみ
            if os.getenv('SKIP_CONFIG_VALIDATION', 'false').lower() in ('true', '1', 'yes'): 
                self.logger.warning(f"設定エラーを無視して続行します: {', '.join(errors)}")
            else:
                raise ValueError(f"設定エラー: {', '.join(errors)}")

    def get_config(self) -> AppConfig:
        """
        設定を取得
        
        Returns:
            AppConfig: アプリケーション設定
        """
        return self.config

    def is_feature_enabled(self, feature: str) -> bool:
        """
        機能が有効かどうかを確認
        
        Args:
            feature (str): 機能名
            
        Returns:
            bool: 機能が有効かどうか
        """
        return self.config.features.get(feature, False)

    def get_service_config(self, service: str) -> Dict[str, Any]:
        """
        サービス固有の設定を取得
        
        Args:
            service (str): サービス名
            
        Returns:
            Dict[str, Any]: サービス設定
        """
        if service == 'weather':
            return {
                'api_key': self.config.weather_api_key,
                'enabled': self.is_feature_enabled('weather')
            }
        elif service == 'search':
            return {
                'api_key': self.config.google_api_key,
                'search_engine_id': self.config.google_search_engine_id,
                'enabled': self.is_feature_enabled('search')
            }
        elif service == 'notifications':
            return {
                'storage_path': self.config.notification_storage_path,
                'check_interval': self.config.notification_check_interval,
                'max_per_user': self.config.max_notifications_per_user,
                'enabled': self.is_feature_enabled('notifications')
            }
        elif service == 'auto_tasks':
            # 自動実行タスクの保存先もプラットフォーム安全な既定パスを使用
            default_data_dir = os.getenv('AUTO_TASK_STORAGE_PATH') or os.getenv('DATA_DIR') or os.path.join(os.getcwd(), 'data')
            return {
                'storage_path': default_data_dir,
                'enabled': self.is_feature_enabled('auto_tasks')
            }
        else:
            return {}

    def save_config_template(self, output_file: str = 'config.template.json') -> None:
        """
        設定テンプレートファイルを生成
        
        Args:
            output_file (str): 出力ファイル名
        """
        template = {
            "port": 8000,
            "debug": False,
            "log_level": "INFO",
            "notification_check_interval": 5,
            "max_notifications_per_user": 100,
            "max_message_length": 5000,
            "request_timeout": 30,
            "max_retries": 3,
            "rate_limit_enabled": True,
            "max_requests_per_minute": 10,
            "features": {
                "weather": True,
                "search": True,
                "notifications": True,
                "auto_tasks": True,
                "quick_reply": True,
                "performance_monitoring": True
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            self.logger.info(f"設定テンプレートを生成しました: {output_file}")
        except Exception as e:
            self.logger.error(f"設定テンプレートの生成に失敗: {str(e)}")

    def get_config_summary(self) -> str:
        """
        設定概要を取得
        
        Returns:
            str: 設定概要
        """
        lines = [
            "⚙️ **設定概要**",
            f"・ポート: {self.config.port}",
            f"・デバッグモード: {'有効' if self.config.debug else '無効'}",
            f"・ログレベル: {self.config.log_level}",
            f"・通知チェック間隔: {self.config.notification_check_interval}秒",
            f"・ユーザー当たり最大通知数: {self.config.max_notifications_per_user}",
            "",
            "🔧 **有効な機能:**"
        ]
        
        for feature, enabled in self.config.features.items():
            status = "✅" if enabled else "❌"
            lines.append(f"・{feature}: {status}")
        
        return "\n".join(lines)

# グローバルインスタンス（アプリ実行時に利用）
config_manager = ConfigManager()

# Add a new line at the end of the file