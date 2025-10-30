"""
Response Variety Manager - 応答の多様性を管理
"""
import logging
import random
import json
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import hashlib

@dataclass
class ResponseStyle:
    """応答スタイル"""
    style_id: str
    name: str
    description: str
    personality_traits: Dict[str, float]
    language_patterns: Dict[str, Any]
    interaction_preferences: Dict[str, Any]
    priority: int = 5

@dataclass
class VarietyRule:
    """多様性ルール"""
    rule_id: str
    condition_type: str  # time, user_history, context, random
    condition_params: Dict[str, Any]
    style_weights: Dict[str, float]
    cooldown_minutes: int = 60

class ResponseVarietyManager:
    """応答多様性マネージャー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 応答スタイル定義
        self.response_styles = self._initialize_response_styles()

        # 多様性ルール
        self.variety_rules = self._initialize_variety_rules()

        # ユーザーごとのスタイル使用履歴
        self.user_style_history: Dict[str, List[Dict[str, Any]]] = {}
        self.history_lock = threading.Lock()

        # スタイル選択アルゴリズム
        self.style_algorithms = {
            "weighted_random": self._weighted_random_selection,
            "context_adaptive": self._context_adaptive_selection,
            "user_history_aware": self._user_history_aware_selection,
            "time_based": self._time_based_selection
        }

        self.logger.info("Response Variety Managerを初期化しました")

    def _initialize_response_styles(self) -> Dict[str, ResponseStyle]:
        """応答スタイルを初期化"""
        styles = {
            "professional": ResponseStyle(
                style_id="professional",
                name="プロフェッショナル",
                description="丁寧で専門的なスタイル",
                personality_traits={
                    "formality": 0.9,
                    "helpfulness": 0.8,
                    "precision": 0.9,
                    "patience": 0.7
                },
                language_patterns={
                    "sentence_endings": ["です。", "ます。", "ください。"],
                    "polite_expressions": ["お手数ですが", "ご確認ください", "お役に立てれば幸いです"],
                    "technical_terms": "formal"
                },
                interaction_preferences={
                    "response_length": "detailed",
                    "question_frequency": "low",
                    "example_usage": "high"
                },
                priority=8
            ),
            "friendly": ResponseStyle(
                style_id="friendly",
                name="フレンドリー",
                description="親しみやすいカジュアルなスタイル",
                personality_traits={
                    "formality": 0.2,
                    "helpfulness": 0.9,
                    "warmth": 0.9,
                    "humor": 0.6
                },
                language_patterns={
                    "sentence_endings": ["！", "よ～", "だよ！", "かな？"],
                    "polite_expressions": ["一緒に", "教えてあげる", "どう？"],
                    "emojis": ["😊", "👍", "✨", "💡"]
                },
                interaction_preferences={
                    "response_length": "moderate",
                    "question_frequency": "high",
                    "example_usage": "moderate"
                },
                priority=9
            ),
            "creative": ResponseStyle(
                style_id="creative",
                name="クリエイティブ",
                description="創造的で革新的なスタイル",
                personality_traits={
                    "creativity": 0.9,
                    "originality": 0.8,
                    "flexibility": 0.9,
                    "inspiration": 0.7
                },
                language_patterns={
                    "sentence_endings": ["！", "かもね", "って感じ！"],
                    "creative_expressions": ["面白い視点", "新しいアプローチ", "想像してみて"],
                    "metaphors": "frequent"
                },
                interaction_preferences={
                    "response_length": "varied",
                    "question_frequency": "high",
                    "alternative_suggestions": "high"
                },
                priority=7
            ),
            "concise": ResponseStyle(
                style_id="concise",
                name="簡潔",
                description="簡潔で効率的なスタイル",
                personality_traits={
                    "efficiency": 0.9,
                    "clarity": 0.9,
                    "directness": 0.8,
                    "precision": 0.9
                },
                language_patterns={
                    "sentence_endings": ["。"],
                    "concise_expressions": ["つまり", "要点", "結論"],
                    "bullet_points": "preferred"
                },
                interaction_preferences={
                    "response_length": "short",
                    "question_frequency": "low",
                    "structure": "bullet_points"
                },
                priority=6
            ),
            "empathetic": ResponseStyle(
                style_id="empathetic",
                name="共感的",
                description="共感を示すサポート的なスタイル",
                personality_traits={
                    "empathy": 0.9,
                    "supportiveness": 0.9,
                    "understanding": 0.8,
                    "patience": 0.9
                },
                language_patterns={
                    "sentence_endings": ["ね。", "よ。"],
                    "empathetic_expressions": ["分かります", "それは大変ですね", "一緒に考えましょう"],
                    "encouraging_words": ["大丈夫", "がんばって", "少しずつ"]
                },
                interaction_preferences={
                    "response_length": "moderate",
                    "question_frequency": "high",
                    "emotional_support": "high"
                },
                priority=8
            ),
            "humorous": ResponseStyle(
                style_id="humorous",
                name="ユーモア",
                description="軽快で楽しいスタイル",
                personality_traits={
                    "humor": 0.9,
                    "lightheartedness": 0.8,
                    "creativity": 0.7,
                    "warmth": 0.6
                },
                language_patterns={
                    "sentence_endings": ["（笑）", "！", "かも？"],
                    "humorous_expressions": ["それじゃまるで", "まるで", "みたいな"],
                    "puns": "occasional"
                },
                interaction_preferences={
                    "response_length": "varied",
                    "question_frequency": "moderate",
                    "jokes": "light"
                },
                priority=5
            )
        }
        return styles

    def _initialize_variety_rules(self) -> List[VarietyRule]:
        """多様性ルールを初期化"""
        rules = [
            VarietyRule(
                rule_id="time_based_morning",
                condition_type="time",
                condition_params={"hour_range": [6, 12]},
                style_weights={
                    "professional": 0.6,
                    "friendly": 0.4,
                    "empathetic": 0.2
                }
            ),
            VarietyRule(
                rule_id="time_based_evening",
                condition_type="time",
                condition_params={"hour_range": [18, 24]},
                style_weights={
                    "friendly": 0.5,
                    "empathetic": 0.3,
                    "humorous": 0.2
                }
            ),
            VarietyRule(
                rule_id="repeated_user",
                condition_type="user_history",
                condition_params={"min_interactions": 5},
                style_weights={
                    "friendly": 0.4,
                    "creative": 0.3,
                    "humorous": 0.3
                }
            ),
            VarietyRule(
                rule_id="technical_context",
                condition_type="context",
                condition_params={"has_technical_terms": True},
                style_weights={
                    "professional": 0.6,
                    "concise": 0.4
                }
            ),
            VarietyRule(
                rule_id="casual_context",
                condition_type="context",
                condition_params={"is_casual": True},
                style_weights={
                    "friendly": 0.5,
                    "humorous": 0.3,
                    "empathetic": 0.2
                }
            ),
            VarietyRule(
                rule_id="random_variety",
                condition_type="random",
                condition_params={"probability": 0.3},
                style_weights={
                    "creative": 0.4,
                    "humorous": 0.3,
                    "empathetic": 0.3
                },
                cooldown_minutes=30
            )
        ]
        return rules

    async def select_response_style(
        self,
        user_id: str,
        context: Dict[str, Any],
        algorithm: str = "context_adaptive"
    ) -> ResponseStyle:
        """
        応答スタイルを選択

        Args:
            user_id: ユーザーID
            context: コンテキスト情報
            algorithm: 使用するアルゴリズム

        Returns:
            選択された応答スタイル
        """
        try:
            # アルゴリズム選択
            if algorithm not in self.style_algorithms:
                algorithm = "context_adaptive"

            # 選択アルゴリズム実行
            selected_style = await self.style_algorithms[algorithm](user_id, context)

            # 使用履歴記録
            self._record_style_usage(user_id, selected_style.style_id)

            return selected_style

        except Exception as e:
            self.logger.error(f"応答スタイル選択エラー: {str(e)}")
            # フォールバックとしてフレンドリースタイルを使用
            return self.response_styles["friendly"]

    async def _context_adaptive_selection(self, user_id: str, context: Dict[str, Any]) -> ResponseStyle:
        """コンテキスト適応型選択"""
        # コンテキスト分析
        context_score = self._analyze_context_for_style(context)

        # ルール適用
        applicable_rules = self._get_applicable_rules(context, user_id)

        # スタイル重み計算
        style_weights = self._calculate_style_weights(context_score, applicable_rules)

        # クールダウンチェック
        available_styles = self._filter_cooldown_styles(user_id, style_weights)

        # 重み付き選択
        return self._select_by_weights(available_styles)

    async def _weighted_random_selection(self, user_id: str, context: Dict[str, Any]) -> ResponseStyle:
        """重み付きランダム選択"""
        style_weights = {
            "friendly": 0.3,
            "professional": 0.2,
            "creative": 0.2,
            "concise": 0.15,
            "empathetic": 0.1,
            "humorous": 0.05
        }

        available_styles = self._filter_cooldown_styles(user_id, style_weights)
        return self._select_by_weights(available_styles)

    async def _user_history_aware_selection(self, user_id: str, context: Dict[str, Any]) -> ResponseStyle:
        """ユーザー履歴考慮選択"""
        # ユーザー履歴取得
        user_history = self._get_user_style_history(user_id)

        # 履歴に基づく重み調整
        base_weights = {
            "friendly": 0.25,
            "professional": 0.2,
            "creative": 0.2,
            "concise": 0.15,
            "empathetic": 0.15,
            "humorous": 0.05
        }

        # 最近使用したスタイルの重みを下げる
        if user_history:
            recent_styles = [h["style_id"] for h in user_history[-3:]]
            for style_id in recent_styles:
                if style_id in base_weights:
                    base_weights[style_id] *= 0.5

        available_styles = self._filter_cooldown_styles(user_id, base_weights)
        return self._select_by_weights(available_styles)

    async def _time_based_selection(self, user_id: str, context: Dict[str, Any]) -> ResponseStyle:
        """時間ベース選択"""
        now = datetime.now()
        hour = now.hour

        if 6 <= hour < 12:
            # 朝はプロフェッショナルとフレンドリー
            style_weights = {"professional": 0.6, "friendly": 0.4}
        elif 12 <= hour < 18:
            # 昼はバランスよく
            style_weights = {
                "professional": 0.3,
                "friendly": 0.3,
                "concise": 0.2,
                "creative": 0.2
            }
        else:
            # 夜はリラックスしたスタイル
            style_weights = {
                "friendly": 0.4,
                "empathetic": 0.3,
                "humorous": 0.3
            }

        available_styles = self._filter_cooldown_styles(user_id, style_weights)
        return self._select_by_weights(available_styles)

    def _analyze_context_for_style(self, context: Dict[str, Any]) -> Dict[str, float]:
        """コンテキストを分析してスタイルスコアを計算"""
        scores = {style_id: 0.0 for style_id in self.response_styles.keys()}

        # 技術的な内容の場合
        if context.get("is_technical", False):
            scores["professional"] += 0.3
            scores["concise"] += 0.2

        # カジュアルな内容の場合
        if context.get("is_casual", False):
            scores["friendly"] += 0.3
            scores["humorous"] += 0.2

        # 問題解決の場合
        if context.get("is_problem_solving", False):
            scores["empathetic"] += 0.3
            scores["professional"] += 0.2

        # 創造的な内容の場合
        if context.get("is_creative", False):
            scores["creative"] += 0.3
            scores["friendly"] += 0.2

        return scores

    def _get_applicable_rules(self, context: Dict[str, Any], user_id: str) -> List[VarietyRule]:
        """適用可能なルールを取得"""
        applicable_rules = []

        for rule in self.variety_rules:
            if self._check_rule_condition(rule, context, user_id):
                applicable_rules.append(rule)

        return applicable_rules

    def _check_rule_condition(self, rule: VarietyRule, context: Dict[str, Any], user_id: str) -> bool:
        """ルールの条件をチェック"""
        if rule.condition_type == "time":
            hour = datetime.now().hour
            hour_range = rule.condition_params.get("hour_range", [0, 24])
            return hour_range[0] <= hour < hour_range[1]

        elif rule.condition_type == "user_history":
            min_interactions = rule.condition_params.get("min_interactions", 0)
            with self.history_lock:
                user_history = self.user_style_history.get(user_id, [])
                return len(user_history) >= min_interactions

        elif rule.condition_type == "context":
            return all(
                context.get(key) == value
                for key, value in rule.condition_params.items()
            )

        elif rule.condition_type == "random":
            probability = rule.condition_params.get("probability", 0.0)
            return random.random() < probability

        return False

    def _calculate_style_weights(self, context_scores: Dict[str, float], rules: List[VarietyRule]) -> Dict[str, float]:
        """スタイル重みを計算"""
        weights = {style_id: 0.0 for style_id in self.response_styles.keys()}

        # コンテキストスコアをベースに
        for style_id, score in context_scores.items():
            weights[style_id] += score

        # ルールによる重み調整
        for rule in rules:
            for style_id, rule_weight in rule.style_weights.items():
                if style_id in weights:
                    weights[style_id] += rule_weight

        # 負の重みを0に
        weights = {k: max(0, v) for k, v in weights.items()}

        return weights

    def _filter_cooldown_styles(self, user_id: str, weights: Dict[str, float]) -> Dict[str, float]:
        """クールダウン中のスタイルをフィルタリング"""
        available_weights = weights.copy()

        with self.history_lock:
            user_history = self.user_style_history.get(user_id, [])

            for rule in self.variety_rules:
                if rule.cooldown_minutes > 0 and rule.condition_type == "random":
                    # クールダウン中のスタイルを確認
                    cooldown_time = datetime.now() - timedelta(minutes=rule.cooldown_minutes)

                    recent_usage = [
                        h for h in user_history
                        if h.get("timestamp", datetime.min) > cooldown_time
                    ]

                    if recent_usage:
                        # クールダウン中のスタイルの重みを下げる
                        for style_id in rule.style_weights.keys():
                            if style_id in available_weights:
                                available_weights[style_id] *= 0.5

        return available_weights

    def _select_by_weights(self, weights: Dict[str, float]) -> ResponseStyle:
        """重み付き選択"""
        if not weights:
            return self.response_styles["friendly"]

        # 総重みを計算
        total_weight = sum(weights.values())
        if total_weight == 0:
            return self.response_styles["friendly"]

        # 重み付きランダム選択
        r = random.random() * total_weight
        current_weight = 0

        for style_id, weight in weights.items():
            current_weight += weight
            if r <= current_weight:
                return self.response_styles[style_id]

        # フォールバック
        return self.response_styles["friendly"]

    def _record_style_usage(self, user_id: str, style_id: str):
        """スタイル使用を記録"""
        with self.history_lock:
            if user_id not in self.user_style_history:
                self.user_style_history[user_id] = []

            usage_record = {
                "style_id": style_id,
                "timestamp": datetime.now(),
                "session_id": hashlib.md5(f"{user_id}:{datetime.now().date()}".encode()).hexdigest()[:8]
            }

            self.user_style_history[user_id].append(usage_record)

            # 履歴を制限（最新50件まで）
            if len(self.user_style_history[user_id]) > 50:
                self.user_style_history[user_id] = self.user_style_history[user_id][-50:]

    def _get_user_style_history(self, user_id: str) -> List[Dict[str, Any]]:
        """ユーザーごとのスタイル履歴を取得"""
        with self.history_lock:
            return self.user_style_history.get(user_id, [])

    async def generate_style_adapted_response(
        self,
        base_response: str,
        style: ResponseStyle,
        context: Dict[str, Any]
    ) -> str:
        """
        スタイルに応じた応答を生成

        Args:
            base_response: ベース応答
            style: 適用するスタイル
            context: コンテキスト

        Returns:
            スタイル適応後の応答
        """
        try:
            # スタイルによる応答調整
            adapted_response = base_response

            # 言語パターン適用
            adapted_response = self._apply_language_patterns(adapted_response, style)

            # 長さ調整
            adapted_response = self._adjust_response_length(adapted_response, style)

            # 絵文字追加（フレンドリー、ユーモアスタイルの場合）
            if style.style_id in ["friendly", "humorous", "empathetic"]:
                adapted_response = self._add_emojis_if_appropriate(adapted_response, style, context)

            return adapted_response

        except Exception as e:
            self.logger.error(f"スタイル適応エラー: {str(e)}")
            return base_response

    def _apply_language_patterns(self, response: str, style: ResponseStyle) -> str:
        """言語パターンを適用"""
        # 簡易的な実装（実際にはより洗練されたNLP処理が必要）
        return response

    def _adjust_response_length(self, response: str, style: ResponseStyle) -> str:
        """応答長さを調整"""
        # 簡易的な実装
        return response

    def _add_emojis_if_appropriate(self, response: str, style: ResponseStyle, context: Dict[str, Any]) -> str:
        """適切な場合に絵文字を追加"""
        # 簡易的な実装
        return response

    def get_style_statistics(self, user_id: str) -> Dict[str, Any]:
        """スタイル使用統計を取得"""
        with self.history_lock:
            user_history = self.user_style_history.get(user_id, [])

            if not user_history:
                return {"total_interactions": 0, "style_distribution": {}}

            style_counts = {}
            for record in user_history:
                style_id = record.get("style_id", "unknown")
                style_counts[style_id] = style_counts.get(style_id, 0) + 1

            total = len(user_history)
            style_distribution = {
                style_id: count / total
                for style_id, count in style_counts.items()
            }

            return {
                "total_interactions": total,
                "style_distribution": style_distribution,
                "most_used_style": max(style_counts, key=style_counts.get),
                "unique_styles_used": len(style_counts)
            }

# グローバルインスタンス
response_variety_manager = ResponseVarietyManager()
