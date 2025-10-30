"""Function Dispatcher
Gemini から返ってきた function_call JSON を実行するヘルパ。
"""
from typing import Any, Dict
from core.function_registry import get_registry


def dispatch(function_call: Dict[str, Any]) -> Any:
    """登録済み関数を実行し結果を返す。

    Args:
        function_call: {"name": str, "arguments": {...}}
    """
    name = function_call.get("name")
    arguments = function_call.get("arguments", {})
    registry = get_registry()
    func = registry.get_callable(name)
    if not func:
        raise ValueError(f"Function '{name}' is not registered")
    # 型安全性は呼び出し側で担保 / Python が自動変換
    return func(**arguments) 