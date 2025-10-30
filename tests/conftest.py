import sys
from pathlib import Path

# プロジェクトルートを sys.path の先頭に追加して、
# 意図しない外部パッケージ（同名の utils など）の読み込みを防ぐ
PROJECT_ROOT = Path(__file__).resolve().parent.parent
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)


def pytest_ignore_collect(path):
    """tests/results 配下の .txt ファイルをテスト収集対象外にする"""
    path_str = str(path)
    if path_str.endswith('.txt') and ('tests/results' in path_str.replace('\\', '/')):
        return True
    return False 