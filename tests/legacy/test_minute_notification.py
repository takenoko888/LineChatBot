#!/usr/bin/env python3
"""
分単位通知設定テスト
"""
import os
import sys
import logging
from datetime import datetime

# テスト用の環境変数を設定
os.environ.update({
    'GOOGLE_API_KEY': 'test_google_api_key_for_testing',
    'SEARCH_ENGINE_ID': 'test_search_engine_id',
    'LINE_CHANNEL_SECRET': 'test_channel_secret_for_testing',
    'LINE_ACCESS_TOKEN': 'test_access_token_for_testing',
    'GEMINI_API_KEY': 'test_gemini_api_key_for_testing'
})

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minute_notification_patterns():
    """分単位通知パターンのテスト"""
    logger.info("🕐 分単位通知パターンテスト開始")
    
    try:
        from services.gemini_service import GeminiService
        gemini_service = GeminiService()
        
        # 分単位通知のテストケース
        test_cases = [
            "12時40分に通知して",
            "明日の15:30に会議",
            "毎日7時30分に起きる",
            "今日の18時45分に薬を飲む",
            "9:15にリマインドして"
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"テスト: '{test_case}'")
            
            # AI判定テスト
            analysis = gemini_service.analyze_text(test_case, "test_user")
            intent = analysis.get('intent')
            
            # 通知解析テスト
            parsed = gemini_service.parse_notification_request(test_case)
            
            result = {
                'input': test_case,
                'intent': intent,
                'parsed': parsed,
                'success': intent == 'notification' and parsed is not None
            }
            
            results.append(result)
            logger.info(f"結果: intent={intent}, parsed={'成功' if parsed else '失敗'}")
            
            if parsed:
                logger.info(f"  解析データ: {parsed}")
        
        # 成功率をチェック
        successful = [r for r in results if r['success']]
        success_rate = len(successful) / len(results) * 100
        
        logger.info(f"📊 成功率: {len(successful)}/{len(results)} ({success_rate:.1f}%)")
        
        if success_rate >= 80:  # 80%以上の成功率を期待
            logger.info("✅ 分単位通知パターンテスト: PASS")
            return True
        else:
            logger.warning(f"⚠️ 成功率が低い: {success_rate:.1f}%")
            return False
            
    except Exception as e:
        logger.error(f"❌ テストエラー: {str(e)}")
        return False

def test_notification_service_minute_integration():
    """NotificationServiceでの分単位設定テスト"""
    logger.info("🔗 NotificationService分単位統合テスト開始")
    
    try:
        from services.notification_service import NotificationService
        
        notification_service = NotificationService()
        
        # 分単位通知設定のテスト
        test_cases = [
            "12時40分に通知して",
            "明日の15:30に会議"
        ]
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"テスト {i+1}: '{test_case}'")
            
            success, message = notification_service.add_notification_from_text(
                user_id=f"test_minute_user_{i}",
                text=test_case
            )
            
            if success:
                logger.info(f"✅ 通知設定成功: {message}")
                
                # 設定された通知を確認
                notifications = notification_service.get_notifications(f"test_minute_user_{i}")
                if notifications:
                    notification = notifications[0]
                    datetime_str = notification.datetime
                    logger.info(f"📅 設定時刻: {datetime_str}")
                    
                    # 分単位が正しく設定されているかチェック
                    if ":" in datetime_str and len(datetime_str.split(":")[-1]) >= 2:
                        logger.info("✅ 分単位設定確認")
                    else:
                        logger.warning("⚠️ 分単位設定が不完全")
                        return False
                else:
                    logger.warning("⚠️ 設定した通知が見つからない")
                    return False
            else:
                logger.error(f"❌ 通知設定失敗: {message}")
                return False
        
        logger.info("✅ NotificationService分単位統合テスト: PASS")
        return True
        
    except Exception as e:
        logger.error(f"❌ 統合テストエラー: {str(e)}")
        return False

def test_specific_time_parsing():
    """特定の時刻解析テスト"""
    logger.info("🎯 特定時刻解析テスト開始")
    
    try:
        from services.gemini_service import GeminiService
        gemini_service = GeminiService()
        
        # "12時40分に通知して"の詳細テスト
        test_input = "12時40分に通知して"
        
        logger.info(f"詳細テスト: '{test_input}'")
        
        # 簡易解析を直接テスト
        parsed = gemini_service._simple_notification_parse(test_input)
        
        if parsed:
            logger.info(f"✅ 簡易解析成功: {parsed}")
            
            # 時刻が正しく設定されているかチェック
            datetime_str = parsed.get('datetime', '')
            if '12:40' in datetime_str:
                logger.info("✅ 12時40分の設定確認")
                return True
            else:
                logger.warning(f"⚠️ 時刻設定が期待と異なる: {datetime_str}")
                return False
        else:
            logger.warning("⚠️ 簡易解析が失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 特定時刻解析テストエラー: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🕐 分単位通知設定テスト")
    logger.info("=" * 60)
    
    # テスト実行
    test_results = {}
    test_results['minute_patterns'] = test_minute_notification_patterns()
    test_results['service_integration'] = test_notification_service_minute_integration()
    test_results['specific_parsing'] = test_specific_time_parsing()
    
    logger.info("=" * 60)
    logger.info("📊 テスト結果サマリー")
    logger.info("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("-" * 60)
    logger.info(f"  合計: {passed}/{total} テスト通過")
    
    if passed == total:
        logger.info("🎉 全テスト通過！分単位通知設定が正常に動作します")
        sys.exit(0)
    else:
        logger.error("⚠️ 一部テストが失敗しました")
        sys.exit(1) 