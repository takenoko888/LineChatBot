"""
Flexible AI Integration Service - 柔軟AI機能の統合
"""
import logging
import asyncio
from typing import Dict, Optional, Any, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict

from .flexible_ai_service import flexible_ai_service
from .ai_function_plugin import ai_function_registry
from .adaptive_prompt_manager import adaptive_prompt_manager
from .response_variety_manager import response_variety_manager

@dataclass
class AIFlexibleRequest:
    """柔軟AIリクエスト"""
    query: str
    user_id: str = "default"
    context: Optional[Dict[str, Any]] = None
    response_style: str = "balanced"
    force_refresh: bool = False
    enable_plugins: bool = True
    enable_variety: bool = True

@dataclass
class AIFlexibleResponse:
    """柔軟AI応答"""
    response: str
    metadata: Dict[str, Any]
    processing_time: float
    plugins_used: List[str]
    style_used: str
    confidence_score: float

class FlexibleAIIntegrationService:
    """柔軟AI統合サービス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # サブサービス
        self.flexible_ai = flexible_ai_service
        self.function_registry = ai_function_registry
        self.prompt_manager = adaptive_prompt_manager
        self.variety_manager = response_variety_manager

        self.logger.info("Flexible AI Integration Serviceを初期化しました")

    async def process_flexible_request(self, request: AIFlexibleRequest) -> AIFlexibleResponse:
        """
        柔軟AIリクエストを処理

        Args:
            request: 柔軟AIリクエスト

        Returns:
            柔軟AI応答
        """
        start_time = datetime.now()

        try:
            # プラグイン機能を確認
            plugins_used = []
            if request.enable_plugins:
                matched_functions = self.function_registry.find_matching_functions(
                    request.query,
                    request.context or {}
                )

                if matched_functions:
                    # 最初のマッチした機能を実行
                    plugin_response = await self._execute_plugin(
                        matched_functions[0],
                        request.user_id,
                        request.context or {}
                    )

                    if plugin_response.get("success"):
                        plugins_used.append(matched_functions[0].function_def.name)

                        return AIFlexibleResponse(
                            response=plugin_response.get("result", "プラグイン実行完了"),
                            metadata=plugin_response,
                            processing_time=(datetime.now() - start_time).total_seconds(),
                            plugins_used=plugins_used,
                            style_used="plugin",
                            confidence_score=1.0
                        )

            # 適応型プロンプト生成
            adaptive_prompt, prompt_info = await self.prompt_manager.generate_adaptive_prompt(
                request.query,
                request.user_id,
                request.context
            )

            # 応答スタイル選択
            selected_style = None
            if request.enable_variety:
                selected_style = await self.variety_manager.select_response_style(
                    request.user_id,
                    request.context or {}
                )
                request.response_style = selected_style.style_id

            # 柔軟AIで応答生成
            ai_response = await self.flexible_ai.generate_flexible_response(
                adaptive_prompt,
                request.user_id,
                request.context,
                request.response_style,
                request.force_refresh
            )

            # スタイル適応
            if selected_style and request.enable_variety:
                ai_response = await self.variety_manager.generate_style_adapted_response(
                    ai_response,
                    selected_style,
                    request.context or {}
                )

            # 応答メタデータ作成
            metadata = {
                "prompt_info": prompt_info,
                "style_info": asdict(selected_style) if selected_style else None,
                "context_analysis": request.context,
                "ai_provider": self.flexible_ai.active_provider.config.name if self.flexible_ai.active_provider else "none"
            }

            # 信頼度スコア計算（簡易版）
            confidence_score = self._calculate_confidence_score(
                ai_response,
                request.context or {},
                prompt_info
            )

            # 使用状況記録
            self._record_interaction(request, ai_response, metadata)

            return AIFlexibleResponse(
                response=ai_response,
                metadata=metadata,
                processing_time=(datetime.now() - start_time).total_seconds(),
                plugins_used=plugins_used,
                style_used=request.response_style,
                confidence_score=confidence_score
            )

        except Exception as e:
            self.logger.error(f"柔軟AI処理エラー: {str(e)}")
            return AIFlexibleResponse(
                response=f"申し訳ありません。処理中にエラーが発生しました: {str(e)}",
                metadata={"error": str(e)},
                processing_time=(datetime.now() - start_time).total_seconds(),
                plugins_used=[],
                style_used="error",
                confidence_score=0.0
            )

    async def _execute_plugin(self, function, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """プラグイン機能を実行"""
        try:
            # プラグインのパラメータ抽出（簡易版）
            parameters = self._extract_plugin_parameters(function.function_def, context)

            # 機能実行
            result = await function.execute(user_id, parameters, context)

            return {
                "success": True,
                "function_name": function.function_def.name,
                "result": result,
                "executed_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "function_name": function.function_def.name,
                "error": str(e)
            }

    def _extract_plugin_parameters(self, function_def, context: Dict[str, Any]) -> Dict[str, Any]:
        """プラグインパラメータを抽出（簡易版）"""
        # 実際にはより洗練されたパラメータ抽出ロジックを実装
        return context.get("parameters", {})

    def _calculate_confidence_score(self, response: str, context: Dict[str, Any], prompt_info: Dict[str, Any]) -> float:
        """信頼度スコアを計算"""
        # 簡易的な信頼度計算
        score = 0.5  # ベーススコア

        # 応答長による調整
        response_length = len(response.split())
        if 10 <= response_length <= 100:
            score += 0.2
        elif response_length > 100:
            score += 0.1

        # コンテキストマッチによる調整
        if context.get("is_technical"):
            score += 0.1

        # プロンプトの質による調整
        if prompt_info.get("template_id") != "fallback":
            score += 0.2

        return min(1.0, score)  # 最大1.0

    def _record_interaction(self, request: AIFlexibleRequest, response: str, metadata: Dict[str, Any]):
        """インタラクションを記録"""
        # プロンプトマネージャーに記録
        self.prompt_manager.record_user_interaction(
            request.user_id,
            request.query,
            response,
            request.context or {}
        )

    def get_user_ai_statistics(self, user_id: str) -> Dict[str, Any]:
        """ユーザーAI統計を取得"""
        stats = {
            "prompt_manager": self.prompt_manager.get_user_history_summary(user_id),
            "style_manager": self.variety_manager.get_style_statistics(user_id),
            "ai_service": self.flexible_ai.get_user_settings(user_id)
        }
        return stats

    def update_user_ai_settings(self, user_id: str, settings: Dict[str, Any]):
        """ユーザーAI設定を更新"""
        self.flexible_ai.update_user_settings(user_id, settings)

    def list_available_functions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """利用可能な機能一覧を取得"""
        functions = self.function_registry.list_functions(category)
        return [asdict(func) for func in functions]

    def add_custom_function(self, function_def: Dict[str, Any], function_class: Any):
        """カスタム機能を追加"""
        # 実際にはより厳密な検証が必要
        from .ai_function_plugin import AIFunction, BaseAIFunction

        ai_function = AIFunction(**function_def)
        function_instance = function_class(ai_function)

        self.function_registry.register_function(function_instance)

    async def test_ai_flexibility(self, user_id: str = "test") -> Dict[str, Any]:
        """AI柔軟性のテスト"""
        test_queries = [
            "2 + 3 * 4 を計算して",
            "今日の運勢を教えて",
            "PythonでFizzBuzzプログラムを作って",
            "最近どう？",
            "新しいアイデアが欲しい"
        ]

        results = []

        for query in test_queries:
            try:
                request = AIFlexibleRequest(
                    query=query,
                    user_id=user_id,
                    context={"test_mode": True}
                )

                response = await self.process_flexible_request(request)

                results.append({
                    "query": query,
                    "response": response.response,
                    "style_used": response.style_used,
                    "plugins_used": response.plugins_used,
                    "confidence": response.confidence_score,
                    "processing_time": response.processing_time
                })

            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e)
                })

        return {
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "successful_responses": len([r for r in results if "error" not in r]),
                "average_confidence": sum(r.get("confidence", 0) for r in results) / len(results),
                "unique_styles": len(set(r.get("style_used", "") for r in results))
            }
        }

# グローバルインスタンス
flexible_ai_integration = FlexibleAIIntegrationService()
