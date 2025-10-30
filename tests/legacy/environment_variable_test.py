#!/usr/bin/env python3
"""
環境変数設定テスト
"""
import os
import sys
import logging

# テスト用の環境変数を先に設定
test_env = {
    'GOOGLE_API_KEY': 'test_google_api_key_for_testing',
    'SEARCH_ENGINE_ID': 'test_search_engine_id',
    # テスト用の必須環境変数
    'LINE_CHANNEL_SECRET': 'test_channel_secret_for_testing',
    'LINE_ACCESS_TOKEN': 'test_access_token_for_testing',
    'GEMINI_API_KEY': 'test_gemini_api_key_for_testing'
}

for key, value in test_env.items():
    os.environ[key] = value

# 環境変数設定後にConfigManagerをインポート
from core.config_manager import ConfigManager, config_manager

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """環境変数設定をテスト"""
    logger.info("🧪 環境変数設定テストを開始")
    
    # 現在の環境変数を確認
    logger.info("🔍 現在の環境変数:")
    for key in ['GOOGLE_API_KEY', 'SEARCH_ENGINE_ID', 'GOOGLE_SEARCH_ENGINE_ID']:
        value = os.getenv(key, 'NOT_SET')
        logger.info(f"  {key}: {value[:20]}..." if len(value) > 20 else f"  {key}: {value}")
    
    try:
        # 新しいConfigManagerインスタンスで確認
        test_config_manager = ConfigManager()
        config = test_config_manager.get_config()
        
        logger.info("✅ ConfigManager設定値:")
        logger.info(f"  google_api_key: {config.google_api_key[:20]}..." if config.google_api_key and len(config.google_api_key) > 20 else f"  google_api_key: {config.google_api_key}")
        logger.info(f"  google_search_engine_id: {config.google_search_engine_id}")
        
        # サービス設定を確認
        search_config = test_config_manager.get_service_config('search')
        logger.info(f"🔍 検索サービス設定: {search_config}")
        
        # 設定の妥当性チェック
        if search_config['api_key'] and search_config['search_engine_id']:
            logger.info("✅ 検索機能設定は正常です")
            return True
        else:
            logger.error("❌ 検索機能設定が不完全です")
            logger.error(f"  api_key: {'あり' if search_config['api_key'] else 'なし'}")
            logger.error(f"  search_engine_id: {'あり' if search_config['search_engine_id'] else 'なし'}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 設定テストエラー: {str(e)}")
        return False

def test_search_service_initialization():
    """SearchServiceの初期化をテスト"""
    logger.info("🔍 SearchService初期化テスト")
    
    try:
        from services.search_service import SearchService
        
        # 環境変数を確認
        api_key = os.getenv('GOOGLE_API_KEY')
        search_engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        logger.info(f"API Key: {'あり' if api_key else 'なし'}")
        logger.info(f"Search Engine ID: {'あり' if search_engine_id else 'なし'}")
        
        if api_key and search_engine_id:
            # SearchServiceを初期化
            search_service = SearchService(api_key=api_key, search_engine_id=search_engine_id)
            logger.info("✅ SearchService初期化成功")
            return True
        else:
            logger.error("❌ 必要な環境変数が設定されていません")
            return False
            
    except Exception as e:
        logger.error(f"❌ SearchService初期化エラー: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🧪 環境変数設定総合テスト")
    logger.info("=" * 60)
    
    # テスト実行
    test1_result = test_environment_variables()
    test2_result = test_search_service_initialization()
    
    logger.info("=" * 60)
    logger.info("📊 テスト結果")
    logger.info(f"  環境変数設定: {'✅ PASS' if test1_result else '❌ FAIL'}")
    logger.info(f"  SearchService初期化: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        logger.info("🎉 全テスト通過！")
        sys.exit(0)
    else:
        logger.error("⚠️ 一部テストが失敗しました")
        sys.exit(1) 