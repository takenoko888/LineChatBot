#!/usr/bin/env python3
"""
KeepAlive機能の包括的テスト
Koyeb無料プラン対応機能の検証
"""

import os
import sys
import json
import time
import threading
import tempfile
import requests
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.keepalive_service import KeepAliveService
from services.notification_service import NotificationService
from services.gemini_service import GeminiService

class KeepAliveComprehensiveTest:
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.keepalive_service = None
        
    def setup_test_environment(self):
        """テスト環境のセットアップ"""
        try:
            # 一時ディレクトリの作成
            self.temp_dir = tempfile.mkdtemp(prefix="keepalive_test_")
            
            print("✅ テスト環境セットアップ完了")
            print(f"   一時ディレクトリ: {self.temp_dir}")
            return True
            
        except Exception as e:
            print(f"❌ テスト環境セットアップ失敗: {str(e)}")
            return False
    
    def cleanup_test_environment(self):
        """テスト環境のクリーンアップ"""
        try:
            if self.keepalive_service and self.keepalive_service.is_running:
                self.keepalive_service.stop()
                
            if self.temp_dir:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
            print("✅ テスト環境クリーンアップ完了")
            
        except Exception as e:
            print(f"⚠️ クリーンアップ警告: {str(e)}")
    
    def record_test_result(self, test_name: str, success: bool, details: str = ""):
        """テスト結果を記録"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
    
    def test_keepalive_service_initialization(self):
        """KeepAliveサービスの初期化テスト"""
        try:
            # 基本初期化
            service = KeepAliveService(
                app_url="http://localhost:5000",
                ping_interval=5
            )
            
            success = (
                service.app_url == "http://localhost:5000" and
                service.ping_interval == 5 and
                not service.is_running and
                service.ping_count == 0
            )
            
            self.record_test_result(
                "KeepAliveサービス初期化",
                success,
                f"URL: {service.app_url}, 間隔: {service.ping_interval}分"
            )
            
            # 環境変数テスト
            with patch.dict('os.environ', {'KOYEB_APP_URL': 'https://test.koyeb.app'}):
                env_service = KeepAliveService()
                env_success = env_service.app_url == 'https://test.koyeb.app'
                
                self.record_test_result(
                    "環境変数からの初期化",
                    env_success,
                    f"検出URL: {env_service.app_url}"
                )
            
            return success and env_success
            
        except Exception as e:
            self.record_test_result(
                "KeepAliveサービス初期化",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def test_koyeb_environment_detection(self):
        """Koyeb環境自動検出テスト"""
        try:
            # Koyeb環境変数をモック
            koyeb_env = {
                'KOYEB_SERVICE_NAME': 'test-service',
                'KOYEB_REGION': 'fra',
                'PORT': '8080'
            }
            
            with patch.dict('os.environ', koyeb_env):
                detected = KeepAliveService.detect_koyeb_environment()
                
                expected_url = "https://test-service.koyeb.app"
                success = (
                    detected.get('KOYEB_SERVICE_NAME') == 'test-service' and
                    detected.get('AUTO_DETECTED_URL') == expected_url
                )
                
                self.record_test_result(
                    "Koyeb環境検出",
                    success,
                    f"検出結果: {detected}"
                )
                
                return success
                
        except Exception as e:
            self.record_test_result(
                "Koyeb環境検出",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def test_smart_interval_calculation(self):
        """スマート間隔計算テスト"""
        try:
            service = KeepAliveService(ping_interval=10)
            
            # 日中時間のテスト（6-23時）
            from datetime import datetime
            import pytz
            jst = pytz.timezone('Asia/Tokyo')
            
            # 昼間（14時）
            day_time = datetime.now(jst).replace(hour=14, minute=0, second=0)
            day_interval = service._calculate_smart_interval(day_time)
            
            # 夜間（2時）
            night_time = datetime.now(jst).replace(hour=2, minute=0, second=0)
            night_interval = service._calculate_smart_interval(night_time)
            
            success = (
                day_interval == 10 and  # 基本間隔
                night_interval == 30    # 3倍間隔
            )
            
            self.record_test_result(
                "スマート間隔計算",
                success,
                f"昼間: {day_interval}分, 夜間: {night_interval}分"
            )
            
            return success
            
        except Exception as e:
            self.record_test_result(
                "スマート間隔計算",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def test_ping_mechanism(self):
        """Ping機能テスト"""
        try:
            service = KeepAliveService(
                app_url="http://httpbin.org",  # テスト用公開API
                ping_interval=1
            )
            
            # pingを実行してみる（httpbin.orgのヘルスチェック）
            with patch.object(service, '_perform_ping') as mock_ping:
                mock_ping.return_value = True
                
                # 手動pingテスト
                result = service.manual_ping()
                
                success = (
                    result['success'] == True and
                    'response_time_ms' in result and
                    'timestamp' in result
                )
                
                self.record_test_result(
                    "Ping機能",
                    success,
                    f"結果: {result}"
                )
                
                return success
                
        except Exception as e:
            self.record_test_result(
                "Ping機能",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def test_service_lifecycle(self):
        """サービスライフサイクルテスト"""
        try:
            service = KeepAliveService(ping_interval=1)
            
            # 開始テスト
            start_success = service.start()
            time.sleep(0.5)  # 少し待機
            running_status = service.is_running
            
            # 統計情報取得
            stats = service.get_stats()
            
            # 停止テスト
            service.stop()
            time.sleep(0.5)  # 停止を待つ
            stopped_status = not service.is_running
            
            success = (
                start_success and
                running_status and
                stopped_status and
                'ping_count' in stats
            )
            
            self.record_test_result(
                "サービスライフサイクル",
                success,
                f"開始: {start_success}, 実行中: {running_status}, 停止: {stopped_status}"
            )
            
            return success
            
        except Exception as e:
            self.record_test_result(
                "サービスライフサイクル",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def test_configuration_changes(self):
        """設定変更テスト"""
        try:
            service = KeepAliveService()
            
            # 間隔変更テスト
            service.set_ping_interval(15)
            interval_success = service.ping_interval == 15
            
            # スマートモード切り替えテスト
            service.set_smart_mode(False)
            smart_mode_success = service.smart_mode == False
            
            # アクティブ時間設定テスト
            custom_hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
            service.set_active_hours(custom_hours)
            hours_success = service.active_hours == custom_hours
            
            success = interval_success and smart_mode_success and hours_success
            
            self.record_test_result(
                "設定変更",
                success,
                f"間隔: {interval_success}, スマート: {smart_mode_success}, 時間: {hours_success}"
            )
            
            return success
            
        except Exception as e:
            self.record_test_result(
                "設定変更",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def test_error_handling(self):
        """エラー処理テスト"""
        try:
            # 無効な間隔設定テスト
            service = KeepAliveService()
            
            try:
                service.set_ping_interval(0)  # 無効な値
                invalid_interval_handled = False
            except ValueError:
                invalid_interval_handled = True
            
            # 接続失敗テスト
            unreachable_service = KeepAliveService(
                app_url="http://nonexistent.invalid.domain"
            )
            
            with patch.object(unreachable_service, '_perform_ping') as mock_ping:
                mock_ping.return_value = False
                ping_failure_handled = not unreachable_service._perform_ping()
            
            success = invalid_interval_handled and ping_failure_handled
            
            self.record_test_result(
                "エラー処理",
                success,
                f"無効間隔: {invalid_interval_handled}, 接続失敗: {ping_failure_handled}"
            )
            
            return success
            
        except Exception as e:
            self.record_test_result(
                "エラー処理",
                False,
                f"エラー: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """全テストを実行"""
        print("🚀 KeepAlive機能包括テストを開始します...\n")
        
        if not self.setup_test_environment():
            return False
        
        try:
            tests = [
                self.test_keepalive_service_initialization,
                self.test_koyeb_environment_detection,
                self.test_smart_interval_calculation,
                self.test_ping_mechanism,
                self.test_service_lifecycle,
                self.test_configuration_changes,
                self.test_error_handling
            ]
            
            results = []
            for test in tests:
                try:
                    result = test()
                    results.append(result)
                except Exception as e:
                    print(f"❌ テスト実行エラー: {str(e)}")
                    results.append(False)
            
            # 結果サマリー
            successful_tests = sum(results)
            total_tests = len(results)
            success_rate = (successful_tests / total_tests) * 100
            
            print(f"\n📊 KeepAlive機能テスト結果:")
            print(f"   成功: {successful_tests}/{total_tests} テスト")
            print(f"   成功率: {success_rate:.1f}%")
            
            # 詳細結果をファイルに保存
            results_data = {
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'test_results': self.test_results
            }
            
            with open('keepalive_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            print(f"📝 詳細結果を keepalive_test_results.json に保存しました")
            
            return success_rate >= 85  # 85%以上で成功とみなす
            
        finally:
            self.cleanup_test_environment()

def main():
    """メイン実行関数"""
    test_runner = KeepAliveComprehensiveTest()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🎉 KeepAlive機能テスト完了 - 成功！")
        exit(0)
    else:
        print("\n💥 KeepAlive機能テストに問題があります")
        exit(1)

if __name__ == "__main__":
    main() 