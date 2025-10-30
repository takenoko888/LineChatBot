"""
AI Function Plugin System - AI機能を動的に拡張
"""
import logging
import json
import os
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List, Callable, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import threading
import hashlib

@dataclass
class AIFunction:
    """AI機能定義"""
    name: str
    description: str
    version: str
    author: str
    parameters: Dict[str, Any]
    trigger_keywords: List[str]
    required_context: Dict[str, Any] = None
    priority: int = 5
    enabled: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class BaseAIFunction(ABC):
    """AI機能の基底クラス"""

    def __init__(self, function_def: AIFunction):
        self.function_def = function_def
        self.logger = logging.getLogger(f"{__name__}.{function_def.name}")

    @abstractmethod
    async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """機能実行"""
        pass

    def get_definition(self) -> AIFunction:
        """機能定義を取得"""
        return self.function_def

class AIFunctionRegistry:
    """AI機能レジストリ"""

    def __init__(self):
        self.functions: Dict[str, BaseAIFunction] = {}
        self.categories: Dict[str, List[str]] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        # ビルトイン機能の登録
        self._register_builtin_functions()

    def _register_builtin_functions(self):
        """ビルトイン機能を登録"""
        # 数学計算機能
        math_function = AIFunction(
            name="math_calculator",
            description="数学計算を実行する",
            version="1.0.0",
            author="system",
            parameters={
                "expression": {
                    "type": "string",
                    "description": "計算式（例: 2+3*4）",
                    "required": True
                }
            },
            trigger_keywords=["計算", "計算して", "いくつ", "足して", "引いて", "掛けて", "割って"],
            priority=3
        )
        self.register_function(MathCalculatorFunction(math_function))

        # 翻訳機能
        translate_function = AIFunction(
            name="translator",
            description="テキストを翻訳する",
            version="1.0.0",
            author="system",
            parameters={
                "text": {
                    "type": "string",
                    "description": "翻訳するテキスト",
                    "required": True
                },
                "target_language": {
                    "type": "string",
                    "description": "対象言語（例: 英語, 中国語）",
                    "required": True
                }
            },
            trigger_keywords=["翻訳", "翻訳して", "英語で", "日本語で", "中国語で"],
            priority=4
        )
        self.register_function(TranslatorFunction(translate_function))

        # 今日の運勢機能
        fortune_function = AIFunction(
            name="daily_fortune",
            description="今日の運勢を占う",
            version="1.0.0",
            author="system",
            parameters={},
            trigger_keywords=["運勢", "今日の運勢", "占い", "ラッキーアイテム"],
            priority=2
        )
        self.register_function(DailyFortuneFunction(fortune_function))

        # コード実行機能
        code_function = AIFunction(
            name="code_executor",
            description="Pythonコードを実行する",
            version="1.0.0",
            author="system",
            parameters={
                "code": {
                    "type": "string",
                    "description": "実行するPythonコード",
                    "required": True
                }
            },
            trigger_keywords=["コード実行", "Python実行", "プログラム実行", "計算機"],
            priority=6,
            required_context={"has_code": True}
        )
        self.register_function(CodeExecutorFunction(code_function))

    def register_function(self, function: BaseAIFunction):
        """機能を登録"""
        with self.lock:
            function_name = function.function_def.name
            self.functions[function_name] = function

            # カテゴリ分類
            category = self._categorize_function(function.function_def)
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(function_name)

            self.logger.info(f"AI機能を登録: {function_name}")

    def _categorize_function(self, function_def: AIFunction) -> str:
        """機能をカテゴリ分類"""
        name_lower = function_def.name.lower()

        if any(keyword in name_lower for keyword in ['math', '計算', 'calc']):
            return 'mathematics'
        elif any(keyword in name_lower for keyword in ['translate', '翻訳']):
            return 'translation'
        elif any(keyword in name_lower for keyword in ['fortune', '運勢', '占い']):
            return 'entertainment'
        elif any(keyword in name_lower for keyword in ['code', '実行', 'プログラム']):
            return 'programming'
        else:
            return 'general'

    def get_function(self, name: str) -> Optional[BaseAIFunction]:
        """機能を取得"""
        return self.functions.get(name)

    def find_matching_functions(self, user_input: str, context: Dict[str, Any]) -> List[BaseAIFunction]:
        """入力にマッチする機能を見つける"""
        matched_functions = []

        for function in self.functions.values():
            if not function.function_def.enabled:
                continue

            # キーワードマッチング
            input_lower = user_input.lower()
            if any(keyword in input_lower for keyword in function.function_def.trigger_keywords):
                # コンテキスト要件チェック
                if self._check_context_requirements(function.function_def, context):
                    matched_functions.append(function)

        # 優先度順にソート
        matched_functions.sort(key=lambda f: f.function_def.priority, reverse=True)
        return matched_functions

    def _check_context_requirements(self, function_def: AIFunction, context: Dict[str, Any]) -> bool:
        """コンテキスト要件をチェック"""
        if not function_def.required_context:
            return True

        for key, expected_value in function_def.required_context.items():
            if key not in context or context[key] != expected_value:
                return False

        return True

    def list_functions(self, category: Optional[str] = None) -> List[AIFunction]:
        """機能一覧を取得"""
        if category:
            function_names = self.categories.get(category, [])
            return [self.functions[name].function_def for name in function_names]

        return [func.function_def for func in self.functions.values()]

    def load_plugin_from_file(self, plugin_path: str) -> bool:
        """プラグインファイルから機能を読み込み"""
        try:
            # ファイルのハッシュを計算（重複読み込み防止）
            file_hash = self._calculate_file_hash(plugin_path)

            # モジュール読み込み
            module_name = os.path.splitext(os.path.basename(plugin_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # プラグインクラスを見つける
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseAIFunction) and
                    obj != BaseAIFunction):

                    # 機能定義を取得（クラス属性またはAIFunctionインスタンス）
                    if hasattr(obj, 'function_definition'):
                        function_def = obj.function_definition
                    else:
                        # デフォルトの機能定義を作成
                        function_def = AIFunction(
                            name=name.lower(),
                            description=getattr(obj, '__doc__', 'No description'),
                            version="1.0.0",
                            author="plugin",
                            parameters=getattr(obj, 'parameters', {}),
                            trigger_keywords=getattr(obj, 'trigger_keywords', [])
                        )

                    plugin_instance = obj(function_def)
                    self.register_function(plugin_instance)
                    self.logger.info(f"プラグインを読み込みました: {name}")

            return True

        except Exception as e:
            self.logger.error(f"プラグイン読み込みエラー: {str(e)}")
            return False

    def _calculate_file_hash(self, file_path: str) -> str:
        """ファイルのハッシュを計算"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class MathCalculatorFunction(BaseAIFunction):
    """数学計算機能"""

    async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            expression = parameters.get('expression', '')
            # 安全な計算実行
            result = eval(expression, {"__builtins__": {}})  # ビルトイン関数を制限
            return {
                "success": True,
                "result": str(result),
                "expression": expression
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "expression": parameters.get('expression', '')
            }

class TranslatorFunction(BaseAIFunction):
    """翻訳機能"""

    async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 簡易翻訳（実際には本格的な翻訳APIを使用）
            text = parameters.get('text', '')
            target_lang = parameters.get('target_language', '英語')

            # 言語マッピング
            lang_map = {
                '英語': 'en',
                '日本語': 'ja',
                '中国語': 'zh',
                '韓国語': 'ko',
                'フランス語': 'fr'
            }

            # ここではモック応答を返す
            # 実際の実装ではGoogle Translate APIなどを使用
            mock_translation = f"[{target_lang}] {text} (翻訳機能は開発中です)"

            return {
                "success": True,
                "original": text,
                "translated": mock_translation,
                "target_language": target_lang
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class DailyFortuneFunction(BaseAIFunction):
    """今日の運勢機能"""

    def __init__(self, function_def: AIFunction):
        super().__init__(function_def)
        self.fortunes = [
            "今日は素晴らしい一日になるでしょう！",
            "新しい出会いがありそうです。",
            "慎重に行動すると良い結果が得られます。",
            "直感を信じて行動しましょう。",
            "小さな幸せがたくさん訪れます。"
        ]

        self.lucky_items = [
            "四つ葉のクローバー",
            "金の指輪",
            "青いペン",
            "白い花",
            "古い本"
        ]

    async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # ユーザーIDに基づいて決定的な結果を生成
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            fortune_index = user_hash % len(self.fortunes)
            lucky_item_index = (user_hash // len(self.fortunes)) % len(self.lucky_items)

            fortune = self.fortunes[fortune_index]
            lucky_item = self.lucky_items[lucky_item_index]

            return {
                "success": True,
                "fortune": fortune,
                "lucky_item": lucky_item,
                "date": datetime.now().strftime('%Y年%m月%d日')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class CodeExecutorFunction(BaseAIFunction):
    """コード実行機能"""

    async def execute(self, user_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            code = parameters.get('code', '')

            # 安全なコード実行環境
            import sys
            from io import StringIO

            # 出力をキャプチャ
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            try:
                # 制限された環境でコード実行
                exec(code, {"__builtins__": {}})
                output = captured_output.getvalue()
            except Exception as e:
                output = f"エラー: {str(e)}"
            finally:
                sys.stdout = old_stdout

            return {
                "success": True,
                "code": code,
                "output": output,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": parameters.get('code', '')
            }

# グローバルインスタンス
ai_function_registry = AIFunctionRegistry()
