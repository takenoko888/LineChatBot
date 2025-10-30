"""
Date utilities implementation
"""
from typing import Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
import re
import pytz
import logging

class DateUtils:
    """日付処理ユーティリティ"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.jst = pytz.timezone('Asia/Tokyo')

    def parse_natural_datetime(self, text: str) -> Tuple[Optional[datetime], Dict[str, str]]:
        """
        自然言語の日時表現を解析
        
        Args:
            text (str): 解析する文字列
            
        Returns:
            Tuple[Optional[datetime], Dict[str, str]]: (解析された日時, 設定情報)
        """
        try:
            now = datetime.now(self.jst)
            settings = {'repeat_type': 'none'}
            
            # 繰り返し設定の検出
            if '毎日' in text:
                settings['repeat_type'] = 'daily'
            elif '毎週' in text:
                settings['repeat_type'] = 'weekly'
            elif '毎月' in text:
                settings['repeat_type'] = 'monthly'

            # 相対的な日付表現
            if '明日' in text:
                target_date = now.date() + timedelta(days=1)
            elif '明後日' in text:
                target_date = now.date() + timedelta(days=2)
            elif '昨日' in text:
                target_date = now.date() - timedelta(days=1)
            elif '今日' in text:
                target_date = now.date()
            else:
                # 絶対的な日付表現を検索
                date_match = re.search(
                    r'(\d{1,2})月(\d{1,2})日',
                    text
                )
                if date_match:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = now.year
                    # 指定された日付が過去の場合、来年の日付として解釈
                    target_date = datetime(year, month, day).date()
                    if target_date < now.date():
                        target_date = datetime(year + 1, month, day).date()
                else:
                    target_date = now.date()

            # 時刻表現の検索
            time_match = re.search(
                r'(\d{1,2})(?:時|:)(\d{1,2})?(?:分)?',
                text
            )
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or '0')
                target_time = datetime.combine(
                    target_date,
                    datetime.min.time().replace(hour=hour, minute=minute)
                )
            else:
                # 時刻が指定されていない場合、現在時刻を使用
                target_time = datetime.combine(
                    target_date,
                    now.time()
                )

            # 相対的な時間表現
            hours_match = re.search(r'(\d+)時間(後|前)', text)
            if hours_match:
                hours = int(hours_match.group(1))
                if '前' in hours_match.group(2):
                    target_time -= timedelta(hours=hours)
                else:
                    target_time += timedelta(hours=hours)

            minutes_match = re.search(r'(\d+)分(後|前)', text)
            if minutes_match:
                minutes = int(minutes_match.group(1))
                if '前' in minutes_match.group(2):
                    target_time -= timedelta(minutes=minutes)
                else:
                    target_time += timedelta(minutes=minutes)

            # JSTタイムゾーンを設定
            target_time = self.jst.localize(target_time)

            # 日時が過去の場合は無効とする
            if target_time < now:
                return None, settings

            return target_time, settings

        except Exception as e:
            self.logger.error(f"日時解析エラー: {str(e)}")
            return None, settings

    def format_datetime(
        self, 
        dt: datetime,
        format_type: str = 'default'
    ) -> str:
        """
        日時を指定された形式で整形
        
        Args:
            dt (datetime): 整形する日時
            format_type (str): 整形タイプ
            
        Returns:
            str: 整形された日時文字列
        """
        try:
            if format_type == 'short':
                return dt.strftime('%m/%d %H:%M')
            elif format_type == 'long':
                return dt.strftime('%Y年%m月%d日 %H時%M分')
            elif format_type == 'date_only':
                return dt.strftime('%Y年%m月%d日')
            elif format_type == 'time_only':
                return dt.strftime('%H時%M分')
            else:
                return dt.strftime('%Y/%m/%d %H:%M')
        except Exception as e:
            self.logger.error(f"日時整形エラー: {str(e)}")
            return str(dt)

    def get_next_occurrence(
        self,
        dt: datetime,
        repeat_type: str
    ) -> Optional[datetime]:
        """
        次回の発生日時を計算
        
        Args:
            dt (datetime): 基準日時
            repeat_type (str): 繰り返しタイプ
            
        Returns:
            Optional[datetime]: 次回の日時
        """
        try:
            if repeat_type == 'daily':
                return dt + timedelta(days=1)
            elif repeat_type == 'weekly':
                return dt + timedelta(weeks=1)
            elif repeat_type == 'monthly':
                # 月末の処理を考慮
                year = dt.year
                month = dt.month + 1
                if month > 12:
                    year += 1
                    month = 1
                try:
                    return dt.replace(year=year, month=month)
                except ValueError:
                    # 月末が存在しない場合（例：1/31 → 2/28）
                    if month == 2:
                        return dt.replace(year=year, month=month, day=28)
                    else:
                        return dt.replace(year=year, month=month, day=30)
            else:
                return None
        except Exception as e:
            self.logger.error(f"次回発生日時計算エラー: {str(e)}")
            return None

    def is_valid_datetime(self, dt: datetime) -> bool:
        """
        日時が有効か検証
        
        Args:
            dt (datetime): 検証する日時
            
        Returns:
            bool: 有効な場合True
        """
        try:
            now = datetime.now(self.jst)
            
            # 過去の日時は無効
            if dt < now:
                return False
                
            # 1年以上先の日時は無効
            if dt > now + timedelta(days=365):
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"日時検証エラー: {str(e)}")
            return False

    def get_relative_time_description(self, dt: datetime) -> str:
        """
        相対的な時間表現を生成
        
        Args:
            dt (datetime): 対象日時
            
        Returns:
            str: 相対的な時間表現
        """
        try:
            now = datetime.now(self.jst)
            diff = dt - now
            
            if diff.days < 0:
                return '過去'
            elif diff.days == 0:
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                if hours > 0:
                    return f'{hours}時間後'
                else:
                    return f'{minutes}分後'
            elif diff.days == 1:
                return '明日'
            elif diff.days == 2:
                return '明後日'
            elif diff.days < 7:
                return f'{diff.days}日後'
            elif diff.days < 30:
                weeks = diff.days // 7
                return f'{weeks}週間後'
            elif diff.days < 365:
                months = diff.days // 30
                return f'{months}ヶ月後'
            else:
                years = diff.days // 365
                return f'{years}年後'
                
        except Exception as e:
            self.logger.error(f"相対時間表現生成エラー: {str(e)}")
            return '不明'