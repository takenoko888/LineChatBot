"""
Flexible AI Service - 柔軟性の高いAI機能を提供
"""
import logging
import json
import os
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib

# プロバイダー設定
@dataclass
class AIProviderConfig:
    """AIプロバイダー設定"""
    name: str
    api_key_env: str
    base_url: str
    model_name: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    rate_limit_rpm: int = 60

class BaseAIProvider(ABC):
    """AIプロバイダーの基底クラス"""

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")

    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """非同期生成"""
        pass

    @abstractmethod
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """同期生成"""
        pass

class GeminiProvider(BaseAIProvider):
    """Geminiプロバイダー"""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        try:
            import google.generativeai as genai
            api_key = os.getenv(config.api_key_env)
            if not api_key:
                raise ValueError(f"{config.api_key_env}が設定されていません")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.model_name)
            self.logger.info(f"{config.name}プロバイダーを初期化しました")
        except ImportError:
            raise ImportError("google-generativeaiがインストールされていません")
        except Exception as e:
            self.logger.error(f"Geminiプロバイダー初期化エラー: {str(e)}")
            raise

    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Geminiでの非同期生成"""
        try:
            # 非同期処理のためのスレッドプール使用
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor,
                    self._generate_sync,
                    prompt,
                    kwargs
                )
                return response
        except Exception as e:
            self.logger.error(f"Gemini非同期生成エラー: {str(e)}")
            raise

    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Geminiでの同期生成"""
        return self._generate_sync(prompt, kwargs)

    def _generate_sync(self, prompt: str, kwargs: dict) -> str:
        """内部同期生成処理"""
        try:
            # 設定のマージ
            config = {**self.config.__dict__, **kwargs}
            generation_config = {
                'temperature': config.get('temperature', self.config.temperature),
                'max_output_tokens': config.get('max_tokens', self.config.max_tokens),
            }

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini生成エラー: {str(e)}")
            raise

@dataclass
class ResponseVariant:
    """応答バリエーション"""
    id: str
    prompt_template: str
    temperature_range: tuple[float, float]
    weight: float = 1.0
    conditions: Dict[str, Any] = None

class FlexibleAIService:
    """柔軟性の高いAIサービス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # プロバイダー設定
        self.providers = self._initialize_providers()
        self.active_provider = self._select_best_provider()

        # 応答バリエーション管理
        self.response_variants = self._initialize_response_variants()

        # コンテキスト管理
        self.context_manager = AIContextManager()

        # ユーザー設定
        self.user_settings: Dict[str, Dict[str, Any]] = {}

        # レート制限管理
        self.rate_limiter = RateLimiter()

        # キャッシュ
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_lock = threading.Lock()

        # モックモード設定
        self.mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true'

        self.logger.info("Flexible AIサービスを初期化しました")
        if self.mock_mode:
            self.logger.info("🧪 モックモードで動作します")

    def _initialize_providers(self) -> Dict[str, BaseAIProvider]:
        """プロバイダーを初期化"""
        providers = {}

        # Gemini設定
        gemini_config = AIProviderConfig(
            name="gemini",
            api_key_env="GEMINI_API_KEY",
            base_url="https://generativelanguage.googleapis.com",
            model_name="gemini-2.5-flash-preview-05-20",
            temperature=0.7,
            max_tokens=4000
        )

        try:
            providers["gemini"] = GeminiProvider(gemini_config)
            self.logger.info("Geminiプロバイダーを初期化しました")
        except Exception as e:
            self.logger.warning(f"Geminiプロバイダーの初期化に失敗: {str(e)}")
            # モックプロバイダーを作成
            providers["gemini"] = self._create_mock_provider()

        # 他のプロバイダーもここに追加可能
        # providers["openai"] = OpenAIProvider(...)
        # providers["claude"] = ClaudeProvider(...)

        return providers

    def _select_best_provider(self) -> Optional[BaseAIProvider]:
        """最適なプロバイダーを選択"""
        if not self.providers:
            # モックモードの場合はモックプロバイダーを使用
            if self.mock_mode:
                return self._create_mock_provider()
            return None

        # 利用可能なプロバイダーから選択（優先度順）
        priorities = ["gemini", "openai", "claude"]

        for provider_name in priorities:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if self._test_provider(provider):
                    return provider

        # フォールバックとして最初のプロバイダーを使用
        return list(self.providers.values())[0] if self.providers else None

    def _test_provider(self, provider: BaseAIProvider) -> bool:
        """プロバイダーの動作確認"""
        try:
            # 簡単なテストプロンプト
            test_prompt = "Hello, are you working?"
            response = provider.generate_sync(test_prompt)
            return len(response) > 0
        except Exception as e:
            self.logger.warning(f"プロバイダーテスト失敗: {str(e)}")
            return False

    def _initialize_response_variants(self) -> Dict[str, List[ResponseVariant]]:
        """応答バリエーションを初期化"""
        variants = {
            "general": [
                ResponseVariant(
                    id="creative",
                    prompt_template="{base_prompt}\n\n創造的に、独自の視点で答えてください。",
                    temperature_range=(0.8, 1.0),
                    weight=0.3
                ),
                ResponseVariant(
                    id="balanced",
                    prompt_template="{base_prompt}\n\nバランスの取れた、役立つ回答をしてください。",
                    temperature_range=(0.5, 0.7),
                    weight=0.5
                ),
                ResponseVariant(
                    id="precise",
                    prompt_template="{base_prompt}\n\n正確で、事実に基づいた回答をしてください。",
                    temperature_range=(0.1, 0.3),
                    weight=0.2
                )
            ],
            "casual": [
                ResponseVariant(
                    id="friendly",
                    prompt_template="{base_prompt}\n\nフレンドリーで、親しみやすい口調で答えてください。",
                    temperature_range=(0.7, 0.9),
                    weight=0.6
                ),
                ResponseVariant(
                    id="humorous",
                    prompt_template="{base_prompt}\n\nユーモアを交えつつ、役立つ回答をしてください。",
                    temperature_range=(0.8, 1.0),
                    weight=0.4
                )
            ],
            "technical": [
                ResponseVariant(
                    id="detailed",
                    prompt_template="{base_prompt}\n\n技術的な詳細を交えて、詳しく説明してください。",
                    temperature_range=(0.3, 0.6),
                    weight=0.7
                ),
                ResponseVariant(
                    id="concise",
                    prompt_template="{base_prompt}\n\n簡潔に、重要なポイントだけをまとめて答えてください。",
                    temperature_range=(0.2, 0.4),
                    weight=0.3
                )
            ]
        }
        return variants

    def generate_flexible_response_sync(
        self,
        prompt: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
        response_style: str = "balanced",
        force_refresh: bool = False
    ) -> str:
        """
        同期版の柔軟な応答生成

        Args:
            prompt: ベースプロンプト
            user_id: ユーザーID
            context: 追加コンテキスト
            response_style: 応答スタイル
            force_refresh: キャッシュを無視

        Returns:
            生成された応答
        """
        try:
            # モックモードの場合
            if self.mock_mode:
                return self._generate_mock_response(prompt, user_id, context, response_style)

            # キャッシュチェック
            cache_key = self._generate_cache_key(prompt, user_id, response_style)
            if not force_refresh:
                cached_response = self._get_cached_response(cache_key)
                if cached_response:
                    return cached_response

            # レート制限チェック
            if not self.rate_limiter.check_limit(user_id):
                return "申し訳ありません。現在リクエストが集中しています。少し待ってからお試しください。"

            # コンテキスト統合
            enhanced_prompt = self._enhance_prompt_with_context_sync(prompt, user_id, context)

            # 応答バリエーション選択
            variant = self._select_response_variant(response_style, context)

            # プロンプト完成
            final_prompt = variant.prompt_template.format(base_prompt=enhanced_prompt)

            # 温度設定
            # ResponseVariant.temperature_range を正しく参照
            temp_min, temp_max = (variant.temperature_range if isinstance(getattr(variant, 'temperature_range', None), tuple)
                                  else (0.5, 0.7))
            temperature = random.uniform(temp_min, temp_max)

            # プロバイダー選択
            provider = self.active_provider
            if not provider:
                return "申し訳ありません。AIサービスが利用できません。"

            # 生成実行
            response = provider.generate_sync(
                final_prompt,
                temperature=temperature,
                max_tokens=self._calculate_max_tokens(prompt)
            )

            # キャッシュ保存
            self._cache_response(cache_key, response)

            # 使用状況記録
            self._record_usage(user_id, "generate_flexible_response")

            return response

        except Exception as e:
            self.logger.error(f"柔軟応答生成エラー: {str(e)}")
            return "申し訳ありません。応答の生成中にエラーが発生しました。"

    def _generate_mock_response(self, prompt: str, user_id: str, context: Optional[Dict[str, Any]], response_style: str) -> str:
        """モックモードでの応答生成"""
        # プロンプトに基づいて適切なモック応答を生成
        prompt_lower = prompt.lower()

        if "天気" in prompt_lower:
            return f"🌤️ 東京の現在の天気は晴れで、気温は22℃です。今日は快適な一日になりそうです。"
        elif "通知" in prompt_lower:
            return "✅ 通知を設定しました。指定された時間にリマインドをお送りします。"
        elif "検索" in prompt_lower:
            return "🔍 検索結果を表示します。関連する情報をいくつか見つけました。"
        elif "こんにちは" in prompt_lower or "始めまして" in prompt_lower:
            return "こんにちは！私はAIアシスタントです。今日はどのようなお手伝いができますか？"
        elif "ありがとう" in prompt_lower:
            return "どういたしまして！お役に立てて嬉しいです。何か他に質問ありますか？"
        elif "エラー" in prompt_lower or "問題" in prompt_lower:
            return "申し訳ありません。問題が発生したようです。もう一度お試しいただけますか？"
        else:
            # 汎用的な応答
            return f"「{prompt[:50]}...」についてのお問い合わせですね。適切な対応を取らせていただきます。"

    def _select_best_provider(self) -> Optional[BaseAIProvider]:
        """最適なプロバイダーを選択"""
        if not self.providers:
            # モックモードの場合はモックプロバイダーを使用
            if self.mock_mode:
                return self._create_mock_provider()
            return None

        # 利用可能なプロバイダーから選択（優先度順）
        priorities = ["gemini", "openai", "claude"]

        for provider_name in priorities:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if self._test_provider(provider):
                    return provider

        # フォールバックとして最初のプロバイダーを使用
        return list(self.providers.values())[0] if self.providers else None

    def _create_mock_provider(self) -> BaseAIProvider:
        """モックプロバイダーを作成"""
        class MockProvider:
            def __init__(self):
                self.config = AIProviderConfig(
                    name="mock",
                    api_key_env="MOCK_API_KEY",
                    base_url="mock://localhost",
                    model_name="mock-model",
                    temperature=0.7,
                    max_tokens=1000
                )

            async def generate_async(self, prompt: str, **kwargs) -> str:
                return self._generate_mock_response(prompt, **kwargs)

            def generate_sync(self, prompt: str, **kwargs) -> str:
                return self._generate_mock_response(prompt, **kwargs)

            def _generate_mock_response(self, prompt: str, **kwargs) -> str:
                """モック応答生成"""
                prompt_lower = prompt.lower()

                if "天気" in prompt_lower:
                    return "現在の天気は晴れで、気温は22℃です。"
                elif "通知" in prompt_lower:
                    return "通知を設定しました。"
                elif "検索" in prompt_lower:
                    return "検索結果を表示します。"
                else:
                    return f"モック応答: {prompt[:100]}..."

        return MockProvider()

    def _generate_cache_key(self, prompt: str, user_id: str, style: str) -> str:
        """キャッシュキーを生成"""
        content = f"{prompt}:{user_id}:{style}:{datetime.now().strftime('%Y%m%d%H')}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """キャッシュから応答を取得"""
        with self.cache_lock:
            if cache_key in self.response_cache:
                cached = self.response_cache[cache_key]
                if datetime.now() - cached['timestamp'] < timedelta(hours=1):
                    return cached['response']
                else:
                    # キャッシュ期限切れ
                    del self.response_cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: str):
        """応答をキャッシュ"""
        with self.cache_lock:
            self.response_cache[cache_key] = {
                'response': response,
                'timestamp': datetime.now()
            }

    def _enhance_prompt_with_context_sync(self, base_prompt: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """同期版コンテキスト統合プロンプト生成"""
        # 非同期版を呼び出し
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._enhance_prompt_with_context(base_prompt, user_id, context))
        finally:
            loop.close()

    async def _enhance_prompt_with_context(self, base_prompt: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """コンテキストを統合したプロンプト生成"""
        # ユーザー設定取得
        user_settings = self.user_settings.get(user_id, {})

        # コンテキストマネージャーで文脈取得
        conversation_context = await self.context_manager.get_context(user_id)

        # 利用可能なAI機能を取得
        available_functions = self._get_available_ai_functions()

        # プロンプト強化
        enhancements = []

        # 会話文脈の追加
        if conversation_context:
            enhancements.append(f"会話の文脈: {conversation_context}")

        # ユーザー設定の追加
        if user_settings.get('preferences'):
            enhancements.append(f"ユーザーの好み: {user_settings['preferences']}")

        # 追加コンテキストの追加
        if context:
            enhancements.append(f"追加情報: {context}")

        # 利用可能なAI機能の追加
        if available_functions:
            function_list = "\n".join(f"- {func['name']}: {func['description']}" for func in available_functions)
            enhancements.append(f"利用可能な機能:\n{function_list}")

        # 時間帯による調整
        hour = datetime.now().hour
        if 6 <= hour < 12:
            enhancements.append("朝の時間帯なので、元気でポジティブなトーンで答えてください。")
        elif 18 <= hour < 24:
            enhancements.append("夜の時間帯なので、リラックスしたトーンで答えてください。")

        if enhancements:
            enhanced_prompt = f"{base_prompt}\n\n追加の指示:\n" + "\n".join(f"- {e}" for e in enhancements)
            return enhanced_prompt

        return base_prompt

    def _select_response_variant(self, style: str, context: Optional[Dict[str, Any]] = None) -> ResponseVariant:
        """応答バリエーションを選択"""
        # デフォルトのバリエーションを使用
        variants = self.response_variants.get("general", [])

        # スタイル指定がある場合
        if style in self.response_variants:
            variants = self.response_variants[style]

        # 文脈に基づいて重み付け
        if context:
            # 技術的な内容の場合、technicalバリエーションを優先
            if context.get('is_technical', False):
                technical_variants = self.response_variants.get("technical", [])
                if technical_variants:
                    variants = technical_variants

        # 重み付けによる選択
        total_weight = sum(v.weight for v in variants)
        if total_weight == 0:
            return variants[0] if variants else ResponseVariant("default", "{base_prompt}", (0.7, 0.7))

        r = random.random() * total_weight
        current_weight = 0
        for variant in variants:
            current_weight += variant.weight
            if r <= current_weight:
                return variant

    def _get_available_ai_functions(self) -> List[Dict[str, Any]]:
        """利用可能なAI機能を取得"""
        try:
            from .ai_function_plugin import ai_function_registry
            functions = ai_function_registry.list_functions()

            return [
                {
                    "name": func.name,
                    "description": func.description,
                    "trigger_keywords": func.trigger_keywords[:3],  # 最初の3つだけ
                    "category": self._categorize_function(func.name)
                }
                for func in functions
            ]
        except Exception as e:
            self.logger.warning(f"AI機能取得エラー: {str(e)}")
            return []

    def _categorize_function(self, function_name: str) -> str:
        """機能をカテゴリ分類"""
        name_lower = function_name.lower()

        if any(keyword in name_lower for keyword in ['notification', '通知', 'remind']):
            return '通知'
        elif any(keyword in name_lower for keyword in ['weather', '天気']):
            return '天気'
        elif any(keyword in name_lower for keyword in ['search', '検索']):
            return '検索'
        elif any(keyword in name_lower for keyword in ['task', 'タスク', 'auto']):
            return 'タスク'
        elif any(keyword in name_lower for keyword in ['math', '計算']):
            return '計算'
        elif any(keyword in name_lower for keyword in ['translate', '翻訳']):
            return '翻訳'
        else:
            return 'その他'

    def _calculate_max_tokens(self, prompt: str) -> int:
        """プロンプト長に基づいて最大トークン数を計算"""
        prompt_length = len(prompt.split())
        # プロンプトが長い場合は応答トークンを減らす
        if prompt_length > 1000:
            return 1000
        elif prompt_length > 500:
            return 2000
        else:
            return 4000

    def _record_usage(self, user_id: str, action: str):
        """使用状況を記録"""
        # 実際の使用状況記録（必要に応じて実装）
        pass

    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """ユーザー設定を取得"""
        return self.user_settings.get(user_id, {})

    def update_user_settings(self, user_id: str, settings: Dict[str, Any]):
        """ユーザー設定を更新"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id].update(settings)

    def add_response_variant(self, category: str, variant: ResponseVariant):
        """応答バリエーションを追加"""
        if category not in self.response_variants:
            self.response_variants[category] = []
        self.response_variants[category].append(variant)

    async def generate_flexible_response(
        self,
        prompt: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
        response_style: str = "balanced",
        force_refresh: bool = False
    ) -> str:
        """
        非同期版の柔軟な応答生成

        Args:
            prompt: ベースプロンプト
            user_id: ユーザーID
            context: 追加コンテキスト
            response_style: 応答スタイル
            force_refresh: キャッシュを無視

        Returns:
            生成された応答
        """
        try:
            # モックモードの場合
            if self.mock_mode:
                return self._generate_mock_response(prompt, user_id, context, response_style)

            # キャッシュチェック
            cache_key = self._generate_cache_key(prompt, user_id, response_style)
            if not force_refresh:
                cached_response = self._get_cached_response(cache_key)
                if cached_response:
                    return cached_response

            # レート制限チェック
            if not self.rate_limiter.check_limit(user_id):
                return "申し訳ありません。現在リクエストが集中しています。少し待ってからお試しください。"

            # コンテキスト統合
            enhanced_prompt = await self._enhance_prompt_with_context(prompt, user_id, context)

            # 応答バリエーション選択
            variant = self._select_response_variant(response_style, context)

            # プロンプト完成
            final_prompt = variant.prompt_template.format(base_prompt=enhanced_prompt)

            # 温度設定
            import random
            temp_min, temp_max = (variant.temperature_range if isinstance(getattr(variant, 'temperature_range', None), tuple)
                                  else (0.5, 0.7))
            temperature = random.uniform(temp_min, temp_max)

            # プロバイダー選択
            provider = self.active_provider
            if not provider:
                return "申し訳ありません。AIサービスが利用できません。"

            # 生成実行
            response = await provider.generate_async(
                final_prompt,
                temperature=temperature,
                max_tokens=self._calculate_max_tokens(prompt)
            )

            # キャッシュ保存
            self._cache_response(cache_key, response)

            # 使用状況記録
            self._record_usage(user_id, "generate_flexible_response")

            return response

        except Exception as e:
            self.logger.error(f"柔軟応答生成エラー: {str(e)}")
            return "申し訳ありません。応答の生成中にエラーが発生しました。"

class RateLimiter:
    """レート制限管理"""

    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.user_requests: Dict[str, List[datetime]] = {}
        self.lock = threading.Lock()

    def check_limit(self, user_id: str) -> bool:
        """レート制限をチェック"""
        now = datetime.now()

        with self.lock:
            if user_id not in self.user_requests:
                self.user_requests[user_id] = []

            # 1分以内のリクエストをフィルタリング
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if now - req_time < timedelta(minutes=1)
            ]

            if len(self.user_requests[user_id]) >= self.max_requests:
                return False

            self.user_requests[user_id].append(now)
            return True

class AIContextManager:
    """AIコンテキスト管理"""

    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    async def get_context(self, user_id: str) -> Optional[str]:
        """ユーザーのコンテキストを取得"""
        with self.lock:
            if user_id in self.contexts:
                return self.contexts[user_id].get('conversation_summary')
        return None

    def update_context(self, user_id: str, context: Dict[str, Any]):
        """コンテキストを更新"""
        with self.lock:
            if user_id not in self.contexts:
                self.contexts[user_id] = {}
            self.contexts[user_id].update(context)

# グローバルインスタンス
flexible_ai_service = FlexibleAIService()
