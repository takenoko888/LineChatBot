"""
AI駆動の動的機能生成システム - 曖昧さ解消サービス
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import random

@dataclass
class ClarificationRequest:
    """明確化リクエスト"""
    request_id: str
    user_id: str
    original_message: str
    clarification_type: str  # 'intent', 'entity', 'parameter', 'context'
    questions: List[str]
    suggestions: List[str]
    priority: str  # 'high', 'medium', 'low'
    timeout_seconds: int

@dataclass
class AmbiguityResolution:
    """曖昧さ解消結果"""
    resolution_id: str
    original_request_id: str
    resolved_intent: str
    resolved_entities: Dict[str, Any]
    confidence_score: float
    resolution_method: str  # 'user_input', 'context', 'ai_suggestion'
    additional_info_needed: bool

@dataclass
class SuggestionContext:
    """提案の文脈"""
    context_type: str  # 'similar_functions', 'user_patterns', 'common_scenarios'
    suggestions: List[str]
    confidence_scores: List[float]
    reasoning: List[str]

class AmbiguityResolver:
    """
    高度な曖昧さ解消システム
    - 曖昧表現の検出と分類
    - 明確化のための質問生成
    - 文脈に基づく自動解消
    - 提案の提示
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 明確化質問テンプレート
        self.clarification_templates = {
            'intent': [
                "どのような機能を作成したいですか？",
                "具体的にどのようなことをしたいですか？",
                "新しい機能の作成ですか？それとも既存の機能の変更ですか？"
            ],
            'entity': [
                "どの機能に対して操作を行いますか？",
                "対象となる機能名を教えてください",
                "どの機能について話していますか？"
            ],
            'parameter': [
                "どのような条件で実行したいですか？",
                "どのくらいの頻度で実行しますか？",
                "いつ実行したいですか？"
            ],
            'context': [
                "どのような状況で使用しますか？",
                "どのような結果を期待していますか？",
                "他の機能とどのように連携しますか？"
            ]
        }

        # 曖昧表現パターン
        self.ambiguity_patterns = {
            'vague_reference': [
                r'それ', r'これ', r'あれ', r'どれ', r'どれか',
                r'なんか', r'みたいな', r'ような'
            ],
            'unclear_intent': [
                r'何か', r'どうにか', r'なんとか', r'なんとかして',
                r'どうしよう', r'どうしたら'
            ],
            'missing_details': [
                r'自動で', r'勝手に', r'勝手にやって',
                r'適当に', r'なんとなく'
            ],
            'unclear_scope': [
                r'全部', r'全部で', r'すべて', r'すべてで',
                r'いつも', r'いつも通り'
            ]
        }

        # 提案パターン
        self.suggestion_patterns = {
            'similar_functions': [
                "似たような機能として「{function_name}」があります",
                "「{function_name}」のような機能はいかがでしょうか",
                "同じような目的で「{function_name}」が利用できます"
            ],
            'common_scenarios': [
                "よく使われる機能として「{function_name}」があります",
                "一般的な用途では「{function_name}」が便利です",
                "多くのユーザーが利用している「{function_name}」をおすすめします"
            ],
            'user_patterns': [
                "あなたはよく「{function_name}」を使っています",
                "過去に「{function_name}」をよく利用されていました",
                "「{function_name}」があなたの使用傾向に合っています"
            ]
        }

    def resolve_ambiguity(self, user_input: str, semantic_analysis: Dict[str, Any],
                        context_tracker: Any, user_id: str = "default") -> Tuple[AmbiguityResolution, List[ClarificationRequest]]:
        """
        曖昧さを解消
        """
        try:
            # 曖昧さの検出と分類
            ambiguity_types = self._detect_ambiguity_types(user_input, semantic_analysis)

            # 自動解消の試行
            auto_resolution = self._attempt_auto_resolution(user_input, semantic_analysis, context_tracker, user_id)

            # 明確化リクエストの生成
            clarification_requests = []
            if not auto_resolution or auto_resolution.confidence_score < 0.7:
                clarification_requests = self._generate_clarification_requests(
                    user_input, semantic_analysis, ambiguity_types, user_id
                )

            # 提案の生成
            suggestions = self._generate_suggestions(user_input, semantic_analysis, context_tracker, user_id)

            # 解消結果の統合
            resolution = AmbiguityResolution(
                resolution_id=f"resolution_{datetime.now().isoformat()}",
                original_request_id=getattr(semantic_analysis, 'request_id', 'unknown'),
                resolved_intent=auto_resolution.resolved_intent if auto_resolution else semantic_analysis.get('primary_intent', 'unknown'),
                resolved_entities=auto_resolution.resolved_entities if auto_resolution else semantic_analysis.get('entities', {}),
                confidence_score=auto_resolution.confidence_score if auto_resolution else 0.3,
                resolution_method=auto_resolution.resolution_method if auto_resolution else 'partial',
                additional_info_needed=len(clarification_requests) > 0
            )

            return resolution, clarification_requests

        except Exception as e:
            self.logger.error(f"曖昧さ解消エラー: {str(e)}")
            return self._create_default_resolution(), []

    def _detect_ambiguity_types(self, user_input: str, semantic_analysis: Dict[str, Any]) -> List[str]:
        """曖昧さの種類を検出"""
        ambiguity_types = []
        input_lower = user_input.lower()

        # 曖昧参照の検出
        for pattern in self.ambiguity_patterns['vague_reference']:
            if re.search(pattern, input_lower):
                ambiguity_types.append('vague_reference')
                break

        # 不明確な意図の検出
        if semantic_analysis.get('confidence_score', 0) < 0.5:
            ambiguity_types.append('unclear_intent')

        # 詳細不足の検出
        for pattern in self.ambiguity_patterns['missing_details']:
            if re.search(pattern, input_lower):
                ambiguity_types.append('missing_details')
                break

        # 曖昧なスコープの検出
        for pattern in self.ambiguity_patterns['unclear_scope']:
            if re.search(pattern, input_lower):
                ambiguity_types.append('unclear_scope')
                break

        return list(set(ambiguity_types))  # 重複除去

    def _attempt_auto_resolution(self, user_input: str, semantic_analysis: Dict[str, Any],
                               context_tracker: Any, user_id: str) -> Optional[AmbiguityResolution]:
        """
        自動解消を試行
        """
        try:
            # 文脈情報から自動解消を試みる
            context_info = context_tracker.get_relevant_context(user_id, semantic_analysis.get('primary_intent', ''))

            # 直近の会話から意図を推測
            recent_turns = context_tracker.conversation_history.get(user_id, [])
            if recent_turns:
                latest_intent = recent_turns[-1].intent
                if semantic_analysis.get('confidence_score', 0) < 0.5 and latest_intent != 'unknown':
                    # 直近の意図を引き継ぐ
                    return AmbiguityResolution(
                        resolution_id="auto_resolution_context",
                        original_request_id=getattr(semantic_analysis, 'request_id', 'unknown'),
                        resolved_intent=latest_intent,
                        resolved_entities=recent_turns[-1].entities,
                        confidence_score=0.6,
                        resolution_method='context',
                        additional_info_needed=False
                    )

            # ユーザー行動パターンから推測
            user_patterns = context_tracker.get_user_patterns(user_id)
            if user_patterns and user_patterns.frequent_intents:
                most_frequent_intent = max(user_patterns.frequent_intents, key=user_patterns.frequent_intents.get)
                if semantic_analysis.get('confidence_score', 0) < 0.3:
                    return AmbiguityResolution(
                        resolution_id="auto_resolution_pattern",
                        original_request_id=getattr(semantic_analysis, 'request_id', 'unknown'),
                        resolved_intent=most_frequent_intent,
                        resolved_entities={'functions': user_patterns.preferred_functions[:3]},
                        confidence_score=0.5,
                        resolution_method='user_patterns',
                        additional_info_needed=True
                    )

            return None

        except Exception as e:
            self.logger.error(f"自動解消エラー: {str(e)}")
            return None

    def _generate_clarification_requests(self, user_input: str, semantic_analysis: Dict[str, Any],
                                       ambiguity_types: List[str], user_id: str) -> List[ClarificationRequest]:
        """
        明確化リクエストを生成
        """
        requests = []

        for ambiguity_type in ambiguity_types:
            if ambiguity_type == 'unclear_intent':
                questions = random.sample(self.clarification_templates['intent'], min(2, len(self.clarification_templates['intent'])))
                requests.append(ClarificationRequest(
                    request_id=f"clarify_intent_{datetime.now().isoformat()}",
                    user_id=user_id,
                    original_message=user_input,
                    clarification_type='intent',
                    questions=questions,
                    suggestions=self._generate_suggestions_for_intent(semantic_analysis),
                    priority='high',
                    timeout_seconds=300
                ))

            elif ambiguity_type == 'vague_reference':
                questions = ["具体的にどの機能のことを指していますか？"]
                requests.append(ClarificationRequest(
                    request_id=f"clarify_entity_{datetime.now().isoformat()}",
                    user_id=user_id,
                    original_message=user_input,
                    clarification_type='entity',
                    questions=questions,
                    suggestions=self._generate_suggestions_for_entity(semantic_analysis),
                    priority='medium',
                    timeout_seconds=300
                ))

            elif ambiguity_type in ['missing_details', 'unclear_scope']:
                questions = random.sample(self.clarification_templates['parameter'], min(2, len(self.clarification_templates['parameter'])))
                requests.append(ClarificationRequest(
                    request_id=f"clarify_parameter_{datetime.now().isoformat()}",
                    user_id=user_id,
                    original_message=user_input,
                    clarification_type='parameter',
                    questions=questions,
                    suggestions=self._generate_suggestions_for_parameter(semantic_analysis),
                    priority='medium',
                    timeout_seconds=300
                ))

        return requests

    def _generate_suggestions(self, user_input: str, semantic_analysis: Dict[str, Any],
                             context_tracker: Any, user_id: str) -> List[SuggestionContext]:
        """
        提案を生成
        """
        suggestions = []

        try:
            # 似た機能の提案
            if 'entities' in semantic_analysis and 'functions' in semantic_analysis['entities']:
                similar_functions = self._find_similar_functions(semantic_analysis['entities']['functions'])
                if similar_functions:
                    suggestions.append(SuggestionContext(
                        context_type='similar_functions',
                        suggestions=similar_functions,
                        confidence_scores=[0.8] * len(similar_functions),
                        reasoning=[f"「{func}」は似たような機能です" for func in similar_functions]
                    ))

            # 一般的なシナリオの提案
            common_suggestions = self._get_common_scenario_suggestions(semantic_analysis)
            if common_suggestions:
                suggestions.append(SuggestionContext(
                    context_type='common_scenarios',
                    suggestions=common_suggestions,
                    confidence_scores=[0.7] * len(common_suggestions),
                    reasoning=["一般的な用途でよく使われる機能です"] * len(common_suggestions)
                ))

            # ユーザーパターンベースの提案
            user_patterns = context_tracker.get_user_patterns(user_id)
            if user_patterns and user_patterns.preferred_functions:
                pattern_suggestions = user_patterns.preferred_functions[:3]
                suggestions.append(SuggestionContext(
                    context_type='user_patterns',
                    suggestions=pattern_suggestions,
                    confidence_scores=[0.9] * len(pattern_suggestions),
                    reasoning=[f"あなたがよく使う「{func}」です" for func in pattern_suggestions]
                ))

        except Exception as e:
            self.logger.error(f"提案生成エラー: {str(e)}")

        return suggestions

    # Helper methods
    def _generate_suggestions_for_intent(self, semantic_analysis: Dict[str, Any]) -> List[str]:
        """意図に対する提案を生成"""
        suggestions = [
            "新しい機能を「機能を作って〜」で作成できます",
            "既存機能の一覧は「機能一覧」と送信してください",
            "機能を「機能を実行して〜」で実行できます"
        ]

        if semantic_analysis.get('primary_intent') == 'create_function':
            suggestions.insert(0, "例: 「毎日の天気予報を自動で通知する機能を作って」")

        return suggestions

    def _generate_suggestions_for_entity(self, semantic_analysis: Dict[str, Any]) -> List[str]:
        """エンティティに対する提案を生成"""
        suggestions = [
            "「機能一覧」と送信して既存の機能を参照してください",
            "新しい機能名を指定して作成できます",
            "例: 「天気通知機能を作って」"
        ]

        return suggestions

    def _generate_suggestions_for_parameter(self, semantic_analysis: Dict[str, Any]) -> List[str]:
        """パラメータに対する提案を生成"""
        suggestions = [
            "「毎日」「毎週」「毎月」などの頻度を指定できます",
            "「今すぐ」「後で」などのタイミングを指定できます",
            "「東京」「大阪」などの場所を指定できます"
        ]

        return suggestions

    def _find_similar_functions(self, functions: List[str]) -> List[str]:
        """似た機能を検索"""
        # 実際の実装ではデータベースから似た機能を検索
        similar_functions = {
            '天気': ['weather_summary', 'daily_forecast', 'weather_notification'],
            '通知': ['notification_system', 'reminder_service', 'alert_manager'],
            '自動': ['auto_scheduler', 'automated_task', 'periodic_executor']
        }

        found_similar = []
        for func in functions:
            func_lower = func.lower()
            for key, similar in similar_functions.items():
                if key in func_lower:
                    found_similar.extend(similar)

        return list(set(found_similar))[:5]  # 最大5件

    def _get_common_scenario_suggestions(self, semantic_analysis: Dict[str, Any]) -> List[str]:
        """一般的なシナリオの提案を取得"""
        common_scenarios = [
            'weather_notification',  # 天気通知
            'daily_reminder',       # デイリーリマインダー
            'auto_backup',          # 自動バックアップ
            'news_summary',         # ニュース要約
            'schedule_manager'      # スケジュール管理
        ]

        # 意図に基づいてフィルタリング
        intent = semantic_analysis.get('primary_intent', '')
        if 'create' in intent:
            return common_scenarios[:3]
        elif 'control' in intent:
            return ['daily_reminder', 'auto_backup', 'schedule_manager']

        return common_scenarios

    def _create_default_resolution(self) -> AmbiguityResolution:
        """デフォルトの解消結果を作成"""
        return AmbiguityResolution(
            resolution_id="default_resolution",
            original_request_id="unknown",
            resolved_intent="unknown",
            resolved_entities={},
            confidence_score=0.0,
            resolution_method="default",
            additional_info_needed=True
        )

    def format_clarification_message(self, clarification_requests: List[ClarificationRequest]) -> str:
        """明確化メッセージをフォーマット"""
        if not clarification_requests:
            return ""

        message_parts = ["🤔 もう少し詳しく教えていただけますか？\n\n"]

        for i, request in enumerate(clarification_requests, 1):
            message_parts.append(f"{i}. {request.questions[0]}")
            if request.suggestions:
                message_parts.append(f"   💡 提案: {request.suggestions[0]}")
            message_parts.append("")

        message_parts.append("\nより具体的に教えてください！")
        return "\n".join(message_parts)

    def format_suggestions_message(self, suggestions: List[SuggestionContext]) -> str:
        """提案メッセージをフォーマット"""
        if not suggestions:
            return ""

        message_parts = ["💡 参考までに、以下のような機能があります:\n\n"]

        for suggestion in suggestions:
            message_parts.append(f"【{suggestion.context_type}】")
            for i, (suggestion_text, confidence) in enumerate(zip(suggestion.suggestions, suggestion.confidence_scores)):
                message_parts.append(f"• {suggestion_text} (信頼度: {confidence:.1f})")
            message_parts.append("")

        message_parts.append("\nこれらの機能を参考に新しい機能を作成できます！")
        return "\n".join(message_parts)
