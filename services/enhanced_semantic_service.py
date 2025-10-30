"""
AI駆動の動的機能生成システム - セマンティック解析強化サービス
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

@dataclass
class SemanticContext:
    """セマンティック解析の文脈情報"""
    user_id: str
    session_id: str
    timestamp: datetime
    conversation_history: List[str]
    user_preferences: Dict[str, Any]
    recent_topics: List[str]
    intent_confidence: float
    extracted_entities: Dict[str, List[str]]

@dataclass
class IntentAnalysis:
    """意図解析結果"""
    primary_intent: str
    secondary_intents: List[str]
    confidence_score: float
    urgency_level: str  # 'high', 'medium', 'low'
    temporal_context: str  # 'immediate', 'scheduled', 'ongoing'
    action_type: str  # 'create', 'modify', 'query', 'control'

@dataclass
class EntityExtraction:
    """エンティティ抽出結果"""
    functions: List[str]
    objects: List[str]
    conditions: List[str]
    parameters: Dict[str, Any]
    time_references: List[str]
    locations: List[str]

@dataclass
class AmbiguityInfo:
    """曖昧さ情報"""
    is_ambiguous: bool
    ambiguous_terms: List[str]
    clarification_questions: List[str]
    possible_interpretations: List[str]
    confidence_threshold: float

class EnhancedSemanticAnalyzer:
    """
    強化されたセマンティック解析システム
    - 意図理解の深化
    - 文脈考慮
    - 曖昧さの検出と解消
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 意図パターン定義
        self.intent_patterns = {
            'create_function': [
                r'機能.*作って', r'機能.*作成', r'自動化.*して',
                r'.*機能.*追加', r'.*作って.*機能', r'実装.*して'
            ],
            'modify_function': [
                r'機能.*変え', r'機能.*修正', r'機能.*更新',
                r'機能.*改善', r'.*変えて', r'.*直して'
            ],
            'query_function': [
                r'機能.*何', r'機能.*どう', r'機能.*一覧',
                r'機能.*確認', r'機能.*見せて', r'機能.*教えて'
            ],
            'control_function': [
                r'機能.*実行', r'機能.*動か', r'機能.*スタート',
                r'機能.*ストップ', r'機能.*停止', r'機能.*開始'
            ]
        }

        # 時間参照パターン
        self.time_patterns = [
            r'毎日', r'毎週', r'毎月', r'毎朝', r'毎晩',
            r'毎時間', r'今すぐ', r'すぐに', r'後で',
            r'明日', r'来週', r'今週', r'今月'
        ]

        # 曖昧表現パターン
        self.ambiguity_patterns = [
            r'なんか', r'みたいな', r'ような', r'くらい',
            r'くらいで', r'とか', r'それ', r'これ',
            r'あれ', r'どれ', r'どれか'
        ]

    def analyze_semantic_context(self, user_input: str, context: SemanticContext) -> Tuple[IntentAnalysis, EntityExtraction, AmbiguityInfo]:
        """
        強化されたセマンティック解析を実行
        """
        try:
            # 1. 意図解析
            intent_analysis = self._analyze_intent(user_input, context)

            # 2. エンティティ抽出
            entity_extraction = self._extract_entities(user_input, context)

            # 3. 曖昧さ検出
            ambiguity_info = self._detect_ambiguity(user_input, intent_analysis, entity_extraction)

            # 4. 文脈統合
            self._integrate_context(intent_analysis, entity_extraction, context)

            return intent_analysis, entity_extraction, ambiguity_info

        except Exception as e:
            self.logger.error(f"セマンティック解析エラー: {str(e)}")
            return self._create_default_analysis()

    def _analyze_intent(self, user_input: str, context: SemanticContext) -> IntentAnalysis:
        """意図を深く解析"""
        input_lower = user_input.lower()

        # プライマリ意図の特定
        primary_intent = 'unknown'
        max_confidence = 0.0

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, input_lower))
                if matches > 0:
                    confidence = min(matches * 0.3, 1.0)
                    if confidence > max_confidence:
                        max_confidence = confidence
                        primary_intent = intent

        # セカンダリ意図の抽出
        secondary_intents = []
        for intent, patterns in self.intent_patterns.items():
            if intent != primary_intent:
                for pattern in patterns:
                    if re.search(pattern, input_lower):
                        secondary_intents.append(intent)
                        break

        # 緊急度判定
        urgency_level = self._determine_urgency(user_input)

        # 時間的文脈判定
        temporal_context = self._determine_temporal_context(user_input)

        # アクションタイプ判定
        action_type = self._determine_action_type(user_input, primary_intent)

        return IntentAnalysis(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence_score=max_confidence,
            urgency_level=urgency_level,
            temporal_context=temporal_context,
            action_type=action_type
        )

    def _extract_entities(self, user_input: str, context: SemanticContext) -> EntityExtraction:
        """エンティティを詳細に抽出"""
        input_lower = user_input.lower()

        # 機能関連エンティティ
        functions = []
        function_patterns = [
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*機能',
            r'機能\s*([a-zA-Z_][a-zA-Z0-9_]*)',
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*を.*して'
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, input_lower)
            functions.extend(matches)

        # オブジェクトエンティティ
        objects = self._extract_objects(user_input)

        # 条件エンティティ
        conditions = self._extract_conditions(user_input)

        # パラメータ抽出
        parameters = self._extract_parameters(user_input)

        # 時間参照
        time_references = []
        for pattern in self.time_patterns:
            if re.search(pattern, input_lower):
                time_references.append(pattern)

        # 場所参照
        locations = self._extract_locations(user_input)

        return EntityExtraction(
            functions=functions,
            objects=objects,
            conditions=conditions,
            parameters=parameters,
            time_references=time_references,
            locations=locations
        )

    def _detect_ambiguity(self, user_input: str, intent: IntentAnalysis, entities: EntityExtraction) -> AmbiguityInfo:
        """曖昧さを検出"""
        ambiguous_terms = []
        clarification_questions = []

        # 曖昧表現の検出
        for pattern in self.ambiguity_patterns:
            if re.search(pattern, user_input.lower()):
                ambiguous_terms.append(pattern)

        # 意図の曖昧さチェック
        if intent.confidence_score < 0.5:
            clarification_questions.append("どのような機能をご希望ですか？")
            clarification_questions.append("具体的にどのようなことをしたいですか？")

        # エンティティの曖昧さチェック
        if len(entities.functions) == 0 and intent.primary_intent in ['create_function', 'modify_function']:
            clarification_questions.append("どの機能に対しての操作でしょうか？")
            clarification_questions.append("新しい機能を作成しますか？それとも既存の機能を変更しますか？")

        # 複数の解釈可能性チェック
        possible_interpretations = self._generate_possible_interpretations(user_input, intent, entities)

        return AmbiguityInfo(
            is_ambiguous=len(ambiguous_terms) > 0 or len(clarification_questions) > 0,
            ambiguous_terms=ambiguous_terms,
            clarification_questions=clarification_questions,
            possible_interpretations=possible_interpretations,
            confidence_threshold=0.7
        )

    def _integrate_context(self, intent: IntentAnalysis, entities: EntityExtraction, context: SemanticContext):
        """文脈情報を統合"""
        # 直近の会話トピックを考慮
        if context.recent_topics:
            recent_topic = context.recent_topics[-1]
            if recent_topic and intent.confidence_score < 0.8:
                # 直近のトピックに関連づける
                intent.confidence_score = min(intent.confidence_score + 0.2, 1.0)

        # ユーザーの嗜好を考慮
        if context.user_preferences:
            for pref_key, pref_value in context.user_preferences.items():
                if pref_key in intent.primary_intent or pref_key in str(entities.parameters):
                    intent.confidence_score = min(intent.confidence_score + 0.1, 1.0)

    # Helper methods
    def _determine_urgency(self, user_input: str) -> str:
        """緊急度を判定"""
        if re.search(r'今すぐ|すぐに|緊急|至急', user_input.lower()):
            return 'high'
        elif re.search(r'早く|なるべく早く', user_input.lower()):
            return 'medium'
        else:
            return 'low'

    def _determine_temporal_context(self, user_input: str) -> str:
        """時間的文脈を判定"""
        if re.search(r'今すぐ|すぐに|即座に', user_input.lower()):
            return 'immediate'
        elif re.search(r'毎日|毎週|毎月|定期的に', user_input.lower()):
            return 'scheduled'
        else:
            return 'ongoing'

    def _determine_action_type(self, user_input: str, primary_intent: str) -> str:
        """アクションタイプを判定"""
        if primary_intent == 'unknown':
            return 'query'
        elif re.search(r'作って|作成|追加', user_input.lower()):
            return 'create'
        elif re.search(r'変え|修正|更新', user_input.lower()):
            return 'modify'
        else:
            return 'control'

    def _extract_objects(self, user_input: str) -> List[str]:
        """オブジェクトを抽出"""
        # シンプルな実装：名詞句を抽出
        objects = []
        words = user_input.split()
        for i, word in enumerate(words):
            if len(word) > 1 and not word.endswith('機能'):
                if i > 0 and words[i-1] in ['の', 'を', 'に', 'で']:
                    objects.append(word)
        return objects

    def _extract_conditions(self, user_input: str) -> List[str]:
        """条件を抽出"""
        conditions = []
        condition_patterns = [
            r'もし.*なら', r'.*場合', r'.*とき', r'.*たら',
            r'.*条件で', r'.*基準で'
        ]

        for pattern in condition_patterns:
            matches = re.findall(pattern, user_input.lower())
            conditions.extend(matches)

        return conditions

    def _extract_parameters(self, user_input: str) -> Dict[str, Any]:
        """パラメータを抽出"""
        parameters = {}

        # 数値パラメータ
        num_matches = re.findall(r'(\d+)', user_input)
        if num_matches:
            parameters['count'] = int(num_matches[0])

        # 時間パラメータ
        time_matches = re.findall(r'(\d+)時間|(\d+)分|(\d+)秒', user_input)
        if time_matches:
            parameters['time_value'] = time_matches[0]

        return parameters

    def _extract_locations(self, user_input: str) -> List[str]:
        """場所を抽出"""
        locations = []
        # 日本の主要都市
        japanese_cities = ['東京', '大阪', '名古屋', '福岡', '札幌', '横浜', '京都']

        for city in japanese_cities:
            if city in user_input:
                locations.append(city)

        return locations

    def _generate_possible_interpretations(self, user_input: str, intent: IntentAnalysis, entities: EntityExtraction) -> List[str]:
        """可能な解釈を生成"""
        interpretations = []

        if intent.primary_intent == 'unknown':
            interpretations.append("新しい機能の作成を希望している可能性")
            interpretations.append("既存機能の確認を希望している可能性")
            interpretations.append("機能の実行を希望している可能性")

        if len(entities.functions) == 0:
            interpretations.append("新しい機能の作成")
            interpretations.append("既存機能の操作")

        return interpretations

    def _create_default_analysis(self) -> Tuple[IntentAnalysis, EntityExtraction, AmbiguityInfo]:
        """デフォルトの解析結果を作成"""
        return (
            IntentAnalysis(
                primary_intent='unknown',
                secondary_intents=[],
                confidence_score=0.0,
                urgency_level='medium',
                temporal_context='ongoing',
                action_type='query'
            ),
            EntityExtraction(
                functions=[],
                objects=[],
                conditions=[],
                parameters={},
                time_references=[],
                locations=[]
            ),
            AmbiguityInfo(
                is_ambiguous=True,
                ambiguous_terms=['不明瞭な表現'],
                clarification_questions=['具体的にどのような機能をご希望ですか？'],
                possible_interpretations=['新しい機能の作成', '既存機能の操作'],
                confidence_threshold=0.7
            )
        )
