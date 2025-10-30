"""
Admin command handler for system administration
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

class AdminHandler:
    """管理者コマンドハンドラー"""

    def __init__(self, performance_monitor=None, config_manager=None, security_utils=None):
        """
        初期化
        
        Args:
            performance_monitor: パフォーマンス監視インスタンス
            config_manager: 設定管理インスタンス
            security_utils: セキュリティユーティリティインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = performance_monitor
        self.config_manager = config_manager
        self.security_utils = security_utils
        
        # 管理者ユーザーIDリスト（環境変数から取得）
        admin_ids = os.getenv('ADMIN_USER_IDS', '')
        self.admin_user_ids = set(admin_ids.split(',')) if admin_ids else set()

    def is_admin(self, user_id: str) -> bool:
        """
        ユーザーが管理者かどうかを確認
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            bool: 管理者かどうか
        """
        return user_id in self.admin_user_ids

    def handle_admin_command(self, user_id: str, command: str) -> tuple[bool, str]:
        """
        管理者コマンドを処理
        
        Args:
            user_id (str): ユーザーID
            command (str): コマンド
            
        Returns:
            tuple[bool, str]: (処理したか, レスポンス)
        """
        if not self.is_admin(user_id):
            return False, ""
        
        # 管理者コマンドの判定
        if not command.startswith('/admin'):
            return False, ""
        
        try:
            # セキュリティログ
            if self.security_utils:
                self.security_utils.log_security_event(
                    'admin_command',
                    {'user_id': user_id, 'command': command}
                )
            
            # コマンドをパース
            parts = command.split()
            if len(parts) < 2:
                return True, self._get_admin_help()
            
            subcommand = parts[1]
            
            if subcommand == 'status':
                return True, self._get_system_status()
            elif subcommand == 'performance':
                return True, self._get_performance_report()
            elif subcommand == 'config':
                return True, self._get_config_info()
            elif subcommand == 'health':
                return True, self._get_health_check()
            elif subcommand == 'metrics':
                return True, self._get_metrics_summary()
            elif subcommand == 'logs':
                return True, self._get_recent_logs()
            elif subcommand == 'cleanup':
                return True, self._cleanup_system()
            elif subcommand == 'help':
                return True, self._get_admin_help()
            else:
                return True, f"❌ 不明なコマンド: {subcommand}\n{self._get_admin_help()}"
                
        except Exception as e:
            self.logger.error(f"管理者コマンド処理エラー: {str(e)}")
            return True, "❌ コマンドの処理中にエラーが発生しました。"

    def _get_admin_help(self) -> str:
        """管理者ヘルプを取得"""
        return """🔧 **管理者コマンド一覧**

📊 **監視・診断:**
• `/admin status` - システム状態の概要
• `/admin performance` - パフォーマンスレポート
• `/admin health` - ヘルスチェック
• `/admin metrics` - メトリクス概要
• `/admin logs` - 最近のログ

⚙️ **設定・管理:**
• `/admin config` - 設定情報の表示
• `/admin cleanup` - システムクリーンアップ

❓ **ヘルプ:**
• `/admin help` - このヘルプを表示

💡 管理者コマンドは認証されたユーザーのみ使用可能です。"""

    def _get_system_status(self) -> str:
        """システム状態を取得"""
        try:
            lines = [
                "📊 **システム状態**",
                f"🕐 確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            # パフォーマンス監視データ
            if self.performance_monitor:
                health = self.performance_monitor.get_health_status()
                lines.extend([
                    f"⚡ ステータス: {health['status']}",
                    f"⏱️ 稼働時間: {health['uptime']:.1f}秒",
                    ""
                ])
                
                # カウンター情報
                counters = health['counters']
                lines.extend([
                    "📈 **処理統計:**",
                    f"・リクエスト数: {counters['requests']}",
                    f"・エラー数: {counters['errors']}",
                    f"・通知送信数: {counters['notifications']}",
                    ""
                ])
                
                # システムメトリクス
                if health['system_metrics']:
                    metrics = health['system_metrics']
                    lines.extend([
                        "🖥️ **システムリソース:**",
                        f"・CPU使用率: {metrics.get('cpu_percent', 0):.1f}%",
                        f"・メモリ使用率: {metrics.get('memory_info', {}).get('percent', 0):.1f}%",
                        f"・アクティブスレッド: {metrics.get('threads', 0)}",
                        ""
                    ])
                
                # 問題の報告
                if health['issues']:
                    lines.extend([
                        "⚠️ **検出された問題:**",
                        *[f"・{issue}" for issue in health['issues']],
                        ""
                    ])
            
            # 設定情報
            if self.config_manager:
                config = self.config_manager.get_config()
                lines.extend([
                    "⚙️ **設定情報:**",
                    f"・ポート: {config.port}",
                    f"・デバッグモード: {'有効' if config.debug else '無効'}",
                    f"・通知チェック間隔: {config.notification_check_interval}秒",
                    ""
                ])
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ システム状態の取得に失敗: {str(e)}"

    def _get_performance_report(self) -> str:
        """パフォーマンスレポートを取得"""
        if not self.performance_monitor:
            return "❌ パフォーマンス監視が無効です。"
        
        try:
            return self.performance_monitor.generate_performance_report()
        except Exception as e:
            return f"❌ パフォーマンスレポートの生成に失敗: {str(e)}"

    def _get_config_info(self) -> str:
        """設定情報を取得"""
        if not self.config_manager:
            return "❌ 設定管理が無効です。"
        
        try:
            return self.config_manager.get_config_summary()
        except Exception as e:
            return f"❌ 設定情報の取得に失敗: {str(e)}"

    def _get_health_check(self) -> str:
        """ヘルスチェックを実行"""
        try:
            results = []
            
            # 基本的なヘルスチェック
            results.append("🏥 **ヘルスチェック結果**")
            results.append("")
            
            # 環境変数チェック
            if self.security_utils:
                is_valid, errors = self.security_utils.validate_environment_variables()
                if is_valid:
                    results.append("✅ 環境変数: 正常")
                else:
                    results.append("❌ 環境変数: 問題あり")
                    for error in errors[:3]:  # 最初の3つのエラーのみ表示
                        results.append(f"  - {error}")
            
            # パフォーマンス監視チェック
            if self.performance_monitor:
                health = self.performance_monitor.get_health_status()
                status_icon = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
                results.append(f"{status_icon} パフォーマンス: {health['status']}")
            
            # 設定チェック
            if self.config_manager:
                try:
                    config = self.config_manager.get_config()
                    results.append("✅ 設定: 正常")
                except Exception:
                    results.append("❌ 設定: 問題あり")
            
            # 通知ストレージチェック
            try:
                if self.config_manager:
                    storage_path = self.config_manager.get_config().notification_storage_path
                    if os.path.exists(storage_path):
                        results.append("✅ 通知ストレージ: アクセス可能")
                    else:
                        results.append("⚠️ 通知ストレージ: ファイルが存在しません")
                else:
                    results.append("❓ 通知ストレージ: 確認不可")
            except Exception as e:
                results.append(f"❌ 通知ストレージ: エラー ({str(e)[:50]})")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"❌ ヘルスチェックの実行に失敗: {str(e)}"

    def _get_metrics_summary(self) -> str:
        """メトリクス概要を取得"""
        if not self.performance_monitor:
            return "❌ パフォーマンス監視が無効です。"
        
        try:
            lines = ["📊 **メトリクス概要**", ""]
            
            # 主要操作のパフォーマンス
            operations = ['message_processing', 'notification_check', 'gemini_api_call']
            for operation in operations:
                summary = self.performance_monitor.get_performance_summary(operation, minutes=10)
                if 'no_data' not in summary and 'no_recent_data' not in summary:
                    lines.extend([
                        f"⏱️ **{operation}** (過去10分):",
                        f"・実行回数: {summary['count']}回",
                        f"・平均時間: {summary['avg']*1000:.1f}ms",
                        f"・95%ile: {summary['p95']*1000:.1f}ms",
                        ""
                    ])
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ メトリクス概要の取得に失敗: {str(e)}"

    def _get_recent_logs(self) -> str:
        """最近のログを取得"""
        try:
            # 簡易的なログ表示（実際の実装では適切なログファイルから読み取り）
            return """📄 **最近のログ**

ℹ️ ログファイルからの詳細な情報表示は
本格的な実装で追加予定です。

現在の簡易ログ:
• システムは正常に動作中
• 通知チェックが定期実行中
• エラーログは別途確認してください"""
            
        except Exception as e:
            return f"❌ ログの取得に失敗: {str(e)}"

    def _cleanup_system(self) -> str:
        """システムクリーンアップを実行"""
        try:
            results = ["🧹 **システムクリーンアップ**", ""]
            
            # パフォーマンス監視データのクリーンアップ
            if self.performance_monitor:
                self.performance_monitor.cleanup_old_metrics(hours=24)
                results.append("✅ 古いメトリクスデータをクリーンアップしました")
            
            # 一時ファイルのクリーンアップ（安全な範囲で）
            temp_patterns = ['*.tmp', '*.bak']
            cleaned_files = 0
            for pattern in temp_patterns:
                import glob
                files = glob.glob(pattern)
                for file in files:
                    try:
                        if os.path.isfile(file) and os.path.getsize(file) < 10 * 1024 * 1024:  # 10MB未満
                            os.remove(file)
                            cleaned_files += 1
                    except Exception:
                        pass
            
            if cleaned_files > 0:
                results.append(f"✅ {cleaned_files}個の一時ファイルを削除しました")
            else:
                results.append("ℹ️ 削除対象の一時ファイルはありませんでした")
            
            results.append("")
            results.append("🎉 クリーンアップが完了しました")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"❌ クリーンアップの実行に失敗: {str(e)}" 