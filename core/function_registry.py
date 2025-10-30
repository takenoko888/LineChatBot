"""Function Registry
Gemini Function-Calling 用の関数スキーマを一元管理するモジュール。
新しいサービス関数を登録すると自動で JSON スキーマに変換され、Gemini へ渡すためのリストを取得できる。
"""
from __future__ import annotations
from typing import Callable, Dict, Any, List
import inspect
import json


class FunctionRegistry:
    """シングルトン形式の関数レジストリ"""
    _instance: "FunctionRegistry" | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._func_map: Dict[str, Callable[..., Any]] = {}
            cls._instance._schemas: Dict[str, Dict[str, Any]] = {}
        return cls._instance

    # ---------------------------------------------------------------------
    # 登録 API
    # ---------------------------------------------------------------------
    def register(self, func: Callable[..., Any], name: str | None = None, description: str | None = None):
        """関数をレジストリへ登録し JSON スキーマを生成する"""
        func_name = name or func.__name__
        if func_name in self._func_map:
            # 既存定義を保持して重複登録は無視 (テスト間の競合を避ける)
            return

        self._func_map[func_name] = func
        self._schemas[func_name] = self._build_schema(func, func_name, description)

    # ------------------------------------------------------------------
    def get_schema_list(self) -> List[Dict[str, Any]]:
        """Gemini に渡す schema 配列を返す"""
        return list(self._schemas.values())

    def get_callable(self, name: str) -> Callable[..., Any] | None:
        return self._func_map.get(name)

    # ------------------------------------------------------------------
    def _build_schema(self, func: Callable[..., Any], name: str, description: str | None) -> Dict[str, Any]:
        sig = inspect.signature(func)
        props: Dict[str, Any] = {}
        required: List[str] = []
        for param in sig.parameters.values():
            # 型ヒント→JSON Type の単純マッピング
            json_type = "string"
            if param.annotation in (int, float):
                json_type = "number"
            elif param.annotation is bool:
                json_type = "boolean"
            props[param.name] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param.name)
        schema = {
            "name": name,
            "description": description or name,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        }
        return schema


# ------------------------------------------------------------------
# デコレータ ヘルパー
# ------------------------------------------------------------------
_registry = FunctionRegistry()

def register_function(name: str | None = None, description: str | None = None):
    """デコレータで関数を登録する"""
    def decorator(func):
        _registry.register(func, name=name, description=description)
        return func
    return decorator

# Expose singleton
get_registry = lambda: _registry 