"""
Notification data model
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging
import os
import pytz
from dataclasses import dataclass, asdict
from threading import Lock
from ..gemini_service import GeminiService
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from datetime import time

@dataclass
class Notification:
    """通知データモデル"""
    id: str
    user_id: str
    title: str
    message: str
    datetime: str
    priority: str = 'medium'
    repeat: str = 'none'
    completed: bool = False
    created_at: str = None
    updated_at: str = None
    template_id: str = None
    is_template: bool = False
    acknowledged: bool = False
    history: List[Dict[str, Any]] = None
    context_metadata: Dict[str, Any] = None

    def __post_init__(self):
        """データモデルの初期化後処理"""
        if not self.created_at:
            self.created_at = datetime.now(pytz.UTC).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.context_metadata:
            self.context_metadata = {
                "related_keywords": [],
                "conversation_context": {},
                "optimization_history": []
            }

    def add_optimization_record(self, optimization_data: dict):
        """
        最適化実施記録を追加
        """
        self.context_metadata["optimization_history"].append({
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "details": optimization_data
        })

    def to_dict(self) -> Dict[str, Any]:
        """通知をディクショナリに変換"""
        return asdict(self)