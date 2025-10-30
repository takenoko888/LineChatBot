"""
Context management utilities
"""
from typing import Dict, List, Optional, Any
from collections import deque
import json
import logging
from datetime import datetime
import pytz

class ContextUtils:
    """コンテキスト管理ユーティリティ"""

    def __init__(self, max_contexts: int = 10):
        """
        初期化
        
        Args:
            max_contexts (int): 保持する最大コンテキスト数
        """
        self.logger = logging.getLogger(__name__)
        self.max_contexts = max_contexts
        self.contexts: Dict[str, deque] = {}
        self.jst = pytz.timezone('Asia/Tokyo')

    def add_context(
        self,
        context_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        コンテキストを追加
        
        Args:
            context_type (str): コンテキストタイプ
            data (Dict[str, Any]): コンテキストデータ
            user_id (Optional[str]): ユーザーID
        """
        try:
            key = f"{context_type}_{user_id}" if user_id else context_type
            
            if key not in self.contexts:
                self.contexts[key] = deque(maxlen=self.max_contexts)
                
            # タイムスタンプを追加
            data['timestamp'] = datetime.now(self.jst).isoformat()
            self.contexts[key].append(data)
            
        except Exception as e:
            self.logger.error(f"コンテキスト追加エラー: {str(e)}")

    def get_recent_contexts(
        self,
        context_type: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        最近のコンテキストを取得
        
        Args:
            context_type (str): コンテキストタイプ
            user_id (Optional[str]): ユーザーID
            limit (Optional[int]): 取得する最大数
            
        Returns:
            List[Dict[str, Any]]: コンテキストリスト
        """
        try:
            key = f"{context_type}_{user_id}" if user_id else context_type
            
            if key not in self.contexts:
                return []
                
            contexts = list(self.contexts[key])
            if limit:
                contexts = contexts[-limit:]
                
            return contexts
            
        except Exception as e:
            self.logger.error(f"コンテキスト取得エラー: {str(e)}")
            return []

    def clear_contexts(
        self,
        context_type: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        コンテキストをクリア
        
        Args:
            context_type (str): コンテキストタイプ
            user_id (Optional[str]): ユーザーID
        """
        try:
            key = f"{context_type}_{user_id}" if user_id else context_type
            if key in self.contexts:
                del self.contexts[key]
        except Exception as e:
            self.logger.error(f"コンテキストクリアエラー: {str(e)}")

    def get_context_summary(
        self,
        context_type: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        コンテキストのサマリーを生成
        
        Args:
            context_type (str): コンテキストタイプ
            user_id (Optional[str]): ユーザーID
            
        Returns:
            str: コンテキストのサマリー
        """
        try:
            contexts = self.get_recent_contexts(context_type, user_id)
            if not contexts:
                return "コンテキストがありません。"
                
            summary = ["最近の会話:"]
            for ctx in contexts:
                timestamp = datetime.fromisoformat(ctx['timestamp'])
                time_str = timestamp.strftime('%H:%M')
                
                if 'role' in ctx and 'content' in ctx:
                    role = '👤' if ctx['role'] == 'user' else '🤖'
                    summary.append(f"{time_str} {role} {ctx['content']}")
                    
            return "\n".join(summary)
            
        except Exception as e:
            self.logger.error(f"コンテキストサマリー生成エラー: {str(e)}")
            return "コンテキストの取得に失敗しました。"

    def analyze_context(
        self,
        context_type: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        コンテキストを分析
        
        Args:
            context_type (str): コンテキストタイプ
            user_id (Optional[str]): ユーザーID
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            contexts = self.get_recent_contexts(context_type, user_id)
            if not contexts:
                return {'status': 'no_context'}
                
            analysis = {
                'context_count': len(contexts),
                'time_span': {
                    'start': contexts[0]['timestamp'],
                    'end': contexts[-1]['timestamp']
                },
                'user_messages': 0,
                'bot_messages': 0,
                'topics': set()
            }
            
            for ctx in contexts:
                if ctx.get('role') == 'user':
                    analysis['user_messages'] += 1
                elif ctx.get('role') == 'assistant':
                    analysis['bot_messages'] += 1
                    
                # トピックの抽出（簡易的な実装）
                content = ctx.get('content', '')
                if '天気' in content:
                    analysis['topics'].add('weather')
                if '通知' in content:
                    analysis['topics'].add('notification')
                if '検索' in content:
                    analysis['topics'].add('search')
                    
            analysis['topics'] = list(analysis['topics'])
            return analysis
            
        except Exception as e:
            self.logger.error(f"コンテキスト分析エラー: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def save_contexts(self, filepath: str) -> bool:
        """
        コンテキストをファイルに保存
        
        Args:
            filepath (str): 保存先ファイルパス
            
        Returns:
            bool: 保存成功時True
        """
        try:
            # dequeをリストに変換
            data = {
                key: list(contexts)
                for key, contexts in self.contexts.items()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
            
        except Exception as e:
            self.logger.error(f"コンテキスト保存エラー: {str(e)}")
            return False

    def load_contexts(self, filepath: str) -> bool:
        """
        コンテキストをファイルから読み込み
        
        Args:
            filepath (str): 読み込むファイルパス
            
        Returns:
            bool: 読み込み成功時True
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 読み込んだデータをdequeに変換
            self.contexts = {
                key: deque(contexts, maxlen=self.max_contexts)
                for key, contexts in data.items()
            }
            return True
            
        except Exception as e:
            self.logger.error(f"コンテキスト読み込みエラー: {str(e)}")
            return False

    def get_conversation_state(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        会話の状態を取得
        
        Args:
            user_id (str): ユーザーID
            
        Returns:
            Dict[str, Any]: 会話の状態情報
        """
        try:
            recent_contexts = self.get_recent_contexts('chat', user_id, limit=5)
            if not recent_contexts:
                return {'state': 'new_conversation'}
                
            last_context = recent_contexts[-1]
            last_time = datetime.fromisoformat(last_context['timestamp'])
            now = datetime.now(self.jst)
            time_diff = now - last_time
            
            state = {
                'last_interaction': last_context,
                'time_since_last': time_diff.total_seconds(),
                'is_active': time_diff.total_seconds() < 300,  # 5分以内なら会話アクティブ
                'context_count': len(recent_contexts)
            }
            
            # 最後の会話タイプを判定
            if 'content' in last_context:
                content = last_context['content']
                if '天気' in content:
                    state['last_topic'] = 'weather'
                elif '通知' in content:
                    state['last_topic'] = 'notification'
                elif '検索' in content:
                    state['last_topic'] = 'search'
                else:
                    state['last_topic'] = 'general'
                    
            return state
            
        except Exception as e:
            self.logger.error(f"会話状態取得エラー: {str(e)}")
            return {'state': 'error', 'message': str(e)}

    def analyze_conversation_context(self, user_id: str) -> dict:
        """
        会話の流れからユーザーの意図を推定
        """
        contexts = self.get_recent_contexts('chat', user_id)
        if not contexts:
            return {}
        
        analysis_result = {
            "common_themes": self._detect_common_themes(contexts),
            "temporal_patterns": self._identify_temporal_patterns(contexts),
            "priority_keywords": self._extract_priority_keywords(contexts)
        }
        return analysis_result

    def extract_user_preferences(self, user_id: str) -> dict:
        """
        会話履歴からユーザーの好みや設定を抽出
        """
        contexts = self.get_recent_contexts('chat', user_id)
        if not contexts:
            return {}
            
        preferences = {
            "preferred_hours": self._extract_preferred_hours(contexts),
            "priority_keywords": self._extract_priority_keywords(contexts)
        }
        return preferences

    def _detect_common_themes(self, contexts: list) -> list:
        """会話履歴から共通テーマを検出"""
        themes = set()
        for ctx in contexts:
            content = ctx.get('content', '')
            if '天気' in content:
                themes.add('weather')
            if '通知' in content:
                themes.add('notification')
            if '検索' in content:
                themes.add('search')
        return list(themes)

    def _identify_temporal_patterns(self, contexts: list) -> list:
        """会話履歴から時間的なパターンを検出"""
        time_patterns = []
        for ctx in contexts:
            timestamp = datetime.fromisoformat(ctx['timestamp'])
            time_patterns.append(timestamp.hour)
        return time_patterns

    def _extract_priority_keywords(self, contexts: list) -> list:
        """会話履歴から優先度の高いキーワードを抽出"""
        keywords = []
        for ctx in contexts:
            content = ctx.get('content', '')
            if '緊急' in content or 'すぐに' in content:
                keywords.append('urgent')
            if '低' in content or 'いつでも' in content:
                keywords.append('low')
        return keywords

    def _extract_preferred_hours(self, contexts: list) -> list:
        """会話履歴から好ましい時間帯を抽出"""
        preferred_hours = []
        for ctx in contexts:
            content = ctx.get('content', '')
            if '午前' in content:
                preferred_hours.extend([9, 10, 11])
            if '午後' in content:
                preferred_hours.extend([13, 14, 15])
            if '夜' in content:
                preferred_hours.extend([18, 19, 20])
        return list(set(preferred_hours))