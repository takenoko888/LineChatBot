"""
Integrated Service Manager - 既存機能とAI機能の完全統合
"""
import logging
import asyncio
from typing import Dict, Optional, Any, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os
import threading

from .service_integration_manager import service_integration_manager
from .context_aware_router import context_aware_router
from .hybrid_response_generator import hybrid_response_generator
from .cross_service_manager import cross_service_manager
from .flexible_ai_service import flexible_ai_service

@dataclass
class IntegratedServiceRequest:
    """統合サービスリクエスト"""
    query: str
    user_id: str = "default"
    context: Optional[Dict[str, Any]] = None
    request_type: str = "auto"  # auto, direct_service, cross_function, ai_enhanced
    priority: str = "normal"  # low, normal, high, urgent
    enable_fallback: bool = True
    timeout_seconds: int = 30
    # AI Function統合用のフィールド
    ai_function_request: bool = False
    service_override: Optional[str] = None
    parameters_override: Optional[Dict[str, Any]] = None

@dataclass
class IntegratedServiceResponse:
    """統合サービス応答"""
    response: str
    service_used: str
    execution_path: List[str]
    processing_time: float
    confidence_score: float
    components_used: Dict[str, Any]
    suggestions: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]

class IntegratedServiceManager:
    """統合サービスマネージャー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # サブマネージャー
        self.service_integration = service_integration_manager
        self.intent_router = context_aware_router
        self.response_generator = hybrid_response_generator
        self.cross_service = cross_service_manager
        self.flexible_ai = flexible_ai_service

        # 実行統計
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        self.stats_lock = threading.Lock()

        # システム状態
        self.system_status = {
            "initialized": True,
            "last_health_check": datetime.now(),
            "available_services": [],
            "performance_mode": "normal",
            "mock_mode": os.getenv('MOCK_MODE', 'false').lower() == 'true'
        }

        # サービス登録
        self._register_default_services()

        if self.system_status["mock_mode"]:
            self.logger.info("🧪 統合サービスマネージャーをモックモードで初期化しました")

    def _register_default_services(self):
        """デフォルトサービスを登録"""
        # 実際のサービスインスタンスを登録
        # ここではモックとしてサービス能力のみを登録

        # 通知サービス能力を登録
        try:
            self.service_integration.register_service(
                "notification",
                None,  # 実際のインスタンスは後で注入
                self.service_integration.service_capabilities["notification"]
            )
        except Exception as e:
            self.logger.warning(f"通知サービス登録エラー: {str(e)}")

        # 天気サービス能力を登録
        try:
            self.service_integration.register_service(
                "weather",
                None,
                self.service_integration.service_capabilities["weather"]
            )
        except Exception as e:
            self.logger.warning(f"天気サービス登録エラー: {str(e)}")

        # 検索サービス能力を登録
        try:
            self.service_integration.register_service(
                "search",
                None,
                self.service_integration.service_capabilities["search"]
            )
        except Exception as e:
            self.logger.warning(f"検索サービス登録エラー: {str(e)}")

        # 自動タスクサービス能力を登録
        try:
            self.service_integration.register_service(
                "auto_task",
                None,
                self.service_integration.service_capabilities["auto_task"]
            )
        except Exception as e:
            self.logger.warning(f"自動タスクサービス登録エラー: {str(e)}")

    async def process_integrated_request(
        self,
        request: IntegratedServiceRequest
    ) -> IntegratedServiceResponse:
        """
        統合リクエストを処理

        Args:
            request: 統合サービスリクエスト

        Returns:
            統合サービス応答
        """
        start_time = datetime.now()

        try:
            # 実行パスを記録
            execution_path = ["integrated_request_start"]

            # リクエストタイプに応じた処理
            if request.request_type == "cross_function":
                # クロスサービス機能実行
                result = await self._handle_cross_service_request(request)
                execution_path.append("cross_service_execution")

            elif request.request_type == "direct_service":
                # 直接サービス実行
                result = await self._handle_direct_service_request(request)
                execution_path.append("direct_service_execution")

            elif request.request_type == "ai_enhanced":
                # AI強化実行
                result = await self._handle_ai_enhanced_request(request)
                execution_path.append("ai_enhanced_execution")

            else:
                # 自動判定実行
                result = await self._handle_auto_request(request)
                execution_path.append("auto_routing_execution")

            # 実行統計更新
            self._update_execution_stats(request, result, (datetime.now() - start_time).total_seconds())

            # 提案生成
            suggestions = await self._generate_suggestions(request, result)

            # パフォーマンス指標
            performance_metrics = self._calculate_performance_metrics(result)

            return IntegratedServiceResponse(
                response=result.get("response", "応答を生成できませんでした"),
                service_used=result.get("service_used", "unknown"),
                execution_path=execution_path,
                processing_time=(datetime.now() - start_time).total_seconds(),
                confidence_score=result.get("confidence_score", 0.0),
                components_used=result.get("components_used", {}),
                suggestions=suggestions,
                performance_metrics=performance_metrics
            )

        except Exception as e:
            self.logger.error(f"統合リクエスト処理エラー: {str(e)}")

            # フォールバック処理
            if request.enable_fallback:
                return await self._create_fallback_response(request, str(e))
            else:
                raise

    def process_integrated_request_sync(
        self,
        request: IntegratedServiceRequest
    ) -> IntegratedServiceResponse:
        """
        同期版統合リクエスト処理

        Args:
            request: 統合サービスリクエスト

        Returns:
            統合サービス応答
        """
        # asyncio.runを使用して非同期関数を同期的に実行
        try:
            return asyncio.run(self.process_integrated_request(request))
        except Exception as e:
            self.logger.error(f"統合リクエスト処理エラー: {str(e)}")

            # フォールバック処理
            if request.enable_fallback:
                return asyncio.run(self._create_fallback_response(request, str(e)))
            else:
                raise

    async def _handle_cross_service_request(self, request: IntegratedServiceRequest) -> Dict[str, Any]:
        """クロスサービスリクエストを処理"""
        # 利用可能なクロスサービス機能を取得
        available_functions = self.cross_service.get_available_cross_functions()

        # クエリに最適な機能を検索
        best_function = None
        best_score = 0.0

        for function in available_functions:
            score = self._calculate_function_match_score(request.query, function)
            if score > best_score and score > 0.5:  # 50%以上のマッチ
                best_function = function
                best_score = score

        if best_function:
            # クロスサービス機能実行
            result = await self.cross_service.execute_cross_service_function(
                best_function["function_id"],
                request.user_id,
                {},
                request.context
            )

            return {
                "response": f"クロスサービス機能「{best_function['name']}」を実行しました",
                "service_used": "cross_service",
                "function_used": best_function["name"],
                "confidence_score": best_score,
                "components_used": {"cross_function": best_function}
            }

        return {
            "response": "適切なクロスサービス機能が見つかりませんでした",
            "service_used": "none",
            "confidence_score": 0.0
        }

    async def _handle_direct_service_request(self, request: IntegratedServiceRequest) -> Dict[str, Any]:
        """直接サービスリクエストを処理"""
        # インテント分析
        routing_decision = await self.intent_router.analyze_and_route(
            request.query, request.user_id, request.context
        )

        # サービス実行
        service_result = await self.service_integration._execute_service_method(
            routing_decision.selected_service,
            routing_decision.selected_method,
            routing_decision.execution_parameters,
            {"user_id": request.user_id}
        )

        return {
            "response": self.service_integration._format_service_result(
                routing_decision.selected_service, service_result
            ),
            "service_used": routing_decision.selected_service,
            "confidence_score": routing_decision.analysis.confidence,
            "components_used": {"direct_service": routing_decision.selected_service}
        }

    async def _handle_ai_enhanced_request(self, request: IntegratedServiceRequest) -> Dict[str, Any]:
        """AI強化リクエストを処理"""
        # ハイブリッド応答生成
        hybrid_response = await self.response_generator.generate_hybrid_response(
            request.query, request.user_id, request.context
        )

        return {
            "response": hybrid_response.final_response,
            "service_used": "hybrid_ai",
            "confidence_score": hybrid_response.quality_score,
            "components_used": {
                "hybrid_components": [c.service_name for c in hybrid_response.components]
            }
        }

    async def _handle_auto_request(self, request: IntegratedServiceRequest) -> Dict[str, Any]:
        """自動リクエストを処理"""
        # インテント分析
        routing_decision = await self.intent_router.analyze_and_route(
            request.query, request.user_id, request.context
        )

        # 複合タスクの場合
        if routing_decision.analysis.intent_type == "composite_task":
            return await self._handle_composite_task_request(request, routing_decision)

        # 信頼度による処理方法決定
        if routing_decision.analysis.confidence > 0.8:
            # 高信頼度: 直接サービス実行
            return await self._handle_direct_service_request(request)
        elif routing_decision.analysis.confidence > 0.5:
            # 中信頼度: ハイブリッド実行
            return await self._handle_ai_enhanced_request(request)
        else:
            # 低信頼度: AI主導実行
            return await self._handle_ai_enhanced_request(request)

    async def _handle_composite_task_request(self, request: IntegratedServiceRequest, routing_decision: Any) -> Dict[str, Any]:
        """複合タスクを処理"""
        try:
            # 検出された要素を取得
            detected_elements = routing_decision.analysis.context_info.get("detected_elements", [])

            # 各要素に対する結果を収集
            results = {}
            execution_path = ["composite_task_start"]

            # 各要素を順次処理
            for element in detected_elements:
                try:
                    if element == "weather":
                        # 天気情報の取得
                        weather_result = await self.service_integration._execute_service_method(
                            "weather", "current", {"location": "東京"}, {"user_id": request.user_id}
                        )
                        results["weather"] = weather_result
                        execution_path.append("weather_executed")

                    elif element == "news":
                        # ニュース検索の実行
                        search_result = await self.service_integration._execute_service_method(
                            "search", "web", {"query": "ニュース"}, {"user_id": request.user_id}
                        )
                        results["news"] = search_result
                        execution_path.append("search_executed")

                    elif element == "notification":
                        # 通知の設定（6時通知として）
                        notification_result = await self.service_integration._execute_service_method(
                            "notification", "add",
                            {
                                "message": f"{'、'.join(results.keys())}の確認をお知らせします",
                                "datetime": "06:00",
                                "title": "定時確認通知"
                            },
                            {"user_id": request.user_id}
                        )
                        results["notification"] = notification_result
                        execution_path.append("notification_executed")

                except Exception as e:
                    self.logger.error(f"複合タスク要素 {element} の実行エラー: {str(e)}")
                    results[element] = {"success": False, "error": str(e)}

            # 統合された応答を作成
            response_parts = []

            if "weather" in results and results["weather"].get("success", True):
                weather_info = results["weather"].get("weather", {})
                response_parts.append(f"🌤️ 天気: {weather_info.get('condition', '晴れ')}（{weather_info.get('temperature', '22℃')}）")

            if "news" in results and results["news"].get("success", True):
                search_info = results["news"].get("search", {})
                response_parts.append(f"📰 ニュース: {len(search_info.get('results', []))}件の最新情報")

            if "notification" in results and results["notification"].get("success", True):
                notification_info = results["notification"].get("notification", {})
                response_parts.append(f"✅ 通知設定完了: {notification_info.get('message', '定時通知')}")

            # 6時の定期実行が含まれる複合要求は、自動タスク（daily 06:00）作成を優先して確実化
            auto_task_created_msg = None
            try:
                if any("06:00" in str(v) or "6時" in self._safe_str(v) for v in [request.query, results]):
                    # ニュース+天気の複合配信を毎日6:00に実行する自動タスク
                    auto_task_params = {
                        "task_type": "news_daily",
                        "title": "毎日のニュース配信",
                        "description": "毎日06:00に最新ニュースを配信",
                        "schedule_pattern": "daily",
                        "schedule_time": "06:00",
                        "parameters": {"keywords": ["最新ニュース"]}
                    }
                    # まずニュースのdailyタスクを作成
                    at_news = await self.service_integration._execute_service_method(
                        "auto_task", "create", auto_task_params, {"user_id": request.user_id}
                    )
                    # 天気も欲しい場合は天気のdailyタスクを作成（デフォルト東京）
                    if "weather" in results:
                        auto_task_params_w = {
                            "task_type": "weather_daily",
                            "title": "毎日の天気配信",
                            "description": "毎日06:00に天気情報を配信",
                            "schedule_pattern": "daily",
                            "schedule_time": "06:00",
                            "parameters": {"location": "東京"}
                        }
                        at_w = await self.service_integration._execute_service_method(
                            "auto_task", "create", auto_task_params_w, {"user_id": request.user_id}
                        )
                        if at_w.get("success"):
                            auto_task_created_msg = "🤖 自動配信（天気・ニュース）を毎日06:00に設定しました"
                    if at_news.get("success") and not auto_task_created_msg:
                        auto_task_created_msg = "🤖 自動配信（ニュース）を毎日06:00に設定しました"
            except Exception as _e:
                self.logger.warning(f"複合→自動タスク作成フォールバック失敗: {_e}")

            # 最終応答
            base = "、".join(response_parts) if response_parts else "複合タスクの処理が完了しました"
            final_response = f"{base}\n{auto_task_created_msg}" if auto_task_created_msg else base

            return {
                "response": final_response,
                "service_used": "composite_task",
                "confidence_score": routing_decision.analysis.confidence,
                "components_used": {
                    "composite_elements": detected_elements,
                    "results": results
                },
                "execution_path": execution_path
            }

        except Exception as e:
            self.logger.error(f"複合タスク処理エラー: {str(e)}")
            return {
                "response": f"複合タスクの処理中にエラーが発生しました: {str(e)}",
                "service_used": "composite_task_error",
                "confidence_score": 0.0,
                "components_used": {},
                "execution_path": ["composite_task_error"]
            }

    def _safe_str(self, obj: Any) -> str:
        try:
            return str(obj)
        except Exception:
            return ""
    def _calculate_function_match_score(self, query: str, function: Dict[str, Any]) -> float:
        """機能マッチングスコアを計算"""
        score = 0.0

        # 名前マッチング
        query_keywords = set(query.lower().split())
        function_name_keywords = set(function.get("name", "").lower().split())
        name_matches = len(query_keywords & function_name_keywords)
        score += min(name_matches * 0.3, 0.6)

        # 説明マッチング
        function_desc_keywords = set(function.get("description", "").lower().split())
        desc_matches = len(query_keywords & function_desc_keywords)
        score += min(desc_matches * 0.2, 0.4)

        # サービス要件マッチング
        required_services = function.get("required_services", [])
        if required_services:
            score += 0.1  # 複数サービス対応ボーナス

        return min(1.0, score)

    async def _generate_suggestions(self, request: IntegratedServiceRequest, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提案を生成"""
        suggestions = []

        try:
            # クロスサービス機能の提案
            cross_suggestions = await self.cross_service.suggest_cross_service_functions(
                request.query, request.user_id, request.context
            )

            suggestions.extend(cross_suggestions)

            # サービス組み合わせの提案
            service_combinations = self.service_integration.analyze_service_combinations(
                request.query
            )

            for combo in service_combinations:
                if combo["type"] == "combined":
                    suggestions.append({
                        "type": "service_combination",
                        "title": combo["description"],
                        "confidence": combo["confidence"],
                        "services": combo["services"]
                    })

            # 最近の使用傾向に基づく提案
            user_stats = self.get_user_statistics(request.user_id)
            if user_stats.get("total_executions", 0) > 5:
                suggestions.append({
                    "type": "usage_based",
                    "title": "ご利用傾向に基づくおすすめ機能",
                    "description": "最近よく使用している機能の拡張版をおすすめします",
                    "confidence": 0.7
                })

        except Exception as e:
            self.logger.warning(f"提案生成エラー: {str(e)}")

        return suggestions[:3]  # 上位3件

    def _calculate_performance_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンス指標を計算"""
        return {
            "response_quality": result.get("confidence_score", 0.0),
            "service_efficiency": 1.0 if result.get("service_used") != "none" else 0.0,
            "ai_enhancement_used": 1.0 if "ai" in result.get("service_used", "").lower() else 0.0,
            "multi_service_usage": 1.0 if len(result.get("components_used", {})) > 1 else 0.0
        }

    async def _create_fallback_response(self, request: IntegratedServiceRequest, error: str) -> IntegratedServiceResponse:
        """フォールバック応答を作成"""
        fallback_response = f"申し訳ありません。処理中にエラーが発生しました: {error}"

        return IntegratedServiceResponse(
            response=fallback_response,
            service_used="fallback",
            execution_path=["fallback"],
            processing_time=0.0,
            confidence_score=0.0,
            components_used={},
            suggestions=[],
            performance_metrics={"error_occurred": True}
        )

    def _update_execution_stats(self, request: IntegratedServiceRequest, result: Dict[str, Any], processing_time: float):
        """実行統計を更新"""
        with self.stats_lock:
            user_id = request.user_id

            if user_id not in self.execution_stats:
                self.execution_stats[user_id] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "average_processing_time": 0.0,
                    "service_usage": {},
                    "error_count": 0
                }

            stats = self.execution_stats[user_id]
            stats["total_requests"] += 1

            if result.get("confidence_score", 0.0) > 0.5:
                stats["successful_requests"] += 1

            # 平均処理時間の更新
            current_avg = stats["average_processing_time"]
            new_avg = (current_avg * (stats["total_requests"] - 1) + processing_time) / stats["total_requests"]
            stats["average_processing_time"] = new_avg

            # サービス使用統計
            service_used = result.get("service_used", "unknown")
            if service_used not in stats["service_usage"]:
                stats["service_usage"][service_used] = 0
            stats["service_usage"][service_used] += 1

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """ユーザー統計を取得"""
        with self.stats_lock:
            return self.execution_stats.get(user_id, {
                "total_requests": 0,
                "successful_requests": 0,
                "average_processing_time": 0.0,
                "service_usage": {},
                "error_count": 0
            })

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態を取得"""
        with self.stats_lock:
            total_requests = sum(stats["total_requests"] for stats in self.execution_stats.values())
            total_successful = sum(stats["successful_requests"] for stats in self.execution_stats.values())
            success_rate = total_successful / total_requests if total_requests > 0 else 0.0

            return {
                **self.system_status,
                "total_requests": total_requests,
                "total_users": len(self.execution_stats),
                "overall_success_rate": success_rate,
                "available_services": list(self.service_integration.get_available_services().keys())
            }

    def update_service_instance(self, service_name: str, service_instance: Any):
        """サービスインスタンスを更新"""
        try:
            capability = self.service_integration.get_service_capability(service_name)
            if capability:
                self.service_integration.registered_services[service_name] = service_instance
                self.logger.info(f"サービスインスタンスを更新: {service_name}")
            else:
                self.logger.warning(f"サービス能力が見つからない: {service_name}")
        except Exception as e:
            self.logger.error(f"サービスインスタンス更新エラー: {str(e)}")

    async def optimize_for_user(self, user_id: str):
        """ユーザー向けに最適化"""
        try:
            # ユーザー統計取得
            user_stats = self.get_user_statistics(user_id)

            # よく使うサービスを優先的に準備
            if user_stats.get("total_requests", 0) > 10:
                frequent_services = sorted(
                    user_stats.get("service_usage", {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]

                for service_name, usage_count in frequent_services:
                    # サービスのプリロードや最適化
                    self.logger.info(f"ユーザー {user_id} の頻用サービス {service_name} を最適化")

            # 応答スタイルの調整
            await self.flexible_ai.update_user_settings(user_id, {
                "optimization_level": "high",
                "preferred_services": [s[0] for s in frequent_services]
            })

        except Exception as e:
            self.logger.error(f"ユーザー最適化エラー: {str(e)}")

    def _create_request_from_ai_function(self, service_name: str, parameters: Dict[str, Any], user_id: str, context: Dict[str, Any]) -> IntegratedServiceRequest:
        """AI Functionからのリクエストを作成"""
        # サービス名からクエリを生成
        capability = service_integration_manager.get_service_capability(service_name)
        if capability:
            query = f"{capability.description}を実行"
        else:
            query = f"{service_name}サービスを実行"

        return IntegratedServiceRequest(
            query=query,
            user_id=user_id,
            context=context,
            enable_fallback=True,
            ai_function_request=True,
            service_override=service_name,
            parameters_override=parameters
        )

    async def run_diagnostics(self) -> Dict[str, Any]:
        """診断を実行"""
        diagnostics: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "service_health": {},
            "ai_service_status": {},
            "performance_metrics": {}
        }

        try:
            # 各サービスのヘルスチェック
            for service_name in self.service_integration.get_available_services().keys():
                try:
                    capability = self.service_integration.get_service_capability(service_name)
                    diagnostics["service_health"][service_name] = {
                        "status": "available",
                        "capability": capability.description if capability else "unknown"
                    }
                except Exception as e:
                    diagnostics["service_health"][service_name] = {
                        "status": "error",
                        "error": str(e)
                    }

            # AIサービス診断
            try:
                test_result = await self.flexible_ai.generate_flexible_response(
                    "診断テストです。正常に動作していますか？",
                    context={"diagnostic": True}
                )
                diagnostics["ai_service_status"] = {
                    "status": "operational",
                    "response_length": len(test_result)
                }
            except Exception as e:
                diagnostics["ai_service_status"] = {
                    "status": "error",
                    "error": str(e)
                }

        except Exception as e:
            self.logger.error(f"診断実行エラー: {str(e)}")
            diagnostics["diagnostic_error"] = str(e)

        return diagnostics

# グローバルインスタンス
integrated_service_manager = IntegratedServiceManager()
