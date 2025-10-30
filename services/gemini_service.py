"""
Gemini AI service implementation
"""
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import google.generativeai as genai
import pytz
import logging
import json
import os
import re

class GeminiService:
    """Gemini AI サービス"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key (Optional[str]): Gemini APIキー
        """
        self.logger = logging.getLogger(__name__)
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # 遅延インポートで循環参照回避
        self._conversation_memory = None
        self._smart_suggestion = None
        
        # モックモード
        self.mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true' or \
                         os.getenv('GEMINI_MOCK', 'false').lower() == 'true'

        if self.mock_mode:
            # 実API呼び出しをスキップ
            self.model = None
            self.logger.info("Gemini AIをモックモードで初期化しました（API呼び出しなし）")
            return

        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini APIキーが設定されていません")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
            self.logger.info("Gemini AIの初期化が完了しました")
        except Exception as e:
            self.logger.error(f"Gemini AI初期化エラー: {str(e)}")
            raise ValueError("Gemini AIの初期化に失敗しました")

    def generate_content(self, prompt: str) -> str:
        """
        プロンプトからコンテンツを生成

        Args:
            prompt (str): 生成プロンプト

        Returns:
            str: 生成されたコンテンツ
        """
        try:
            if getattr(self, 'mock_mode', False) or self.model is None:
                # 簡易モック応答
                if 'コードを生成' in prompt:
                    return (
                        "import requests\n"
                        "from typing import Dict, Any\n\n"
                        "def generated_function(user_input: str, parameters: Dict[str, Any]) -> str:\n"
                        "    \"\"\"モック生成コード\"\"\"\n"
                        "    return f'モック実行: {user_input}'\n"
                    )
                return "テスト用のモック応答です"

            # 実API呼び出し
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"コンテンツ生成エラー: {str(e)}")
            raise

    def generate_json_content(self, prompt: str) -> Dict[str, Any]:
        """
        プロンプトからJSONコンテンツを生成

        Args:
            prompt (str): JSON生成プロンプト

        Returns:
            Dict[str, Any]: 生成されたJSONコンテンツ
        """
        try:
            if getattr(self, 'mock_mode', False) or self.model is None:
                # 簡易モックJSON
                return {
                    "functionality": "カスタム機能",
                    "function_name": "test_weather_function",
                    "description": "天気情報を取得して通知する",
                    "parameters": [{"name": "location", "type": "string", "required": True}],
                    "trigger_conditions": ["天気", "weather"],
                    "return_type": "text",
                    "dependencies": ["requests"],
                    "priority": 1,
                }

            # JSON生成を指示
            json_prompt = prompt + "\n\n出力はJSON形式でのみ行ってください。マークダウン記法などは使用せず、純粋なJSONのみを出力してください。"
            response = self.model.generate_content(json_prompt)

            # JSONパースを試行
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # JSONとしてパースできない場合、テキストからJSON部分を抽出
                text = response.text.strip()
                # コードブロックや余分なテキストを除去
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                # JSONパース再試行
                return json.loads(text)

        except Exception as e:
            self.logger.error(f"JSONコンテンツ生成エラー: {str(e)}")
            raise

    def _get_conversation_memory(self):
        """対話履歴サービスの取得（遅延初期化）"""
        if self._conversation_memory is None:
            try:
                from .conversation_memory_service import ConversationMemoryService
                self._conversation_memory = ConversationMemoryService(self)
            except ImportError:
                self.logger.warning("ConversationMemoryService が利用できません")
                self._conversation_memory = False
        return self._conversation_memory if self._conversation_memory is not False else None

    def _get_smart_suggestion(self):
        """スマート提案サービスの取得（遅延初期化）"""
        if self._smart_suggestion is None:
            try:
                from .smart_suggestion_service import SmartSuggestionService
                self._smart_suggestion = SmartSuggestionService(self)
            except ImportError:
                self.logger.warning("SmartSuggestionService が利用できません")
                self._smart_suggestion = False
        return self._smart_suggestion if self._smart_suggestion is not False else None

    def analyze_text(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        テキストを分析（統一AI判定 + 対話履歴考慮）
        
        Args:
            text (str): 解析するテキスト
            user_id (str): ユーザーID
            
        Returns:
            Dict[str, Any]: 解析結果
        """
        try:
            # モックモードでは簡易パスで高速・安全に返す
            if getattr(self, 'mock_mode', False) or getattr(self, 'model', None) is None:
                simple_result = self._check_simple_patterns(text)
                if simple_result:
                    return self._format_ai_analysis_result(simple_result, text)
                # フォールバック（雑談/ヘルプなども包含）
                return self._fallback_analysis(text)

            # 統一AI判定（履歴考慮版）
            result = self._unified_ai_analysis_with_context(text, user_id)
            
            # 行動記録（提案機能向け）
            self._record_user_behavior(user_id, text, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"テキスト分析エラー: {str(e)}")
            return self._fallback_analysis(text)

    def _unified_ai_analysis_with_context(self, text: str, user_id: str) -> Dict[str, Any]:
        """
        統一AI判定システム（対話履歴考慮版）
        
        Args:
            text (str): 解析するテキスト
            user_id (str): ユーザーID
            
        Returns:
            Dict[str, Any]: 解析結果
        """
        try:
            # コスト最適化: 簡単なケースは先にチェック
            simple_result = self._check_simple_patterns(text)
            if simple_result:
                self.logger.info(f"簡単パターンで判定: {simple_result['intent']}")
                # 以降の処理系と揃えるため、形式を統一して返却
                return self._format_ai_analysis_result(simple_result, text)
            
            # 文字数制限でコスト抑制
            if len(text) > 500:
                text = text[:500] + "..."
                self.logger.warning(f"長すぎるテキストを短縮: {len(text)}文字")
            
            # 対話履歴の取得
            conversation_context = ""
            user_profile_info = ""
            conversation_memory = self._get_conversation_memory()
            
            if conversation_memory:
                conversation_context = conversation_memory.get_conversation_context(user_id, limit=3)
                profile = conversation_memory.get_user_profile(user_id)
                if profile:
                    user_profile_info = f"""
ユーザープロファイル:
- よく使う機能: {', '.join(profile.frequent_topics[-3:]) if profile.frequent_topics else '未学習'}
- コミュニケーションスタイル: {profile.communication_style}
- よく使う時間: {', '.join(profile.preferred_times[-3:]) if profile.preferred_times else '未記録'}
"""
            
            now = datetime.now()
            
            prompt = f"""
あなたは多機能チャットボットのインテント分析エキスパートです。
ユーザーのメッセージを分析し、最適な機能と必要な情報を判定してください。

現在時刻: {now.strftime('%Y-%m-%d %H:%M')}

{conversation_context}

{user_profile_info}

現在のメッセージ: "{text}"

利用可能な機能:
1. notification - 通知/リマインダー設定
2. list_notifications - 通知一覧表示
3. delete_notification - 特定通知削除
4. delete_all_notifications - 全通知削除
5. weather - 天気情報
6. search - 明示的検索要求
7. auto_search - 文脈から検索が必要と判断
8. smart_suggestion - スマート提案要求
9. conversation_history - 対話履歴確認
10. create_auto_task - 自動実行タスク作成
11. list_auto_tasks - 自動実行タスク一覧
12. delete_auto_task - 自動実行タスク削除
13. toggle_auto_task - 自動実行タスク有効/無効切替
14. help - ヘルプ表示
15. chat - 一般的な会話

新機能の判定基準:

【自動実行・モニタリング機能】
- create_auto_task: 定期配信要求 ("毎日7時に天気を配信", "毎朝ニュースを送って", "定期的にレポート", "キーワードを監視")
- list_auto_tasks: タスク確認要求 ("自動実行一覧", "設定したタスク", "定期実行確認")
- delete_auto_task: タスク削除要求 ("タスク削除", "自動実行を止めて", "定期配信停止")
- toggle_auto_task: タスク状態変更 ("タスクを無効に", "配信再開", "一時停止")

【スマート提案】
- smart_suggestion: 提案要求 ("おすすめは？", "何かアドバイス", "提案して", "最適化して")

【対話履歴】
- conversation_history: 履歴確認要求 ("前回何話した？", "会話履歴", "前の話", "履歴確認")

【従来機能】
- notification: 時間指定 + 行動 ("毎日7時に起きる", "明日15時に会議")
- list_notifications: 通知確認意図 ("通知一覧", "設定した通知", "予定確認")
- delete_notification: ID指定削除 ("通知n_123を削除")
- delete_all_notifications: 全削除意図 ("全通知削除", "すべての通知を消して")
- weather: 天気関連 ("東京の天気", "明日の気温", "雨降る?")
- auto_search: 明確に最新情報や具体的事実が必要な質問のみ ("今日のニュース", "最新の株価", "現在の感染者数", "今年のトレンド", "営業時間を調べて")
- search: 明示的検索指示 ("○○について検索して", "○○を調べて")
- help: ヘルプ要求 ("ヘルプ", "使い方", "機能一覧")
- chat: 挨拶、雑談、感情表現、物語や創作要求、一般的な知識質問、説明要求

コンテキスト考慮のポイント:
1. 前回の会話との関連性を重視
2. ユーザーの使用パターンを参考
3. 曖昧な場合はユーザーの習慣を優先
4. 継続した話題の場合は前回の意図を考慮

重要な判定ルール:
★ auto_search と chat の区別:
- auto_search: ユーザーが明確に最新の外部情報を求めている場合のみ
  ○ "今日の株価は？" "最新のニュース" "営業時間を調べて"
  × "原神について教えて" "面白い話をして" "○○の説明"
  
- chat: 一般的な会話、創作要求、ゲーム・アニメ等の説明、物語など
  ○ "雑談しよう" "面白い話を聞かせて" "原神について知ってる？" "架空の物語で"
  ○ "こんにちは" "どう思う？" "説明して" "教えて"

★ 迷った場合は chat を選択する（ユーザー体験を優先）

以下のJSON形式で回答:
{{
  "intent": "機能名",
  "confidence": 0.0-1.0,
  "parameters": {{
    // 機能別の必要パラメータ
    "location": "地名(weather用)",
    "query": "検索クエリ(search/auto_search用)", 
    "search_type": "general/news/recipe/tech等",
    "notification": {{
      "datetime": "YYYY-MM-DD HH:MM",
      "title": "タイトル",
      "message": "メッセージ",
      "priority": "high/medium/low",
      "repeat": "none/daily/weekly/monthly"
    }},
    "notification_id": "通知ID(削除用)",
    "auto_task": {{
      "task_type": "weather_daily/news_daily/keyword_monitor/usage_report",
      "title": "タスクタイトル",
      "description": "タスク説明",
      "schedule_pattern": "daily/weekly/hourly",
      "schedule_time": "HH:MM形式の実行時刻",
      "parameters": {{"location": "東京", "keywords": ["キーワード1", "キーワード2"]}}
    }},
    "task_id": "タスクID(削除・切替用)",
    "suggestion_type": "timing/grouping/scheduling/optimization(smart_suggestion用)",
    "history_scope": "recent/all/pattern(conversation_history用)",
    "response": "回答テキスト(chat用)"
  }},
  "reasoning": "判定理由（コンテキスト考慮含む）",
  "alternative_intents": ["可能性のある他の意図"],
  "contextual_suggestions": ["文脈に基づく追加提案"]
}}

重要: 
- 対話履歴を積極的に活用
- ユーザーの習慣・パターンを重視
- 曖昧な場合は confidence を低く設定
- コンテキストに基づく提案も含める
- 簡潔に回答してください（効率重視）
"""
            
            # Function-Calling スキーマを追記
            try:
                from core.function_registry import get_registry
                schemas = get_registry().get_schema_list()
                if schemas:
                    prompt += "\n利用可能な関数スキーマ一覧(JSON):\n" + json.dumps(schemas, ensure_ascii=False)
            except Exception as sc_err:
                self.logger.warning(f"schema attach error: {sc_err}")
            
            # Function-Calling ループ (utility 実装版)
            # --------------------
            try:
                from core.function_call_loop import run_function_call_loop
                from core.function_dispatcher import dispatch
                result, tool_results, response = run_function_call_loop(
                    self.model,
                    prompt,
                    dispatcher=dispatch,
                    max_calls=1  # 安全のためまずは 1 回のみ
                )
            except Exception as loop_err:
                self.logger.error(f"Function-Calling loop error: {loop_err}")
                return self._fallback_analysis(text)

            # ループ完了後 result には Gemini 解析結果が入る
            
            # レスポンスの安全性チェック強化
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    # finish_reason 2 = SAFETY （安全性フィルターによるブロック）
                    # finish_reason 3 = RECITATION （著作権などによるブロック）
                    if finish_reason in [2, 3]:
                        self.logger.warning(f"Gemini APIレスポンスがブロックされました (finish_reason: {finish_reason})")
                        return self._fallback_analysis(text)
            
            # 結果の妥当性検証
            if not result.get('intent'):
                return self._fallback_analysis(text)
            
            # 信頼度チェック
            confidence = result.get('confidence', 0.5)
            if confidence < 0.3:
                self.logger.warning(f"低信頼度判定: {confidence}, text: {text}")
                # 代替案があれば使用
                alternatives = result.get('alternative_intents', [])
                if alternatives:
                    result['intent'] = alternatives[0]
            
            # パラメータを適切な形式に変換
            formatted_result = self._format_ai_analysis_result(result, text)
            
            # コンテキスト提案も追加
            if result.get('contextual_suggestions'):
                formatted_result['contextual_suggestions'] = result['contextual_suggestions']
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"統一AI判定エラー: {str(e)}")
            return self._fallback_analysis(text)

    def _record_user_behavior(self, user_id: str, message: str, result: Dict[str, Any]) -> None:
        """ユーザー行動を記録（スマート提案用）"""
        try:
            smart_suggestion = self._get_smart_suggestion()
            if smart_suggestion:
                smart_suggestion.record_user_behavior(
                    user_id=user_id,
                    action_type=result.get('intent', 'unknown'),
                    content=message,
                    context={
                        'confidence': result.get('confidence', 0),
                        'parameters': result.get('parameters', {}),
                        'timestamp': datetime.now(self.jst).isoformat()
                    },
                    success=result.get('confidence', 0) > 0.5
                )
        except Exception as e:
            self.logger.error(f"行動記録エラー: {str(e)}")

    def add_conversation_turn(self, user_id: str, user_message: str, bot_response: str, intent: str, confidence: float) -> None:
        """会話ターンを記録"""
        try:
            conversation_memory = self._get_conversation_memory()
            if conversation_memory:
                conversation_memory.add_conversation_turn(
                    user_id=user_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    intent=intent,
                    confidence=confidence
                )
        except Exception as e:
            self.logger.error(f"会話ターン記録エラー: {str(e)}")

    def get_smart_suggestions(self, user_id: str) -> Dict[str, Any]:
        """スマート提案を取得"""
        try:
            smart_suggestion = self._get_smart_suggestion()
            if smart_suggestion:
                suggestions = smart_suggestion.get_all_suggestions(user_id, limit=5)
                if suggestions:
                    return {
                        'suggestions': [
                            {
                                'title': s.title,
                                'description': s.description,
                                'type': s.suggestion_type,
                                'confidence': s.confidence,
                                'id': s.suggestion_id
                            }
                            for s in suggestions
                        ],
                        'formatted_message': smart_suggestion.format_suggestions_message(suggestions)
                    }
            
            # フォールバック提案
            return {
                'suggestions': [],
                'formatted_message': '現在利用可能な提案はありません。もう少し機能を使ってみてください！'
            }
            
        except Exception as e:
            self.logger.error(f"スマート提案取得エラー: {str(e)}")
            return {
                'suggestions': [],
                'formatted_message': '提案の取得に失敗しました。'
            }

    def get_conversation_summary(self, user_id: str) -> str:
        """対話履歴のサマリーを取得"""
        try:
            conversation_memory = self._get_conversation_memory()
            if conversation_memory:
                analysis = conversation_memory.analyze_conversation_patterns(user_id)
                if 'error' not in analysis:
                    summary_parts = []
                    summary_parts.append("📊 **あなたの利用パターン**")
                    summary_parts.append(f"- 総会話数: {analysis['total_conversations']}回")
                    
                    if analysis['recent_analysis']['most_used_features']:
                        features = list(analysis['recent_analysis']['most_used_features'].keys())[:3]
                        summary_parts.append(f"- よく使う機能: {', '.join(features)}")
                    
                    if analysis['recent_analysis']['active_hours']:
                        hours = sorted(analysis['recent_analysis']['active_hours'].items(), key=lambda x: x[1], reverse=True)[:2]
                        hour_str = ', '.join([f"{h}時" for h, _ in hours])
                        summary_parts.append(f"- よく使う時間: {hour_str}")
                    
                    summary_parts.append(f"- コミュニケーションスタイル: {analysis['communication_style']}")
                    
                    return "\n".join(summary_parts)
                
            return "まだ十分な会話履歴がありません。いろいろな機能を試してみてください！"
            
        except Exception as e:
            self.logger.error(f"会話サマリー取得エラー: {str(e)}")
            return "会話履歴の分析に失敗しました。"

    def get_contextual_suggestions(self, user_id: str, current_message: str) -> List[str]:
        """コンテキストに基づく提案を取得"""
        try:
            conversation_memory = self._get_conversation_memory()
            if conversation_memory:
                return conversation_memory.get_contextual_suggestions(user_id, current_message)
            return []
        except Exception as e:
            self.logger.error(f"コンテキスト提案エラー: {str(e)}")
            return []

    def _extract_location(self, text: str) -> Optional[str]:
        """
        テキストから地名を抽出
        
        Args:
            text (str): 解析するテキスト
            
        Returns:
            Optional[str]: 抽出された地名、見つからない場合はNone
        """
        try:
            prompt = f"""
            以下のテキストから地名を抽出してください：
            {text}
            
            地名のみを返してください。見つからない場合は「なし」と返してください。
            """
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                location = response.text.strip()
                if location and location != "なし":
                    return location
                    
            return None
            
        except Exception as e:
            self.logger.error(f"地名抽出エラー: {str(e)}")
            return None

    def _check_if_notification_intent(self, text: str) -> bool:
        """
        テキストが通知設定の意図かどうかをAIで判定
        
        Args:
            text (str): 判定するテキスト
            
        Returns:
            bool: 通知設定の意図と判定された場合True
        """
        try:
            prompt = f"""
以下のテキストが通知・リマインダー設定の意図かどうかを判定してください。

テキスト: "{text}"

通知設定と判定する条件:
1. 時間指定 + 行動の組み合わせ
   例: 「毎日7時に起きる」「明日の15時に会議」「3時間後に薬を飲む」

2. 定期的なスケジュールの表現
   例: 「毎週月曜に〜」「毎月1日に〜」「毎朝〜」

3. 将来の予定・アクションの表現
   例: 「〜時に〜する」「〜日に〜の予定」

4. リマインダーが必要そうな内容
   例: 服薬、会議、起床、睡眠など

通知設定ではないもの:
- 単純な質問や雑談
- 天気の問い合わせ
- 検索リクエスト
- 過去の出来事の話

true または false のみで回答してください。
"""
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                result = response.text.strip().lower()
                return result == 'true'
                
            return False
            
        except Exception as e:
            self.logger.error(f"通知意図判定エラー: {str(e)}")
            return False

    def _analyze_search_intent(self, text: str) -> Dict[str, Any]:
        """
        テキストから検索が必要かどうかをAIで判定
        
        Args:
            text (str): 解析するテキスト
            
        Returns:
            Dict[str, Any]: 検索意図の解析結果
        """
        try:
            prompt = f"""
以下のテキストが検索を必要とする質問かどうかを判定し、検索が必要な場合は適切な検索クエリを生成してください。

テキスト: "{text}"

検索が必要と判定する条件:
1. 最新の情報が必要な質問
   例: 「今日の株価は？」「最新のニュース」「今年の流行」

2. 専門的な知識や事実確認が必要な質問
   例: 「○○の作り方」「△△という病気について」「歴史上の人物について」

3. 現在の状況やトレンドに関する質問
   例: 「話題の映画は？」「人気のレストラン」「おすすめの商品」

4. 具体的な情報を求める質問
   例: 「○○の営業時間は？」「○○への行き方」「○○の価格」

検索が不要なもの:
- 挨拶や雑談
- 通知設定のリクエスト
- 天気の問い合わせ（専用サービスがある）
- 個人的な感想や意見
- 計算問題

以下のJSON形式で回答してください:
{{
  "needs_search": true または false,
  "search_query": "検索が必要な場合のクエリ（不要な場合は空文字）",
  "search_type": "general または news または shopping または location または recipe または medical または tech"
}}
"""
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                try:
                    # JSONレスポンスをパース
                    import json
                    result = json.loads(response.text.strip())
                    
                    # 必要なキーが存在するかチェック
                    if 'needs_search' in result:
                        return {
                            'needs_search': result.get('needs_search', False),
                            'search_query': result.get('search_query', ''),
                            'search_type': result.get('search_type', 'general')
                        }
                        
                except json.JSONDecodeError:
                    # JSON解析に失敗した場合、テキストから簡単に判定
                    response_text = response.text.strip().lower()
                    if 'true' in response_text:
                        # 簡単な検索クエリを生成
                        simple_query = text.replace('？', '').replace('?', '').strip()
                        return {
                            'needs_search': True,
                            'search_query': simple_query,
                            'search_type': 'general'
                        }
                        
            return {
                'needs_search': False,
                'search_query': '',
                'search_type': 'general'
            }
            
        except Exception as e:
            self.logger.error(f"検索意図判定エラー: {str(e)}")
            return {
                'needs_search': False,
                'search_query': '',
                'search_type': 'general'
            }

    def _check_simple_patterns(self, text: str) -> Optional[Dict[str, Any]]:
        """
        コスト最適化: 簡単なパターンは事前チェック
        """
        text_lower = text.lower()
        
        # 会話履歴・前回の話題を尋ねる簡易パターン（先に判定）
        history_triggers = [
            "前回", "会話履歴", "履歴", "前の話", "何話した", "なにを話した", "なに話した"
        ]
        if any(trigger in text for trigger in history_triggers):
            return {
                "intent": "conversation_history",
                "history_scope": "recent",
                "confidence": 0.9,
            }

        # 完全一致パターン
        exact_matches = {
            "通知一覧": {"intent": "list_notifications"},
            "通知確認": {"intent": "list_notifications"},
            "全通知削除": {"intent": "delete_all_notifications"},
            "すべての通知を削除": {"intent": "delete_all_notifications"},
            "ヘルプ": {"intent": "help"},
            "help": {"intent": "help"},
            "使い方": {"intent": "help"},
        }
        
        if text in exact_matches:
            return exact_matches[text]
        
        # 簡単な挨拶パターン
        greetings = ["こんにちは", "おはよう", "こんばんは", "hi", "hello", "はい", "ありがとう"]
        if text_lower in greetings:
            return {
                "intent": "chat",
                "response": text + "！何かお手伝いできることはありますか？ 😊"
            }
        
        # 雑談・創作要求パターン（検索を避けるため）
        chat_patterns = [
            "雑談", "話", "聞かせて", "教えて", "知ってる", "について", "物語", "創作", 
            "面白い", "楽しい", "どう思う", "意見", "感想", "おすすめ", "普通に"
        ]
        
        # 明確な検索指示でない場合は chat として処理
        is_explicit_search = any(keyword in text for keyword in ["検索して", "調べて", "最新の", "今日の", "現在の"])
        
        if not is_explicit_search and any(pattern in text for pattern in chat_patterns):
            # 天気の定期配信（毎日+時刻）が含まれている場合は create_auto_task を優先
            import re
            has_weather = "天気" in text
            has_daily = any(k in text for k in ["毎日", "毎朝", "毎晩"]) 
            time_match = re.search(r"(\d{1,2})時(?:([0-5]?\d)分)?", text)
            if has_weather and has_daily and time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                schedule_time = f"{hour:02d}:{minute:02d}"
                # 簡易ロケーション抽出（代表都市 + 新潟）
                known_cities = [
                    "新潟", "東京", "大阪", "名古屋", "札幌", "福岡", "京都", "横浜", "仙台", "神戸", "広島",
                    "千葉", "埼玉", "沖縄"
                ]
                location = next((c for c in known_cities if c in text), "東京")
                return {
                    "intent": "create_auto_task",
                    "confidence": 0.9,
                    "parameters": {
                        "auto_task": {
                            "task_type": "weather_daily",
                            "title": f"毎日の{location}天気配信",
                            "description": f"毎日{schedule_time}に{location}の天気情報を配信",
                            "schedule_pattern": "daily",
                            "schedule_time": schedule_time,
                            "parameters": {"location": location}
                        }
                    },
                    "reasoning": "天気 + 毎日 + 時刻 を検出し、天気の定期配信タスクを生成（簡易判定）"
                }
            # それ以外は chat
            return {
                "intent": "chat",
                "confidence": 0.8,
                "reasoning": "雑談・説明要求パターンを検出（簡易判定）"
            }
        
        return None

    def _format_ai_analysis_result(self, ai_result: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """
        AI分析結果を適切な形式に変換
        """
        intent = ai_result.get('intent')
        parameters = ai_result.get('parameters', {})
        
        # 基本の返却構造
        result = {
            "intent": intent,
            "confidence": ai_result.get('confidence', 0.8),
            "reasoning": ai_result.get('reasoning', '')
        }
        
        # 意図別のパラメータ設定
        if intent == 'notification':
            result['notification'] = parameters.get('notification', {})
            
        elif intent == 'weather':
            result['location'] = parameters.get('location', '東京')
            
        elif intent in ['search', 'auto_search']:
            result['query'] = parameters.get('query', original_text)
            if intent == 'auto_search':
                result['original_question'] = original_text
                result['search_type'] = parameters.get('search_type', 'general')
                
        elif intent == 'delete_notification':
            result['notification_id'] = parameters.get('notification_id', '')
            
        elif intent == 'chat':
            result['response'] = parameters.get('response', original_text)
        
        # Function 呼び出し結果
        elif intent == 'function_result':
            # そのまま関数実行結果を格納
            result['result'] = ai_result.get('result')
        
        # 自動実行タスク関連の処理を強化
        elif intent == 'create_auto_task':
            auto_task_data = parameters.get('auto_task', {})
            
            # フォールバック処理: 天気配信パターンの検出
            if not auto_task_data or not all(key in auto_task_data for key in ['task_type', 'title', 'description', 'schedule_pattern', 'schedule_time']):
                # 天気配信パターンの自動補完
                if '天気' in original_text and ('配信' in original_text or '送って' in original_text):
                    # 時間の抽出
                    import re
                    time_match = re.search(r'(\d{1,2})時', original_text)
                    schedule_time = f"{time_match.group(1)}:00" if time_match else "07:00"
                    
                    # 地名の抽出
                    location = '東京'  # デフォルト
                    if '新潟' in original_text:
                        location = '新潟'
                    elif '東京' in original_text:
                        location = '東京'
                    elif '大阪' in original_text:
                        location = '大阪'
                    
                    auto_task_data = {
                        'task_type': 'weather_daily',
                        'title': f'毎日の{location}天気配信',
                        'description': f'毎日{schedule_time}に{location}の天気情報を配信',
                        'schedule_pattern': 'daily',
                        'schedule_time': schedule_time,
                        'parameters': {
                            'location': location
                        }
                    }
                    
                    self.logger.info(f"天気配信タスクの自動補完: {auto_task_data}")
                
                # ニュース配信パターンの自動補完
                elif 'ニュース' in original_text and ('配信' in original_text or '送って' in original_text):
                    import re
                    time_match = re.search(r'(\d{1,2})時', original_text)
                    schedule_time = f"{time_match.group(1)}:00" if time_match else "08:00"
                    
                    auto_task_data = {
                        'task_type': 'news_daily',
                        'title': '毎日のニュース配信',
                        'description': f'毎日{schedule_time}に最新ニュースを配信',
                        'schedule_pattern': 'daily',
                        'schedule_time': schedule_time,
                        'parameters': {
                            'keywords': ['最新ニュース', '話題']
                        }
                    }
                    
                    self.logger.info(f"ニュース配信タスクの自動補完: {auto_task_data}")
            
            result['auto_task'] = auto_task_data
            
        elif intent in ['delete_auto_task', 'toggle_auto_task']:
            result['task_id'] = parameters.get('task_id', '')
            
        elif intent == 'smart_suggestion':
            result['suggestion_type'] = parameters.get('suggestion_type', 'all')
            
        elif intent == 'conversation_history':
            result['history_scope'] = parameters.get('history_scope', 'recent')
        
        return result
    
    def _generate_safe_fallback_response(self, text: str) -> Dict[str, Any]:
        """
        安全性フィルター回避用のフォールバック応答を生成
        """
        # 明確な検索指示の場合のみ検索として処理
        explicit_search_keywords = ["検索して", "調べて", "検索", "最新の", "今日の", "現在の"]
        if any(keyword in text for keyword in explicit_search_keywords):
            return {
                "intent": "search",
                "query": text.replace("について検索", "").replace("を検索", "").replace("検索して", "").strip(),
                "confidence": 0.8,
                "reasoning": "明確な検索指示を検出（フォールバック処理）"
            }
        
        # 一般的な会話として処理（検索に誘導しない）
        return {
            "intent": "chat",
            "response": "申し訳ありません。理解できませんでした。何について話したいですか？",
            "confidence": 0.7,
            "reasoning": "安全性フィルター回避のためのフォールバック応答（chat処理）"
        }

    def _is_search_intent(self, text: str) -> bool:
        """
        簡易的な検索意図判定
        """
        search_keywords = ["検索", "調べ", "について", "とは", "方法", "やり方", "情報"]
        return any(keyword in text for keyword in search_keywords)

    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """
        AI判定失敗時のフォールバック処理（強化版）
        """
        # 通知パターンの詳細判定
        if self._is_notification_pattern(text):
            # 通知設定として処理
            self.logger.info(f"簡単パターンで判定: notification")
            
            # 基本的な通知情報を解析
            notification_data = self._simple_notification_parse(text)
            
            return {
                "intent": "notification",
                "confidence": 0.8,
                "reasoning": "時間指定と行動の組み合わせを検出（フォールバック処理）",
                "notification": notification_data if notification_data else {
                    "title": "リマインダー",
                    "message": text,
                    "datetime": self._extract_simple_time(text)
                }
            }
        
        # 従来のキーワードベース判定
        if text in ["通知一覧", "通知確認"]:
            return {"intent": "list_notifications", "confidence": 0.8}
        elif text in ["全通知削除", "すべての通知を削除"]:
            return {"intent": "delete_all_notifications", "confidence": 0.8}
        elif text in ["ヘルプ", "help", "使い方"]:
            return {"intent": "help", "confidence": 0.8}
        else:
            # デフォルトは chat として処理（検索に誘導しない）
            return {
                "intent": "chat",
                "confidence": 0.6,
                "reasoning": "AI判定失敗時のフォールバック - chat処理を選択",
                "response": "申し訳ありません。理解できませんでした。何について話したいですか？"
            }

    def _extract_simple_time(self, text: str) -> str:
        """
        シンプルな時間抽出（フォールバック用）
        """
        import re
        from datetime import datetime, timedelta
        import pytz
        
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        
        # 時間と分のパターンをチェック
        time_match = re.search(r'(\d{1,2})時(\d{1,2})分', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 過去の時間の場合は翌日に設定
            if target_time < now:
                target_time += timedelta(days=1)
            
            return target_time.strftime('%Y-%m-%d %H:%M')
        
        # 時間のみのパターン
        time_match = re.search(r'(\d{1,2})時', text)
        if time_match:
            hour = int(time_match.group(1))
            target_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # 過去の時間の場合は翌日に設定
            if target_time < now:
                target_time += timedelta(days=1)
            
            return target_time.strftime('%Y-%m-%d %H:%M')
        
        # デフォルトは1時間後
        target_time = now + timedelta(hours=1)
        return target_time.strftime('%Y-%m-%d %H:%M')

    def _is_notification_pattern(self, text: str) -> bool:
        """
        通知パターンの簡易判定（分単位対応）
        """
        # 時間指定パターンをチェック（分単位対応）
        time_patterns = [
            r'毎日.*?時',         # 毎日7時
            r'毎朝',              # 毎朝
            r'毎晩',              # 毎晩
            r'毎週',              # 毎週
            r'毎月',              # 毎月
            r'\d+時\d+分',        # 7時30分
            r'\d+:\d+',           # 7:30
            r'\d+時',             # 7時、15時など
            r'明日.*?時',         # 明日の3時
            r'今日.*?時',         # 今日の6時
            r'\d+時\d+分に',      # 12時40分に
        ]
        
        # 行動パターンをチェック  
        action_patterns = [
            r'起きる',            # 起きる
            r'寝る',              # 寝る
            r'薬',                # 薬を飲む
            r'会議',              # 会議
            r'食事',              # 食事
            r'運動',              # 運動
            r'勉強',              # 勉強
            r'通知',              # 通知して
            r'リマインド',        # リマインドして
            r'知らせ',            # 知らせて
        ]
        
        # 時間と行動が両方含まれている場合は通知パターンと判定
        has_time = any(re.search(pattern, text) for pattern in time_patterns)
        has_action = any(re.search(pattern, text) for pattern in action_patterns)
        
        return has_time and has_action

    def parse_notification_request(self, text: str) -> Optional[Dict[str, Any]]:
        """
        通知要求のテキストを解析して構造化データを返す
        
        Args:
            text (str): ユーザーの入力テキスト
            
        Returns:
            Optional[Dict[str, Any]]: 解析結果、失敗時はNone
        """
        try:
            prompt = f"""
ユーザーの通知設定リクエストを解析してください。

入力テキスト: "{text}"

以下のJSON形式で回答してください:
{{
  "datetime": "YYYY-MM-DD HH:MM", // 通知日時
  "title": "通知タイトル",
  "message": "通知メッセージ",
  "priority": "high/medium/low", // 優先度
  "repeat": "none/daily/weekly/monthly" // 繰り返し
}}

解析できない場合はnullを返してください。
"""
            
            response = self.model.generate_content(prompt)
            
            # レスポンスの安全性チェック
            response_text = None
            try:
                if response and hasattr(response, 'text') and response.text:
                    response_text = response.text
                elif response and hasattr(response, 'candidates') and response.candidates:
                    # candidatesから直接テキストを取得
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            response_text = candidate.content.parts[0].text
            except Exception as e:
                self.logger.warning(f"通知解析レスポンステキスト取得エラー: {str(e)}")
            
            if response_text:
                import json
                result = json.loads(response_text.strip())
                # あいまいな表現への対処: 夕方/朝/夜 などの候補を提示
                # 夕方→ 17:00/18:00, 朝→ 8:00/9:00, 夜→ 20:00/21:00 など
                if result and not result.get('datetime'):
                    candidates = []
                    tl = text
                    if any(k in tl for k in ['夕方','ゆうがた']):
                        candidates.extend(['17:00','18:00'])
                    if any(k in tl for k in ['朝','あさ']):
                        candidates.extend(['08:00','09:00'])
                    if any(k in tl for k in ['夜','よる']):
                        candidates.extend(['20:00','21:00'])
                    if candidates:
                        result['time_candidates'] = candidates
                return result
            else:
                # APIが失敗した場合の簡易パース
                return self._simple_notification_parse(text)
                
        except Exception as e:
            self.logger.error(f"通知解析エラー: {str(e)}")
            # フォールバック: 簡易パース
            return self._simple_notification_parse(text)

    def _simple_notification_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """
        API失敗時の簡易通知解析（分単位対応強化版）
        """
        try:
            from datetime import datetime, timedelta
            import re
            
            # 時刻パターンの解析（分単位対応）
            time_patterns = [
                (r'(\d{1,2})時(\d{1,2})分', lambda h, m: (int(h), int(m))),  # "12時40分"
                (r'(\d{1,2}):(\d{2})', lambda h, m: (int(h), int(m))),       # "12:40"
                (r'(\d{1,2})時', lambda h: (int(h), 0)),                      # "7時"
            ]
            
            # 繰り返しパターンの解析
            repeat_patterns = {
                '毎日': 'daily',
                '毎朝': 'daily',
                '毎晩': 'daily',
                '毎週': 'weekly',
                '毎月': 'monthly',
            }
            
            # 日付パターンの解析
            date_patterns = [
                (r'明日', lambda: datetime.now() + timedelta(days=1)),
                (r'今日', lambda: datetime.now()),
                (r'毎日|毎朝|毎晩', lambda: datetime.now() + timedelta(days=1)),  # 毎日系は翌日から
            ]
            
            hour, minute = None, None
            repeat_type = 'none'
            target_date = datetime.now()
            title = "通知"
            
            # 時刻を解析
            for pattern, parser in time_patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 2:  # 時と分
                        hour, minute = parser(match.group(1), match.group(2))
                    else:  # 時のみ
                        hour, minute = parser(match.group(1))
                    break
            
            # 繰り返しパターンを解析
            for pattern, repeat in repeat_patterns.items():
                if pattern in text:
                    repeat_type = repeat
                    break
            
            # 日付パターンを解析
            for pattern, date_func in date_patterns:
                if re.search(pattern, text):
                    target_date = date_func()
                    break
            
            # 時刻が見つからない場合はデフォルト処理
            if hour is None:
                # 特定パターンのマッチング
                if "毎日7時に起きる" in text:
                    hour, minute = 7, 0
                    repeat_type = 'daily'
                    target_date = datetime.now() + timedelta(days=1)
                    title = "起床"
                elif "7時に起きる" in text:
                    hour, minute = 7, 0
                    title = "起床"
                else:
                    return None
            
            # 通知時刻を設定
            if hour is not None:
                target_time = target_date.replace(
                    hour=hour, 
                    minute=minute if minute is not None else 0, 
                    second=0, 
                    microsecond=0
                )
                
                # 過去の時刻の場合は翌日に設定
                if target_time <= datetime.now():
                    target_time += timedelta(days=1)
                
                # タイトルを推定（より詳細な判定）
                if "起きる" in text:
                    title = "起床時間"
                elif "会議" in text:
                    title = "会議リマインダー"
                elif "課題" in text:
                    title = "課題リマインダー"
                elif "薬" in text:
                    title = "服薬リマインダー"
                elif "食事" in text:
                    title = "食事時間"
                elif "運動" in text:
                    title = "運動時間"
                elif "勉強" in text:
                    title = "勉強時間"
                else:
                    # 時間から推定
                    if minute and minute > 0:
                        title = f"{hour}時{minute}分の通知"
                    else:
                        title = f"{hour}時の通知"
                
                return {
                    "datetime": target_time.strftime("%Y-%m-%d %H:%M"),
                    "title": title,
                    "message": text,
                    "priority": "medium",
                    "repeat": repeat_type
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"簡易通知解析エラー: {str(e)}")
            return None