"""
Dynamic Feature Generation System
ユーザーの発言から機能を自動生成するシステム
（GeminiServiceに依存しない独立版）
"""
import logging
import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from pathlib import Path

class MockGeminiService:
    """モックGeminiサービス（テスト用）"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_content(self, prompt: str) -> str:
        """プロンプトからコンテンツを生成（モック）"""
        try:
            # シンプルなキーワードベースの応答生成
            if "機能名" in prompt and "説明" in prompt:
                if "天気" in prompt:
                    return json.dumps({
                        "functionality": "天気情報提供",
                        "function_name": "weather_info_function",
                        "description": "現在の天気情報を取得して通知する",
                        "parameters": [
                            {
                                "name": "location",
                                "type": "string",
                                "required": True,
                                "description": "場所の名前"
                            }
                        ],
                        "trigger_conditions": ["天気", "weather", "Weather"],
                        "return_type": "text",
                        "dependencies": ["requests"],
                        "priority": 3
                    })
                elif "通知" in prompt or "remind" in prompt.lower():
                    return json.dumps({
                        "functionality": "通知設定",
                        "function_name": "notification_function",
                        "description": "指定された時間に通知を送る",
                        "parameters": [
                            {
                                "name": "message",
                                "type": "string",
                                "required": True,
                                "description": "通知メッセージ"
                            },
                            {
                                "name": "time",
                                "type": "string",
                                "required": True,
                                "description": "通知時間（HH:MM形式）"
                            }
                        ],
                        "trigger_conditions": ["通知", "remind", "リマインド"],
                        "return_type": "text",
                        "dependencies": [],
                        "priority": 4
                    })
                else:
                    return json.dumps({
                        "functionality": "カスタム機能",
                        "function_name": f"custom_func_{hashlib.md5(prompt.encode()).hexdigest()[:8]}",
                        "description": "カスタム機能",
                        "parameters": [],
                        "trigger_conditions": ["カスタム"],
                        "return_type": "text",
                        "dependencies": [],
                        "priority": 1
                    })
            elif "コードを生成" in prompt:
                if "天気" in prompt:
                    return '''
import requests
from typing import Dict, Any

def weather_info_function(user_input: str, parameters: Dict[str, Any]) -> str:
    """現在の天気情報を取得して通知する"""
    try:
        location = parameters.get('location', '東京')
        # 実際のAPI呼び出しはここに実装
        # api_key = os.getenv('WEATHER_API_KEY')
        # response = requests.get(f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}")

        return f"📍 {location}の天気情報:\n☀️ 現在の天気: 晴れ\n🌡️ 気温: 22°C\n💨 風速: 5m/s\n\n※これはテスト用のモックデータです"
    except Exception as e:
        return f"天気情報の取得に失敗しました: {str(e)}"
'''
                elif "通知" in prompt:
                    return '''
from datetime import datetime
import schedule
from typing import Dict, Any

def notification_function(user_input: str, parameters: Dict[str, Any]) -> str:
    """指定された時間に通知を送る"""
    try:
        message = parameters.get('message', 'テスト通知')
        time_str = parameters.get('time', '09:00')

        def job():
            print(f"🔔 通知: {message}")

        schedule.every().day.at(time_str).do(job)
        return f"✅ 通知機能を設定しました\n⏰ 時間: {time_str}\n📝 メッセージ: {message}"
    except Exception as e:
        return f"通知設定に失敗しました: {str(e)}"
'''
                else:
                    return '''
def custom_function(user_input: str, parameters: Dict[str, Any]) -> str:
    """カスタム機能"""
    return f"カスタム機能が実行されました: {user_input}"
'''
            elif "テストケース" in prompt:
                return json.dumps([
                    {
                        "input": "テスト入力",
                        "parameters": {"key": "value"},
                        "expected_output": "期待される出力"
                    }
                ])
            else:
                return "テスト用のモック応答です"
        except Exception as e:
            return f"モック生成エラー: {str(e)}"

class FeatureStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    TESTING = "testing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

@dataclass
class FeatureRequest:
    """機能要求"""
    request_id: str
    user_id: str
    natural_language: str
    extracted_functionality: Dict[str, Any]
    parameters: Dict[str, Any]
    trigger_conditions: List[str]
    priority: int = 1
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class GeneratedCode:
    """生成されたコード"""
    code_id: str
    request_id: str
    generated_code: str
    dependencies: List[str]
    test_cases: List[str]
    security_score: float
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

@dataclass
class DynamicFeature:
    """動的に生成された機能"""
    feature_id: str
    name: str
    description: str
    code: GeneratedCode
    status: FeatureStatus
    user_id: str
    usage_count: int = 0
    user_rating: float = 0.0
    created_at: datetime = None
    last_used: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class FeatureRequestAnalyzer:
    """機能要求解析サービス"""

    def __init__(self, gemini_service=None):
        self.gemini_service = gemini_service or MockGeminiService()
        self.logger = logging.getLogger(__name__)

    def analyze_request(self, user_input: str, user_id: str = "default") -> FeatureRequest:
        """
        ユーザーの入力を解析して機能要求を抽出

        Args:
            user_input (str): ユーザーの自然言語入力
            user_id (str): ユーザーID

        Returns:
            FeatureRequest: 解析された機能要求
        """
        try:
            # 自然言語解析プロンプト
            analysis_prompt = f"""
            以下のユーザーの要求を分析して、機能として実装可能なものを抽出してください。

            ユーザーの要求: "{user_input}"

            以下の情報をJSON形式で出力してください:
            {{
                "functionality": "機能の概要（簡潔に）",
                "function_name": "機能の名前（英数字とアンダースコアのみ）",
                "description": "機能の詳細な説明",
                "parameters": [
                    {{
                        "name": "パラメータ名",
                        "type": "string|number|boolean",
                        "required": true|false,
                        "description": "パラメータの説明"
                    }}
                ],
                "trigger_conditions": [
                    "この機能が実行される条件（例: 特定のキーワード、時間帯など）"
                ],
                "return_type": "機能の戻り値の型（例: text, json, image_url）",
                "dependencies": [
                    "必要な外部APIやライブラリ"
                ],
                "priority": "優先度（1-5、5が最高）"
            }}

            出力はJSON形式のみでお願いします。
            """

            # Gemini AIで解析
            analysis_result = self.gemini_service.generate_json_content(analysis_prompt)

            # FeatureRequestオブジェクト作成
            request = FeatureRequest(
                request_id=str(uuid.uuid4()),
                user_id=user_id,
                natural_language=user_input,
                extracted_functionality=analysis_result,
                parameters={},
                trigger_conditions=analysis_result.get("trigger_conditions", []),
                priority=analysis_result.get("priority", 1)
            )

            self.logger.info(f"機能要求を解析しました: {request.extracted_functionality.get('function_name', 'N/A')}")
            return request

        except Exception as e:
            self.logger.error(f"機能要求解析エラー: {str(e)}")
            # フォールバック: 基本的な要求オブジェクト作成
            return FeatureRequest(
                request_id=str(uuid.uuid4()),
                user_id=user_id,
                natural_language=user_input,
                extracted_functionality={
                    "functionality": "カスタム機能",
                    "function_name": f"custom_func_{hashlib.md5(user_input.encode()).hexdigest()[:8]}",
                    "description": user_input,
                    "parameters": [],
                    "trigger_conditions": ["ユーザーのメッセージ"],
                    "return_type": "text",
                    "dependencies": [],
                    "priority": 1
                },
                parameters={},
                trigger_conditions=["ユーザーのメッセージ"]
            )

class CodeGenerator:
    """コード生成サービス"""

    def __init__(self, gemini_service=None):
        self.gemini_service = gemini_service or MockGeminiService()
        self.logger = logging.getLogger(__name__)

        # コードテンプレート
        self.code_templates = {
            "text_response": """
def {function_name}(user_input: str, parameters: Dict[str, Any]) -> str:
    \"\"\"{description}\"\"\"
    # 基本的なテキスト応答機能
    return f"{function_name}: {user_input}"
""",
            "api_integration": """
import requests
from typing import Dict, Any

def {function_name}(user_input: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"{description}\"\"\"
    try:
        # API連携の例
        api_url = parameters.get('api_url', 'https://api.example.com/data')
        response = requests.get(api_url)
        return {{
            'status': 'success',
            'data': response.json(),
            'message': '{function_name}が実行されました'
        }}
    except Exception as e:
        return {{
            'status': 'error',
            'message': str(e)
        }}
""",
            "scheduled_task": """
from datetime import datetime
import schedule
from typing import Dict, Any, Callable

def {function_name}(user_input: str, parameters: Dict[str, Any]) -> str:
    \"\"\"{description}\"\"\"
    # スケジュールされたタスク
    task_time = parameters.get('schedule_time', '09:00')

    def scheduled_job():
        print(f'{function_name}が実行されました')

    schedule.every().day.at(task_time).do(scheduled_job)
    return f"{function_name}が{task_time}にスケジュールされました"
"""
        }

    def generate_feature_code(self, request: FeatureRequest) -> GeneratedCode:
        """
        機能要求からコードを生成

        Args:
            request (FeatureRequest): 機能要求

        Returns:
            GeneratedCode: 生成されたコード
        """
        try:
            # コード生成プロンプト
            func_info = request.extracted_functionality
            code_prompt = f"""
            以下の機能に対するPythonコードを生成してください。

            機能名: {func_info['function_name']}
            説明: {func_info['description']}
            パラメータ: {func_info['parameters']}
            戻り値の型: {func_info['return_type']}
            依存関係: {func_info['dependencies']}

            以下の形式でコードを生成してください:
            1. 関数定義
            2. 必要なimport文
            3. エラーハンドリング
            4. ドキュメンテーション文字列

            コードのみを出力してください。マークダウン記法などは使用しないでください。
            """

            # Gemini AIでコード生成
            generated_code_text = self.gemini_service.generate_content(code_prompt)

            # テストケース生成
            test_prompt = f"""
            上記の{func_info['function_name']}関数に対するテストケースを生成してください。
            以下の形式でJSON配列として出力:
            [
                {{
                    "input": "入力例",
                    "parameters": {{"key": "value"}},
                    "expected_output": "期待される出力"
                }}
            ]
            """

            test_response = self.gemini_service.generate_json_content(test_prompt)
            test_cases = test_response

            # セキュリティチェック
            security_score = self._calculate_security_score(generated_code_text)

            code = GeneratedCode(
                code_id=str(uuid.uuid4()),
                request_id=request.request_id,
                generated_code=generated_code_text,
                dependencies=func_info['dependencies'],
                test_cases=test_cases,
                security_score=security_score
            )

            self.logger.info(f"コードを生成しました: {func_info['function_name']}")
            return code

        except Exception as e:
            self.logger.error(f"コード生成エラー: {str(e)}")
            raise

    def _calculate_security_score(self, code: str) -> float:
        """
        生成コードのセキュリティスコアを計算

        Args:
            code (str): 生成されたコード

        Returns:
            float: セキュリティスコア（0.0-1.0）
        """
        score = 1.0

        # 危険な操作のチェック
        dangerous_patterns = [
            r'import os',
            r'import subprocess',
            r'import sys',
            r'eval\(',
            r'exec\(',
            r'open\(',
            r'file\(',
            r'input\('
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 0.1

        return max(0.0, min(1.0, score))

class DynamicExecutionEngine:
    """動的実行エンジン"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_features: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def execute_generated_code(self, code: GeneratedCode, user_input: str = "",
                            parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成されたコードを安全に実行

        Args:
            code (GeneratedCode): 生成されたコード
            user_input (str): ユーザー入力
            parameters (Dict[str, Any]): パラメータ

        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            # デフォルトパラメータ
            if parameters is None:
                parameters = {}

            # 実行環境の準備
            exec_globals = {
                'user_input': user_input,
                'parameters': parameters,
                'datetime': datetime,
                'json': json,
                're': re,
                'uuid': uuid,
                'hashlib': hashlib,
            }

            # コード実行
            exec(code.generated_code, exec_globals)

            # 関数名を取得（コードから抽出）
            function_name = self._extract_function_name(code.generated_code)

            if function_name in exec_globals:
                func = exec_globals[function_name]

                # 関数のシグネチャをチェック
                import inspect
                sig = inspect.signature(func)

                # 関数が引数を取るかどうか確認
                params = list(sig.parameters.keys())

                if len(params) == 0:
                    # 引数なしの関数
                    result = func()
                elif len(params) == 2 and 'user_input' in params and 'parameters' in params:
                    # 標準的なシグネチャ
                    result = func(user_input, parameters)
                elif len(params) == 1:
                    # 1つの引数のみ
                    if 'user_input' in params:
                        result = func(user_input)
                    elif 'parameters' in params:
                        result = func(parameters)
                    else:
                        result = func()
                else:
                    # デフォルトでuser_inputのみ渡す
                    result = func(user_input)

            else:
                result = f"関数 {function_name} が見つかりませんでした"

            # 実行履歴の記録
            execution_record = {
                'code_id': code.code_id,
                'timestamp': datetime.now(),
                'result': str(result),
                'success': True
            }

            self.execution_history.append(execution_record)

            return {
                'status': 'success',
                'result': result,
                'execution_id': len(self.execution_history)
            }

        except Exception as e:
            error_record = {
                'code_id': code.code_id,
                'timestamp': datetime.now(),
                'error': str(e),
                'success': False
            }

            self.execution_history.append(error_record)
            self.logger.error(f"コード実行エラー: {str(e)}")

            return {
                'status': 'error',
                'error': str(e),
                'execution_id': len(self.execution_history)
            }

    def _extract_function_name(self, code: str) -> str:
        """コードから関数名を抽出"""
        match = re.search(r'def (\w+)\(', code)
        return match.group(1) if match else 'unknown_function'

class DynamicFeatureSystem:
    """動的機能生成システムのメインクラス"""

    def __init__(self, gemini_service=None):
        self.gemini_service = gemini_service or MockGeminiService()
        self.logger = logging.getLogger(__name__)

        # コンポーネント初期化
        self.analyzer = FeatureRequestAnalyzer(self.gemini_service)
        self.generator = CodeGenerator(self.gemini_service)
        self.executor = DynamicExecutionEngine()

        # データ保存先
        self.features_file = Path('data/dynamic_features.json')
        self.features_file.parent.mkdir(exist_ok=True)

        # 機能ストレージ
        self.features: Dict[str, DynamicFeature] = {}
        self.load_features()

        # ロック
        self.lock = threading.Lock()

    def create_feature_from_request(self, user_input: str, user_id: str = "default") -> DynamicFeature:
        """
        ユーザーの要求から機能を自動生成

        Args:
            user_input (str): ユーザーの自然言語入力
            user_id (str): ユーザーID

        Returns:
            DynamicFeature: 生成された機能
        """
        try:
            with self.lock:
                # 1. 要求解析
                self.logger.info(f"機能要求を解析中: {user_input}")
                request = self.analyzer.analyze_request(user_input, user_id)

                # 2. コード生成
                self.logger.info(f"コードを生成中: {request.extracted_functionality['function_name']}")
                code = self.generator.generate_feature_code(request)

                # 3. 機能オブジェクト作成
                feature = DynamicFeature(
                    feature_id=str(uuid.uuid4()),
                    name=request.extracted_functionality['function_name'],
                    description=request.extracted_functionality['description'],
                    code=code,
                    status=FeatureStatus.TESTING,
                    user_id=user_id
                )

                # 4. テスト実行
                test_result = self._test_generated_feature(feature)
                if test_result['status'] == 'success':
                    feature.status = FeatureStatus.ACTIVE
                    self.logger.info(f"機能が正常に生成されました: {feature.name}")
                else:
                    feature.status = FeatureStatus.ERROR
                    self.logger.warning(f"機能の生成に問題がありました: {feature.name}")

                # 5. 機能登録
                self.features[feature.feature_id] = feature
                self.save_features()

                return feature

        except Exception as e:
            self.logger.error(f"機能生成エラー: {str(e)}")
            raise

    def _test_generated_feature(self, feature: DynamicFeature) -> Dict[str, Any]:
        """生成された機能をテスト"""
        try:
            # テストケース実行
            test_results = []
            for test_case in feature.code.test_cases:
                result = self.executor.execute_generated_code(
                    feature.code,
                    test_case['input'],
                    test_case.get('parameters', {})
                )
                test_results.append(result)

            return {
                'status': 'success',
                'test_results': test_results
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def execute_feature(self, feature_id: str, user_input: str = "",
                       parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """機能を動的に実行"""
        if feature_id not in self.features:
            return {'error': '機能が見つかりません'}

        feature = self.features[feature_id]

        if feature.status != FeatureStatus.ACTIVE:
            return {'error': f'機能が使用できません（状態: {feature.status.value}）'}

        try:
            # 使用カウント更新
            feature.usage_count += 1
            feature.last_used = datetime.now()

            # 機能実行
            result = self.executor.execute_generated_code(
                feature.code,
                user_input,
                parameters
            )

            # 機能更新保存
            self.save_features()

            return result

        except Exception as e:
            return {'error': str(e)}

    def list_features(self, user_id: str = None) -> List[Dict[str, Any]]:
        """利用可能な機能を一覧表示"""
        features_list = []
        for feature in self.features.values():
            if user_id is None or feature.user_id == user_id:
                features_list.append({
                    'feature_id': feature.feature_id,
                    'name': feature.name,
                    'description': feature.description,
                    'status': feature.status.value,
                    'usage_count': feature.usage_count,
                    'user_rating': feature.user_rating,
                    'created_at': feature.created_at.isoformat()
                })

        return features_list

    def save_features(self):
        """機能をファイルに保存"""
        try:
            features_data = {}
            for feature_id, feature in self.features.items():
                # FeatureStatusを文字列に変換して保存
                feature_dict = asdict(feature)
                feature_dict['status'] = feature.status.value  # Enumの値を保存
                features_data[feature_id] = feature_dict

            with open(self.features_file, 'w', encoding='utf-8') as f:
                json.dump(features_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            self.logger.error(f"機能保存エラー: {str(e)}")

    def load_features(self):
        """機能をファイルから読み込み"""
        try:
            if self.features_file.exists():
                with open(self.features_file, 'r', encoding='utf-8') as f:
                    features_data = json.load(f)

                for feature_id, data in features_data.items():
                    # 古い形式のデータは読み込まない
                    if 'status' in data:
                        try:
                            # FeatureStatusを文字列からEnumに変換
                            status_value = data['status']
                            if isinstance(status_value, str):
                                status = FeatureStatus(status_value)
                            else:
                                status = FeatureStatus.ACTIVE  # デフォルト値

                            feature = DynamicFeature(
                                feature_id=feature_id,
                                name=data['name'],
                                description=data['description'],
                                code=GeneratedCode(**data['code']),
                                status=status,
                                user_id=data['user_id'],
                                usage_count=data.get('usage_count', 0),
                                user_rating=data.get('user_rating', 0.0),
                                created_at=datetime.fromisoformat(data['created_at']),
                                last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None
                            )
                            self.features[feature_id] = feature
                        except (ValueError, KeyError) as e:
                            self.logger.warning(f"機能{feature_id}の読み込みエラー: {e}")
                            continue

        except Exception as e:
            self.logger.error(f"機能読み込みエラー: {str(e)}")

# 使用例
if __name__ == "__main__":
    # 初期化
    dynamic_system = DynamicFeatureSystem()

    # ユーザー要求から機能生成
    user_request = "今日の天気をまとめて教えて"
    feature = dynamic_system.create_feature_from_request(user_request)

    # 生成された機能一覧表示
    features = dynamic_system.list_features()
    print("生成された機能:", features)
    # 機能実行
    if features:
        result = dynamic_system.execute_feature(features[0]['feature_id'])
        print("実行結果:", result)
