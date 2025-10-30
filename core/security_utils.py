"""
Security and validation utilities
"""
import os
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

class SecurityUtils:
    """セキュリティとバリデーション機能"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)

    def validate_environment_variables(self) -> tuple[bool, List[str]]:
        """
        環境変数の妥当性を検証
        
        Returns:
            tuple[bool, List[str]]: (有効か, エラーメッセージリスト)
        """
        errors = []
        
        # 必須環境変数の定義
        required_vars = {
            'LINE_CHANNEL_SECRET': {'min_length': 32, 'type': 'string'},
            'LINE_ACCESS_TOKEN': {'min_length': 50, 'type': 'string'},
            'GEMINI_API_KEY': {'min_length': 20, 'type': 'string'}
        }
        
        # オプション環境変数の定義
        optional_vars = {
            'WEATHER_API_KEY': {'min_length': 20, 'type': 'string'},
            'GOOGLE_API_KEY': {'min_length': 30, 'type': 'string'},
            'GOOGLE_SEARCH_ENGINE_ID': {'min_length': 10, 'type': 'string'},
            'PORT': {'type': 'int', 'min_value': 1000, 'max_value': 65535},
            'NOTIFICATION_STORAGE_PATH': {'type': 'path'}
        }
        
        # 必須変数のチェック
        for var_name, config in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                errors.append(f"必須の環境変数 {var_name} が設定されていません")
                continue
                
            if not self._validate_env_value(var_name, value, config):
                errors.append(f"環境変数 {var_name} の値が無効です")
        
        # オプション変数のチェック（設定されている場合のみ）
        for var_name, config in optional_vars.items():
            value = os.getenv(var_name)
            if value and not self._validate_env_value(var_name, value, config):
                errors.append(f"環境変数 {var_name} の値が無効です")
        
        return len(errors) == 0, errors

    def _validate_env_value(self, name: str, value: str, config: Dict[str, Any]) -> bool:
        """環境変数値の妥当性チェック"""
        try:
            if config['type'] == 'string':
                if 'min_length' in config and len(value) < config['min_length']:
                    return False
                # APIキーの基本的なフォーマットチェック
                if 'API_KEY' in name and not re.match(r'^[A-Za-z0-9_-]+$', value):
                    return False
                    
            elif config['type'] == 'int':
                int_value = int(value)
                if 'min_value' in config and int_value < config['min_value']:
                    return False
                if 'max_value' in config and int_value > config['max_value']:
                    return False
                    
            elif config['type'] == 'path':
                # パスの妥当性チェック（相対パスまたは絶対パス）
                if not value or len(value.strip()) == 0:
                    return False
                    
            return True
        except (ValueError, TypeError):
            return False

    def sanitize_user_input(self, text: str, max_length: int = 1000) -> str:
        """
        ユーザー入力のサニタイズ
        
        Args:
            text (str): 入力テキスト
            max_length (int): 最大長
            
        Returns:
            str: サニタイズされたテキスト
        """
        if not isinstance(text, str):
            text = str(text)
            
        # 長さ制限
        if len(text) > max_length:
            text = text[:max_length]
            
        # 危険な文字の除去
        text = re.sub(r'[<>"\'\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # 改行の正規化
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        
        # 連続する空白の制限
        text = re.sub(r'\s{5,}', '    ', text)
        
        return text.strip()

    def validate_notification_data(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        通知データの妥当性検証
        
        Args:
            data (Dict[str, Any]): 通知データ
            
        Returns:
            tuple[bool, Optional[str]]: (有効か, エラーメッセージ)
        """
        required_fields = ['datetime', 'title', 'message', 'user_id']
        
        # 必須フィールドのチェック
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"必須フィールド '{field}' が不足しています"
        
        # 日時フォーマットのチェック
        try:
            datetime.strptime(data['datetime'], '%Y-%m-%d %H:%M')
        except ValueError:
            return False, "日時フォーマットが無効です（YYYY-MM-DD HH:MM形式で指定してください）"
        
        # テキスト長のチェック
        if len(data['title']) > 100:
            return False, "タイトルが長すぎます（100文字以内）"
        if len(data['message']) > 500:
            return False, "メッセージが長すぎます（500文字以内）"
        
        # 優先度のチェック
        if 'priority' in data and data['priority'] not in ['high', 'medium', 'low']:
            return False, "優先度の値が無効です"
        
        # 繰り返し設定のチェック
        if 'repeat' in data and data['repeat'] not in ['none', 'daily', 'weekly', 'monthly']:
            return False, "繰り返し設定の値が無効です"
        
        return True, None

    def generate_safe_error_message(self, error: Exception, user_friendly: bool = True) -> str:
        """
        安全なエラーメッセージを生成
        
        Args:
            error (Exception): 発生したエラー
            user_friendly (bool): ユーザー向けの表示か
            
        Returns:
            str: 安全なエラーメッセージ
        """
        if user_friendly:
            # ユーザー向けには技術的詳細を隠す
            error_type_messages = {
                'ValueError': "入力値に問題があります。正しい形式で入力してください。",
                'TypeError': "データの形式に問題があります。",
                'KeyError': "必要な情報が不足しています。",
                'ConnectionError': "ネットワーク接続に問題があります。しばらく時間をおいて再度お試しください。",
                'TimeoutError': "処理に時間がかかりすぎています。しばらく時間をおいて再度お試しください。",
                'PermissionError': "アクセス権限に問題があります。",
                'FileNotFoundError': "ファイルが見つかりません。"
            }
            
            error_type = type(error).__name__
            return error_type_messages.get(
                error_type,
                "申し訳ありません。一時的な問題が発生しました。しばらく時間をおいて再度お試しください。"
            )
        else:
            # ログ用には詳細情報を含める
            return f"{type(error).__name__}: {str(error)}"

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        セキュリティイベントのログ記録
        
        Args:
            event_type (str): イベントタイプ
            details (Dict[str, Any]): イベント詳細
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        self.logger.warning(f"SECURITY_EVENT: {json.dumps(log_entry, ensure_ascii=False)}")

    def rate_limit_check(self, user_id: str, action: str, window_minutes: int = 1, max_requests: int = 10) -> bool:
        """
        簡易的なレート制限チェック
        
        Args:
            user_id (str): ユーザーID
            action (str): アクション名
            window_minutes (int): 時間窓（分）
            max_requests (int): 最大リクエスト数
            
        Returns:
            bool: リクエストが許可されるか
        """
        # 実装は簡略化（本格的にはRedisなどを使用）
        # ここでは基本的なフレームワークのみ提供
        key = f"{user_id}:{action}"
        # 実際の実装では永続化が必要
        return True  # 現在は常に許可 