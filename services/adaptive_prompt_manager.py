"""
Adaptive Prompt Manager - コンテキストに応じた動的プロンプト生成
"""
import logging
import json
import os
import re
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
import threading
import random

@dataclass
class PromptTemplate:
    """プロンプトテンプレート"""
    id: str
    name: str
    template: str
    variables: Dict[str, str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    category: str = "general"

@dataclass
class ContextPattern:
    """コンテキストパターン"""
    pattern_id: str
    keywords: List[str]
    context_type: str  # conversation, user_intent, time_context, etc.
    weight: float = 1.0
    prompt_modifications: Dict[str, Any] = field(default_factory=dict)

class AdaptivePromptManager:
    """適応型プロンプトマネージャー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # プロンプトテンプレート
        self.templates = self._initialize_templates()

        # コンテキストパターン
        self.context_patterns = self._initialize_context_patterns()

        # ユーザー履歴
        self.user_histories: Dict[str, List[Dict[str, Any]]] = {}
        self.history_lock = threading.Lock()

        # 動的変数解決関数
        self.variable_resolvers = {
            'current_time': self._resolve_current_time,
            'user_name': self._resolve_user_name,
            'conversation_count': self._resolve_conversation_count,
            'recent_topics': self._resolve_recent_topics,
            'user_mood': self._resolve_user_mood,
            'weather_info': self._resolve_weather_info,
            'time_of_day': self._resolve_time_of_day
        }

        self.logger.info("Adaptive Prompt Managerを初期化しました")

    def _initialize_templates(self) -> Dict[str, List[PromptTemplate]]:
        """プロンプトテンプレートを初期化"""
        templates = {
            "general": [
                PromptTemplate(
                    id="helpful_assistant",
                    name="役立つアシスタント",
                    template="""あなたは親切で知識豊富なAIアシスタントです。
以下のクエリに対して、正確で役立つ回答を提供してください。

クエリ: {query}

回答のガイドライン:
- 明確で理解しやすい言葉を使用
- 具体的な例を交えて説明
- 必要に応じてステップバイステップで説明
- 追加の質問で深掘りできることを示唆

現在の時間: {current_time}
ユーザーの会話数: {conversation_count}
最近のトピック: {recent_topics}

回答:""",
                    variables={
                        'query': 'ユーザーのクエリ',
                        'current_time': '現在の時間',
                        'conversation_count': '会話数',
                        'recent_topics': '最近のトピック'
                    },
                    priority=10,
                    category="general"
                ),
                PromptTemplate(
                    id="creative_helper",
                    name="創造的なヘルパー",
                    template="""あなたは創造的で革新的なAIアシスタントです。
以下のクエリに対して、独創的な視点と新しいアイデアを提供してください。

クエリ: {query}

創造的なアプローチ:
- 従来の方法にとらわれない
- 複数の選択肢を提示
- 意外性のある提案も含む
- 実用的で実現可能なアイデア

現在の状況: {current_time}
ユーザーの気分: {user_mood}
天気情報: {weather_info}

回答:""",
                    variables={
                        'query': 'ユーザーのクエリ',
                        'current_time': '現在の時間',
                        'user_mood': 'ユーザーの気分',
                        'weather_info': '天気情報'
                    },
                    priority=8,
                    category="creative"
                )
            ],
            "technical": [
                PromptTemplate(
                    id="technical_expert",
                    name="技術専門家",
                    template="""あなたは技術分野の専門家です。
以下の技術的なクエリに対して、正確で詳細な回答を提供してください。

クエリ: {query}

技術的な回答ガイドライン:
- 専門用語は適切に説明
- コード例は具体的に
- ベストプラクティスを言及
- 潜在的な問題点と解決策を提示
- 参考資料やドキュメントを推奨

技術レベル: {technical_level}
関連技術: {related_technologies}
時間帯: {time_of_day}

回答:""",
                    variables={
                        'query': '技術的なクエリ',
                        'technical_level': '技術レベル',
                        'related_technologies': '関連技術',
                        'time_of_day': '時間帯'
                    },
                    priority=9,
                    category="technical"
                )
            ],
            "casual": [
                PromptTemplate(
                    id="friendly_chat",
                    name="フレンドリーな会話",
                    template="""あなたはフレンドリーで話しやすいAIアシスタントです。
以下のカジュアルなクエリに対して、親しみやすいトーンで答えてください。

クエリ: {query}

カジュアルな会話のポイント:
- 日常会話のような自然な表現
- 絵文字や感嘆符を適度に使用
- 相手の興味を引き出す質問を交える
- 共感を示す言葉を入れる

現在の時間帯: {time_of_day}
ユーザーの気分: {user_mood}
会話の雰囲気: {conversation_mood}

回答:""",
                    variables={
                        'query': 'カジュアルなクエリ',
                        'time_of_day': '時間帯',
                        'user_mood': 'ユーザーの気分',
                        'conversation_mood': '会話の雰囲気'
                    },
                    priority=7,
                    category="casual"
                )
            ]
        }
        return templates

    def _initialize_context_patterns(self) -> List[ContextPattern]:
        """コンテキストパターンを初期化"""
        patterns = [
            ContextPattern(
                pattern_id="technical_query",
                keywords=["コード", "プログラム", "開発", "API", "データベース", "アルゴリズム"],
                context_type="technical",
                weight=1.2,
                prompt_modifications={
                    "category": "technical",
                    "technical_level": "intermediate"
                }
            ),
            ContextPattern(
                pattern_id="creative_request",
                keywords=["アイデア", "新しい", "創造", "デザイン", "発想", "コンセプト"],
                context_type="creative",
                weight=1.1,
                prompt_modifications={
                    "category": "creative",
                    "creativity_level": "high"
                }
            ),
            ContextPattern(
                pattern_id="casual_talk",
                keywords=["最近", "どう", "元気", "おすすめ", "教えて", "話"],
                context_type="casual",
                weight=1.0,
                prompt_modifications={
                    "category": "casual",
                    "tone": "friendly"
                }
            ),
            ContextPattern(
                pattern_id="problem_solving",
                keywords=["問題", "解決", "方法", "やり方", "できない", "困って"],
                context_type="problem_solving",
                weight=1.3,
                prompt_modifications={
                    "approach": "systematic",
                    "detail_level": "detailed"
                }
            ),
            ContextPattern(
                pattern_id="learning_request",
                keywords=["学びたい", "勉強", "チュートリアル", "基礎", "初心者"],
                context_type="educational",
                weight=1.2,
                prompt_modifications={
                    "teaching_style": "step_by_step",
                    "difficulty": "beginner_friendly"
                }
            )
        ]
        return patterns

    async def generate_adaptive_prompt(
        self,
        base_query: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        適応型プロンプトを生成

        Args:
            base_query: ベースクエリ
            user_id: ユーザーID
            context: 追加コンテキスト

        Returns:
            Tuple[生成されたプロンプト, 使用されたテンプレート情報]
        """
        try:
            # コンテキスト分析
            context_analysis = self._analyze_context(base_query, context)

            # 最適なテンプレート選択
            selected_template = self._select_template(context_analysis)

            # 変数解決
            resolved_variables = await self._resolve_variables(
                selected_template.variables,
                user_id,
                context_analysis
            )

            # プロンプト生成
            prompt = selected_template.template.format(**resolved_variables)

            # 追加のコンテキスト情報付与
            enhanced_prompt = await self._enhance_prompt_with_context(
                prompt,
                context_analysis,
                user_id
            )

            template_info = {
                "template_id": selected_template.id,
                "template_name": selected_template.name,
                "category": selected_template.category,
                "context_analysis": context_analysis,
                "resolved_variables": resolved_variables
            }

            return enhanced_prompt, template_info

        except Exception as e:
            self.logger.error(f"適応型プロンプト生成エラー: {str(e)}")
            # フォールバックとしてシンプルなプロンプトを生成
            fallback_prompt = f"以下のクエリに対して役立つ回答を提供してください:\n\nクエリ: {base_query}"
            return fallback_prompt, {"error": str(e)}

    def _analyze_context(self, query: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """コンテキストを分析"""
        context = {
            "query_length": len(query),
            "query_complexity": self._calculate_complexity(query),
            "detected_intent": self._detect_intent(query),
            "time_context": self._get_time_context(),
            "additional_context": additional_context or {}
        }

        # コンテキストパターンにマッチするか確認
        matched_patterns = []
        for pattern in self.context_patterns:
            if any(keyword in query.lower() for keyword in pattern.keywords):
                matched_patterns.append(pattern)
                # パターンによるコンテキスト更新
                context.update(pattern.prompt_modifications)

        context["matched_patterns"] = [p.pattern_id for p in matched_patterns]
        return context

    def _calculate_complexity(self, query: str) -> str:
        """クエリの複雑さを計算"""
        words = query.split()
        word_count = len(words)

        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "moderate"
        else:
            return "complex"

    def _detect_intent(self, query: str) -> str:
        """クエリの意図を検出"""
        query_lower = query.lower()

        # 質問パターン
        if any(word in query_lower for word in ["何", "どう", "いつ", "どこ", "誰", "なぜ", "どのように"]):
            return "question"

        # リクエストパターン
        if any(word in query_lower for word in ["して", "やって", "作成", "実行", "計算", "翻訳"]):
            return "request"

        # 会話パターン
        if any(word in query_lower for word in ["最近", "どう", "元気", "おすすめ", "教えて"]):
            return "casual_talk"

        return "general"

    def _get_time_context(self) -> Dict[str, Any]:
        """時間コンテキストを取得"""
        now = datetime.now()
        hour = now.hour

        time_context = {
            "hour": hour,
            "time_of_day": self._resolve_time_of_day(now),
            "is_weekend": now.weekday() >= 5,
            "is_morning": 6 <= hour < 12,
            "is_afternoon": 12 <= hour < 18,
            "is_evening": 18 <= hour < 24
        }

        return time_context

    def _select_template(self, context_analysis: Dict[str, Any]) -> PromptTemplate:
        """最適なテンプレートを選択"""
        # コンテキストに基づいてカテゴリを決定
        category = context_analysis.get("context_type", "general")

        # カテゴリに対応するテンプレートを取得
        available_templates = self.templates.get(category, self.templates.get("general", []))

        if not available_templates:
            # フォールバック
            return PromptTemplate(
                id="fallback",
                name="フォールバック",
                template="{query}",
                variables={"query": "クエリ"},
                priority=1
            )

        # 優先度順にソート
        available_templates.sort(key=lambda t: t.priority, reverse=True)

        # コンテキストパターンによる重み付け
        matched_patterns = context_analysis.get("matched_patterns", [])
        if matched_patterns:
            # マッチしたパターンに関連するテンプレートを優先
            for template in available_templates:
                # 簡単なマッチングロジック（実際にはより洗練された方法を使用）
                if any(pattern in template.id for pattern in matched_patterns):
                    return template

        return available_templates[0]

    async def _resolve_variables(self, variables: Dict[str, str], user_id: str, context: Dict[str, Any]) -> Dict[str, str]:
        """変数を解決"""
        resolved = {}

        for var_name, description in variables.items():
            if var_name in self.variable_resolvers:
                try:
                    value = await self.variable_resolvers[var_name](user_id, context)
                    resolved[var_name] = value
                except Exception as e:
                    self.logger.warning(f"変数解決エラー ({var_name}): {str(e)}")
                    resolved[var_name] = f"[{description}]"
            else:
                resolved[var_name] = f"[{description}]"

        return resolved

    async def _resolve_current_time(self, user_id: str, context: Dict[str, Any]) -> str:
        """現在時間を解決"""
        now = datetime.now()
        return now.strftime('%Y年%m月%d日 %H時%M分')

    async def _resolve_user_name(self, user_id: str, context: Dict[str, Any]) -> str:
        """ユーザー名を解決"""
        # 実際にはユーザー管理システムから取得
        return f"ユーザー{user_id[:4]}"

    async def _resolve_conversation_count(self, user_id: str, context: Dict[str, Any]) -> str:
        """会話数を解決"""
        with self.history_lock:
            user_history = self.user_histories.get(user_id, [])
            return str(len(user_history) + 1)

    async def _resolve_recent_topics(self, user_id: str, context: Dict[str, Any]) -> str:
        """最近のトピックを解決"""
        with self.history_lock:
            user_history = self.user_histories.get(user_id, [])
            if len(user_history) >= 3:
                recent_queries = [h.get('query', '') for h in user_history[-3:]]
                return ', '.join(recent_queries)
            return "なし"

    async def _resolve_user_mood(self, user_id: str, context: Dict[str, Any]) -> str:
        """ユーザーの気分を解決"""
        # 簡易的な気分推定（実際にはより洗練された分析が必要）
        return "良好"

    async def _resolve_weather_info(self, user_id: str, context: Dict[str, Any]) -> str:
        """天気情報を解決"""
        # 実際にはWeatherServiceから取得
        return "晴れ"

    async def _resolve_time_of_day(self, user_id: str, context: Dict[str, Any]) -> str:
        """時間帯を解決"""
        now = datetime.now()
        hour = now.hour

        if 6 <= hour < 12:
            return "朝"
        elif 12 <= hour < 18:
            return "昼"
        elif 18 <= hour < 24:
            return "夜"
        else:
            return "深夜"

    async def _enhance_prompt_with_context(self, base_prompt: str, context_analysis: Dict[str, Any], user_id: str) -> str:
        """コンテキストによるプロンプト強化"""
        enhancements = []

        # 複雑さによる調整
        complexity = context_analysis.get("query_complexity", "moderate")
        if complexity == "complex":
            enhancements.append("クエリが複雑なため、詳細で体系的な回答をしてください。")
        elif complexity == "simple":
            enhancements.append("クエリがシンプルなため、簡潔で分かりやすい回答をしてください。")

        # 意図による調整
        intent = context_analysis.get("detected_intent", "general")
        if intent == "question":
            enhancements.append("質問形式なので、明確で具体的な回答をしてください。")
        elif intent == "request":
            enhancements.append("リクエスト形式なので、実行可能な解決策を提供してください。")

        # 時間帯による調整
        time_context = context_analysis.get("time_context", {})
        if time_context.get("is_morning"):
            enhancements.append("朝の時間帯なので、元気でポジティブなトーンを保ってください。")
        elif time_context.get("is_evening"):
            enhancements.append("夜の時間帯なので、リラックスしたトーンで答えてください。")

        if enhancements:
            enhanced_prompt = base_prompt + "\n\n追加の指示:\n" + "\n".join(f"- {e}" for e in enhancements)
            return enhanced_prompt

        return base_prompt

    def record_user_interaction(self, user_id: str, query: str, response: str, context: Dict[str, Any]):
        """ユーザーインタラクションを記録"""
        with self.history_lock:
            if user_id not in self.user_histories:
                self.user_histories[user_id] = []

            interaction = {
                "timestamp": datetime.now(),
                "query": query,
                "response": response,
                "context": context
            }

            self.user_histories[user_id].append(interaction)

            # 履歴を制限（最新100件まで）
            if len(self.user_histories[user_id]) > 100:
                self.user_histories[user_id] = self.user_histories[user_id][-100:]

    def get_user_history_summary(self, user_id: str) -> Dict[str, Any]:
        """ユーザー履歴のサマリーを取得"""
        with self.history_lock:
            if user_id not in self.user_histories:
                return {"interaction_count": 0, "recent_topics": []}

            history = self.user_histories[user_id]

            # 最近のトピック抽出
            recent_queries = [h.get("query", "") for h in history[-5:]]
            topics = list(set(recent_queries))

            return {
                "interaction_count": len(history),
                "recent_topics": topics,
                "first_interaction": history[0]["timestamp"] if history else None,
                "last_interaction": history[-1]["timestamp"] if history else None
            }

# グローバルインスタンス
adaptive_prompt_manager = AdaptivePromptManager()
