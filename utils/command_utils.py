"""
Command parsing utilities
"""
from typing import Dict, List, Optional, Tuple, Any
import re
import logging

class CommandUtils:
    """コマンドパースユーティリティ"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)

    def parse_command(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        テキストからコマンドとパラメータを抽出
        
        Args:
            text (str): パースするテキスト
            
        Returns:
            Tuple[str, Dict[str, Any]]: (コマンドタイプ, パラメータ)
        """
        try:
            text = text.strip()
            command_type = self._determine_command_type(text)
            params = self._extract_parameters(text, command_type)
            return command_type, params
        except Exception as e:
            self.logger.error(f"コマンドパースエラー: {str(e)}")
            return 'unknown', {}

    def _determine_command_type(self, text: str) -> str:
        """
        コマンドタイプを判定
        
        Args:
            text (str): 判定するテキスト
            
        Returns:
            str: コマンドタイプ
        """
        # 通知関連コマンド
        if text == '通知機能':
            return 'notification_menu'
        elif text == '通知一覧':
            return 'notification_list'
        elif '通知検索' in text:
            return 'notification_search'
        elif '通知編集' in text:
            return 'notification_edit'
        elif '通知削除' in text:
            return 'notification_delete'
        elif '通知' in text:
            return 'notification_set'
            
        # 天気関連コマンド
        elif '天気予報' in text:
            return 'weather_forecast'
        elif '天気' in text:
            return 'weather_current'
            
        # 検索関連コマンド
        elif any(keyword in text for keyword in ['検索', '調べて']):
            return 'search'
            
        # ヘルプ関連コマンド
        elif text in ['ヘルプ', '使い方', '機能']:
            return 'help'
            
        return 'chat'

    def _extract_parameters(
        self,
        text: str,
        command_type: str
    ) -> Dict[str, Any]:
        """
        テキストからパラメータを抽出
        
        Args:
            text (str): パース対象テキスト
            command_type (str): コマンドタイプ
            
        Returns:
            Dict[str, Any]: 抽出されたパラメータ
        """
        params = {}
        
        if command_type == 'notification_search':
            params.update(self._parse_search_options(text))
            
        elif command_type == 'notification_edit':
            params.update(self._parse_edit_options(text))
            
        elif command_type == 'notification_set':
            params.update(self._parse_notification_options(text))
            
        elif command_type in ['weather_current', 'weather_forecast']:
            params.update(self._parse_weather_options(text))
            
        elif command_type == 'search':
            params.update(self._parse_search_query(text))
            
        return params

    def _parse_search_options(self, text: str) -> Dict[str, Any]:
        """検索オプションをパース"""
        options = {}
        
        # 日付範囲
        if '今日' in text:
            options['date_range'] = 'today'
        elif '今週' in text:
            options['date_range'] = 'week'
        elif '今月' in text:
            options['date_range'] = 'month'
            
        # 優先度
        if '重要' in text:
            options['priority'] = 'high'
        elif '普通' in text:
            options['priority'] = 'medium'
        elif '低' in text:
            options['priority'] = 'low'
            
        # ソート順
        if '新しい順' in text:
            options['sort'] = 'newest'
        elif '古い順' in text:
            options['sort'] = 'oldest'
            
        return options

    def _parse_edit_options(self, text: str) -> Dict[str, Any]:
        """編集オプションをパース"""
        options = {}
        
        # タイトルの抽出
        title_match = re.search(r'「(.+?)」を', text)
        if title_match:
            options['title'] = title_match.group(1)
            
        # 時刻の変更
        time_match = re.search(
            r'(\d{1,2})時(\d{1,2})?分?に変更',
            text
        )
        if time_match:
            options['hour'] = int(time_match.group(1))
            options['minute'] = int(time_match.group(2) or '0')
            
        # 優先度の変更
        if '重要に変更' in text:
            options['priority'] = 'high'
        elif '普通に変更' in text:
            options['priority'] = 'medium'
        elif '低に変更' in text:
            options['priority'] = 'low'
            
        # 繰り返し設定の変更
        if '毎日に変更' in text:
            options['repeat'] = 'daily'
        elif '毎週に変更' in text:
            options['repeat'] = 'weekly'
        elif '毎月に変更' in text:
            options['repeat'] = 'monthly'
            
        return options

    def _parse_notification_options(self, text: str) -> Dict[str, Any]:
        """通知オプションをパース"""
        options = {}
        
        # 優先度の検出
        if '重要' in text:
            options['priority'] = 'high'
        elif '普通' in text:
            options['priority'] = 'medium'
        elif '低' in text:
            options['priority'] = 'low'
            
        # 繰り返し設定の検出
        if '毎日' in text:
            options['repeat'] = 'daily'
        elif '毎週' in text:
            options['repeat'] = 'weekly'
        elif '毎月' in text:
            options['repeat'] = 'monthly'
            
        # タイトルの抽出
        title_match = re.search(r'「(.+?)」の通知', text)
        if title_match:
            options['title'] = title_match.group(1)
            
        return options

    def _parse_weather_options(self, text: str) -> Dict[str, Any]:
        """天気オプションをパース"""
        options = {}
        
        # 場所の抽出
        location_match = re.search(r'(.+?)の天気', text)
        if location_match:
            options['location'] = location_match.group(1)
            
        # 予報期間の検出
        if '週間' in text:
            options['period'] = 'week'
        elif '明日' in text:
            options['period'] = 'tomorrow'
        else:
            options['period'] = 'today'
            
        return options

    def _parse_search_query(self, text: str) -> Dict[str, Any]:
        """検索クエリをパース"""
        options = {}
        
        # 検索キーワードを除去してクエリを抽出
        query = text
        for keyword in ['検索', '調べて', 'について']:
            query = query.replace(keyword, '')
        
        options['query'] = query.strip()
        
        # 検索タイプの判定
        if 'ニュース' in text:
            options['type'] = 'news'
        elif '画像' in text:
            options['type'] = 'image'
        else:
            options['type'] = 'web'
            
        return options

    def format_command_help(self, command_type: str) -> str:
        """
        コマンドのヘルプメッセージを生成
        
        Args:
            command_type (str): コマンドタイプ
            
        Returns:
            str: ヘルプメッセージ
        """
        help_messages = {
            'notification_search': (
                "📝 通知検索の使い方:\n\n"
                "以下のようなオプションを組み合わせて検索できます：\n"
                "・時期: 今日、今週、今月\n"
                "・優先度: 重要、普通、低\n"
                "・順序: 新しい順、古い順\n\n"
                "例: 「今週の重要な通知を検索」"
            ),
            'notification_edit': (
                "✏️ 通知編集の使い方:\n\n"
                "「通知タイトル」を指定して、以下の項目を変更できます：\n"
                "・時刻: ○時○分に変更\n"
                "・優先度: 重要/普通/低に変更\n"
                "・繰り返し: 毎日/毎週/毎月に変更\n\n"
                "例: 「買い物」を15時に変更して重要に設定"
            ),
            'weather': (
                "🌤 天気機能の使い方:\n\n"
                "場所を指定して天気情報を取得できます：\n"
                "・現在の天気: 「東京の天気」\n"
                "・天気予報: 「東京の天気予報」\n"
                "・週間天気: 「東京の週間天気」"
            ),
            'search': (
                "🔍 検索機能の使い方:\n\n"
                "以下のような検索が可能です：\n"
                "・ウェブ検索: 「キーワード 検索」\n"
                "・ニュース検索: 「キーワード ニュース検索」\n"
                "・画像検索: 「キーワード 画像検索」"
            )
        }
        
        return help_messages.get(
            command_type,
            "そのコマンドのヘルプは準備されていません。"
        )