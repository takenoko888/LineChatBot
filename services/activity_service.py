"""
Activity service to keep app active
アプリをアクティブに保つためのアクティビティサービス
"""
import threading
import time
import logging
import requests
from datetime import datetime
from typing import Optional

class ActivityService:
    """アプリをアクティブに保つためのサービス"""
    
    def __init__(self, app_url: str = None):
        """
        初期化
        
        Args:
            app_url (str): アプリケーションのURL
        """
        self.logger = logging.getLogger(__name__)
        self.app_url = app_url or "http://localhost:8000"
        self.is_running = False
        self.activity_thread = None
        self.activity_count = 0
        
        # Koyeb無料プラン用設定
        self.activity_interval = 60  # 1分間隔
        self.endpoints = ['/health', '/keepalive', '/']
        
        self.logger.info(f"ActivityService初期化: URL={self.app_url}")
    
    def start(self) -> bool:
        """
        アクティビティサービスを開始
        
        Returns:
            bool: 開始成功時True
        """
        try:
            if self.is_running:
                self.logger.warning("ActivityServiceは既に実行中です")
                return True
            
            self.is_running = True
            self.activity_thread = threading.Thread(target=self._activity_loop, daemon=True)
            self.activity_thread.start()
            
            self.logger.info("ActivityServiceを開始しました")
            return True
            
        except Exception as e:
            self.logger.error(f"ActivityService開始エラー: {str(e)}")
            return False
    
    def stop(self) -> None:
        """アクティビティサービスを停止"""
        self.is_running = False
        if self.activity_thread:
            self.logger.info("ActivityServiceを停止中...")
            self.activity_thread.join(timeout=5)
        self.logger.info("ActivityService停止完了")
    
    def _activity_loop(self) -> None:
        """アクティビティループのメイン処理"""
        self.logger.info("アクティビティループを開始")
        
        while self.is_running:
            try:
                # 各エンドポイントにアクセス
                for endpoint in self.endpoints:
                    if not self.is_running:
                        break
                    
                    try:
                        url = f"{self.app_url.rstrip('/')}{endpoint}"
                        response = requests.get(
                            url,
                            timeout=10,
                            headers={'User-Agent': 'ActivityKeeper/1.0'}
                        )
                        
                        if response.status_code == 200:
                            self.activity_count += 1
                            self.logger.debug(f"アクティビティ成功 ({endpoint}): #{self.activity_count}")
                        
                    except Exception as e:
                        self.logger.warning(f"アクティビティエラー ({endpoint}): {str(e)}")
                    
                    # エンドポイント間の間隔
                    time.sleep(20)
                
                # 次のサイクルまで待機
                time.sleep(self.activity_interval)
                
            except Exception as e:
                self.logger.error(f"アクティビティループエラー: {str(e)}")
                time.sleep(30)
    
    def get_stats(self) -> dict:
        """アクティビティ統計を取得"""
        return {
            'is_running': self.is_running,
            'activity_count': self.activity_count,
            'app_url': self.app_url,
            'activity_interval': self.activity_interval,
            'current_time': datetime.now().isoformat()
        } 