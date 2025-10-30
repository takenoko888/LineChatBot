"""
Hybrid Response Generator - AIと既存サービスのハイブリッド応答
"""
import logging
import asyncio
from typing import Dict, Optional, Any, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import json

from .flexible_ai_service import flexible_ai_service
from .service_integration_manager import service_integration_manager
from .context_aware_router import context_aware_router, RoutingDecision
from .adaptive_prompt_manager import adaptive_prompt_manager

@dataclass
class HybridResponseComponent:
    """ハイブリッド応答コンポーネント"""
    component_type: str  # ai, service, combined
    service_name: str
    content: str
    confidence: float
    metadata: Dict[str, Any]
    priority: int = 5

@dataclass
class HybridResponse:
    """ハイブリッド応答"""
    response_id: str
    user_id: str
    original_query: str
    components: List[HybridResponseComponent]
    final_response: str
    routing_decision: RoutingDecision
    processing_time: float
    quality_score: float
    user_feedback: Optional[Dict[str, Any]] = None

class HybridResponseGenerator:
    """ハイブリッド応答生成器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 応答統合ルール
        self.integration_rules = self._initialize_integration_rules()

        # 応答品質評価基準
        self.quality_metrics = self._initialize_quality_metrics()

        # 応答テンプレート
        self.response_templates = self._initialize_response_templates()

        # キャッシュ
        self.response_cache: Dict[str, HybridResponse] = {}
        self.cache_lock = threading.Lock()

        self.logger.info("Hybrid Response Generatorを初期化しました")

    def _initialize_integration_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """統合ルールを初期化"""
        return {
            "notification": [
                {
                    "condition": "single_notification",
                    "template": "notification_confirmation",
                    "priority": 10
                },
                {
                    "condition": "multiple_notifications",
                    "template": "notification_summary",
                    "priority": 8
                }
            ],
            "weather": [
                {
                    "condition": "weather_with_location",
                    "template": "weather_detailed",
                    "priority": 9
                },
                {
                    "condition": "weather_forecast",
                    "template": "weather_forecast",
                    "priority": 8
                }
            ],
            "search": [
                {
                    "condition": "search_with_ai_summary",
                    "template": "search_with_ai_insights",
                    "priority": 9
                },
                {
                    "condition": "simple_search",
                    "template": "search_results",
                    "priority": 7
                }
            ],
            "auto_task": [
                {
                    "condition": "task_creation",
                    "template": "task_confirmation",
                    "priority": 10
                },
                {
                    "condition": "task_management",
                    "template": "task_management",
                    "priority": 8
                }
            ],
            "combined": [
                {
                    "condition": "multi_service",
                    "template": "combined_services",
                    "priority": 9
                }
            ]
        }

    def _initialize_quality_metrics(self) -> Dict[str, Dict[str, float]]:
        """品質評価基準を初期化"""
        return {
            "completeness": {
                "min_length": 10,
                "has_details": 1.0,
                "structured": 0.5,
                "weight": 0.3
            },
            "relevance": {
                "keyword_match": 1.0,
                "context_appropriate": 0.8,
                "user_intent_fulfilled": 1.0,
                "weight": 0.3
            },
            "accuracy": {
                "factual_correctness": 1.0,
                "up_to_date": 0.5,
                "consistent": 0.5,
                "weight": 0.2
            },
            "usability": {
                "actionable": 0.8,
                "clear_instructions": 0.5,
                "follow_up_options": 0.3,
                "weight": 0.2
            }
        }

    def _initialize_response_templates(self) -> Dict[str, str]:
        """応答テンプレートを初期化"""
        return {
            "notification_confirmation": """
✅ 通知を設定しました

{notification_details}

🆔 通知ID: {notification_id}
⏰ 実行予定: {schedule_time}
🔄 繰り返し: {repeat_pattern}

変更が必要な場合は「通知編集 {notification_id}」とお知らせください。
            """.strip(),

            "notification_summary": """
📋 通知一覧

{multiple_notifications}

合計: {total_count} 件の通知が設定されています。
            """.strip(),

            "weather_detailed": """
🌤️ {location}の天気情報

{today_weather}

{tomorrow_forecast}

💡 今日のアドバイス: {weather_advice}
            """.strip(),

            "weather_forecast": """
📅 {location}の天気予報

{forecast_details}

次回の天気確認は「{location}の天気」とお知らせください。
            """.strip(),

            "search_with_ai_insights": """
🔍 検索結果: "{query}"

{search_results}

🤖 AIによる追加分析:
{ai_insights}
            """.strip(),

            "search_results": """
🔍 検索結果: "{query}"

{search_results}

より詳しい情報が必要ですか？
            """.strip(),

            "task_confirmation": """
✅ 自動タスクを設定しました

📝 タスク: {task_title}
⏰ 実行タイミング: {schedule}
🔄 繰り返し: {repeat_pattern}
🆔 タスクID: {task_id}

管理は「自動実行一覧」で確認できます。
            """.strip(),

            "task_management": """
🤖 自動タスク管理

{task_management_info}

他のタスクも設定しますか？
            """.strip(),

            "combined_services": """
🔄 複数の機能を使用した総合的な対応

{service_integration_details}

追加の対応が必要ですか？
            """.strip(),

            "ai_enhanced_response": """
{ai_response}

💡 この回答はAIの分析と既存のサービス機能を組み合わせて生成されました。
            """.strip(),

            "general_assistance": """
{primary_response}

{additional_suggestions}

ご質問があればいつでもどうぞ！
            """.strip()
        }

    async def generate_hybrid_response(
        self,
        query: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> HybridResponse:
        """
        ハイブリッド応答を生成

        Args:
            query: ユーザークエリ
            user_id: ユーザーID
            context: 追加コンテキスト

        Returns:
            ハイブリッド応答
        """
        start_time = datetime.now()

        try:
            # ルーティング決定を取得
            routing_decision = await context_aware_router.analyze_and_route(
                query, user_id, context
            )

            # コンポーネント生成
            components = await self._generate_response_components(
                query, routing_decision, context or {}
            )

            # 最終応答統合
            final_response = await self._integrate_response_components(
                components, routing_decision
            )

            # 品質評価
            quality_score = self._evaluate_response_quality(
                final_response, components, routing_decision
            )

            # 応答ID生成
            response_id = f"hybrid_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:4]}"

            hybrid_response = HybridResponse(
                response_id=response_id,
                user_id=user_id,
                original_query=query,
                components=components,
                final_response=final_response,
                routing_decision=routing_decision,
                processing_time=(datetime.now() - start_time).total_seconds(),
                quality_score=quality_score
            )

            # キャッシュ保存
            self._cache_response(hybrid_response)

            return hybrid_response

        except Exception as e:
            self.logger.error(f"ハイブリッド応答生成エラー: {str(e)}")
            return self._create_error_response(query, user_id, str(e))

    async def _generate_response_components(
        self,
        query: str,
        routing_decision: RoutingDecision,
        context: Dict[str, Any]
    ) -> List[HybridResponseComponent]:
        """応答コンポーネントを生成"""
        components = []

        try:
            # 主要サービスコンポーネント
            primary_component = await self._generate_service_component(
                routing_decision.selected_service,
                routing_decision.selected_method,
                routing_decision.execution_parameters,
                context
            )

            if primary_component:
                components.append(primary_component)

            # 副次的サービスコンポーネント
            for service in routing_decision.analysis.secondary_services:
                secondary_component = await self._generate_service_component(
                    service, "default", {}, context
                )
                if secondary_component:
                    components.append(secondary_component)

            # AIコンポーネント（必要な場合）
            if routing_decision.ai_enhanced:
                ai_component = await self._generate_ai_component(
                    query, routing_decision, context
                )
                if ai_component:
                    components.append(ai_component)

        except Exception as e:
            self.logger.error(f"コンポーネント生成エラー: {str(e)}")
            # フォールバックコンポーネント
            fallback_component = HybridResponseComponent(
                component_type="service",
                service_name="fallback",
                content="申し訳ありませんが、処理中にエラーが発生しました。",
                confidence=0.0,
                metadata={"error": str(e)}
            )
            components.append(fallback_component)

        return components

    async def _generate_service_component(
        self,
        service_name: str,
        method: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[HybridResponseComponent]:
        """サービスコンポーネントを生成"""
        try:
            # サービス統合マネージャーを通じて実行
            result = await self._execute_service_method(service_name, method, parameters, context)

            if result and result.get("success", False):
                return HybridResponseComponent(
                    component_type="service",
                    service_name=service_name,
                    content=self._format_service_result(service_name, result),
                    confidence=0.9,
                    metadata=result,
                    priority=8
                )

        except Exception as e:
            self.logger.warning(f"サービスコンポーネント生成エラー ({service_name}): {str(e)}")

        return None

    async def _execute_service_method(
        self,
        service_name: str,
        method: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """サービスメソッドを実行"""
        # 実際のサービス実行
        # ここではモック実装
        if service_name == "notification":
            return await self._mock_notification_service(method, parameters, context)
        elif service_name == "weather":
            return await self._mock_weather_service(method, parameters, context)
        elif service_name == "search":
            return await self._mock_search_service(method, parameters, context)
        elif service_name == "auto_task":
            return await self._mock_auto_task_service(method, parameters, context)
        else:
            return {"success": False, "error": "Unknown service"}

    async def _mock_notification_service(self, method: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """通知サービスモック"""
        if method == "add":
            return {
                "success": True,
                "notification_id": f"n_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": parameters.get("title", "通知"),
                "message": parameters.get("message", ""),
                "schedule": parameters.get("datetime", ""),
                "created_at": datetime.now().isoformat()
            }
        elif method == "list":
            return {
                "success": True,
                "notifications": [
                    {"id": "n1", "title": "テスト通知1", "message": "テストメッセージ1"},
                    {"id": "n2", "title": "テスト通知2", "message": "テストメッセージ2"}
                ]
            }
        return {"success": False}

    async def _mock_weather_service(self, method: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """天気サービスモック"""
        location = parameters.get("location", "東京")
        return {
            "success": True,
            "location": location,
            "temperature": "22°C",
            "condition": "晴れ",
            "humidity": "60%",
            "wind_speed": "3m/s",
            "retrieved_at": datetime.now().isoformat()
        }

    async def _mock_search_service(self, method: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """検索サービスモック"""
        query = parameters.get("query", "")
        return {
            "success": True,
            "query": query,
            "results": [
                f"{query}の検索結果1",
                f"{query}の検索結果2",
                f"{query}の検索結果3"
            ],
            "total_results": 3,
            "search_time": datetime.now().isoformat()
        }

    async def _mock_auto_task_service(self, method: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """自動タスクサービスモック"""
        if method == "create":
            return {
                "success": True,
                "task_id": f"t_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": parameters.get("title", "タスク"),
                "schedule": parameters.get("schedule", ""),
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
        elif method == "list":
            return {
                "success": True,
                "tasks": [
                    {"id": "t1", "title": "テストタスク1", "status": "active"},
                    {"id": "t2", "title": "テストタスク2", "status": "inactive"}
                ]
            }
        return {"success": False}

    def _format_service_result(self, service_name: str, result: Dict[str, Any]) -> str:
        """サービス結果をフォーマット"""
        if service_name == "notification":
            return f"通知: {result.get('title', '')} - {result.get('message', '')}"
        elif service_name == "weather":
            return f"{result.get('location', '')}の天気: {result.get('condition', '')} {result.get('temperature', '')}"
        elif service_name == "search":
            results = result.get('results', [])
            return f"検索結果: {' | '.join(results[:2])}"
        elif service_name == "auto_task":
            return f"タスク: {result.get('title', '')} - {result.get('status', '')}"
        else:
            return str(result)

    async def _generate_ai_component(
        self,
        query: str,
        routing_decision: RoutingDecision,
        context: Dict[str, Any]
    ) -> Optional[HybridResponseComponent]:
        """AIコンポーネントを生成"""
        try:
            # AIプロンプト生成
            ai_prompt = await self._generate_ai_enhancement_prompt(
                query, routing_decision, context
            )

            # AI応答生成
            ai_response = await flexible_ai_service.generate_flexible_response(
                ai_prompt,
                context={"hybrid_ai": True, "routing_decision": asdict(routing_decision)}
            )

            return HybridResponseComponent(
                component_type="ai",
                service_name="flexible_ai",
                content=ai_response,
                confidence=0.8,
                metadata={
                    "prompt": ai_prompt,
                    "ai_model": "gemini",
                    "generated_at": datetime.now().isoformat()
                },
                priority=7
            )

        except Exception as e:
            self.logger.warning(f"AIコンポーネント生成エラー: {str(e)}")
            return None

    async def _generate_ai_enhancement_prompt(
        self,
        query: str,
        routing_decision: RoutingDecision,
        context: Dict[str, Any]
    ) -> str:
        """AI強化プロンプトを生成"""
        service_context = service_integration_manager.get_service_capability(
            routing_decision.selected_service
        )

        prompt = f"""
        ユーザーのクエリに対して、既存の{routing_decision.selected_service}サービスと連携した回答を生成してください。

        クエリ: {query}

        選択されたサービス: {routing_decision.selected_service}
        サービス情報: {service_context.description if service_context else "情報なし"}

        あなたの役割:
        - サービスの機能を補完・強化する
        - よりパーソナライズされた対応を提供
        - 追加の洞察や提案を加える
        - ユーザーの体験を向上させる

        回答ガイドライン:
        - サービスの基本機能を尊重
        - 追加価値を提供
        - 明確で役立つ情報を含める
        - 過度に複雑にしない

        回答:
        """

        return prompt.strip()

    async def _integrate_response_components(
        self,
        components: List[HybridResponseComponent],
        routing_decision: RoutingDecision
    ) -> str:
        """応答コンポーネントを統合"""
        if not components:
            return "申し訳ありませんが、適切な応答を生成できませんでした。"

        # 優先度順にソート
        components.sort(key=lambda c: c.priority, reverse=True)

        # 統合ルールに基づいてテンプレート選択
        integration_type = self._determine_integration_type(components, routing_decision)

        # 最適な統合方法を選択
        integration_method = self._select_integration_method(
            integration_type, routing_decision
        )

        # 統合実行
        if integration_method == "template_based":
            return await self._integrate_with_template(components, routing_decision, integration_type)
        elif integration_method == "ai_powered":
            return await self._integrate_with_ai(components, routing_decision)
        else:
            # シンプル統合
            return self._integrate_simple(components)

    def _determine_integration_type(
        self,
        components: List[HybridResponseComponent],
        routing_decision: RoutingDecision
    ) -> str:
        """統合タイプを決定"""
        if len(components) == 1:
            return routing_decision.selected_service
        else:
            return "combined"

    def _select_integration_method(
        self,
        integration_type: str,
        routing_decision: RoutingDecision
    ) -> str:
        """統合方法を選択"""
        if routing_decision.ai_enhanced:
            return "ai_powered"
        elif integration_type in self.integration_rules:
            return "template_based"
        else:
            return "simple"

    async def _integrate_with_template(
        self,
        components: List[HybridResponseComponent],
        routing_decision: RoutingDecision,
        integration_type: str
    ) -> str:
        """テンプレートベース統合"""
        template_name = self._get_best_template(integration_type, components)

        if template_name and template_name in self.response_templates:
            template = self.response_templates[template_name]

            # テンプレート変数を置換
            formatted_response = template

            # コンポーネント内容の挿入
            for component in components:
                if component.service_name in routing_decision.selected_service:
                    formatted_response = formatted_response.replace(
                        f"{{{component.service_name}_details}}",
                        component.content
                    )

            # デフォルト値の設定
            formatted_response = formatted_response.replace("{query}", routing_decision.original_query)
            formatted_response = formatted_response.replace("{notification_id}", "N/A")
            formatted_response = formatted_response.replace("{schedule_time}", "指定なし")
            formatted_response = formatted_response.replace("{repeat_pattern}", "なし")

            return formatted_response

        return self._integrate_simple(components)

    async def _integrate_with_ai(
        self,
        components: List[HybridResponseComponent],
        routing_decision: RoutingDecision
    ) -> str:
        """AIを活用した統合"""
        # 統合プロンプト生成
        integration_prompt = self._generate_integration_prompt(components, routing_decision)

        try:
            # AIによる統合応答生成
            ai_response = await flexible_ai_service.generate_flexible_response(
                integration_prompt,
                context={"response_integration": True}
            )

            return ai_response

        except Exception as e:
            self.logger.warning(f"AI統合エラー: {str(e)}")
            return self._integrate_simple(components)

    def _generate_integration_prompt(
        self,
        components: List[HybridResponseComponent],
        routing_decision: RoutingDecision
    ) -> str:
        """統合プロンプトを生成"""
        components_text = "\n".join([
            f"- {c.service_name}: {c.content}"
            for c in components
        ])

        prompt = f"""
        複数のサービスからの応答を統合して、ユーザーに最適な回答を作成してください。

        元のクエリ: {routing_decision.original_query}

        サービスからの応答:
        {components_text}

        統合ガイドライン:
        - 各サービスの情報を適切に組み合わせる
        - 重複を避け、簡潔にまとめる
        - ユーザーの利益になるよう整理
        - 自然で読みやすい形式にする

        統合された回答:
        """

        return prompt.strip()

    def _integrate_simple(self, components: List[HybridResponseComponent]) -> str:
        """シンプル統合"""
        if not components:
            return "応答を生成できませんでした。"

        # 最高優先度のコンポーネントを使用
        best_component = max(components, key=lambda c: c.priority)
        return best_component.content

    def _get_best_template(
        self,
        integration_type: str,
        components: List[HybridResponseComponent]
    ) -> Optional[str]:
        """最適なテンプレートを取得"""
        rules = self.integration_rules.get(integration_type, [])

        if not rules:
            return None

        # 条件にマッチするルールを探す
        for rule in rules:
            if self._check_integration_condition(rule, components):
                return rule.get("template")

        return None

    def _check_integration_condition(self, rule: Dict[str, Any], components: List[HybridResponseComponent]) -> bool:
        """統合条件をチェック"""
        condition = rule.get("condition", "")

        if condition == "single_notification" and len(components) == 1:
            return components[0].service_name == "notification"

        elif condition == "multiple_notifications" and len(components) > 1:
            return all(c.service_name == "notification" for c in components)

        elif condition == "weather_with_location":
            return any("location" in c.content.lower() for c in components)

        elif condition == "search_with_ai_summary":
            return any(c.component_type == "ai" for c in components)

        return True

    def _evaluate_response_quality(
        self,
        final_response: str,
        components: List[HybridResponseComponent],
        routing_decision: RoutingDecision
    ) -> float:
        """応答品質を評価"""
        total_score = 0.0
        total_weight = 0.0

        for metric, criteria in self.quality_metrics.items():
            weight = criteria.get("weight", 0.2)

            # 各評価基準に基づいてスコア計算
            if metric == "completeness":
                score = self._evaluate_completeness(final_response, criteria)
            elif metric == "relevance":
                score = self._evaluate_relevance(final_response, routing_decision, criteria)
            elif metric == "accuracy":
                score = self._evaluate_accuracy(components, criteria)
            elif metric == "usability":
                score = self._evaluate_usability(final_response, criteria)
            else:
                score = 0.5

            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _evaluate_completeness(self, response: str, criteria: Dict[str, Any]) -> float:
        """完全性を評価"""
        score = 0.5

        # 長さチェック
        min_length = criteria.get("min_length", 10)
        if len(response) >= min_length:
            score += 0.2

        # 詳細情報の有無
        if criteria.get("has_details", 0):
            if len(response.split('\n')) > 2:
                score += 0.2

        # 構造化
        if criteria.get("structured", 0):
            if any(char in response for char in ['•', '-', '*', '1.', '2.']):
                score += 0.1

        return min(1.0, score)

    def _evaluate_relevance(self, response: str, routing_decision: RoutingDecision, criteria: Dict[str, Any]) -> float:
        """関連性を評価"""
        score = 0.5

        # キーワードマッチ
        query_keywords = routing_decision.original_query.split()
        response_keywords = response.split()

        if criteria.get("keyword_match", 0):
            matches = sum(1 for kw in query_keywords if kw in response)
            if matches > 0:
                score += 0.2

        # 文脈適合性
        if criteria.get("context_appropriate", 0):
            if routing_decision.selected_service in response.lower():
                score += 0.2

        # 意図充足
        if criteria.get("user_intent_fulfilled", 0):
            intent_type = routing_decision.analysis.intent_type
            if intent_type in response.lower():
                score += 0.1

        return min(1.0, score)

    def _evaluate_accuracy(self, components: List[HybridResponseComponent], criteria: Dict[str, Any]) -> float:
        """正確性を評価"""
        score = 0.5

        # 事実の正確性（コンポーネントの信頼度に基づく）
        if criteria.get("factual_correctness", 0):
            avg_confidence = sum(c.confidence for c in components) / len(components)
            score += (avg_confidence - 0.5) * 0.4

        # 一貫性
        if criteria.get("consistent", 0):
            if len(components) > 1:
                score += 0.1

        return min(1.0, score)

    def _evaluate_usability(self, response: str, criteria: Dict[str, Any]) -> float:
        """使いやすさを評価"""
        score = 0.5

        # 実行可能性
        if criteria.get("actionable", 0):
            if any(word in response.lower() for word in ["設定", "実行", "確認", "使用"]):
                score += 0.2

        # 明確な指示
        if criteria.get("clear_instructions", 0):
            if any(word in response for word in ["：", "・", "→", "ステップ"]):
                score += 0.2

        # フォローアップオプション
        if criteria.get("follow_up_options", 0):
            if any(word in response for word in ["他に", "追加", "さらに", "質問"]):
                score += 0.1

        return min(1.0, score)

    def _create_error_response(self, query: str, user_id: str, error: str) -> HybridResponse:
        """エラー応答を作成"""
        return HybridResponse(
            response_id=f"error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_id,
            original_query=query,
            components=[
                HybridResponseComponent(
                    component_type="service",
                    service_name="error",
                    content=f"エラーが発生しました: {error}",
                    confidence=0.0,
                    metadata={"error": error}
                )
            ],
            final_response=f"申し訳ありませんが、エラーが発生しました: {error}",
            routing_decision=None,
            processing_time=0.0,
            quality_score=0.0
        )

    def _cache_response(self, response: HybridResponse):
        """応答をキャッシュ"""
        with self.cache_lock:
            self.response_cache[response.response_id] = response

    def get_response_statistics(self, user_id: str) -> Dict[str, Any]:
        """応答統計を取得"""
        # キャッシュから統計を計算
        user_responses = [
            r for r in self.response_cache.values()
            if r.user_id == user_id
        ]

        if not user_responses:
            return {"total_responses": 0, "average_quality": 0.0}

        total_quality = sum(r.quality_score for r in user_responses)
        avg_quality = total_quality / len(user_responses)

        service_usage = {}
        for response in user_responses:
            for component in response.components:
                service = component.service_name
                service_usage[service] = service_usage.get(service, 0) + 1

        return {
            "total_responses": len(user_responses),
            "average_quality": avg_quality,
            "service_usage": service_usage,
            "average_processing_time": sum(r.processing_time for r in user_responses) / len(user_responses)
        }

# グローバルインスタンス
hybrid_response_generator = HybridResponseGenerator()
