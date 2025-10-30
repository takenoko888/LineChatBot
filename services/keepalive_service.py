"""
Keep-alive service for Koyeb free plan
Koyeb無料プラン対応のキープアライブサービス
"""
import threading
import time
import requests
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pytz

class KeepAliveService:
    """Koyeb無料プランのスリープ回避サービス"""
    
    def __init__(self, app_url: str = None, ping_interval: int = 3):
        """
        初期化
        
        Args:
            app_url (str): アプリケーションのURL
            ping_interval (int): ping間隔（分）
        """
        self.logger = logging.getLogger(__name__)
        self.app_url = app_url or os.getenv('KOYEB_APP_URL', 'http://localhost:5000')
        self.ping_interval = ping_interval  # 分単位
        self.is_running = False
        self.ping_thread = None
        self.last_ping_time = None
        self.ping_count = 0
        self.failed_pings = 0
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # Koyeb無料プラン専用設定
        self.koyeb_free_mode = True  # 無料プラン用の積極的キープアライブ
        self.force_active_interval = 3  # 強制アクティブ間隔（分）
        self.max_sleep_time = 10  # 最大スリープ時間（分）
        
        # スマートpingモード設定
        self.smart_mode = True
        self.active_hours = list(range(6, 23))  # 6時〜23時がアクティブ時間
        self.sleep_hours = list(range(0, 6)) + [23]  # 0〜6時、23時は低頻度
        
        self.logger.info(f"KeepAliveService初期化: URL={self.app_url}, 間隔={ping_interval}分")
    
    def start(self) -> bool:
        """
        キープアライブサービスを開始
        
        Returns:
            bool: 開始成功時True
        """
        if self.is_running:
            self.logger.warning("KeepAliveServiceは既に実行中です")
            return True

        try:
            # 本番環境でのみ有効化
            if not self.is_production:
                self.logger.info("開発環境のため、KeepAliveサービスをスキップします")
                return True

            self.is_running = True
            self.ping_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
            self.ping_thread.start()
            
            self.logger.info("KeepAliveServiceを開始しました")
            return True
            
        except Exception as e:
            self.logger.error(f"KeepAliveService開始エラー: {str(e)}")
            self.is_running = False
            return False
    
    def stop(self) -> None:
        """キープアライブサービスを停止"""
        self.is_running = False
        if self.ping_thread:
            self.logger.info("KeepAliveServiceを停止中...")
            # スレッドの終了を待機（最大10秒）
            self.ping_thread.join(timeout=10)
        self.logger.info("KeepAliveService停止完了")
    
    def _keepalive_loop(self) -> None:
        """KeepAliveメインループ（改善版）"""
        consecutive_failures = 0
        max_failures = 5
        base_interval = self.ping_interval
        
        while self.is_running:
            try:
                # Ping実行
                success = self._ping()
                
                if success:
                    consecutive_failures = 0
                    current_interval = base_interval
                else:
                    consecutive_failures += 1
                    # 失敗時は間隔を段階的に延長
                    current_interval = min(base_interval * (2 ** consecutive_failures), 300)  # 最大5分
                    
                    if consecutive_failures >= max_failures:
                        self.logger.critical(f"連続失敗が{max_failures}回に達しました。KeepAliveを一時停止します。")
                        break

                # 待機（中断可能）
                time.sleep(current_interval)
                
            except Exception as e:
                self.logger.error(f"KeepAliveループエラー: {str(e)}")
                time.sleep(base_interval)

        self.logger.info("KeepAliveループを終了しました")
    
    def _ping(self) -> bool:
        """サーバーにPingを送信（改善版）"""
        for endpoint in self.endpoints:
            try:
                url = f"{self.app_url}{endpoint}"
                
                # タイムアウトを短縮してリソース節約
                response = requests.get(
                    url, 
                    timeout=10,  # 10秒タイムアウト
                    headers={'User-Agent': 'KeepAlive-Service'},
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    self.ping_count += 1
                    self.failed_pings = 0
                    self.last_ping_time = datetime.now(self.jst)
                    self.logger.debug(f"Ping成功 (#{self.ping_count}): {self.last_ping_time.strftime('%H:%M:%S')}")
                    return True
                else:
                    self.failed_pings += 1
                    self.logger.warning(f"Ping応答エラー: {response.status_code} - {url}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Pingタイムアウト: {url}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Ping接続エラー: {url}")
            except Exception as e:
                self.logger.warning(f"Ping例外: {url} - {str(e)}")

        # すべてのエンドポイントで失敗
        self.failed_pings += 1
        self.logger.warning(f"連続ping失敗によりサービス状態を確認中... (連続{self.failed_pings}回)")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        キープアライブサービスの統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        current_time = datetime.now(self.jst)
        
        return {
            'is_running': self.is_running,
            'ping_count': self.ping_count,
            'failed_pings': self.failed_pings,
            'last_ping_time': self.last_ping_time.isoformat() if self.last_ping_time else None,
            'current_time': current_time.isoformat(),
            'app_url': self.app_url,
            'ping_interval': self.ping_interval,
            'smart_mode': self.smart_mode,
            'koyeb_free_mode': self.koyeb_free_mode,
            'next_ping_in_minutes': self._get_next_ping_time_diff(current_time)
        }
    
    def _get_next_ping_time_diff(self, current_time: datetime) -> Optional[int]:
        """次のping時刻までの分数を計算"""
        if not self.last_ping_time:
            return 0
        
        interval = self.ping_interval
        elapsed = (current_time - self.last_ping_time).total_seconds() / 60
        remaining = interval - elapsed
        
        return max(0, int(remaining))
    
    def manual_ping(self) -> Dict[str, Any]:
        """
        手動ping実行
        
        Returns:
            Dict[str, Any]: ping結果
        """
        start_time = datetime.now(self.jst)
        success = self._ping()
        end_time = datetime.now(self.jst)
        
        response_time = (end_time - start_time).total_seconds() * 1000  # ミリ秒
        
        result = {
            'success': success,
            'response_time_ms': response_time,
            'timestamp': start_time.isoformat(),
            'url': f"{self.app_url.rstrip('/')}/health"
        }
        
        if success:
            self.ping_count += 1
            self.last_ping_time = start_time
            self.failed_pings = 0
        else:
            self.failed_pings += 1
        
        return result
    
    def set_smart_mode(self, enabled: bool) -> None:
        """スマートモードの有効/無効を設定"""
        self.smart_mode = enabled
        self.logger.info(f"スマートモード: {'有効' if enabled else '無効'}")
    
    def set_ping_interval(self, interval_minutes: int) -> None:
        """ping間隔を設定"""
        if interval_minutes < 1:
            raise ValueError("ping間隔は1分以上である必要があります")
        
        self.ping_interval = interval_minutes
        self.logger.info(f"Ping間隔を{interval_minutes}分に設定")
    
    def set_active_hours(self, hours: list) -> None:
        """アクティブ時間を設定"""
        self.active_hours = hours
        self.sleep_hours = [h for h in range(24) if h not in hours]
        self.logger.info(f"アクティブ時間を設定: {hours}")
    
    def check_and_respond(self) -> Dict[str, Any]:
        """
        外部からのキープアライブチェックに応答
        
        Returns:
            Dict[str, Any]: 応答データ
        """
        current_time = datetime.now(self.jst)
        
        # 最後のping時刻を更新（外部からのアクセスがあったことを記録）
        self.last_ping_time = current_time
        
        response = {
            'keepalive_active': self.is_running,
            'ping_count': self.ping_count,
            'last_internal_ping': self.last_ping_time.isoformat() if self.last_ping_time else None,
            'current_time': current_time.isoformat(),
            'smart_mode': self.smart_mode,
            'koyeb_free_mode': self.koyeb_free_mode,
            'message': 'KeepAlive service is active - Koyeb free plan optimized'
        }
        
        self.logger.debug(f"外部KeepAliveチェック応答: {response}")
        return response
    
    @staticmethod
    def detect_koyeb_environment() -> Dict[str, str]:
        """
        Koyeb環境を自動検出してURLを特定
        
        Returns:
            Dict[str, str]: 検出された環境情報
        """
        # Koyeb環境変数の検出
        koyeb_vars = {
            'KOYEB_APP_URL': os.getenv('KOYEB_APP_URL'),
            'KOYEB_SERVICE_NAME': os.getenv('KOYEB_SERVICE_NAME'),
            'KOYEB_REGION': os.getenv('KOYEB_REGION'),
            'PORT': os.getenv('PORT', '5000')
        }
        
        # 自動URL生成
        if koyeb_vars['KOYEB_SERVICE_NAME']:
            # Koyebの標準URL形式
            auto_url = f"https://{koyeb_vars['KOYEB_SERVICE_NAME']}.koyeb.app"
            koyeb_vars['AUTO_DETECTED_URL'] = auto_url
        
        return {k: v for k, v in koyeb_vars.items() if v is not None}
    
    def configure_for_production(self) -> bool:
        """本番環境（Koyeb等）の自動検出と設定"""
        try:
            # Koyeb環境の検出
            koyeb_instance_url = os.getenv('KOYEB_INSTANCE_URL') or os.getenv('KOYEB_PUBLIC_DOMAIN')
            if koyeb_instance_url:
                self.app_url = f"https://{koyeb_instance_url}" if not koyeb_instance_url.startswith('http') else koyeb_instance_url
                self.is_production = True
                self.ping_interval = 45  # Koyeb用に最適化（45秒間隔）
                self.endpoints = ['/health', '/']  # シンプルなエンドポイントを使用
                self.logger.info(f"Koyeb環境を検出: {self.app_url}")
                return True
            
            # 他の本番環境の検出
            if os.getenv('PORT') and (os.getenv('DYNO') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('VERCEL_ENV')):
                port = os.getenv('PORT', '8000')
                self.app_url = f"http://localhost:{port}"
                self.is_production = True
                self.ping_interval = 60  # 他の環境用
                self.logger.info(f"本番環境を検出: {self.app_url}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"本番環境設定エラー: {str(e)}")
            return False 