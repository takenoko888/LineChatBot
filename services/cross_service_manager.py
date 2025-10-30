"""
Cross-Service Function Manager - 複数サービスの組み合わせ機能
"""
import logging
import asyncio
from typing import Dict, Optional, Any, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import itertools

from .service_integration_manager import service_integration_manager
from .context_aware_router import context_aware_router
from .hybrid_response_generator import hybrid_response_generator

@dataclass
class CrossServiceFunction:
    """クロスサービス機能定義"""
    function_id: str
    name: str
    description: str
    required_services: List[str]
    execution_sequence: List[Dict[str, Any]]
    input_parameters: Dict[str, Any]
    output_format: str
    priority: int = 5
    cooldown_minutes: int = 0

@dataclass
class ServiceOrchestration:
    """サービスオーケストレーション"""
    orchestration_id: str
    user_id: str
    primary_intent: str
    involved_services: List[str]
    execution_steps: List[Dict[str, Any]]
    shared_context: Dict[str, Any]
    status: str  # pending, executing, completed, failed
    created_at: datetime
    completed_at: Optional[datetime] = None

class CrossServiceFunctionManager:
    """クロスサービス機能マネージャー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 定義済みクロスサービス機能
        self.defined_functions = self._initialize_cross_service_functions()

        # 実行中のオーケストレーション
        self.active_orchestrations: Dict[str, ServiceOrchestration] = {}
        self.orchestration_lock = threading.Lock()

        # 機能実行履歴
        self.execution_history: Dict[str, List[Dict[str, Any]]] = {}
        self.history_lock = threading.Lock()

        self.logger.info("Cross-Service Function Managerを初期化しました")

    def _initialize_cross_service_functions(self) -> Dict[str, CrossServiceFunction]:
        """クロスサービス機能を初期化"""
        functions = {}

        # 毎日のルーチン設定機能
        functions["daily_routine_setup"] = CrossServiceFunction(
            function_id="daily_routine_setup",
            name="毎日のルーチン設定",
            description="通知と自動タスクを組み合わせて毎日のルーチンを設定",
            required_services=["notification", "auto_task"],
            execution_sequence=[
                {
                    "step": 1,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "起床通知",
                        "message": "おはようございます！今日も一日がんばりましょう。",
                        "datetime": "07:00",
                        "repeat": "daily"
                    }
                },
                {
                    "step": 2,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "就寝通知",
                        "message": "今日もお疲れ様でした。良い睡眠をお取りください。",
                        "datetime": "22:00",
                        "repeat": "daily"
                    }
                },
                {
                    "step": 3,
                    "service": "auto_task",
                    "method": "create",
                    "parameters": {
                        "title": "天気チェック",
                        "schedule": "daily 08:00",
                        "task_type": "weather_check"
                    }
                }
            ],
            input_parameters={
                "wake_up_time": {"type": "string", "required": False, "default": "07:00"},
                "bed_time": {"type": "string", "required": False, "default": "22:00"},
                "include_weather": {"type": "boolean", "required": False, "default": True}
            },
            output_format="structured",
            priority=10
        )

        # 週次レポート機能
        functions["weekly_report"] = CrossServiceFunction(
            function_id="weekly_report",
            name="週次レポート",
            description="通知、検索、自動タスクを組み合わせて週次レポートを生成",
            required_services=["notification", "search", "auto_task"],
            execution_sequence=[
                {
                    "step": 1,
                    "service": "search",
                    "method": "web",
                    "parameters": {
                        "query": "今週のニュース",
                        "type": "news"
                    }
                },
                {
                    "step": 2,
                    "service": "auto_task",
                    "method": "create",
                    "parameters": {
                        "title": "週次レポート生成",
                        "schedule": "weekly monday 09:00",
                        "task_type": "report_generation"
                    }
                },
                {
                    "step": 3,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "週次レポート",
                        "message": "今週のレポートが生成されました。確認してください。",
                        "datetime": "monday 09:30",
                        "repeat": "weekly"
                    }
                }
            ],
            input_parameters={
                "report_topics": {"type": "list", "required": False, "default": ["ニュース", "天気", "予定"]},
                "report_time": {"type": "string", "required": False, "default": "monday 09:00"}
            },
            output_format="structured",
            priority=8
        )

        # 旅行計画機能
        functions["travel_planning"] = CrossServiceFunction(
            function_id="travel_planning",
            name="旅行計画",
            description="天気、検索、通知を組み合わせて旅行計画を作成",
            required_services=["weather", "search", "notification"],
            execution_sequence=[
                {
                    "step": 1,
                    "service": "weather",
                    "method": "forecast",
                    "parameters": {
                        "location": "destination"
                    }
                },
                {
                    "step": 2,
                    "service": "search",
                    "method": "web",
                    "parameters": {
                        "query": "destination 観光スポット",
                        "type": "general"
                    }
                },
                {
                    "step": 3,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "旅行リマインダー",
                        "message": "destinationへの旅行の準備を忘れずに。",
                        "datetime": "1 day before travel",
                        "repeat": "none"
                    }
                }
            ],
            input_parameters={
                "destination": {"type": "string", "required": True},
                "travel_date": {"type": "string", "required": True},
                "duration_days": {"type": "integer", "required": False, "default": 1}
            },
            output_format="structured",
            priority=9
        )

        # 健康管理機能
        functions["health_monitoring"] = CrossServiceFunction(
            function_id="health_monitoring",
            name="健康管理",
            description="通知と自動タスクを組み合わせて健康管理を支援",
            required_services=["notification", "auto_task"],
            execution_sequence=[
                {
                    "step": 1,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "水分補給のリマインダー",
                        "message": "水分補給の時間です。コップ一杯の水を飲んでください。",
                        "datetime": "every 2 hours",
                        "repeat": "daily"
                    }
                },
                {
                    "step": 2,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "休憩のリマインダー",
                        "message": "長時間の作業です。5分間休憩を取って目を休めましょう。",
                        "datetime": "every 1 hour",
                        "repeat": "daily"
                    }
                },
                {
                    "step": 3,
                    "service": "auto_task",
                    "method": "create",
                    "parameters": {
                        "title": "健康チェック",
                        "schedule": "weekly sunday 20:00",
                        "task_type": "health_review"
                    }
                }
            ],
            input_parameters={
                "water_reminder": {"type": "boolean", "required": False, "default": True},
                "break_reminder": {"type": "boolean", "required": False, "default": True},
                "weekly_review": {"type": "boolean", "required": False, "default": True}
            },
            output_format="structured",
            priority=8
        )

        # 学習支援機能
        functions["study_assistant"] = CrossServiceFunction(
            function_id="study_assistant",
            name="学習支援",
            description="検索、通知、自動タスクを組み合わせて学習を支援",
            required_services=["search", "notification", "auto_task"],
            execution_sequence=[
                {
                    "step": 1,
                    "service": "search",
                    "method": "web",
                    "parameters": {
                        "query": "study_topic 学習方法",
                        "type": "educational"
                    }
                },
                {
                    "step": 2,
                    "service": "notification",
                    "method": "add",
                    "parameters": {
                        "title": "学習リマインダー",
                        "message": "学習の時間です。今日のトピックに取り組みましょう。",
                        "datetime": "study_time",
                        "repeat": "daily"
                    }
                },
                {
                    "step": 3,
                    "service": "auto_task",
                    "method": "create",
                    "parameters": {
                        "title": "学習進捗確認",
                        "schedule": "weekly friday 19:00",
                        "task_type": "study_progress"
                    }
                }
            ],
            input_parameters={
                "study_topic": {"type": "string", "required": True},
                "study_time": {"type": "string", "required": False, "default": "19:00"},
                "study_days": {"type": "list", "required": False, "default": ["monday", "wednesday", "friday"]}
            },
            output_format="structured",
            priority=7
        )

        return functions

    async def execute_cross_service_function(
        self,
        function_id: str,
        user_id: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        クロスサービス機能を実行

        Args:
            function_id: 機能ID
            user_id: ユーザーID
            parameters: 実行パラメータ
            context: 追加コンテキスト

        Returns:
            実行結果
        """
        try:
            # 機能定義を取得
            function = self.defined_functions.get(function_id)
            if not function:
                return {
                    "success": False,
                    "error": f"機能が見つかりません: {function_id}"
                }

            # オーケストレーション作成
            orchestration = self._create_orchestration(
                function_id, user_id, function, parameters, context
            )

            # 実行開始
            result = await self._execute_orchestration(orchestration)

            # 履歴保存
            self._save_execution_history(user_id, function_id, result)

            return result

        except Exception as e:
            self.logger.error(f"クロスサービス機能実行エラー: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "function_id": function_id
            }

    def _create_orchestration(
        self,
        function_id: str,
        user_id: str,
        function: CrossServiceFunction,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ServiceOrchestration:
        """オーケストレーションを作成"""
        orchestration_id = f"orch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:4]}"

        # 実行ステップのカスタマイズ
        customized_steps = self._customize_execution_steps(
            function.execution_sequence, parameters, context
        )

        orchestration = ServiceOrchestration(
            orchestration_id=orchestration_id,
            user_id=user_id,
            primary_intent=function.name,
            involved_services=function.required_services,
            execution_steps=customized_steps,
            shared_context={
                "user_id": user_id,
                "function_id": function_id,
                "parameters": parameters,
                "context": context or {}
            },
            status="pending",
            created_at=datetime.now()
        )

        # アクティブオーケストレーションに登録
        with self.orchestration_lock:
            self.active_orchestrations[orchestration_id] = orchestration

        return orchestration

    def _customize_execution_steps(
        self,
        base_steps: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """実行ステップをカスタマイズ"""
        customized_steps = []

        for step in base_steps:
            customized_step = step.copy()

            # パラメータのカスタマイズ
            if "parameters" in customized_step:
                for param_key, param_config in customized_step["parameters"].items():
                    if isinstance(param_config, str) and param_config in parameters:
                        customized_step["parameters"][param_key] = parameters[param_config]
                    elif param_config == "context_value" and context:
                        # コンテキストから値を取得
                        customized_step["parameters"][param_key] = context.get(param_key, param_config)

            customized_steps.append(customized_step)

        return customized_steps

    async def _execute_orchestration(self, orchestration: ServiceOrchestration) -> Dict[str, Any]:
        """オーケストレーションを実行"""
        try:
            # ステータス更新
            orchestration.status = "executing"

            results = []
            step_results = {}

            # 各ステップを実行
            for i, step in enumerate(orchestration.execution_steps):
                step_result = await self._execute_orchestration_step(
                    orchestration, step, step_results
                )

                results.append(step_result)
                step_results[f"step_{i+1}"] = step_result

                # エラーチェック
                if not step_result.get("success", False):
                    orchestration.status = "failed"
                    return {
                        "success": False,
                        "error": f"ステップ {i+1} でエラーが発生しました",
                        "failed_step": step.get("step", i+1),
                        "step_results": results
                    }

            # 成功
            orchestration.status = "completed"
            orchestration.completed_at = datetime.now()

            return {
                "success": True,
                "orchestration_id": orchestration.orchestration_id,
                "function_name": orchestration.primary_intent,
                "results": results,
                "step_results": step_results,
                "execution_time": (orchestration.completed_at - orchestration.created_at).total_seconds()
            }

        except Exception as e:
            orchestration.status = "failed"
            return {
                "success": False,
                "error": str(e),
                "orchestration_id": orchestration.orchestration_id
            }

    async def _execute_orchestration_step(
        self,
        orchestration: ServiceOrchestration,
        step: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """オーケストレーションステップを実行"""
        try:
            service = step.get("service")
            method = step.get("method", "default")
            parameters = step.get("parameters", {})

            # サービス統合マネージャーを通じて実行
            result = await service_integration_manager._execute_service_method(
                service, method, parameters, orchestration.shared_context
            )

            return {
                "success": result.get("success", False),
                "service": service,
                "method": method,
                "parameters": parameters,
                "result": result,
                "step": step.get("step", 0),
                "executed_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "service": step.get("service"),
                "method": step.get("method"),
                "error": str(e),
                "step": step.get("step", 0)
            }

    def _save_execution_history(self, user_id: str, function_id: str, result: Dict[str, Any]):
        """実行履歴を保存"""
        with self.history_lock:
            if user_id not in self.execution_history:
                self.execution_history[user_id] = []

            history_entry = {
                "function_id": function_id,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }

            self.execution_history[user_id].append(history_entry)

            # 履歴を制限（最新50件）
            if len(self.execution_history[user_id]) > 50:
                self.execution_history[user_id] = self.execution_history[user_id][-50:]

    def analyze_cross_service_patterns(self, user_id: str) -> Dict[str, Any]:
        """クロスサービスパターンを分析"""
        with self.history_lock:
            user_history = self.execution_history.get(user_id, [])

            if not user_history:
                return {"total_executions": 0, "patterns": []}

            # 機能別カウント
            function_counts = {}
            for entry in user_history:
                func_id = entry.get("function_id", "unknown")
                function_counts[func_id] = function_counts.get(func_id, 0) + 1

            # 時間帯別分析
            time_patterns = self._analyze_time_patterns(user_history)

            # 成功率分析
            success_rate = len([e for e in user_history if e.get("result", {}).get("success", False)]) / len(user_history)

            return {
                "total_executions": len(user_history),
                "function_distribution": function_counts,
                "success_rate": success_rate,
                "time_patterns": time_patterns,
                "most_used_function": max(function_counts, key=function_counts.get),
                "average_executions_per_day": len(user_history) / 30  # 簡易計算
            }

    def _analyze_time_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """時間パターンを分析"""
        hourly_patterns = {}
        daily_patterns = {}

        for entry in history:
            timestamp_str = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp_str)
                hour = dt.hour
                day = dt.weekday()

                hourly_patterns[hour] = hourly_patterns.get(hour, 0) + 1

                day_names = ["月", "火", "水", "木", "金", "土", "日"]
                daily_patterns[day_names[day]] = daily_patterns.get(day_names[day], 0) + 1

            except:
                pass

        return {
            "hourly": hourly_patterns,
            "daily": daily_patterns
        }

    def get_available_cross_functions(self) -> List[Dict[str, Any]]:
        """利用可能なクロスサービス機能一覧を取得"""
        functions = []
        for func_id, function in self.defined_functions.items():
            functions.append({
                "function_id": func_id,
                "name": function.name,
                "description": function.description,
                "required_services": function.required_services,
                "input_parameters": function.input_parameters,
                "priority": function.priority
            })

        # 優先度順にソート
        functions.sort(key=lambda f: f["priority"], reverse=True)
        return functions

    def create_custom_cross_function(
        self,
        name: str,
        description: str,
        required_services: List[str],
        execution_sequence: List[Dict[str, Any]],
        input_parameters: Dict[str, Any],
        output_format: str = "structured"
    ) -> str:
        """カスタムクロスサービス機能を作成"""
        function_id = f"custom_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        custom_function = CrossServiceFunction(
            function_id=function_id,
            name=name,
            description=description,
            required_services=required_services,
            execution_sequence=execution_sequence,
            input_parameters=input_parameters,
            output_format=output_format,
            priority=5
        )

        self.defined_functions[function_id] = custom_function

        self.logger.info(f"カスタムクロスサービス機能を作成: {function_id}")
        return function_id

    async def suggest_cross_service_functions(
        self,
        user_query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """クロスサービス機能を提案"""
        suggestions = []

        try:
            # ルーティング分析
            routing_decision = await context_aware_router.analyze_and_route(
                user_query, user_id, context
            )

            # 複数のサービスが必要な場合
            if len(routing_decision.analysis.secondary_services) > 0:
                # 既存のクロスサービス機能から提案
                available_functions = self.get_available_cross_functions()

                for function in available_functions:
                    # 関連性の計算
                    relevance_score = self._calculate_function_relevance(
                        function, routing_decision, user_query
                    )

                    if relevance_score > 0.5:  # 一定以上の関連性がある場合
                        suggestions.append({
                            "function_id": function["function_id"],
                            "name": function["name"],
                            "description": function["description"],
                            "relevance_score": relevance_score,
                            "required_services": function["required_services"],
                            "estimated_benefits": self._estimate_function_benefits(function)
                        })

            # 関連度順にソート
            suggestions.sort(key=lambda s: s["relevance_score"], reverse=True)

            return suggestions[:5]  # 上位5件

        except Exception as e:
            self.logger.warning(f"クロスサービス機能提案エラー: {str(e)}")
            return []

    def _calculate_function_relevance(
        self,
        function: Dict[str, Any],
        routing_decision: "RoutingDecision",
        user_query: str
    ) -> float:
        """機能の関連性を計算"""
        score = 0.0

        # サービス一致度
        required_services = function.get("required_services", [])
        primary_service = routing_decision.selected_service
        secondary_services = routing_decision.analysis.secondary_services

        if primary_service in required_services:
            score += 0.4

        for service in secondary_services:
            if service in required_services:
                score += 0.2

        # クエリキーワード一致度
        query_keywords = set(user_query.lower().split())
        function_name_keywords = set(function.get("name", "").lower().split())
        function_desc_keywords = set(function.get("description", "").lower().split())

        name_matches = len(query_keywords & function_name_keywords)
        desc_matches = len(query_keywords & function_desc_keywords)

        score += min(name_matches * 0.1, 0.2)
        score += min(desc_matches * 0.05, 0.2)

        # インテント一致度
        intent_type = routing_decision.analysis.intent_type
        if intent_type in function.get("description", "").lower():
            score += 0.1

        return min(1.0, score)

    def _estimate_function_benefits(self, function: Dict[str, Any]) -> List[str]:
        """機能の利点を推定"""
        benefits = []

        required_services = function.get("required_services", [])

        if len(required_services) > 1:
            benefits.append("複数の機能の連携による総合的な対応")
        if "notification" in required_services:
            benefits.append("適切なタイミングでの通知")
        if "auto_task" in required_services:
            benefits.append("自動化による手間削減")
        if "search" in required_services:
            benefits.append("最新情報の取得")
        if "weather" in required_services:
            benefits.append("天気情報を活用した計画")

        return benefits

    def get_orchestration_status(self, orchestration_id: str) -> Optional[ServiceOrchestration]:
        """オーケストレーションの状態を取得"""
        with self.orchestration_lock:
            return self.active_orchestrations.get(orchestration_id)

# グローバルインスタンス
cross_service_manager = CrossServiceFunctionManager()
