"""
Enhanced Message Handler with Flexible AI Integration
既存のメッセージハンドラーに柔軟AI機能を統合
"""
import logging
from typing import Dict, Optional, Any, Tuple
from datetime import datetime

from .flexible_ai_integration import flexible_ai_integration, AIFlexibleRequest, AIFlexibleResponse

class FlexibleAIMessageHandler:
    """柔軟AI機能を統合したメッセージハンドラー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.flexible_ai = flexible_ai_integration

        # 柔軟AI有効化設定
        self.enable_flexible_ai = True
        self.fallback_to_original = True

        self.logger.info("Flexible AI Message Handlerを初期化しました")

    async def handle_message_with_flexible_ai(
        self,
        text: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        柔軟AIを使用してメッセージを処理

        Args:
            text: ユーザーメッセージ
            user_id: ユーザーID
            context: 追加コンテキスト

        Returns:
            Tuple[応答メッセージ, クイックリプライタイプ, メタデータ]
        """
        try:
            # 柔軟AIリクエスト作成
            request = AIFlexibleRequest(
                query=text,
                user_id=user_id,
                context=context or {},
                enable_plugins=True,
                enable_variety=True
            )

            # 柔軟AI処理実行
            response = await self.flexible_ai.process_flexible_request(request)

            # メタデータ作成
            metadata = {
                "ai_flexible_used": True,
                "response_metadata": response.metadata,
                "processing_time": response.processing_time,
                "plugins_used": response.plugins_used,
                "style_used": response.style_used,
                "confidence_score": response.confidence_score
            }

            # クイックリプライタイプの決定
            quick_reply_type = self._determine_quick_reply_type(response)

            return response.response, quick_reply_type, metadata

        except Exception as e:
            self.logger.error(f"柔軟AIメッセージ処理エラー: {str(e)}")

            # フォールバック処理
            if self.fallback_to_original:
                return self._generate_fallback_response(text, str(e)), "default", {"error": str(e)}

            return f"申し訳ありません。AI処理中にエラーが発生しました: {str(e)}", "default", {"error": str(e)}

    def _determine_quick_reply_type(self, response: AIFlexibleResponse) -> str:
        """クイックリプライタイプを決定"""
        # プラグインが使用された場合
        if response.plugins_used:
            return "plugin_result"

        # スタイルに基づく決定
        style = response.style_used
        if style == "friendly":
            return "friendly_response"
        elif style == "professional":
            return "professional_response"
        elif style == "creative":
            return "creative_response"

        return "default"

    def _generate_fallback_response(self, original_text: str, error: str) -> str:
        """フォールバック応答を生成"""
        return f"「{original_text}」についてお答えします。通常のAI機能で対応いたします。"

    def get_ai_statistics(self, user_id: str) -> Dict[str, Any]:
        """AI統計を取得"""
        return self.flexible_ai.get_user_ai_statistics(user_id)

    def update_ai_settings(self, user_id: str, settings: Dict[str, Any]):
        """AI設定を更新"""
        self.flexible_ai.update_user_ai_settings(user_id, settings)

    async def test_flexible_ai(self, user_id: str = "test") -> Dict[str, Any]:
        """柔軟AIのテストを実行"""
        return await self.flexible_ai.test_ai_flexibility(user_id)

# 統合用のヘルパー関数
def integrate_flexible_ai_to_message_handler(original_handler):
    """
    既存のメッセージハンドラーに柔軟AI機能を統合

    Args:
        original_handler: 既存のメッセージハンドラーインスタンス

    Returns:
        拡張されたハンドラー
    """
    class EnhancedMessageHandler(original_handler.__class__):
        """拡張メッセージハンドラー"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.flexible_ai_handler = FlexibleAIMessageHandler()

        async def handle_message_flexible(
            self,
            event,
            *args,
            **kwargs
        ) -> Tuple[str, Optional[str], Dict[str, Any]]:
            """柔軟AI対応のメッセージ処理"""
            text = event.message.text.strip()
            user_id = event.source.user_id

            # コンテキスト収集（必要に応じて拡張）
            context = {
                "message_type": "line_message",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }

            # 柔軟AI処理
            response, quick_reply_type, metadata = await self.flexible_ai_handler.handle_message_with_flexible_ai(
                text, user_id, context
            )

            return response, quick_reply_type, metadata

    return EnhancedMessageHandler()

# 使用例と設定
FLEXIBLE_AI_CONFIG = {
    "enable_by_default": True,
    "fallback_to_original": True,
    "max_processing_time": 10.0,  # 秒
    "enable_plugins": True,
    "enable_response_variety": True,
    "enable_adaptive_prompts": True
}

def create_flexible_ai_enabled_handler():
    """柔軟AI有効化済みハンドラーを作成"""
    return FlexibleAIMessageHandler()

# テスト関数
async def test_flexible_ai_integration():
    """柔軟AI統合のテスト"""
    handler = FlexibleAIMessageHandler()

    test_messages = [
        "こんにちは",
        "2 + 3 * 4 を計算して",
        "今日の運勢は？",
        "新しいアプリのアイデアが欲しい",
        "Pythonで簡単なプログラムを作って"
    ]

    for message in test_messages:
        print(f"\n--- テスト: {message} ---")
        try:
            response, reply_type, metadata = await handler.handle_message_with_flexible_ai(
                message, "test_user"
            )
            print(f"応答: {response}")
            print(f"スタイル: {metadata.get('style_used', 'unknown')}")
            print(f"信頼度: {metadata.get('confidence_score', 0):.2f}")
            if metadata.get('plugins_used'):
                print(f"使用プラグイン: {metadata['plugins_used']}")
        except Exception as e:
            print(f"エラー: {str(e)}")

if __name__ == "__main__":
    # 非同期テスト実行
    async def run_test():
        await test_flexible_ai_integration()

    import asyncio
    asyncio.run(run_test())
