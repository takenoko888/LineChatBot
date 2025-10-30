"""
Context-Aware Intent Router - AIベースのインテントルーティング
"""
import logging
import os
import re
import asyncio
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
from collections import Counter, defaultdict

from .flexible_ai_service import flexible_ai_service
from .service_integration_manager import service_integration_manager
from .adaptive_prompt_manager import adaptive_prompt_manager

@dataclass
class IntentAnalysis:
    """インテント分析結果"""
    intent_type: str
    confidence: float
    primary_service: str
    secondary_services: List[str]
    parameters: Dict[str, Any]
    context_info: Dict[str, Any]
    routing_recommendation: str
    requires_ai_assistance: bool = False

@dataclass
class RoutingDecision:
    """ルーティング決定"""
    decision_id: str
    user_id: str
    original_query: str
    analysis: IntentAnalysis
    selected_service: str
    selected_method: str
    execution_parameters: Dict[str, Any]
    ai_enhanced: bool
    confidence_threshold: float
    reasoning: str

class ContextAwareIntentRouter:
    """コンテキスト対応インテントルーター"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # インテントパターン定義
        self.intent_patterns = self._initialize_intent_patterns()

        # ルーティング履歴
        self.routing_history: Dict[str, List[RoutingDecision]] = defaultdict(list)
        self.history_lock = threading.Lock()

        # ルーティングルール
        self.routing_rules = self._initialize_routing_rules()

        # AI支援インテント検出
        self.ai_intent_patterns = {
            "creative": [
                "新しい", "創造", "アイデア", "発想", "革新的", "独自"
            ],
            "complex": [
                "複雑", "難しい", "高度", "専門的", "詳細", "分析"
            ],
            "personalized": [
                "私に", "私の", "自分用", "カスタム", "特別", "おすすめ"
            ],
            "multi_step": [
                "次に", "その後", "続けて", "まず", "そして", "最後に"
            ]
        }

        # モックモード設定
        self.mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true'

        self.logger.info("Context-Aware Intent Routerを初期化しました")
        if self.mock_mode:
            self.logger.info("🧪 モックモードで動作します")

    def _initialize_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """インテントパターンを初期化"""
        return {
            "create_notification": {
                "patterns": [
                    r"(.+?)(?:を|に|で)(?:通知|リマインド|教えて|起こして|思い出して)",
                    r"(.+?)(?:時間|分)(?:後|に)(?:通知|連絡|教えて)",
                    r"(?:明日|今日|今週|来週)(.+?)(?:に)(.+?)(?:して)",
                    r"(.+?)を(?:毎日|毎週|毎月)(.+?)(?:に)(.+?)",
                    r"(?:定期的に|自動で)(.+?)(?:通知|実行)"
                ],
                "parameters": ["content", "schedule", "message"],
                "required_context": ["time_context"]
            },
            "list_notifications": {
                "patterns": [
                    r"(?:通知|リマインダー)(?:一覧|リスト|確認|見て|見せて)",
                    r"(?:今日|明日|今週)(?:の)(?:予定|通知|タスク)",
                    r"(?:登録|設定)(?:した|されている)(?:通知|予定)"
                ],
                "parameters": [],
                "required_context": []
            },
            "delete_notification": {
                "patterns": [
                    r"(?:通知|リマインダー)(?:削除|消去|キャンセル|止めて|やめて)",
                    r"(.+?)(?:削除|キャンセル)(?:して|お願い)"
                ],
                "parameters": ["notification_id"],
                "required_context": []
            },
            "get_weather": {
                "patterns": [
                    r"(.+?)(?:の)(?:天気|気温|予報)",
                    r"(?:天気|気温|予報)(?:教えて|知りたい)",
                    r"(?:今日|明日|明後日)(?:の)(?:天気|気温)",
                    r"(?:雨|雪|晴れ|曇り)(?:降る|になる)"
                ],
                "parameters": ["location"],
                "required_context": []
            },
            "search_web": {
                "patterns": [
                    r"(.+?)(?:検索|調べて|教えて|について)",
                    r"(.+?)(?:の)(?:情報|詳細|説明)",
                    r"(?:最新|新しい)(.+?)(?:情報|ニュース)",
                    r"(.+?)(?:どう|どんな|何)"
                ],
                "parameters": ["query"],
                "required_context": []
            },
            "create_auto_task": {
                "patterns": [
                    r"(.+?)(?:を)(?:自動で|定期的に|毎日|毎週)(.+?)(?:して|実行)",
                    r"(.+?)(?:スケジュール|予定)(?:設定|登録)",
                    r"(?:決まった|特定の)(?:時間|タイミング)(?:に)(.+?)(?:して)"
                ],
                "parameters": ["task_type", "schedule"],
                "required_context": ["time_context"]
            },
            "general_assistance": {
                "patterns": [
                    r"(?:助けて|手伝って|どうしたら|方法)",
                    r"(?:分からない|教えて|アドバイス)",
                    r"(?:おすすめ|提案|アイデア)"
                ],
                "parameters": ["query"],
                "required_context": []
            }
        }

    def _initialize_routing_rules(self) -> List[Dict[str, Any]]:
        """ルーティングルールを初期化"""
        return [
            {
                "name": "time_specific_queries",
                "condition": lambda context: context.get("time_specific", False),
                "priority_services": ["notification", "auto_task"],
                "reasoning": "時間指定のクエリは通知・自動タスクサービスを優先"
            },
            {
                "name": "location_specific_queries",
                "condition": lambda context: context.get("location_mentioned", False),
                "priority_services": ["weather", "search"],
                "reasoning": "場所指定のクエリは天気・検索サービスを優先"
            },
            {
                "name": "recurring_patterns",
                "condition": lambda context: context.get("recurring", False),
                "priority_services": ["auto_task", "notification"],
                "reasoning": "繰り返しのクエリは自動タスク・通知サービスを優先"
            },
            {
                "name": "information_queries",
                "condition": lambda context: context.get("information_seeking", False),
                "priority_services": ["search", "weather"],
                "reasoning": "情報収集のクエリは検索・天気サービスを優先"
            },
            {
                "name": "complex_multi_step",
                "condition": lambda context: context.get("multi_step", False),
                "priority_services": ["auto_task"],
                "ai_assisted": True,
                "reasoning": "複数ステップの複雑なクエリはAI支援を推奨"
            }
        ]

    def analyze_and_route_sync(
        self,
        query: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        同期版のクエリ分析・ルーティング

        Args:
            query: ユーザークエリ
            user_id: ユーザーID
            context: 追加コンテキスト

        Returns:
            ルーティング決定
        """
        try:
            # インテント分析（同期版）
            analysis = self._analyze_intent_sync(query, context or {})

            # ルーティング決定
            routing_decision = self._make_routing_decision_sync(
                query, user_id, analysis, context or {}
            )

            # 履歴保存
            self._save_routing_history(user_id, routing_decision)

            return routing_decision

        except Exception as e:
            self.logger.error(f"インテント分析・ルーティングエラー: {str(e)}")
            # フォールバック決定
            return self._create_fallback_decision(query, user_id, str(e))

    async def _analyze_intent(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> IntentAnalysis:
        """インテントを分析"""
        # 基本的なコンテキスト分析
        context_info = self._extract_context_info(query, context)

        # パターンによるインテントマッチング
        intent_match = self._match_intent_patterns(query)

        # AIによるインテント分析
        ai_analysis = await self._perform_ai_intent_analysis(query, context_info)

        # 信頼度計算
        confidence = self._calculate_intent_confidence(intent_match, ai_analysis, context_info)

        # サービス候補の決定
        primary_service = self._determine_primary_service(intent_match, context_info)
        secondary_services = self._determine_secondary_services(intent_match, context_info)

        # パラメータ抽出
        parameters = self._extract_parameters(query, intent_match)

        # AI支援の必要性判定
        requires_ai = self._determine_ai_assistance_need(query, context_info, ai_analysis)

        # ルーティング推奨
        routing_rec = self._generate_routing_recommendation(
            intent_match, context_info, requires_ai
        )

        return IntentAnalysis(
            intent_type=intent_match.get("intent_type", "general"),
            confidence=confidence,
            primary_service=primary_service,
            secondary_services=secondary_services,
            parameters=parameters,
            context_info=context_info,
            routing_recommendation=routing_rec,
            requires_ai_assistance=requires_ai
        )

    async def _perform_ai_intent_analysis(self, query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """AIによるインテント分析（モック/本番両対応）"""
        try:
            # モックモードは軽量ロジック
            if self.mock_mode:
                return self._mock_ai_intent_analysis(query, context_info)

            # 本番でも安全のため軽量ロジックを既定とし、必要に応じてAI呼び出しへ拡張
            # TODO: flexible_ai_service を用いた高度分析に切替可能
            return self._mock_ai_intent_analysis(query, context_info)

        except Exception as e:
            self.logger.error(f"AIインテント分析エラー: {str(e)}")
            return {
                "detected_intent": "general_assistance",
                "confidence": 0.5,
                "required_services": [],
                "intent_category": "general",
                "ai_assistance_needed": False
            }

    def _extract_context_info(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト情報を抽出"""
        context_info = {
            "time_specific": self._detect_time_specific(query),
            "location_mentioned": self._detect_location(query),
            "recurring": self._detect_recurring_pattern(query),
            "information_seeking": self._detect_information_seeking(query),
            "multi_step": self._detect_multi_step(query),
            "urgency": self._detect_urgency(query),
            "personal": self._detect_personal_context(query),
            "technical": self._detect_technical_content(query)
        }

        # 追加コンテキストの統合
        context_info.update(context)

        return context_info

    def _detect_time_specific(self, query: str) -> bool:
        """時間指定を検出"""
        time_patterns = [
            r"\d{1,2}[:時]\d{0,2}",
            r"\d{1,2}[時分]",
            r"(?:今|すぐ|直後|後で)",
            r"(?:今日|明日|明後日|今週|来週|今月|来月)",
            r"(?:毎朝|毎晩|毎日|毎週|毎月)"
        ]

        return any(re.search(pattern, query) for pattern in time_patterns)

    def _detect_location(self, query: str) -> bool:
        """場所指定を検出"""
        location_keywords = [
            "の", "で", "から", "まで", "東京", "大阪", "名古屋", "福岡",
            "北海道", "東北", "関東", "中部", "関西", "中国", "四国", "九州"
        ]

        return any(keyword in query for keyword in location_keywords)

    def _detect_recurring_pattern(self, query: str) -> bool:
        """繰り返しパターンを検出"""
        recurring_keywords = [
            "毎日", "毎週", "毎月", "定期的に", "毎回", "いつも",
            "習慣", "ルーチン", "繰り返し"
        ]

        return any(keyword in query for keyword in recurring_keywords)

    def _detect_information_seeking(self, query: str) -> bool:
        """情報収集を検出"""
        info_keywords = [
            "教えて", "知りたい", "情報", "詳細", "説明", "について",
            "どう", "何", "いつ", "どこ", "誰", "なぜ", "どのように"
        ]

        return any(keyword in query for keyword in info_keywords)

    def _detect_multi_step(self, query: str) -> bool:
        """複数ステップを検出"""
        multi_step_keywords = [
            "次に", "その後", "続けて", "まず", "そして", "最後に",
            "ステップ", "段階", "プロセス", "順番"
        ]

        return any(keyword in query for keyword in multi_step_keywords)

    def _detect_urgency(self, query: str) -> bool:
        """緊急性を検出"""
        urgent_keywords = [
            "今すぐ", "すぐに", "至急", "急ぎ", "早く", "今",
            "今日中", "今日まで", "締め切り"
        ]

        return any(keyword in query for keyword in urgent_keywords)

    def _detect_personal_context(self, query: str) -> bool:
        """個人的文脈を検出"""
        personal_keywords = [
            "私", "僕", "俺", "自分", "私の", "自分の",
            "好み", "趣味", "興味", "個人的"
        ]

        return any(keyword in query for keyword in personal_keywords)

    def _detect_technical_content(self, query: str) -> bool:
        """技術的内容を検出"""
        technical_keywords = [
            "プログラミング", "コード", "開発", "API", "データベース",
            "アルゴリズム", "システム", "技術", "専門", "高度"
        ]

        return any(keyword in query for keyword in technical_keywords)

    def _match_intent_patterns(self, query: str) -> Dict[str, Any]:
        """インテントパターンにマッチング"""
        best_match = {
            "intent_type": "general",
            "confidence": 0.0,
            "matched_pattern": None,
            "extracted_params": {}
        }

        for intent_type, config in self.intent_patterns.items():
            for pattern in config["patterns"]:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    # 信頼度計算（パターン一致度 + キーワード数）
                    confidence = min(0.8 + len(match.groups()) * 0.1, 1.0)

                    if confidence > best_match["confidence"]:
                        best_match = {
                            "intent_type": intent_type,
                            "confidence": confidence,
                            "matched_pattern": pattern,
                            "extracted_params": dict(match.groupdict())
                        }
        return best_match

    def _analyze_intent_sync(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> IntentAnalysis:
        """同期版インテント分析"""
        # 基本的なコンテキスト分析
        context_info = self._extract_context_info(query, context)

        # パターンによるインテントマッチング
        intent_match = self._match_intent_patterns(query)

        # モックモードでのAI分析
        ai_analysis = self._mock_ai_intent_analysis(query, context_info)

        # 信頼度計算
        confidence = self._calculate_intent_confidence(intent_match, ai_analysis, context_info)

        # サービス候補の決定
        primary_service = self._determine_primary_service(intent_match, context_info)
        secondary_services = self._determine_secondary_services(intent_match, context_info)

        # パラメータ抽出
        parameters = self._extract_parameters(query, intent_match)

        # AI支援の必要性判定
        requires_ai = self._determine_ai_assistance_need(query, context_info, ai_analysis)

        # ルーティング推奨
        routing_rec = self._generate_routing_recommendation(
            intent_match, context_info, requires_ai
        )

        return IntentAnalysis(
            intent_type=intent_match.get("intent_type", "general"),
            confidence=confidence,
            primary_service=primary_service,
            secondary_services=secondary_services,
            parameters=parameters,
            context_info=context_info,
            routing_recommendation=routing_rec,
            requires_ai_assistance=requires_ai
        )

    def _make_routing_decision_sync(
        self,
        query: str,
        user_id: str,
        analysis: IntentAnalysis,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """同期版ルーティング決定"""
        decision_id = f"route_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:4]}"

        # 主要サービスの決定
        selected_service = analysis.primary_service

        # メソッドの決定
        selected_method = self._determine_service_method(selected_service, analysis, context)

        # 実行パラメータの作成
        execution_parameters = self._create_execution_parameters(
            query, analysis, selected_service, context
        )

        # AI強化の決定
        ai_enhanced = analysis.requires_ai_assistance or analysis.confidence < 0.6

        # 信頼度しきい値の決定
        confidence_threshold = 0.7 if ai_enhanced else 0.5

        # 決定の理由
        reasoning = self._generate_decision_reasoning(analysis, selected_service, ai_enhanced)

        return RoutingDecision(
            decision_id=decision_id,
            user_id=user_id,
            original_query=query,
            analysis=analysis,
            selected_service=selected_service,
            selected_method=selected_method,
            execution_parameters=execution_parameters,
            ai_enhanced=ai_enhanced,
            confidence_threshold=confidence_threshold,
            reasoning=reasoning
        )

    def _mock_ai_intent_analysis(self, query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """モックモードでのAIインテント分析"""
        query_lower = query.lower()

        # 複数の要素を検出するためのキーワード
        detected_elements = []

        if "天気" in query_lower:
            detected_elements.append("weather")
        if "ニュース" in query_lower or "情報" in query_lower:
            detected_elements.append("news")
        if "通知" in query_lower or "リマインダー" in query_lower or "起こして" in query_lower:
            detected_elements.append("notification")
        if "検索" in query_lower or "調べて" in query_lower:
            detected_elements.append("search")
        if "タスク" in query_lower or "自動" in query_lower:
            detected_elements.append("task")

        # 複合クエリの判定
        if len(detected_elements) > 1:
            return {
                "detected_intent": "composite_task",
                "confidence": 0.9,
                "required_services": detected_elements,
                "intent_category": "composite",
                "complexity_level": "complex",
                "ai_assistance_needed": True,
                "reasoning": f"複合クエリを検出: {', '.join(detected_elements)}",
                "detected_elements": detected_elements
            }

        # 単一要素のクエリ
        if "天気" in query_lower:
            return {
                "detected_intent": "get_weather",
                "confidence": 0.9,
                "required_services": ["weather"],
                "intent_category": "search",
                "complexity_level": "simple",
                "ai_assistance_needed": False,
                "reasoning": "天気関連クエリを検出"
            }
        elif "通知" in query_lower or "リマインダー" in query_lower:
            return {
                "detected_intent": "create_notification",
                "confidence": 0.9,
                "required_services": ["notification"],
                "intent_category": "create",
                "complexity_level": "simple",
                "ai_assistance_needed": False,
                "reasoning": "通知作成クエリを検出"
            }
        elif "検索" in query_lower or "調べて" in query_lower:
            return {
                "detected_intent": "search_web",
                "confidence": 0.8,
                "required_services": ["search"],
                "intent_category": "search",
                "complexity_level": "simple",
                "ai_assistance_needed": False,
                "reasoning": "検索クエリを検出"
            }
        elif "タスク" in query_lower or "自動" in query_lower:
            return {
                "detected_intent": "create_auto_task",
                "confidence": 0.8,
                "required_services": ["auto_task"],
                "intent_category": "create",
                "complexity_level": "moderate",
                "ai_assistance_needed": False,
                "reasoning": "自動タスク関連クエリを検出"
            }
        else:
            return {
                "detected_intent": "general_assistance",
                "confidence": 0.6,
                "required_services": ["search", "notification"],
                "intent_category": "general",
                "complexity_level": "moderate",
                "ai_assistance_needed": True,
                "reasoning": "一般的な支援クエリを検出"
            }

    def _calculate_intent_confidence(
        self,
        pattern_match: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context_info: Dict[str, Any]
    ) -> float:
        """インテント信頼度を計算"""
        base_confidence = pattern_match.get("confidence", 0.0)
        ai_confidence = ai_analysis.get("confidence", 0.0)

        # コンテキストによる調整
        context_bonus = 0.0
        if context_info.get("time_specific"):
            context_bonus += 0.1
        if context_info.get("location_mentioned"):
            context_bonus += 0.1
        if context_info.get("technical"):
            context_bonus += 0.1

        # 最終信頼度（パターンとAIの平均にコンテキストボーナス）
        final_confidence = (base_confidence + ai_confidence) / 2 + context_bonus
        return min(1.0, final_confidence)

    def _determine_primary_service(
        self,
        intent_match: Dict[str, Any],
        context_info: Dict[str, Any]
    ) -> str:
        """主要サービスを決定"""
        # インテントマッピングから
        intent_type = intent_match.get("intent_type", "general")
        services = service_integration_manager.find_services_for_intent(intent_type)

        if services:
            return services[0]

        # コンテキストベースで決定
        if context_info.get("time_specific"):
            return "notification"
        elif context_info.get("location_mentioned"):
            return "weather"
        elif context_info.get("information_seeking"):
            return "search"
        else:
            return "search"

    def _determine_secondary_services(
        self,
        intent_match: Dict[str, Any],
        context_info: Dict[str, Any]
    ) -> List[str]:
        """副次的サービスを決定"""
        intent_type = intent_match.get("intent_type", "general")
        all_services = service_integration_manager.find_services_for_intent(intent_type)

        # 最初のサービスを主要サービスとして除外
        if len(all_services) > 1:
            return all_services[1:3]  # 最大2つまで

        return []

    def _extract_parameters(self, query: str, intent_match: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータを抽出"""
        parameters = {}

        # 時間情報
        if self._detect_time_specific(query):
            parameters["time_info"] = self._extract_time_info(query)

        # 場所情報
        if self._detect_location(query):
            parameters["location"] = self._extract_location_info(query)

        # 繰り返し情報
        if self._detect_recurring_pattern(query):
            parameters["recurring"] = self._extract_recurring_info(query)

        return parameters

    def _extract_time_info(self, query: str) -> Dict[str, Any]:
        """時間情報を抽出"""
        # 簡易的な時間抽出
        time_info = {}

        # 時間パターン検索
        time_patterns = {
            "specific_time": r"(\d{1,2})[:時](\d{0,2})",
            "relative_time": r"(\d+)(?:分|時間|日)(?:後|前)",
            "daily_time": r"(?:毎日|毎朝|毎晩)(\d{1,2})[:時](\d{0,2})"
        }

        for pattern_name, pattern in time_patterns.items():
            match = re.search(pattern, query)
            if match:
                time_info[pattern_name] = match.groups()

        return time_info

    def _extract_location_info(self, query: str) -> str:
        """場所情報を抽出"""
        # 主要都市名
        cities = ["東京", "大阪", "名古屋", "福岡", "札幌", "仙台", "横浜", "京都"]

        for city in cities:
            if city in query:
                return city

        # 地域名
        regions = ["北海道", "東北", "関東", "中部", "関西", "中国", "四国", "九州"]

        for region in regions:
            if region in query:
                return region

        return "東京"  # デフォルト

    def _extract_recurring_info(self, query: str) -> Dict[str, Any]:
        """繰り返し情報を抽出"""
        recurring_info = {}

        if "毎日" in query or "毎朝" in query or "毎晩" in query:
            recurring_info["frequency"] = "daily"
        elif "毎週" in query:
            recurring_info["frequency"] = "weekly"
        elif "毎月" in query:
            recurring_info["frequency"] = "monthly"

        return recurring_info

    def _determine_ai_assistance_need(
        self,
        query: str,
        context_info: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> bool:
        """AI支援の必要性を判定"""
        # AI分析結果に基づく
        if ai_analysis.get("ai_assistance_needed"):
            return True

        # 複雑さによる判定
        if context_info.get("multi_step") or context_info.get("technical"):
            return True

        # 創造性が必要な場合
        if ai_analysis.get("intent_category") == "creative":
            return True

        return False

    def _generate_routing_recommendation(self, intent_match: Dict[str, Any], context_info: Dict[str, Any], requires_ai: bool) -> str:
        """ルーティング推奨を生成"""
        recommendation = []

        intent_type = intent_match.get("intent_type", "general")
        confidence = intent_match.get("confidence", 0.0)

        if confidence > 0.7:
            recommendation.append(f"高信頼度({confidence:.2f})で{intent_type}インテントを検出")
        elif confidence > 0.4:
            recommendation.append(f"中程度の信頼度({confidence:.2f})で{intent_type}インテントを検出")
        else:
            recommendation.append(f"低信頼度({confidence:.2f})で一般インテントを検出")

        if context_info.get("time_specific"):
            recommendation.append("時間指定要素を含むため通知サービスを推奨")

        if context_info.get("location_mentioned"):
            recommendation.append("場所指定要素を含むため天気・検索サービスを推奨")

        if requires_ai:
            recommendation.append("AI支援を推奨")

        return " | ".join(recommendation)

    async def _make_routing_decision(
        self,
        query: str,
        user_id: str,
        analysis: IntentAnalysis,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """ルーティング決定を作成"""
        decision_id = f"route_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:4]}"

        # 主要サービスの決定
        selected_service = analysis.primary_service

        # メソッドの決定
        selected_method = self._determine_service_method(selected_service, analysis, context)

        # 実行パラメータの作成
        execution_parameters = self._create_execution_parameters(
            query, analysis, selected_service, context
        )

        # AI強化の決定
        ai_enhanced = analysis.requires_ai_assistance or analysis.confidence < 0.6

        # 信頼度しきい値の決定
        confidence_threshold = 0.7 if ai_enhanced else 0.5

        # 決定の理由
        reasoning = self._generate_decision_reasoning(analysis, selected_service, ai_enhanced)

        return RoutingDecision(
            decision_id=decision_id,
            user_id=user_id,
            original_query=query,
            analysis=analysis,
            selected_service=selected_service,
            selected_method=selected_method,
            execution_parameters=execution_parameters,
            ai_enhanced=ai_enhanced,
            confidence_threshold=confidence_threshold,
            reasoning=reasoning
        )

    def _determine_service_method(self, service: str, analysis: IntentAnalysis, context: Dict[str, Any]) -> str:
        """サービスメソッドを決定"""
        intent_type = analysis.intent_type

        method_mapping = {
            "create_notification": "add",
            "list_notifications": "list",
            "delete_notification": "delete",
            "get_weather": "current",
            "search_web": "web",
            "create_auto_task": "create",
            "composite_task": "combined"  # 複合タスク用
        }

        return method_mapping.get(intent_type, "default")

    def _create_execution_parameters(self, query: str, analysis: IntentAnalysis, service: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """実行パラメータを作成"""
        parameters = analysis.parameters.copy()

        # サービス固有のパラメータ追加
        if service == "notification":
            parameters["user_id"] = context.get("user_id", "default")
            parameters["priority"] = "normal"
        elif service == "weather":
            parameters["location"] = parameters.get("location", "東京")
        elif service == "search":
            parameters["max_results"] = 3
        elif service == "auto_task":
            parameters["enabled"] = True
        elif analysis.intent_type == "composite_task":
            # 複合タスク用のパラメータ設定
            parameters["user_id"] = context.get("user_id", "default")
            parameters["composite"] = True
            parameters["services"] = analysis.context_info.get("detected_elements", [])

        return parameters

    def _generate_decision_reasoning(self, analysis: IntentAnalysis, service: str, ai_enhanced: bool) -> str:
        """決定の理由を生成"""
        reasons = []

        reasons.append(f"インテント: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")
        reasons.append(f"選択サービス: {service}")

        if ai_enhanced:
            reasons.append("AI支援を有効化")

        if analysis.context_info.get("time_specific"):
            reasons.append("時間指定要素を検出")

        return " | ".join(reasons)

    def _create_fallback_decision(self, query: str, user_id: str, error: str) -> RoutingDecision:
        """フォールバック決定を作成"""
        return RoutingDecision(
            decision_id=f"fallback_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_id,
            original_query=query,
            analysis=IntentAnalysis(
                intent_type="general",
                confidence=0.0,
                primary_service="search",
                secondary_services=[],
                parameters={},
                context_info={"error": error},
                routing_recommendation="エラーによるフォールバック",
                requires_ai_assistance=False
            ),
            selected_service="search",
            selected_method="web",
            execution_parameters={"query": query},
            ai_enhanced=False,
            confidence_threshold=0.0,
            reasoning=f"エラーによるフォールバック: {error}"
        )

    def _save_routing_history(self, user_id: str, decision: RoutingDecision):
        """ルーティング履歴を保存"""
        with self.history_lock:
            self.routing_history[user_id].append(decision)

            # 履歴を制限（最新100件）
            if len(self.routing_history[user_id]) > 100:
                self.routing_history[user_id] = self.routing_history[user_id][-100:]

    def get_routing_statistics(self, user_id: str) -> Dict[str, Any]:
        """ルーティング統計を取得"""
        with self.history_lock:
            user_history = self.routing_history.get(user_id, [])

            if not user_history:
                return {"total_routings": 0, "service_distribution": {}}

            # サービス別カウント
            service_counts = Counter(d.selected_service for d in user_history)

            # 成功率計算
            successful_routings = len([d for d in user_history if d.analysis.confidence > 0.5])

            return {
                "total_routings": len(user_history),
                "service_distribution": dict(service_counts),
                "success_rate": successful_routings / len(user_history),
                "average_confidence": sum(d.analysis.confidence for d in user_history) / len(user_history),
            }

    async def analyze_and_route(
        self,
        query: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        非同期版のクエリ分析・ルーティング

        Args:
            query: ユーザークエリ
            user_id: ユーザーID
            context: 追加コンテキスト

        Returns:
            ルーティング決定
        """
        try:
            # インテント分析（非同期版）
            analysis = await self._analyze_intent(query, context or {})

            # ルーティング決定
            routing_decision = await self._make_routing_decision(
                query, user_id, analysis, context or {}
            )

            # 履歴保存
            self._save_routing_history(user_id, routing_decision)

            return routing_decision

        except Exception as e:
            self.logger.error(f"インテント分析・ルーティングエラー: {str(e)}")
            # フォールバック決定
            return self._create_fallback_decision(query, user_id, str(e))

# グローバルインスタンス
context_aware_router = ContextAwareIntentRouter()
