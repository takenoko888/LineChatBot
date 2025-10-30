"""
Conversation memory service implementation
対話履歴管理とコンテキスト記憶サービス
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pytz
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
import threading
from .gemini_service import GeminiService

@dataclass
class ConversationTurn:
    """会話ターン"""
    user_id: str
    turn_id: str
    timestamp: datetime
    user_message: str
    bot_response: str
    intent: str
    confidence: float
    context: Dict[str, Any]
    sentiment: str = "neutral"

@dataclass
class UserProfile:
    """ユーザープロファイル"""
    user_id: str
    preferences: Dict[str, Any]
    communication_style: str
    frequent_topics: List[str]
    preferred_times: List[str]
    language_preference: str = "ja"
    last_updated: datetime = None

class ConversationMemoryService:
    """対話履歴管理サービス"""

    def __init__(self, gemini_service: Optional[GeminiService] = None, storage_path: str = None):
        """
        初期化
        
        Args:
            gemini_service (Optional[GeminiService]): Gemini AIサービス
            storage_path (str): データ保存パス
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_service = gemini_service or GeminiService()
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # ストレージ設定
        base_storage = storage_path or "/workspace/data"
        os.makedirs(base_storage, exist_ok=True)
        self.conversation_storage = os.path.join(base_storage, "conversations.json")
        self.profiles_storage = os.path.join(base_storage, "user_profiles.json")
        
        # データ構造
        self.conversations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))  # ユーザーごとに最大50ターン
        self.user_profiles: Dict[str, UserProfile] = {}
        self.memory_cache: Dict[str, Any] = {}  # 一時キャッシュ（ユーザー毎の任意データ格納）
        
        # ロック
        self.lock = threading.Lock()
        
        # データ読み込み
        self._load_data()
        
        self.logger.info("対話履歴管理サービスを初期化しました")

    # -------------------------
    # ユーザー一時メモ ユーティリティ
    # -------------------------
    def set_user_temp(self, user_id: str, key: str, value: Any) -> None:
        try:
            if user_id not in self.memory_cache:
                self.memory_cache[user_id] = {}
            self.memory_cache[user_id][key] = value
        except Exception as e:
            self.logger.error(f"一時メモ設定エラー: {str(e)}")

    def get_user_temp(self, user_id: str, key: str, default: Any = None) -> Any:
        try:
            return self.memory_cache.get(user_id, {}).get(key, default)
        except Exception:
            return default

    def clear_user_temp(self, user_id: str, key: str) -> None:
        try:
            if user_id in self.memory_cache and key in self.memory_cache[user_id]:
                del self.memory_cache[user_id][key]
        except Exception as e:
            self.logger.error(f"一時メモ削除エラー: {str(e)}")

    def _load_data(self) -> None:
        """保存データを読み込み"""
        try:
            # 会話履歴の読み込み
            if os.path.exists(self.conversation_storage):
                with open(self.conversation_storage, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, turns in data.items():
                        conversation_deque = deque(maxlen=50)
                        for turn_data in turns:
                            turn = ConversationTurn(
                                user_id=turn_data['user_id'],
                                turn_id=turn_data['turn_id'],
                                timestamp=datetime.fromisoformat(turn_data['timestamp']),
                                user_message=turn_data['user_message'],
                                bot_response=turn_data['bot_response'],
                                intent=turn_data['intent'],
                                confidence=turn_data['confidence'],
                                context=turn_data['context'],
                                sentiment=turn_data.get('sentiment', 'neutral')
                            )
                            conversation_deque.append(turn)
                        self.conversations[user_id] = conversation_deque

            # ユーザープロファイルの読み込み
            if os.path.exists(self.profiles_storage):
                with open(self.profiles_storage, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, profile_data in data.items():
                        profile = UserProfile(
                            user_id=profile_data['user_id'],
                            preferences=profile_data['preferences'],
                            communication_style=profile_data['communication_style'],
                            frequent_topics=profile_data['frequent_topics'],
                            preferred_times=profile_data['preferred_times'],
                            language_preference=profile_data.get('language_preference', 'ja'),
                            last_updated=datetime.fromisoformat(profile_data['last_updated']) if profile_data.get('last_updated') else None
                        )
                        self.user_profiles[user_id] = profile

        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {str(e)}")

    def _save_data(self) -> None:
        """データを保存"""
        try:
            with self.lock:
                # 会話履歴の保存
                conversations_data = {}
                for user_id, turns in self.conversations.items():
                    conversations_data[user_id] = []
                    for turn in turns:
                        turn_dict = asdict(turn)
                        turn_dict['timestamp'] = turn.timestamp.isoformat()
                        conversations_data[user_id].append(turn_dict)

                with open(self.conversation_storage, 'w', encoding='utf-8') as f:
                    json.dump(conversations_data, f, ensure_ascii=False, indent=2)

                # ユーザープロファイルの保存
                profiles_data = {}
                for user_id, profile in self.user_profiles.items():
                    profile_dict = asdict(profile)
                    if profile.last_updated:
                        profile_dict['last_updated'] = profile.last_updated.isoformat()
                    profiles_data[user_id] = profile_dict

                with open(self.profiles_storage, 'w', encoding='utf-8') as f:
                    json.dump(profiles_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"データ保存エラー: {str(e)}")

    def add_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        intent: str,
        confidence: float,
        context: Dict[str, Any] = None
    ) -> str:
        """
        会話ターンを追加
        
        Args:
            user_id (str): ユーザーID
            user_message (str): ユーザーのメッセージ
            bot_response (str): ボットの応答
            intent (str): 判定された意図
            confidence (float): 信頼度
            context (Dict[str, Any]): コンテキスト情報
            
        Returns:
            str: 会話ターンID
        """
        try:
            # 感情分析（簡易版）
            sentiment = self._analyze_sentiment(user_message)
            
            # ターンIDの生成
            turn_id = f"{user_id}_{datetime.now(self.jst).strftime('%Y%m%d_%H%M%S')}"
            
            # 会話ターンの作成
            turn = ConversationTurn(
                user_id=user_id,
                turn_id=turn_id,
                timestamp=datetime.now(self.jst),
                user_message=user_message,
                bot_response=bot_response,
                intent=intent,
                confidence=confidence,
                context=context or {},
                sentiment=sentiment
            )
            
            with self.lock:
                self.conversations[user_id].append(turn)
            
            # ユーザープロファイルの更新
            self._update_user_profile(user_id, user_message, intent)
            
            # 定期保存
            self._save_data()
            
            return turn_id
            
        except Exception as e:
            self.logger.error(f"会話ターン追加エラー: {str(e)}")
            return ""

    def get_conversation_context(self, user_id: str, limit: int = 5) -> str:
        """
        会話コンテキストを取得（AI判定用）
        
        Args:
            user_id (str): ユーザーID
            limit (int): 取得する会話ターン数
            
        Returns:
            str: 会話コンテキストの文字列
        """
        try:
            with self.lock:
                recent_turns = list(self.conversations[user_id])[-limit:]
            
            if not recent_turns:
                return ""
            
            context_parts = ["前回までの会話:"]
            for turn in recent_turns:
                time_str = turn.timestamp.strftime('%H:%M')
                context_parts.append(f"[{time_str}] ユーザー: {turn.user_message}")
                context_parts.append(f"[{time_str}] ボット: {turn.bot_response}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"会話コンテキスト取得エラー: {str(e)}")
            return ""

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        ユーザープロファイルを取得
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Optional[UserProfile]: ユーザープロファイル
        """
        return self.user_profiles.get(user_id)

    def analyze_conversation_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        会話パターンを分析
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            with self.lock:
                turns = list(self.conversations[user_id])
            
            if not turns:
                return {"error": "会話履歴がありません"}
            
            # 基本統計
            total_turns = len(turns)
            recent_turns = turns[-10:] if len(turns) > 10 else turns
            
            # 意図分析
            intent_counts = defaultdict(int)
            confidence_scores = []
            sentiment_counts = defaultdict(int)
            
            for turn in recent_turns:
                intent_counts[turn.intent] += 1
                confidence_scores.append(turn.confidence)
                sentiment_counts[turn.sentiment] += 1
            
            # 時間パターン分析
            hour_distribution = defaultdict(int)
            for turn in recent_turns:
                hour_distribution[turn.timestamp.hour] += 1
            
            # 分析結果
            analysis = {
                "total_conversations": total_turns,
                "recent_analysis": {
                    "most_used_features": dict(intent_counts),
                    "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                    "sentiment_distribution": dict(sentiment_counts),
                    "active_hours": dict(hour_distribution)
                },
                "communication_style": self._analyze_communication_style(recent_turns),
                "preferences": self._extract_preferences(recent_turns)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"会話パターン分析エラー: {str(e)}")
            return {"error": str(e)}

    def get_contextual_suggestions(self, user_id: str, current_message: str) -> List[str]:
        """
        コンテキストに基づく提案を生成
        
        Args:
            user_id (str): ユーザーID
            current_message (str): 現在のメッセージ
            
        Returns:
            List[str]: 提案リスト
        """
        try:
            # 会話履歴の取得
            context = self.get_conversation_context(user_id)
            profile = self.get_user_profile(user_id)
            
            # AIによる提案生成
            suggestions_prompt = f"""
ユーザーの会話履歴と現在のメッセージから、適切な機能提案を生成してください。

{context}

現在のメッセージ: "{current_message}"

ユーザープロファイル:
- よく使う機能: {profile.frequent_topics if profile else "不明"}
- コミュニケーションスタイル: {profile.communication_style if profile else "不明"}

以下の観点で3つの提案を生成してください：
1. 過去の会話から関連する機能
2. 現在のメッセージから推測される次のアクション
3. 時間や状況に応じた有用な機能

簡潔で実用的な提案を日本語で生成してください。
"""
            
            response = self.gemini_service.model.generate_content(suggestions_prompt)
            if response and response.text:
                # 提案を解析してリスト化
                suggestions = self._parse_suggestions(response.text)
                return suggestions
            
            return []
            
        except Exception as e:
            self.logger.error(f"コンテキスト提案生成エラー: {str(e)}")
            return []

    def _analyze_sentiment(self, message: str) -> str:
        """簡易感情分析"""
        positive_words = ["ありがとう", "嬉しい", "よい", "楽しい", "素晴らしい"]
        negative_words = ["困った", "大変", "忙しい", "疲れた", "難しい"]
        
        positive_count = sum(1 for word in positive_words if word in message)
        negative_count = sum(1 for word in negative_words if word in message)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _update_user_profile(self, user_id: str, message: str, intent: str) -> None:
        """ユーザープロファイルを更新"""
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserProfile(
                    user_id=user_id,
                    preferences={},
                    communication_style="standard",
                    frequent_topics=[],
                    preferred_times=[]
                )
            
            profile = self.user_profiles[user_id]
            
            # よく使う機能の更新
            if intent not in profile.frequent_topics:
                profile.frequent_topics.append(intent)
            
            # 最大5つまで保持
            if len(profile.frequent_topics) > 5:
                profile.frequent_topics = profile.frequent_topics[-5:]
            
            # 利用時間の記録
            current_hour = datetime.now(self.jst).hour
            hour_str = f"{current_hour:02d}:00"
            if hour_str not in profile.preferred_times:
                profile.preferred_times.append(hour_str)
                if len(profile.preferred_times) > 10:
                    profile.preferred_times = profile.preferred_times[-10:]
            
            profile.last_updated = datetime.now(self.jst)
            
        except Exception as e:
            self.logger.error(f"ユーザープロファイル更新エラー: {str(e)}")

    def _analyze_communication_style(self, turns: List[ConversationTurn]) -> str:
        """コミュニケーションスタイルを分析"""
        if not turns:
            return "standard"
        
        # メッセージの長さと丁寧さを分析
        avg_length = sum(len(turn.user_message) for turn in turns) / len(turns)
        polite_count = sum(1 for turn in turns if any(word in turn.user_message for word in ["です", "ます", "ください"]))
        
        if avg_length > 30 and polite_count / len(turns) > 0.7:
            return "formal"
        elif avg_length < 15:
            return "casual"
        else:
            return "standard"

    def _extract_preferences(self, turns: List[ConversationTurn]) -> Dict[str, Any]:
        """設定や好みを抽出"""
        preferences = {}
        
        # 通知時間の好み
        notification_turns = [turn for turn in turns if turn.intent == "notification"]
        if notification_turns:
            times = []
            for turn in notification_turns:
                # 簡易的な時間抽出
                if "朝" in turn.user_message:
                    times.append("morning")
                elif "夜" in turn.user_message:
                    times.append("evening")
            if times:
                preferences["preferred_notification_time"] = max(set(times), key=times.count)
        
        return preferences

    def _parse_suggestions(self, ai_response: str) -> List[str]:
        """AI応答から提案を解析"""
        try:
            lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
            suggestions = []
            
            for line in lines:
                if line.startswith(('1.', '2.', '3.', '-', '•')):
                    suggestion = line.split('.', 1)[-1].strip()
                    if suggestion and len(suggestion) > 5:  # 最小限の長さチェック
                        suggestions.append(suggestion)
            
            return suggestions[:3]  # 最大3つまで
            
        except Exception as e:
            self.logger.error(f"提案解析エラー: {str(e)}")
            return []

    def clear_old_conversations(self, days: int = 30) -> int:
        """古い会話を削除"""
        try:
            cutoff_date = datetime.now(self.jst) - timedelta(days=days)
            cleaned_count = 0
            
            with self.lock:
                for user_id in list(self.conversations.keys()):
                    original_count = len(self.conversations[user_id])
                    # 日付でフィルタリング
                    filtered_turns = deque(
                        [turn for turn in self.conversations[user_id] if turn.timestamp > cutoff_date],
                        maxlen=50
                    )
                    self.conversations[user_id] = filtered_turns
                    cleaned_count += original_count - len(filtered_turns)
            
            self._save_data()
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"古い会話削除エラー: {str(e)}")
            return 0 