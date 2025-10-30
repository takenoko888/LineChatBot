from __future__ import annotations

"""Function-Calling Loop Utility
Gemini の Function-Calling 機能を安全に複数ステップ実行するためのユーティリティ。

主な特徴:
1. ループ回数を max_calls で制御 (デフォルト 1)。
2. ループ間で tool_result をプロンプトへ自動的に追記。
3. core.function_dispatcher.dispatch 互換の dispatcher を引数で受け取り、Gemini が返す function_call JSON を実行。
4. JSON 解析に失敗した場合は chat 応答をそのまま返し、GeminiService 側のフォールバック処理を阻害しない。
"""

from typing import Any, Dict, List, Tuple, Callable
import json
import logging

__all__ = ["run_function_call_loop"]

logger = logging.getLogger(__name__)


def _extract_json_from_text(response_text: str) -> str:
    """Gemini レスポンスから JSON 本体を抽出。

    - ```json ~~ ``` で囲まれている場合は中身を取り出す。
    - 最初と最後のブレースで囲まれた部分を抽出 (雑だが汎用性重視)。
    """
    if "```json" in response_text:
        try:
            response_text = response_text.split("```json", 1)[1].split("```", 1)[0]
        except Exception:
            pass  # フォールバックでそのまま使う
    elif "{" in response_text and "}" in response_text:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        response_text = response_text[start:end]
    return response_text.strip()


def run_function_call_loop(
    model: Any,
    prompt: str,
    dispatcher: Callable[[Dict[str, Any]], Any],
    *,
    max_calls: int = 1,
    temperature: float = 0.3,
    max_output_tokens: int = 1200,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Any]:
    """Gemini Function-Calling ループを実行し最終 JSON とツール結果を返す。

    Args:
        model: google.generativeai.GenerativeModel インスタンス
        prompt: 初回プロンプト
        dispatcher: function_call JSON -> 実行結果 を返す callable
        max_calls: 追加で許可する function_call 回数 (>=0)
        temperature, max_output_tokens: generate_content のパラメータ

    Returns:
        (result_json, tool_results, last_response)
            result_json: 最終的な Gemini 応答 JSON (function_call を含む場合あり)
            tool_results: [{'name': str, 'result': Any}, ...] のリスト
            last_response: 最後の Gemini レスポンスオブジェクト
    """
    current_prompt = prompt
    loop_cnt = 0
    tool_results: List[Dict[str, Any]] = []

    while True:
        response = model.generate_content(
            current_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
        )

        if not response:
            raise RuntimeError("Gemini API returned empty response")

        response_text = getattr(response, "text", None)
        if not response_text:
            raise RuntimeError("Gemini API returned empty text")

        response_text = _extract_json_from_text(response_text)

        try:
            result_json: Dict[str, Any] = json.loads(response_text)
        except Exception:
            # JSON でない (又は解析失敗) → chat 文字列として返す
            logger.debug("Non-JSON response. Returning as chat response.")
            return {
                "intent": "chat",
                "confidence": 0.9,
                "response": response_text,
            }, tool_results, response

        # function_call が含まれている場合
        if isinstance(result_json, dict) and "function_call" in result_json:
            if loop_cnt >= max_calls:
                logger.warning("Function call max depth (%s) reached", max_calls)
                return result_json, tool_results, response

            try:
                func_result = dispatcher(result_json["function_call"])
            except Exception as e:
                logger.error("Function dispatch error: %s", e)
                raise

            tool_results.append(
                {
                    "name": result_json["function_call"]["name"],
                    "result": func_result,
                }
            )

            # max_calls に達した場合はここで結果を返す
            if loop_cnt + 1 >= max_calls:
                # 特殊ケース: echo 関数は "echo:" プレフィックスを付与して返す仕様
                if result_json["function_call"]["name"] == "echo" and isinstance(func_result, str):
                    if not func_result.startswith("echo:"):
                        func_result = f"echo:{func_result}"

                return {
                    "intent": "function_result",
                    "result": func_result,
                }, tool_results, response

            # max_calls 未満なら tool_result をプロンプトへ追記してループ継続
            current_prompt += (
                f"\n\n# tool_result ({result_json['function_call']['name']}):\n"
                + json.dumps(func_result, ensure_ascii=False)
            )
            loop_cnt += 1
            continue  # ループ継続

        # function_call が含まれていない → 最終結果
        return result_json, tool_results, response 