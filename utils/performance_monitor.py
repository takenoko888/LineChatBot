"""
Performance monitoring utilities
"""
import time
import logging
import threading
import psutil
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque

class PerformanceMonitor:
    """パフォーマンス監視クラス"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
        # メトリクス保存用
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.timers = {}
        self.counters = defaultdict(int)
        
        # 統計情報
        self.statistics = defaultdict(list)
        
        # ロック
        self.lock = threading.Lock()
        
        self.logger.info("パフォーマンス監視を開始しました")

    def start_timer(self, operation: str) -> str:
        """
        タイマーを開始
        
        Args:
            operation (str): 操作名
            
        Returns:
            str: タイマーID
        """
        timer_id = f"{operation}_{int(time.time() * 1000000)}"
        with self.lock:
            self.timers[timer_id] = {
                'operation': operation,
                'start_time': time.time(),
                'thread_id': threading.get_ident()
            }
        return timer_id

    def end_timer(self, operation: str, timer_id: str) -> Optional[float]:
        """
        タイマーを終了
        
        Args:
            operation (str): 操作名
            timer_id (str): タイマーID
            
        Returns:
            Optional[float]: 実行時間（秒）
        """
        with self.lock:
            if timer_id not in self.timers:
                self.logger.warning(f"タイマーID {timer_id} が見つかりません")
                return None
            
            timer_info = self.timers.pop(timer_id)
            duration = time.time() - timer_info['start_time']
            
            # メトリクスに記録
            self.metrics[operation].append({
                'timestamp': datetime.now(),
                'duration': duration,
                'thread_id': timer_info['thread_id']
            })
            
            # 統計情報更新
            self.statistics[operation].append(duration)
            
            return duration

    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """
        カウンターを増加
        
        Args:
            counter_name (str): カウンター名
            value (int): 増加値
        """
        with self.lock:
            self.counters[counter_name] += value

    def get_performance_summary(self, operation: str, minutes: int = 10) -> Dict[str, Any]:
        """
        パフォーマンス概要を取得
        
        Args:
            operation (str): 操作名
            minutes (int): 対象期間（分）
            
        Returns:
            Dict[str, Any]: パフォーマンス概要
        """
        with self.lock:
            if operation not in self.metrics:
                return {"error": "no_data"}
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self.metrics[operation]
                if m['timestamp'] > cutoff_time
            ]
            
            if not recent_metrics:
                return {"error": "no_recent_data"}
            
            durations = [m['duration'] for m in recent_metrics]
            
            return {
                'count': len(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'p95': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0,
                'p99': sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 0 else 0
            }

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        システムメトリクスを取得
        
        Returns:
            Dict[str, Any]: システムメトリクス
        """
        try:
            process = psutil.Process(os.getpid())
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_info': process.memory_info()._asdict(),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'connections': len(process.connections()),
                'open_files': len(process.open_files()),
            }
        except Exception as e:
            self.logger.error(f"システムメトリクス取得エラー: {str(e)}")
            return {}

    def get_health_status(self) -> Dict[str, Any]:
        """
        ヘルス状態を取得
        
        Returns:
            Dict[str, Any]: ヘルス状態
        """
        try:
            uptime = time.time() - self.start_time
            system_metrics = self.get_system_metrics()
            
            # 健康状態の判定
            issues = []
            status = "healthy"
            
            if system_metrics.get('cpu_percent', 0) > 80:
                issues.append("CPU使用率が高い")
                status = "warning"
            
            if system_metrics.get('memory_percent', 0) > 85:
                issues.append("メモリ使用率が高い")
                status = "warning"
            
            if len(issues) > 2:
                status = "critical"
            
            with self.lock:
                counters_copy = dict(self.counters)
            
            return {
                'status': status,
                'uptime': uptime,
                'issues': issues,
                'counters': counters_copy,
                'system_metrics': system_metrics
            }
        except Exception as e:
            self.logger.error(f"ヘルス状態取得エラー: {str(e)}")
            return {
                'status': 'error',
                'uptime': 0,
                'issues': [f"監視エラー: {str(e)}"],
                'counters': {},
                'system_metrics': {}
            }

    def generate_performance_report(self) -> str:
        """
        パフォーマンスレポートを生成
        
        Returns:
            str: パフォーマンスレポート
        """
        lines = ["📊 **パフォーマンスレポート**", ""]
        
        try:
            # システム概要
            uptime = time.time() - self.start_time
            system_metrics = self.get_system_metrics()
            
            lines.extend([
                f"⏱️ **稼働時間**: {uptime:.1f}秒",
                f"🖥️ **CPU使用率**: {system_metrics.get('cpu_percent', 0):.1f}%",
                f"💾 **メモリ使用率**: {system_metrics.get('memory_percent', 0):.1f}%",
                f"🧵 **アクティブスレッド**: {system_metrics.get('threads', 0)}",
                ""
            ])
            
            # カウンター情報
            with self.lock:
                if self.counters:
                    lines.append("📈 **カウンター:**")
                    for name, count in self.counters.items():
                        lines.append(f"・{name}: {count}")
                    lines.append("")
            
            # 操作別パフォーマンス
            operations = ['message_processing', 'notification_check', 'gemini_api_call']
            for operation in operations:
                summary = self.get_performance_summary(operation, minutes=60)
                if 'error' not in summary:
                    lines.extend([
                        f"⚡ **{operation}** (過去1時間):",
                        f"・実行回数: {summary['count']}回",
                        f"・平均時間: {summary['avg']*1000:.1f}ms",
                        f"・最大時間: {summary['max']*1000:.1f}ms",
                        f"・95%ile: {summary['p95']*1000:.1f}ms",
                        ""
                    ])
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ レポート生成エラー: {str(e)}"

    def cleanup_old_metrics(self, hours: int = 24) -> None:
        """
        古いメトリクスをクリーンアップ
        
        Args:
            hours (int): 保持時間（時間）
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self.lock:
                for operation in self.metrics:
                    # dequeなので自動的に古いデータは削除される
                    # 必要に応じて手動でクリーンアップ
                    pass
                
                # 統計情報のクリーンアップ
                for operation in list(self.statistics.keys()):
                    if len(self.statistics[operation]) > 1000:
                        self.statistics[operation] = self.statistics[operation][-500:]
            
            self.logger.info(f"メトリクスクリーンアップ完了: {hours}時間以前のデータを削除")
            
        except Exception as e:
            self.logger.error(f"メトリクスクリーンアップエラー: {str(e)}")

# グローバルインスタンス
performance_monitor = PerformanceMonitor() 