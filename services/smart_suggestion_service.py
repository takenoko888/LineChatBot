"""
Smart suggestion service implementation
AIによる個人最適化機能
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pytz
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import threading
from .gemini_service import GeminiService

@dataclass
class UserBehaviorPattern:
    """ユーザー行動パターン"""
    user_id: str
    action_type: str
    timestamp: datetime
    content: str
    context: Dict[str, Any]
    success: bool = True

@dataclass
class SmartSuggestion:
    """スマート提案"""
    suggestion_id: str
    user_id: str
    suggestion_type: str  # timing, grouping, scheduling, optimization
    title: str
    description: str
    confidence: float
    data: Dict[str, Any]
    created_at: datetime
    applied: bool = False

class SmartSuggestionService:
    """スマート提案サービス"""

    def __init__(self, gemini_service: Optional[GeminiService] = None, storage_path: str = None):
        """
        初期化
        
        Args:
            gemini_service (Optional[GeminiService]): Gemini AIサービス
            storage_path (str): データ保存パス
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_service = gemini_service or GeminiService()
        
        # ストレージ設定
        self.storage_path = storage_path or os.path.join('/workspace', 'data', 'smart_suggestions.json')
        self.behavior_storage_path = os.path.join('/workspace', 'data', 'user_behaviors.json')
        
        # データストレージ
        self.user_behaviors: Dict[str, List[UserBehaviorPattern]] = defaultdict(list)
        self.suggestions: Dict[str, List[SmartSuggestion]] = defaultdict(list)
        
        # ロック
        self.lock = threading.Lock()
        
        # データ読み込み
        self._load_data()
        
        self.logger.info("スマート提案サービスを初期化しました")

    def _load_data(self) -> None:
        """データを読み込み"""
        try:
            # ディレクトリ作成
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # 行動パターンデータ読み込み
            if os.path.exists(self.behavior_storage_path):
                with open(self.behavior_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, behaviors in data.items():
                        self.user_behaviors[user_id] = [
                            UserBehaviorPattern(
                                user_id=b['user_id'],
                                action_type=b['action_type'],
                                timestamp=datetime.fromisoformat(b['timestamp']),
                                content=b['content'],
                                context=b['context'],
                                success=b.get('success', True)
                            ) for b in behaviors
                        ]
            
            # 提案データ読み込み
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, suggestions in data.items():
                        self.suggestions[user_id] = [
                            SmartSuggestion(
                                suggestion_id=s['suggestion_id'],
                                user_id=s['user_id'],
                                suggestion_type=s['suggestion_type'],
                                title=s['title'],
                                description=s['description'],
                                confidence=s['confidence'],
                                data=s['data'],
                                created_at=datetime.fromisoformat(s['created_at']),
                                applied=s.get('applied', False)
                            ) for s in suggestions
                        ]
                        
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {str(e)}")

    def _save_data(self) -> None:
        """データを保存"""
        try:
            with self.lock:
                # 行動パターンデータ保存
                behaviors_data = {}
                for user_id, behaviors in self.user_behaviors.items():
                    behaviors_data[user_id] = [asdict(b) for b in behaviors[-1000:]]  # 最新1000件のみ保存
                    for b_dict in behaviors_data[user_id]:
                        b_dict['timestamp'] = b_dict['timestamp'].isoformat()
                
                with open(self.behavior_storage_path, 'w', encoding='utf-8') as f:
                    json.dump(behaviors_data, f, ensure_ascii=False, indent=2)
                
                # 提案データ保存
                suggestions_data = {}
                for user_id, suggestions in self.suggestions.items():
                    suggestions_data[user_id] = [asdict(s) for s in suggestions[-100:]]  # 最新100件のみ保存
                    for s_dict in suggestions_data[user_id]:
                        s_dict['created_at'] = s_dict['created_at'].isoformat()
                
                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    json.dump(suggestions_data, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            self.logger.error(f"データ保存エラー: {str(e)}")

    def record_user_behavior(self, user_id: str, action_type: str, content: str, 
                           context: Dict[str, Any] = None, success: bool = True) -> None:
        """
        ユーザー行動を記録
        
        Args:
            user_id (str): ユーザーID
            action_type (str): アクション種別
            content (str): コンテンツ
            context (Dict[str, Any]): コンテキスト
            success (bool): 成功フラグ
        """
        try:
            behavior = UserBehaviorPattern(
                user_id=user_id,
                action_type=action_type,
                timestamp=datetime.now(pytz.timezone('Asia/Tokyo')),
                content=content,
                context=context or {},
                success=success
            )
            
            with self.lock:
                self.user_behaviors[user_id].append(behavior)
                
                # 古いデータのクリーンアップ（1週間以上前）
                cutoff_date = datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(days=7)
                self.user_behaviors[user_id] = [
                    b for b in self.user_behaviors[user_id]
                    if b.timestamp > cutoff_date
                ]
            
            # 定期的に保存
            self._save_data()
            
        except Exception as e:
            self.logger.error(f"行動記録エラー: {str(e)}")

    def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        ユーザーパターンを分析
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            with self.lock:
                behaviors = self.user_behaviors.get(user_id, [])
            
            if not behaviors:
                return {"error": "データ不足"}
            
            # 時間パターン分析
            hour_distribution = defaultdict(int)
            day_distribution = defaultdict(int)
            
            # アクション種別分析
            action_counts = Counter()
            
            # 成功率分析
            success_rates = defaultdict(lambda: {'total': 0, 'success': 0})
            
            for behavior in behaviors:
                hour = behavior.timestamp.hour
                day = behavior.timestamp.strftime('%A')
                
                hour_distribution[hour] += 1
                day_distribution[day] += 1
                action_counts[behavior.action_type] += 1
                
                success_rates[behavior.action_type]['total'] += 1
                if behavior.success:
                    success_rates[behavior.action_type]['success'] += 1
            
            # 最適時間帯の特定
            most_active_hours = sorted(hour_distribution.items(), 
                                     key=lambda x: x[1], reverse=True)[:3]
            
            # 好みのアクション特定
            preferred_actions = action_counts.most_common(5)
            
            return {
                'total_behaviors': len(behaviors),
                'most_active_hours': [hour for hour, count in most_active_hours],
                'day_distribution': dict(day_distribution),
                'preferred_actions': preferred_actions,
                'success_rates': {
                    action: rates['success'] / rates['total'] if rates['total'] > 0 else 0
                    for action, rates in success_rates.items()
                },
                'analysis_period': {
                    'start': min(b.timestamp for b in behaviors).isoformat(),
                    'end': max(b.timestamp for b in behaviors).isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"パターン分析エラー: {str(e)}")
            return {"error": f"分析エラー: {str(e)}"}

    def generate_timing_suggestions(self, user_id: str) -> List[SmartSuggestion]:
        """
        タイミング提案を生成
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            List[SmartSuggestion]: タイミング提案リスト
        """
        try:
            patterns = self.analyze_user_patterns(user_id)
            if 'error' in patterns:
                return []
            
            suggestions = []
            
            # 最適な通知時間を提案
            if patterns['most_active_hours']:
                optimal_hour = patterns['most_active_hours'][0]
                suggestion = SmartSuggestion(
                    suggestion_id=f"timing_{user_id}_{int(datetime.now().timestamp())}",
                    user_id=user_id,
                    suggestion_type="timing",
                    title="最適な通知時間",
                    description=f"あなたが最もアクティブな{optimal_hour}時頃に通知を設定することをお勧めします。",
                    confidence=0.8,
                    data={"optimal_hour": optimal_hour, "activity_pattern": patterns['most_active_hours']},
                    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                )
                suggestions.append(suggestion)
            
            # 成功率の高いアクション時間を提案
            high_success_actions = [
                action for action, rate in patterns['success_rates'].items()
                if rate > 0.8 and patterns['preferred_actions']
            ]
            
            if high_success_actions:
                suggestion = SmartSuggestion(
                    suggestion_id=f"success_{user_id}_{int(datetime.now().timestamp())}",
                    user_id=user_id,
                    suggestion_type="timing",
                    title="成功率の高い活動時間",
                    description=f"これらの活動は成功率が高いです: {', '.join(high_success_actions[:3])}",
                    confidence=0.7,
                    data={"high_success_actions": high_success_actions},
                    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"タイミング提案生成エラー: {str(e)}")
            return []

    def generate_grouping_suggestions(self, user_id: str, notifications: List[Any]) -> List[SmartSuggestion]:
        """
        グループ化提案を生成
        
        Args:
            user_id (str): ユーザーID
            notifications (List[Any]): 通知リスト
            
        Returns:
            List[SmartSuggestion]: グループ化提案リスト
        """
        try:
            if len(notifications) < 3:
                return []
            
            # AIで類似性を分析
            notification_texts = [n.title + " " + n.message for n in notifications]
            
            prompt = f"""
以下の通知リストを分析し、類似性に基づいてグループ化提案を作成してください。

通知リスト:
{chr(10).join([f"- {text}" for text in notification_texts[:10]])}

以下の形式でJSONを返してください:
{{
    "groups": [
        {{
            "name": "グループ名",
            "description": "グループの説明",
            "notification_indices": [0, 1, 2],
            "reasoning": "グループ化の理由"
        }}
    ],
    "confidence": 0.8
}}
"""
            
            response = self.gemini_service.model.generate_content(prompt)
            if not response or not response.text:
                return []
            
            # JSONを抽出
            json_text = response.text
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '{' in json_text and '}' in json_text:
                start = json_text.find('{')
                end = json_text.rfind('}') + 1
                json_text = json_text[start:end]
            
            try:
                result = json.loads(json_text)
                suggestions = []
                
                for group in result.get('groups', []):
                    suggestion = SmartSuggestion(
                        suggestion_id=f"group_{user_id}_{int(datetime.now().timestamp())}",
                        user_id=user_id,
                        suggestion_type="grouping",
                        title=f"通知グループ化: {group['name']}",
                        description=group['description'],
                        confidence=result.get('confidence', 0.7),
                        data={
                            "group_name": group['name'],
                            "notification_indices": group['notification_indices'],
                            "reasoning": group['reasoning']
                        },
                        created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                    )
                    suggestions.append(suggestion)
                
                return suggestions
                
            except json.JSONDecodeError:
                return []
            
        except Exception as e:
            self.logger.error(f"グループ化提案生成エラー: {str(e)}")
            return []

    def generate_scheduling_suggestions(self, user_id: str) -> List[SmartSuggestion]:
        """
        スケジューリング提案を生成
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            List[SmartSuggestion]: スケジューリング提案リスト
        """
        try:
            patterns = self.analyze_user_patterns(user_id)
            if 'error' in patterns:
                return []
            
            suggestions = []
            
            # 週間パターンに基づく提案
            day_dist = patterns.get('day_distribution', {})
            if day_dist:
                # 最もアクティブな曜日を特定
                most_active_day = max(day_dist, key=day_dist.get)
                
                suggestion = SmartSuggestion(
                    suggestion_id=f"schedule_{user_id}_{int(datetime.now().timestamp())}",
                    user_id=user_id,
                    suggestion_type="scheduling",
                    title="効率的な週間スケジュール",
                    description=f"{most_active_day}曜日は特に活発です。重要なタスクをこの日に配置することをお勧めします。",
                    confidence=0.75,
                    data={
                        "most_active_day": most_active_day,
                        "day_distribution": day_dist
                    },
                    created_at=datetime.now(pytz.timezone('Asia/Tokyo'))
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"スケジューリング提案生成エラー: {str(e)}")
            return []

    def get_all_suggestions(self, user_id: str, limit: int = 10) -> List[SmartSuggestion]:
        """
        全ての提案を取得
        
        Args:
            user_id (str): ユーザーID
            limit (int): 取得件数制限
            
        Returns:
            List[SmartSuggestion]: 提案リスト
        """
        try:
            with self.lock:
                user_suggestions = self.suggestions.get(user_id, [])
            
            # 未適用の提案を優先してソート
            sorted_suggestions = sorted(
                user_suggestions,
                key=lambda s: (s.applied, -s.confidence, -s.created_at.timestamp())
            )
            
            return sorted_suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"提案取得エラー: {str(e)}")
            return []

    def apply_suggestion(self, user_id: str, suggestion_id: str) -> bool:
        """
        提案を適用
        
        Args:
            user_id (str): ユーザーID
            suggestion_id (str): 提案ID
            
        Returns:
            bool: 適用成功フラグ
        """
        try:
            with self.lock:
                for suggestion in self.suggestions.get(user_id, []):
                    if suggestion.suggestion_id == suggestion_id:
                        suggestion.applied = True
                        self._save_data()
                        return True
            return False
            
        except Exception as e:
            self.logger.error(f"提案適用エラー: {str(e)}")
            return False

    def generate_comprehensive_suggestions(self, user_id: str, notifications: List[Any] = None) -> List[SmartSuggestion]:
        """
        包括的な提案を生成
        
        Args:
            user_id (str): ユーザーID
            notifications (List[Any]): 通知リスト
            
        Returns:
            List[SmartSuggestion]: 提案リスト
        """
        try:
            all_suggestions = []
            
            # タイミング提案
            timing_suggestions = self.generate_timing_suggestions(user_id)
            all_suggestions.extend(timing_suggestions)
            
            # スケジューリング提案
            scheduling_suggestions = self.generate_scheduling_suggestions(user_id)
            all_suggestions.extend(scheduling_suggestions)
            
            # グループ化提案（通知がある場合）
            if notifications:
                grouping_suggestions = self.generate_grouping_suggestions(user_id, notifications)
                all_suggestions.extend(grouping_suggestions)
            
            # 提案を保存
            with self.lock:
                self.suggestions[user_id].extend(all_suggestions)
                self._save_data()
            
            return all_suggestions
            
        except Exception as e:
            self.logger.error(f"包括的提案生成エラー: {str(e)}")
            return []

    def format_suggestions_message(self, suggestions: List[SmartSuggestion]) -> str:
        """
        提案をメッセージ形式でフォーマット
        
        Args:
            suggestions (List[SmartSuggestion]): 提案リスト
            
        Returns:
            str: フォーマットされたメッセージ
        """
        if not suggestions:
            return "💡 現在、新しい提案はありません。もう少し使用してからお試しください。"
        
        lines = ["🧠 **スマート提案**", ""]
        
        for i, suggestion in enumerate(suggestions[:5], 1):
            confidence_emoji = "🔥" if suggestion.confidence > 0.8 else "⭐" if suggestion.confidence > 0.6 else "💡"
            applied_status = " ✅" if suggestion.applied else ""
            
            lines.extend([
                f"{confidence_emoji} **{suggestion.title}**{applied_status}",
                f"   {suggestion.description}",
                f"   信頼度: {suggestion.confidence:.0%}",
                ""
            ])
        
        if len(suggestions) > 5:
            lines.append(f"...他に{len(suggestions) - 5}件の提案があります")
        
        return "\n".join(lines) 