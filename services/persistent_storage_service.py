"""
永続的ストレージサービス - デプロイ時のデータ保持機能
"""
import os
import json
import logging
import requests
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import time

class PersistentStorageService:
    """永続的ストレージサービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO')  # "owner/repo" 形式
        self.backup_branch = os.getenv('BACKUP_BRANCH', 'data-backup')
        self.data_file_path = 'data/notifications.json'
        self.last_backup_time = datetime.now()
        self.backup_interval = timedelta(minutes=30)  # 30分ごとにバックアップ
        self.lock = threading.Lock()
        
        # GitHubが利用できない場合のフォールバック設定
        self.fallback_enabled = True
        self.local_backup_paths = [
            '/tmp/notifications_backup.json',
            './notifications_backup.json'
        ]
        
        self.logger.info("永続的ストレージサービスを初期化")
        
    def save_data(self, data: Dict[str, Any], force_backup: bool = False) -> bool:
        """
        データを永続的に保存
        
        Args:
            data: 保存するデータ
            force_backup: 強制的にバックアップを実行するかどうか
            
        Returns:
            bool: 保存成功かどうか
        """
        try:
            with self.lock:
                success = False
                
                # GitHubへのバックアップを試行
                if self._should_backup() or force_backup:
                    if self._backup_to_github(data):
                        success = True
                        self.last_backup_time = datetime.now()
                        self.logger.info("GitHubへのデータバックアップが完了")
                    else:
                        self.logger.warning("GitHubバックアップに失敗、フォールバックを使用")
                
                # フォールバックストレージ（ローカル）
                if self.fallback_enabled:
                    if self._backup_to_local(data):
                        success = True
                        self.logger.debug("ローカルバックアップが完了")
                
                return success
                
        except Exception as e:
            self.logger.error(f"データ保存エラー: {str(e)}")
            return False
    
    def load_data(self) -> Optional[Dict[str, Any]]:
        """
        永続的ストレージからデータを読み込み
        
        Returns:
            Dict[str, Any]: 読み込んだデータ、失敗時はNone
        """
        try:
            with self.lock:
                # GitHubから復元を試行
                data = self._restore_from_github()
                if data is not None:
                    self.logger.info("GitHubからデータを復元")
                    return data
                
                # フォールバックからの復元
                if self.fallback_enabled:
                    data = self._restore_from_local()
                    if data is not None:
                        self.logger.info("ローカルバックアップからデータを復元")
                        return data
                
                self.logger.warning("復元可能なデータが見つかりません")
                return None
                
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {str(e)}")
            return None
    
    def _should_backup(self) -> bool:
        """バックアップが必要かどうかを判定"""
        return datetime.now() - self.last_backup_time > self.backup_interval
    
    def _backup_to_github(self, data: Dict[str, Any]) -> bool:
        """GitHubにデータをバックアップ"""
        if not self.github_token or not self.github_repo:
            self.logger.debug("GitHub設定が不完全、スキップします")
            return False
        
        try:
            # データをJSONとしてエンコード
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            content = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
            
            # GitHub API URL
            url = f"https://api.github.com/repos/{self.github_repo}/contents/{self.data_file_path}"
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Content-Type': 'application/json'
            }
            
            # 既存ファイルのSHAを取得
            get_response = requests.get(url, headers=headers, timeout=10)
            sha = None
            if get_response.status_code == 200:
                sha = get_response.json().get('sha')
            
            # ファイルを更新または作成
            payload = {
                'message': f'データバックアップ {datetime.now().isoformat()}',
                'content': content,
                'branch': self.backup_branch
            }
            
            if sha:
                payload['sha'] = sha
            
            response = requests.put(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                self.logger.debug("GitHubバックアップ成功")
                return True
            else:
                self.logger.warning(f"GitHubバックアップ失敗: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.warning(f"GitHubバックアップエラー: {str(e)}")
            return False
    
    def _restore_from_github(self) -> Optional[Dict[str, Any]]:
        """GitHubからデータを復元"""
        if not self.github_token or not self.github_repo:
            return None
        
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/contents/{self.data_file_path}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{url}?ref={self.backup_branch}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.json().get('content', '')
                decoded_content = base64.b64decode(content).decode('utf-8')
                data = json.loads(decoded_content)
                return data
            else:
                self.logger.debug(f"GitHub復元失敗: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.warning(f"GitHub復元エラー: {str(e)}")
            return None
    
    def _backup_to_local(self, data: Dict[str, Any]) -> bool:
        """ローカルにデータをバックアップ"""
        for backup_path in self.local_backup_paths:
            try:
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self.logger.debug(f"ローカルバックアップ成功: {backup_path}")
                return True
                
            except Exception as e:
                self.logger.debug(f"ローカルバックアップ失敗 {backup_path}: {str(e)}")
                continue
        
        return False
    
    def _restore_from_local(self) -> Optional[Dict[str, Any]]:
        """ローカルバックアップからデータを復元"""
        for backup_path in self.local_backup_paths:
            try:
                if not os.path.exists(backup_path):
                    continue
                
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.logger.debug(f"ローカル復元成功: {backup_path}")
                return data
                
            except Exception as e:
                self.logger.debug(f"ローカル復元失敗 {backup_path}: {str(e)}")
                continue
        
        return None
    
    def create_backup_now(self, data: Dict[str, Any]) -> bool:
        """即座にバックアップを作成"""
        return self.save_data(data, force_backup=True)
    
    def get_backup_status(self) -> Dict[str, Any]:
        """バックアップ状況を取得"""
        return {
            'last_backup_time': self.last_backup_time.isoformat(),
            'next_backup_due': (self.last_backup_time + self.backup_interval).isoformat(),
            'github_enabled': bool(self.github_token and self.github_repo),
            'fallback_enabled': self.fallback_enabled,
            'backup_paths': self.local_backup_paths
        } 