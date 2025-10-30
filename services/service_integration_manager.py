"""
Service Integration Manager - 既存サービスとAI機能の統合
"""
import logging
import asyncio
from typing import Dict, Optional, Any, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import inspect

from .ai_function_plugin import BaseAIFunction, AIFunction, ai_function_registry
from .flexible_ai_service import flexible_ai_service

@dataclass
class ServiceCapability:
    """サービス能力定義"""
    service_name: str
    service_type: str  # notification, weather, search, auto_task, etc.
    methods: List[str]
    description: str
    parameters: Dict[str, Any]
    trigger_keywords: List[str]
    priority: int = 5
    requires_auth: bool = False

class ServiceIntegrationManager:
    """サービス統合マネージャー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 登録されたサービス
        self.registered_services: Dict[str, Any] = {}

        # サービス能力マッピング
        self.service_capabilities: Dict[str, ServiceCapability] = {}

        # インテントからサービスへのマッピング
        self.intent_service_mapping: Dict[str, List[str]] = {}

        # サービス依存関係
        self.service_dependencies: Dict[str, List[str]] = {}

        # 初期化
        self._initialize_default_mappings()

        # AI Function Registryに全サービスを登録
        self._register_all_services_as_ai_functions()

        self.logger.info("Service Integration Managerを初期化しました")

    def _register_all_services_as_ai_functions(self):
        """すべてのサービス機能をAI Function Registryに登録"""
        try:
            # 各サービスをAI機能として登録
            for service_name, capability in self.service_capabilities.items():
                self._register_service_as_ai_function(service_name, capability)

            self.logger.info(f"AI Function Registryに全{len(self.service_capabilities)}個のサービス機能を登録しました")

        except Exception as e:
            self.logger.error(f"サービス機能のAI Function Registry登録エラー: {str(e)}")

    def _register_service_as_ai_function(self, service_name: str, capability: ServiceCapability):
        """個別のサービスをAI機能として登録"""
        try:
            # 動的にAI機能クラスを作成
            service_function_class = self._create_service_ai_function_class(service_name, capability)

            # AI機能定義を作成
            function_def = AIFunction(
                name=f"{service_name}_handler",
                description=capability.description,
                version="1.0.0",
                author="service_integration",
                parameters=capability.parameters,
                trigger_keywords=capability.trigger_keywords,
                priority=capability.priority
            )

            # AI機能インスタンスを作成・登録
            function_instance = service_function_class(function_def)
            ai_function_registry.register_function(function_instance)

            self.logger.info(f"サービス {service_name} をAI機能として登録しました")

        except Exception as e:
            self.logger.error(f"サービス {service_name} のAI機能登録エラー: {str(e)}")

    def _create_service_ai_function_class(self, service_name: str, capability: ServiceCapability):
        """サービス用のAI機能クラスを動的に作成"""
        class ServiceAIFunction(BaseAIFunction):
            def __init__(self, function_def: AIFunction):
                super().__init__(function_def)
                self.service_name = service_name
                self.capability = capability

            async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    # サービス統合マネージャーで実行
                    from .integrated_service_manager import integrated_service_manager

                    # 統合サービスリクエストを作成
                    request = integrated_service_manager._create_request_from_ai_function(
                        self.service_name, parameters, user_id, context
                    )

                    # サービス実行
                    result = await integrated_service_manager.process_integrated_request(request)

                    return {
                        "success": True,
                        "service": service_name,
                        "result": result.response,
                        "method_used": parameters.get("method", "default"),
                        "executed_at": datetime.now().isoformat(),
                        "ai_function": True
                    }

                except Exception as e:
                    self.logger.error(f"サービス実行エラー ({service_name}): {str(e)}")
                    return {
                        "success": False,
                        "service": service_name,
                        "error": str(e),
                        "parameters": parameters,
                        "ai_function": True
                    }

        return ServiceAIFunction

    def _initialize_default_mappings(self):
        """デフォルトのマッピングを初期化"""
        # 通知サービス
        self.service_capabilities["notification"] = ServiceCapability(
            service_name="notification",
            service_type="notification",
            methods=["add", "list", "delete", "edit", "check"],
            description="通知の作成、管理、送信機能",
            parameters={
                "title": {"type": "string", "required": False},
                "message": {"type": "string", "required": True},
                "datetime": {"type": "string", "required": True},
                "repeat": {"type": "string", "required": False}
            },
            trigger_keywords=[
                "通知", "リマインド", "教えて", "起こして", "思い出して",
                "毎日", "毎週", "毎月", "時間", "分後", "後に"
            ],
            priority=8
        )

        # 天気サービス
        self.service_capabilities["weather"] = ServiceCapability(
            service_name="weather",
            service_type="weather",
            methods=["current", "forecast"],
            description="天気情報の取得機能",
            parameters={
                "location": {"type": "string", "required": True}
            },
            trigger_keywords=[
                "天気", "気温", "予報", "雨", "晴れ", "曇り", "雪"
            ],
            priority=7
        )

        # 検索サービス
        self.service_capabilities["search"] = ServiceCapability(
            service_name="search",
            service_type="search",
            methods=["web", "news", "custom"],
            description="ウェブ検索機能",
            parameters={
                "query": {"type": "string", "required": True},
                "type": {"type": "string", "required": False}
            },
            trigger_keywords=[
                "検索", "調べて", "教えて", "情報", "ニュース", "最新"
            ],
            priority=6
        )

        # 自動タスクサービス
        self.service_capabilities["auto_task"] = ServiceCapability(
            service_name="auto_task",
            service_type="automation",
            methods=["create", "list", "execute", "delete", "toggle"],
            description="自動実行タスクの管理",
            parameters={
                "task_type": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "schedule": {"type": "string", "required": True}
            },
            trigger_keywords=[
                "自動", "定期的に", "毎日", "毎週", "スケジュール", "決まった時間に"
            ],
            priority=7
        )

        # インテントマッピング
        self.intent_service_mapping = {
            "create_notification": ["notification"],
            "list_notifications": ["notification"],
            "delete_notification": ["notification"],
            "get_weather": ["weather"],
            "search_web": ["search"],
            "search_news": ["search"],
            "create_auto_task": ["auto_task"],
            "manage_auto_task": ["auto_task"],
            "general_query": ["search", "notification", "weather"],
            "complex_task": ["auto_task", "notification", "search"],
            "composite_task": ["notification", "weather", "search"]  # 複合タスク用
        }

    def register_service(
        self,
        service_name: str,
        service_instance: Any,
        capability: ServiceCapability
    ):
        """サービスを登録"""
        try:
            self.registered_services[service_name] = service_instance
            self.service_capabilities[service_name] = capability

            self.logger.info(f"サービスを登録: {service_name}")

            # AIプラグインとして登録
            self._register_as_ai_plugin(service_name, capability, service_instance)

        except Exception as e:
            self.logger.error(f"サービス登録エラー ({service_name}): {str(e)}")
            raise

    def _register_as_ai_plugin(self, service_name: str, capability: ServiceCapability, service_instance: Any):
        """AIプラグインとして登録"""
        try:
            # 動的にプラグインクラスを生成
            plugin_class = self._create_service_plugin_class(service_name, capability, service_instance)

            # 機能定義を作成
            function_def = AIFunction(
                name=f"{service_name}_handler",
                description=capability.description,
                version="1.0.0",
                author="service_integration",
                parameters=capability.parameters,
                trigger_keywords=capability.trigger_keywords,
                priority=capability.priority
            )

            # プラグインインスタンスを作成・登録
            plugin_instance = plugin_class(function_def)
            ai_function_registry.register_function(plugin_instance)

            self.logger.info(f"AIプラグインとして登録: {service_name}")

        except Exception as e:
            self.logger.error(f"AIプラグイン登録エラー ({service_name}): {str(e)}")

    def _create_service_plugin_class(self, service_name: str, capability: ServiceCapability, service_instance: Any):
        """サービス用のプラグインクラスを動的に作成"""

        class ServicePlugin(BaseAIFunction):
            def __init__(self, function_def: AIFunction):
                super().__init__(function_def)
                self.service_name = service_name
                self.capability = capability
                self.service_instance = service_instance

            async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    # サービスメソッドの実行
                    result = await self._execute_service_method(parameters, context)

                    return {
                        "success": True,
                        "service": service_name,
                        "result": result,
                        "method_used": parameters.get("method", "unknown"),
                        "executed_at": datetime.now().isoformat()
                    }

                except Exception as e:
                    self.logger.error(f"サービス実行エラー ({service_name}): {str(e)}")
                    return {
                        "success": False,
                        "service": service_name,
                        "error": str(e),
                        "parameters": parameters
                    }

            async def _execute_service_method(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
                """サービスメソッドを実行"""
                method = parameters.get("method", "default")

                if hasattr(self.service_instance, method):
                    method_obj = getattr(self.service_instance, method)

                    # メソッドがコルーチンかチェック
                    if asyncio.iscoroutinefunction(method_obj):
                        return await method_obj(**parameters)
                    else:
                        return method_obj(**parameters)

                # デフォルトの実行方法
                return await self._execute_default_service(parameters, context)

            async def _execute_default_service(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
                """デフォルトのサービス実行"""
                # サービス固有のデフォルト実行ロジック
                service_type = self.capability.service_type

                if service_type == "notification":
                    return await self._handle_notification_service(parameters, context)
                elif service_type == "weather":
                    return await self._handle_weather_service(parameters, context)
                elif service_type == "search":
                    return await self._handle_search_service(parameters, context)
                elif service_type == "auto_task":
                    return await self._handle_auto_task_service(parameters, context)
                else:
                    return {"message": "サービスが利用できません"}

            async def _handle_notification_service(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
                """通知サービス処理"""
                # 簡易的な通知処理
                message = parameters.get("message", "")
                return {
                    "notification": {
                        "message": message,
                        "status": "created",
                        "id": f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    }
                }

            async def _handle_weather_service(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
                """天気サービス処理"""
                location = parameters.get("location", "東京")
                return {
                    "weather": {
                        "location": location,
                        "temperature": "22°C",
                        "condition": "晴れ",
                        "note": "（実際のWeatherServiceとの連携が必要）"
                    }
                }

            async def _handle_search_service(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
                """検索サービス処理"""
                query = parameters.get("query", "")
                return {
                    "search": {
                        "query": query,
                        "results": ["検索結果1", "検索結果2"],
                        "note": "（実際のSearchServiceとの連携が必要）"
                    }
                }

            async def _handle_auto_task_service(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
                """自動タスクサービス処理"""
                title = parameters.get("title", "")
                return {
                    "auto_task": {
                        "title": title,
                        "status": "scheduled",
                        "id": f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "note": "（実際のAutoTaskServiceとの連携が必要）"
                    }
                }

    def _format_service_result(self, service_name: str, result: Any) -> str:
        """サービス実行結果をフォーマット"""
        try:
            if isinstance(result, dict):
                if service_name == "notification":
                    return f"通知: {result.get('notification', {}).get('message', '処理完了')}"
                elif service_name == "weather":
                    weather = result.get('weather', {})
                    return f"天気: {weather.get('location', '不明')} - {weather.get('condition', '不明')} {weather.get('temperature', '')}"
                elif service_name == "search":
                    search = result.get('search', {})
                    return f"検索結果: {search.get('query', '')} - {len(search.get('results', []))}件の結果"
                elif service_name == "auto_task":
                    task = result.get('auto_task', {})
                    return f"タスク: {task.get('title', '')} - {task.get('status', '処理中')}"
                else:
                    return str(result)
            else:
                return str(result)
        except Exception as e:
            self.logger.error(f"結果フォーマットエラー ({service_name}): {str(e)}")
            return f"サービス {service_name} の実行結果"

    def get_service_capability(self, service_name: str) -> Optional[ServiceCapability]:
        """サービス能力を取得"""
        return self.service_capabilities.get(service_name)

    def find_services_for_intent(self, intent: str) -> List[str]:
        """インテントに適したサービスを取得"""
        services = self.intent_service_mapping.get(intent, [])

        # キーワードベースのフォールバック
        if not services:
            # クエリからキーワードを抽出してサービスを検索
            services = self._find_services_by_keywords(intent)

        return services

    def _find_services_by_keywords(self, text: str) -> List[str]:
        """キーワードからサービスを検索"""
        found_services = []
        text_lower = text.lower()

        for service_name, capability in self.service_capabilities.items():
            for keyword in capability.trigger_keywords:
                if keyword in text_lower:
                    found_services.append(service_name)
                    break

        return found_services

    def get_available_services(self) -> Dict[str, ServiceCapability]:
        """利用可能なサービス一覧を取得"""
        return self.service_capabilities.copy()

    def analyze_service_combinations(self, user_intent: str) -> List[Dict[str, Any]]:
        """サービス組み合わせの分析"""
        # 単一サービスの場合
        single_services = self.find_services_for_intent(user_intent)

        # 複数サービス組み合わせの場合
        combinations = []

        for service in single_services:
            combinations.append({
                "type": "single",
                "services": [service],
                "description": f"{service} サービスの使用",
                "confidence": 0.8
            })

        # 複合的なタスクの場合の組み合わせ
        if len(single_services) > 1:
            combinations.append({
                "type": "combined",
                "services": single_services,
                "description": f"{', '.join(single_services)} サービスの連携",
                "confidence": 0.6
            })

        return combinations

    def create_service_context(self, service_name: str, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """サービス実行用のコンテキストを作成"""
        context = {
            "service_name": service_name,
            "user_id": user_id,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat(),
            "ai_enhanced": True
        }

        # サービス固有のコンテキスト追加
        capability = self.get_service_capability(service_name)
        if capability:
            context["service_type"] = capability.service_type
            context["methods_available"] = capability.methods

        return context

    async def _execute_service_method(
        self,
        service_name: str,
        method: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        サービスメソッドを実行

        Args:
            service_name: サービス名
            method: メソッド名
            parameters: パラメータ
            context: コンテキスト

        Returns:
            実行結果
        """
        try:
            capability = self.get_service_capability(service_name)
            if not capability:
                return {"success": False, "error": f"Unknown service: {service_name}"}

            # まず実サービスが登録されていれば優先して呼び出す（安定運用向け）
            service_instance = self.registered_services.get(service_name)
            if service_instance is not None:
                user_id = context.get("user_id", "default")

                # 通知サービス
                if service_name == "notification":
                    if method == "add":
                        title = parameters.get("title", "通知")
                        message = parameters.get("message", "")
                        datetime_str = parameters.get("datetime")
                        repeat = parameters.get("repeat", "none")
                        priority = parameters.get("priority", "medium")
                        if not datetime_str:
                            return {"success": False, "error": "datetime is required"}
                        try:
                            nid = service_instance.add_notification(
                                user_id=user_id,
                                title=title,
                                message=message,
                                datetime_str=datetime_str,
                                priority=priority,
                                repeat=repeat,
                            )
                            return {
                                "success": bool(nid),
                                "notification": {
                                    "id": nid,
                                    "title": title,
                                    "message": message,
                                    "datetime": datetime_str,
                                    "repeat": repeat,
                                },
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    elif method == "list":
                        try:
                            notes = service_instance.get_notifications(user_id)
                            return {"success": True, "count": len(notes)}
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    elif method == "delete":
                        nid = parameters.get("notification_id")
                        if not nid:
                            return {"success": False, "error": "notification_id is required"}
                        try:
                            ok = service_instance.delete_notification(user_id, nid)
                            return {"success": ok}
                        except Exception as e:
                            return {"success": False, "error": str(e)}

                # 天気サービス
                if service_name == "weather":
                    try:
                        location = parameters.get("location", "東京")
                        if method == "current" and hasattr(service_instance, "get_current_weather"):
                            w = service_instance.get_current_weather(location)
                            return {"success": True, "weather": (w if isinstance(w, dict) else getattr(w, "__dict__", {}))}
                        if method == "forecast" and hasattr(service_instance, "get_weather_forecast"):
                            f = service_instance.get_weather_forecast(location)
                            return {"success": True, "forecast": getattr(f, "__dict__", f)}
                    except Exception as e:
                        return {"success": False, "error": str(e)}

                # 検索サービス
                if service_name == "search":
                    try:
                        query = parameters.get("query", "")
                        result_type = "news" if method == "news" else "web"
                        if hasattr(service_instance, "search"):
                            res = service_instance.search(query, result_type=result_type, max_results=parameters.get("max_results", 3), japan_only=True)
                            return {"success": True, "search": {"query": query, "results": res}}
                    except Exception as e:
                        return {"success": False, "error": str(e)}

                # 自動タスクサービス
                if service_name == "auto_task":
                    try:
                        if method == "create" and hasattr(service_instance, "create_auto_task"):
                            task_id = service_instance.create_auto_task(
                                user_id=user_id,
                                task_type=parameters.get("task_type"),
                                title=parameters.get("title", "自動タスク"),
                                description=parameters.get("description", "自動実行タスク"),
                                schedule_pattern=parameters.get("schedule_pattern", "daily"),
                                schedule_time=parameters.get("schedule_time", "08:00"),
                                parameters=parameters.get("parameters", {}),
                            )
                            return {"success": bool(task_id), "auto_task": {"id": task_id}}
                        if method == "delete" and hasattr(service_instance, "delete_task"):
                            ok = service_instance.delete_task(user_id, parameters.get("task_id", ""))
                            return {"success": ok}
                        if method == "toggle" and hasattr(service_instance, "toggle_task"):
                            ok = service_instance.toggle_task(user_id, parameters.get("task_id", ""))
                            return {"success": ok}
                        if method == "list" and hasattr(service_instance, "get_user_tasks"):
                            tasks = service_instance.get_user_tasks(user_id)
                            return {"success": True, "count": len(tasks)}
                    except Exception as e:
                        return {"success": False, "error": str(e)}

            # 実サービスが未登録の場合や、該当メソッドがない場合はデフォルトのハンドラにフォールバック
            if service_name == "notification":
                return await self._handle_notification_service(parameters, context)
            elif service_name == "weather":
                return await self._handle_weather_service(parameters, context)
            elif service_name == "search":
                return await self._handle_search_service(parameters, context)
            elif service_name == "auto_task":
                return await self._handle_auto_task_service(parameters, context)
            else:
                return {"success": False, "error": f"Unsupported service: {service_name}"}

        except Exception as e:
            self.logger.error(f"サービス実行エラー ({service_name}.{method}): {str(e)}")
            return {"success": False, "error": str(e)}

# グローバルインスタンス
service_integration_manager = ServiceIntegrationManager()
