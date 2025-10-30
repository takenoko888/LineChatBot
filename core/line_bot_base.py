"""
Base class for LINE Bot implementation
"""
from typing import Optional, Dict, Any
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
import os
import logging

class LineBotBase:
    """LINEボットの基本機能を提供するベースクラス"""

    def __init__(self):
        """ベースクラスの初期化"""
        self.logger = logging.getLogger(__name__)
        
        # LINE API設定
        self.channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        self.channel_access_token = os.getenv('LINE_ACCESS_TOKEN')
        
        if not self.channel_secret or not self.channel_access_token:
            raise ValueError("LINE credentials are not properly configured")
            
        self.line_bot_api = LineBotApi(self.channel_access_token)
        self.handler = WebhookHandler(self.channel_secret)

    def send_message(
        self, 
        user_id: str, 
        text: str, 
        quick_reply: Optional[QuickReply] = None
    ) -> bool:
        """
        ユーザーにメッセージを送信
        
        Args:
            user_id (str): 送信先のユーザーID
            text (str): 送信するテキスト
            quick_reply (Optional[QuickReply]): クイックリプライオプション
            
        Returns:
            bool: 送信成功時True、失敗時False
        """
        try:
            message = TextSendMessage(text=text, quick_reply=quick_reply)
            self.line_bot_api.push_message(user_id, message)
            return True
        except Exception as e:
            self.logger.error(f"メッセージ送信エラー: {str(e)}")
            return False

    def reply_message(
        self, 
        reply_token: str, 
        text: str, 
        quick_reply_type: Optional[str] = None
    ) -> bool:
        """
        メッセージに返信
        
        Args:
            reply_token (str): リプライトークン
            text (str): 送信するテキスト
            quick_reply_type (Optional[str]): クイックリプライのタイプ
            
        Returns:
            bool: 送信成功時True、失敗時False
        """
        try:
            # text が dict または list の場合は Flex Message として送信
            if isinstance(text, (dict, list)):
                try:
                    message = FlexSendMessage(
                        alt_text="情報を表示します",
                        contents=text,
                        quick_reply=self.get_quick_reply_items(quick_reply_type)
                    )
                except Exception as e:
                    self.logger.error(f"FlexSendMessage 生成エラー: {str(e)}")
                    message = TextSendMessage(
                        text=str(text)[:1000],  # フォールバックとして文字列化
                        quick_reply=self.get_quick_reply_items(quick_reply_type)
                    )
            else:
                message = TextSendMessage(
                    text=text,
                    quick_reply=self.get_quick_reply_items(quick_reply_type)
                )
            self.line_bot_api.reply_message(reply_token, message)
            return True
        except Exception as e:
            self.logger.error(f"返信エラー: {str(e)}")
            return False

    def get_quick_reply_items(self, quick_reply_type: Optional[str] = None) -> Optional[QuickReply]:
        """
        クイックリプライの項目を生成
        
        Args:
            quick_reply_type (Optional[str]): クイックリプライのタイプ
            
        Returns:
            Optional[QuickReply]: クイックリプライオブジェクト
        """
        items = []
        
        # 通知一覧表示時のクイックリプライ
        if quick_reply_type == 'notification_list':
            items = [
                QuickReplyButton(
                    action=MessageAction(label="🔔 新しい通知作成", text="明日の9時に起きる")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🔄 一覧を更新", text="通知一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🗑️ 全削除", text="全通知削除")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🌤️ 天気", text="今日の天気")
                ),
                QuickReplyButton(
                    action=MessageAction(label="❓ ヘルプ", text="ヘルプ")
                )
            ]
        # 通知削除・操作時のクイックリプライ
        elif quick_reply_type == 'notification_action':
            items = [
                QuickReplyButton(
                    action=MessageAction(label="📝 通知一覧", text="通知一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🔔 新しい通知", text="毎日7時に起きる")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🌤️ 今日の天気", text="今日の天気")
                ),
                QuickReplyButton(
                    action=MessageAction(label="❓ ヘルプ", text="ヘルプ")
                )
            ]
        # 通知関連のクイックリプライ
        elif quick_reply_type == 'notification':
            items = [
                QuickReplyButton(
                    action=MessageAction(label="📝 通知一覧", text="通知一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🔔 新しい通知", text="毎日7時に起きる")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🗑️ 全削除", text="全通知削除")
                ),
                QuickReplyButton(
                    action=MessageAction(label="❓ ヘルプ", text="ヘルプ")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🌤️ 天気", text="今日の天気")
                )
            ]
        # 自動実行タスク用のクイックリプライ
        elif quick_reply_type == 'auto_task':
            items = [
                QuickReplyButton(
                    action=MessageAction(label="➕ 天気の自動配信", text="毎日7時に東京の天気を教えて")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🤖 自動実行一覧", text="自動実行一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="📋 タスク一覧(テキスト)", text="タスク一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="📝 通知一覧", text="通知一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="❓ ヘルプ", text="ヘルプ")
                )
            ]
        else:
            # デフォルトのクイックリプライ
            items = [
                QuickReplyButton(
                    action=MessageAction(label="🔔 通知設定", text="毎日7時に起きる")
                ),
                QuickReplyButton(
                    action=MessageAction(label="📝 通知一覧", text="通知一覧")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🌤️ 今日の天気", text="今日の天気")
                ),
                QuickReplyButton(
                    action=MessageAction(label="🔍 検索", text="Pythonについて教えて")
                ),
                QuickReplyButton(
                    action=MessageAction(label="❓ ヘルプ", text="ヘルプ")
                )
            ]
        
        return QuickReply(items=items) if items else None

    def handle_webhook(self, body: str, signature: str) -> bool:
        """
        Webhookリクエストを処理
        
        Args:
            body (str): リクエストボディ
            signature (str): X-Line-Signature
            
        Returns:
            bool: 処理成功時True、失敗時False
        """
        try:
            self.handler.handle(body, signature)
            return True
        except Exception as e:
            self.logger.error(f"Webhookエラー: {str(e)}")
            return False

    def validate_signature(self, body: str, signature: str) -> bool:
        """
        署名を検証
        
        Args:
            body (str): リクエストボディ
            signature (str): X-Line-Signature
            
        Returns:
            bool: 検証成功時True、失敗時False
        """
        try:
            self.handler.handle(body, signature)
            return True
        except Exception:
            return False