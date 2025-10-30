"""
拡張 動的機能生成サービス

テスト内で参照される `EnhancedDynamicFeatureSystem` を提供する薄いファサード。
既存の `services.dynamic_feature_service.DynamicFeatureSystem` をラップし、
互換APIを露出してテストの ModuleNotFoundError を解消する。
"""

from typing import Dict, Any, List, Optional

try:
    # 既存実装を再利用
    from services.dynamic_feature_service import (
        DynamicFeatureSystem,
        FeatureRequestAnalyzer,
        CodeGenerator,
        DynamicExecutionEngine,
        DynamicFeature,
    )
except Exception:
    # 相対/実行環境差異へのフォールバック
    from .dynamic_feature_service import (
        DynamicFeatureSystem,
        FeatureRequestAnalyzer,
        CodeGenerator,
        DynamicExecutionEngine,
        DynamicFeature,
    )


class EnhancedDynamicFeatureSystem:
    """
    強化版のインターフェースを名乗るが、実体は既存の DynamicFeatureSystem を委譲して提供。

    目的:
    - 互換クラス名を提供してテストを通す
    - 将来的な拡張ポイントを一箇所に集約
    """

    def __init__(self, gemini_service: Optional[object] = None) -> None:
        self._delegate = DynamicFeatureSystem(gemini_service)

    # 互換メソッド: テストで使用される API を委譲
    def create_feature_from_request(self, user_input: str, user_id: str = "default") -> DynamicFeature:
        return self._delegate.create_feature_from_request(user_input, user_id)

    def execute_feature(self, feature_id: str, parameters: Dict[str, Any] | None = None, user_input: str = "") -> Dict[str, Any]:
        return self._delegate.execute_feature(feature_id, user_input, parameters or {})

    def list_features(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._delegate.list_features(user_id)

    # 拡張用: 必要に応じて analyzer / generator / executor へのアクセサ
    @property
    def analyzer(self) -> FeatureRequestAnalyzer:
        return self._delegate.analyzer

    @property
    def generator(self) -> CodeGenerator:
        return self._delegate.generator

    @property
    def executor(self) -> DynamicExecutionEngine:
        return self._delegate.executor


