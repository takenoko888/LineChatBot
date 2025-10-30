"""
AI駆動の動的機能生成システム - コンテキスト追跡サービス
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict, deque

@dataclass
class ConversationTurn:
    """会話のターン情報"""
    turn_id: str
    user_id: str
    timestamp: datetime
    user_message: str
    system_response: str
    intent: str
    entities: Dict[str, Any]
    context_features: Dict[str, Any]

@dataclass
class UserBehaviorPattern:
    """ユーザーの行動パターン"""
    user_id: str
    preferred_times: List[str]  # よく使用する時間帯
    frequent_intents: Dict[str, int]  # よく使う意図
    preferred_functions: List[str]  # よく使う機能
    conversation_style: Dict[str, Any]  # 会話スタイル
    temporal_patterns: Dict[str, Any]  # 時間的パターン

@dataclass
class ContextWindow:
    """コンテキストウィンドウ"""
    user_id: str
    session_id: str
    start_time: datetime
    current_topics: List[str]
    recent_entities: Dict[str, List[str]]
    conversation_history: deque  # 直近の会話履歴
    user_preferences: Dict[str, Any]
    active_features: List[str]  # 現在アクティブな機能
    context_score: float  # コンテキストの継続性スコア

class ContextTracker:
    """
    高度なコンテキスト追跡システム
    - 会話の文脈を追跡
    - ユーザーの行動パターンを学習
    - コンテキストの継続性を評価
    """

    def __init__(self, max_context_size: int = 50, context_window_hours: int = 24):
        self.logger = logging.getLogger(__name__)
        self.max_context_size = max_context_size
        self.context_window_hours = context_window_hours

        # コンテキストストレージ
        self.context_windows: Dict[str, ContextWindow] = {}
        self.user_patterns: Dict[str, UserBehaviorPattern] = {}
        self.conversation_history: Dict[str, List[ConversationTurn]] = defaultdict(list)

        # コンテキスト特徴量
        self.context_features = {
            'topic_continuity': 0.0,
            'intent_consistency': 0.0,
            'temporal_relevance': 0.0,
            'entity_coherence': 0.0,
            'user_familiarity': 0.0
        }

    def track_context(self, user_id: str, user_message: str, semantic_analysis: Dict[str, Any],
                     system_response: str = "") -> ContextWindow:
        """
        コンテキストを追跡・更新
        """
        try:
            # セッションIDの生成
            session_id = self._generate_session_id(user_id, user_message)

            # コンテキストウィンドウの取得または作成
            context_window = self._get_or_create_context_window(user_id, session_id)

            # 会話ターンの記録
            conversation_turn = ConversationTurn(
                turn_id=hashlib.md5(f"{user_id}_{datetime.now().isoformat()}".encode()).hexdigest(),
                user_id=user_id,
                timestamp=datetime.now(),
                user_message=user_message,
                system_response=system_response,
                intent=semantic_analysis.get('primary_intent', 'unknown'),
                entities=semantic_analysis.get('entities', {}),
                context_features=self._extract_context_features(user_message, semantic_analysis)
            )

            self._record_conversation_turn(conversation_turn)

            # コンテキストの更新
            self._update_context_window(context_window, conversation_turn, semantic_analysis)

            # ユーザー行動パターンの更新
            self._update_user_patterns(user_id, conversation_turn)

            # コンテキストスコアの計算
            context_window.context_score = self._calculate_context_score(context_window)

            return context_window

        except Exception as e:
            self.logger.error(f"コンテキスト追跡エラー: {str(e)}")
            return self._create_empty_context(user_id)

    def get_context_for_user(self, user_id: str) -> Optional[ContextWindow]:
        """ユーザーの現在のコンテキストを取得"""
        session_id = self._get_current_session_id(user_id)
        return self.context_windows.get(session_id)

    def get_user_patterns(self, user_id: str) -> Optional[UserBehaviorPattern]:
        """ユーザーの行動パターンを取得"""
        return self.user_patterns.get(user_id)

    def predict_next_intent(self, user_id: str) -> Dict[str, float]:
        """
        次の意図を予測
        """
        patterns = self.user_patterns.get(user_id)
        if not patterns:
            return {'unknown': 1.0}

        # 直近の意図に基づいて予測
        recent_turns = self.conversation_history[user_id][-5:]  # 直近5ターン
        intent_counts = defaultdict(int)

        for turn in recent_turns:
            intent_counts[turn.intent] += 1

        total = sum(intent_counts.values())
        predictions = {intent: count/total for intent, count in intent_counts.items()}

        return predictions

    def get_relevant_context(self, user_id: str, current_intent: str) -> Dict[str, Any]:
        """
        現在の意図に関連するコンテキストを取得
        """
        context_window = self.get_context_for_user(user_id)
        if not context_window:
            return {}

        relevant_info = {
            'recent_topics': context_window.current_topics[-3:],  # 直近3トピック
            'related_entities': self._get_related_entities(context_window, current_intent),
            'temporal_context': self._get_temporal_context(context_window),
            'active_features': context_window.active_features,
            'context_score': context_window.context_score
        }

        return relevant_info

    def _get_or_create_context_window(self, user_id: str, session_id: str) -> ContextWindow:
        """コンテキストウィンドウを取得または作成"""
        if session_id in self.context_windows:
            return self.context_windows[session_id]

        # 新しいコンテキストウィンドウを作成
        context_window = ContextWindow(
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now(),
            current_topics=[],
            recent_entities=defaultdict(list),
            conversation_history=deque(maxlen=self.max_context_size),
            user_preferences={},
            active_features=[],
            context_score=0.0
        )

        self.context_windows[session_id] = context_window
        return context_window

    def _generate_session_id(self, user_id: str, user_message: str) -> str:
        """セッションIDを生成"""
        # 時間ベースと内容ベースのハッシュを組み合わせ
        time_hash = hashlib.md5(str(datetime.now().hour).encode()).hexdigest()[:8]
        content_hash = hashlib.md5(user_message[:50].encode()).hexdigest()[:8]
        return f"{user_id}_{time_hash}_{content_hash}"

    def _get_current_session_id(self, user_id: str) -> str:
        """現在のセッションIDを取得"""
        # 最新の会話ターンからセッションIDを取得
        if user_id in self.conversation_history and self.conversation_history[user_id]:
            latest_turn = self.conversation_history[user_id][-1]
            return self._extract_session_id_from_turn(latest_turn)

        return self._generate_session_id(user_id, "default")

    def _extract_session_id_from_turn(self, turn: ConversationTurn) -> str:
        """会話ターンからセッションIDを抽出"""
        # 実装では実際のセッションID抽出ロジック
        return hashlib.md5(f"{turn.user_id}_{turn.timestamp.hour}".encode()).hexdigest()[:16]

    def _record_conversation_turn(self, turn: ConversationTurn):
        """会話ターンを記録"""
        if turn.user_id not in self.conversation_history:
            self.conversation_history[turn.user_id] = []

        self.conversation_history[turn.user_id].append(turn)

        # 古いターンを削除（最大サイズ制限）
        if len(self.conversation_history[turn.user_id]) > self.max_context_size:
            self.conversation_history[turn.user_id] = self.conversation_history[turn.user_id][-self.max_context_size:]

    def _update_context_window(self, context_window: ContextWindow, turn: ConversationTurn, semantic_analysis: Dict[str, Any]):
        """コンテキストウィンドウを更新"""
        # 現在のトピック更新
        if 'entities' in semantic_analysis and 'functions' in semantic_analysis['entities']:
            functions = semantic_analysis['entities']['functions']
            if functions:
                context_window.current_topics.extend(functions)
                context_window.current_topics = list(set(context_window.current_topics))[-5:]  # 直近5トピック

        # エンティティ更新
        if 'entities' in semantic_analysis:
            for entity_type, entities in semantic_analysis['entities'].items():
                if entities:
                    context_window.recent_entities[entity_type].extend(entities)
                    context_window.recent_entities[entity_type] = list(set(context_window.recent_entities[entity_type]))[-10:]

        # 会話履歴更新
        context_window.conversation_history.append({
            'message': turn.user_message,
            'intent': turn.intent,
            'timestamp': turn.timestamp
        })

        # アクティブ機能更新
        if turn.intent == 'create_function':
            if 'entities' in semantic_analysis and 'functions' in semantic_analysis['entities']:
                new_functions = semantic_analysis['entities']['functions']
                context_window.active_features.extend(new_functions)

    def _update_user_patterns(self, user_id: str, turn: ConversationTurn):
        """ユーザー行動パターンを更新"""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = UserBehaviorPattern(
                user_id=user_id,
                preferred_times=[],
                frequent_intents=defaultdict(int),
                preferred_functions=[],
                conversation_style={},
                temporal_patterns={}
            )

        patterns = self.user_patterns[user_id]

        # 意図カウント更新
        patterns.frequent_intents[turn.intent] += 1

        # 時間帯パターン更新
        hour = turn.timestamp.hour
        if hour not in patterns.preferred_times:
            patterns.preferred_times.append(hour)

        # 機能パターン更新
        if 'entities' in turn.entities and 'functions' in turn.entities:
            functions = turn.entities['functions']
            for func in functions:
                if func not in patterns.preferred_functions:
                    patterns.preferred_functions.append(func)

    def _calculate_context_score(self, context_window: ContextWindow) -> float:
        """コンテキストスコアを計算"""
        score = 0.0

        # トピック継続性
        if len(context_window.current_topics) > 1:
            score += 0.3

        # 会話の時間的連続性
        if context_window.conversation_history:
            latest_time = context_window.conversation_history[-1]['timestamp']
            if isinstance(latest_time, datetime):
                time_diff = datetime.now() - latest_time
                if time_diff < timedelta(hours=1):
                    score += 0.2

        # エンティティの一貫性
        entity_count = sum(len(entities) for entities in context_window.recent_entities.values())
        if entity_count > 0:
            score += 0.2

        # アクティブ機能の存在
        if context_window.active_features:
            score += 0.3

        return min(score, 1.0)

    def _extract_context_features(self, user_message: str, semantic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト特徴量を抽出"""
        features = {
            'message_length': len(user_message),
            'intent_complexity': len(semantic_analysis.get('secondary_intents', [])),
            'entity_richness': len(semantic_analysis.get('entities', {})),
            'temporal_references': len(semantic_analysis.get('time_references', [])),
            'ambiguity_level': 1.0 if semantic_analysis.get('is_ambiguous', False) else 0.0
        }

        return features

    def _get_related_entities(self, context_window: ContextWindow, current_intent: str) -> Dict[str, List[str]]:
        """現在の意図に関連するエンティティを取得"""
        related = {}

        # 意図に基づいて関連エンティティをフィルタリング
        for entity_type, entities in context_window.recent_entities.items():
            if entity_type == 'functions' and current_intent in ['create_function', 'modify_function']:
                related[entity_type] = entities[-3:]  # 直近3機能
            elif entity_type == 'locations' and 'location' in current_intent:
                related[entity_type] = entities[-2:]  # 直近2場所

        return related

    def _get_temporal_context(self, context_window: ContextWindow) -> Dict[str, Any]:
        """時間的コンテキストを取得"""
        temporal_info = {
            'session_duration': datetime.now() - context_window.start_time,
            'conversation_frequency': len(context_window.conversation_history),
            'preferred_time_slots': []
        }

        # 時間帯パターンを分析
        if context_window.conversation_history:
            hours = [turn['timestamp'].hour for turn in context_window.conversation_history if isinstance(turn['timestamp'], datetime)]
            if hours:
                temporal_info['preferred_time_slots'] = sorted(set(hours))

        return temporal_info

    def _create_empty_context(self, user_id: str) -> ContextWindow:
        """空のコンテキストを作成"""
        return ContextWindow(
            user_id=user_id,
            session_id="default",
            start_time=datetime.now(),
            current_topics=[],
            recent_entities=defaultdict(list),
            conversation_history=deque(maxlen=self.max_context_size),
            user_preferences={},
            active_features=[],
            context_score=0.0
        )

    def cleanup_old_contexts(self):
        """古いコンテキストをクリーンアップ"""
        current_time = datetime.now()

        # 古いコンテキストウィンドウを削除
        expired_sessions = []
        for session_id, context_window in self.context_windows.items():
            if current_time - context_window.start_time > timedelta(hours=self.context_window_hours):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.context_windows[session_id]

        # 古い会話履歴を削除
        for user_id in list(self.conversation_history.keys()):
            # 24時間以上前の会話を削除
            self.conversation_history[user_id] = [
                turn for turn in self.conversation_history[user_id]
                if current_time - turn.timestamp < timedelta(hours=24)
            ]

            # 空になった履歴は削除
            if not self.conversation_history[user_id]:
                del self.conversation_history[user_id]
