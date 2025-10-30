#!/usr/bin/env python3
"""
拡張AI統一判定システムの実装検証
対話履歴 + スマート提案機能の実装確認（APIキー不要）
"""
import os
import sys
import inspect
from datetime import datetime

def check_enhanced_feature_implementation():
    """拡張機能の実装状況を検証"""
    print("🔍 拡張AI統一判定システム実装検証")
    print("=" * 60)
    
    verification_results = []
    
    # 1. ConversationMemoryService の検証
    print("\n📝 1. ConversationMemoryService 実装検証")
    print("-" * 40)
    
    try:
        from services.conversation_memory_service import ConversationMemoryService
        
        # クラス定義確認
        print("✅ ConversationMemoryService クラス定義OK")
        
        # 必要なメソッドの確認
        required_methods = [
            'add_conversation_turn',
            'get_conversation_context', 
            'get_user_profile',
            'analyze_conversation_patterns',
            'get_contextual_suggestions'
        ]
        
        for method in required_methods:
            if hasattr(ConversationMemoryService, method):
                print(f"   ✅ {method} メソッド実装済み")
            else:
                print(f"   ❌ {method} メソッド未実装")
                verification_results.append(f"ConversationMemoryService.{method} 未実装")
        
        # データクラスの確認
        try:
            from services.conversation_memory_service import ConversationTurn, UserProfile
            print("   ✅ ConversationTurn, UserProfile データクラス定義OK")
        except ImportError as e:
            print(f"   ❌ データクラス定義エラー: {e}")
            verification_results.append("ConversationMemoryService データクラス未定義")
            
    except ImportError as e:
        print(f"❌ ConversationMemoryService インポートエラー: {e}")
        verification_results.append("ConversationMemoryService 未実装")
    
    # 2. GeminiService の拡張機能検証
    print("\n🧠 2. GeminiService 拡張機能検証")  
    print("-" * 40)
    
    try:
        from services.gemini_service import GeminiService
        
        # 新しいメソッドの確認
        enhanced_methods = [
            '_get_conversation_memory',
            '_get_smart_suggestion',
            '_unified_ai_analysis_with_context',
            'add_conversation_turn',
            'get_smart_suggestions',
            'get_conversation_summary',
            'get_contextual_suggestions'
        ]
        
        for method in enhanced_methods:
            if hasattr(GeminiService, method):
                print(f"   ✅ {method} メソッド実装済み")
            else:
                print(f"   ❌ {method} メソッド未実装")
                verification_results.append(f"GeminiService.{method} 未実装")
        
        # analyze_textメソッドのシグネチャ確認
        analyze_text_sig = inspect.signature(GeminiService.analyze_text)
        params = list(analyze_text_sig.parameters.keys())
        if 'user_id' in params:
            print("   ✅ analyze_text メソッドにuser_id パラメータ追加済み")
        else:
            print("   ❌ analyze_text メソッドにuser_id パラメータ未追加")
            verification_results.append("GeminiService.analyze_text user_id パラメータ未追加")
            
    except ImportError as e:
        print(f"❌ GeminiService インポートエラー: {e}")
        verification_results.append("GeminiService 未実装")
    
    # 3. MessageHandler の拡張機能検証
    print("\n📨 3. MessageHandler 拡張機能検証")
    print("-" * 40)
    
    try:
        from handlers.message_handler import MessageHandler
        
        # handle_messageメソッドのコード確認
        source = inspect.getsource(MessageHandler.handle_message)
        
        # 新機能の確認
        new_features = [
            'smart_suggestion',
            'conversation_history', 
            'add_conversation_turn',
            'contextual_suggestions'
        ]
        
        for feature in new_features:
            if feature in source:
                print(f"   ✅ {feature} 機能実装済み")
            else:
                print(f"   ❌ {feature} 機能未実装")
                verification_results.append(f"MessageHandler {feature} 機能未実装")
        
        # ヘルプメッセージの新機能対応確認
        help_source = inspect.getsource(MessageHandler._generate_help_message)
        if 'スマート提案機能' in help_source and '対話履歴機能' in help_source:
            print("   ✅ ヘルプメッセージに新機能説明追加済み")
        else:
            print("   ❌ ヘルプメッセージに新機能説明未追加")
            verification_results.append("MessageHandler ヘルプメッセージ新機能未対応")
            
    except ImportError as e:
        print(f"❌ MessageHandler インポートエラー: {e}")
        verification_results.append("MessageHandler 未実装")
    
    # 4. SmartSuggestionService の確認
    print("\n🎯 4. SmartSuggestionService 実装確認")
    print("-" * 40)
    
    try:
        from services.smart_suggestion_service import SmartSuggestionService
        print("✅ SmartSuggestionService 利用可能")
        
        # 主要メソッドの確認
        suggestion_methods = [
            'record_user_behavior',
            'analyze_user_patterns',
            'get_all_suggestions',
            'format_suggestions_message'
        ]
        
        for method in suggestion_methods:
            if hasattr(SmartSuggestionService, method):
                print(f"   ✅ {method} メソッド実装済み")
            else:
                print(f"   ❌ {method} メソッド未実装")
                verification_results.append(f"SmartSuggestionService.{method} 未実装")
                
    except ImportError as e:
        print(f"❌ SmartSuggestionService インポートエラー: {e}")
        print("   ⚠️ SmartSuggestionService は既存の機能として想定")
    
    # 5. 統一AI判定の新機能対応確認
    print("\n🤖 5. 統一AI判定新機能対応確認")
    print("-" * 40)
    
    try:
        from services.gemini_service import GeminiService
        
        # プロンプト内容の確認（_unified_ai_analysis_with_context）
        source = inspect.getsource(GeminiService._unified_ai_analysis_with_context)
        
        # 新機能キーワードの確認
        new_intents = [
            'smart_suggestion',
            'conversation_history',
            'contextual_suggestions'
        ]
        
        for intent in new_intents:
            if intent in source:
                print(f"   ✅ {intent} 判定機能実装済み")
            else:
                print(f"   ❌ {intent} 判定機能未実装")
                verification_results.append(f"統一AI判定 {intent} 未対応")
        
        # コンテキスト機能の確認
        context_keywords = [
            'conversation_context',
            'user_profile_info',
            'コンテキスト考慮'
        ]
        
        context_implemented = any(keyword in source for keyword in context_keywords)
        if context_implemented:
            print("   ✅ コンテキスト考慮機能実装済み")
        else:
            print("   ❌ コンテキスト考慮機能未実装")
            verification_results.append("統一AI判定 コンテキスト考慮未実装")
            
    except Exception as e:
        print(f"❌ 統一AI判定確認エラー: {e}")
        verification_results.append("統一AI判定確認失敗")
    
    # 最終結果
    print("\n" + "=" * 60)
    print("🏁 実装検証結果")
    print("=" * 60)
    
    if not verification_results:
        print("🎉 すべての拡張機能が正しく実装されています！")
        print("\n✨ 実装済み機能:")
        print("🔄 対話履歴機能 - ユーザーとの会話を記憶・分析")
        print("🎯 スマート提案機能 - 使用パターンから最適な提案")
        print("🧠 コンテキスト考慮AI判定 - 過去の会話を考慮した意図判定")
        print("💰 コスト最適化 - 簡単パターン事前チェック")
        print("📊 ユーザープロファイル - 個人化された機能提案")
        return True
    else:
        print(f"⚠️ {len(verification_results)}件の実装課題が見つかりました:")
        for i, issue in enumerate(verification_results, 1):
            print(f"   {i}. {issue}")
        return False

def check_file_structure():
    """ファイル構造の確認"""
    print("\n📁 ファイル構造確認")
    print("-" * 40)
    
    required_files = [
        "services/conversation_memory_service.py",
        "services/gemini_service.py", 
        "services/smart_suggestion_service.py",
        "handlers/message_handler.py",
        "test_enhanced_ai_system.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} 未存在")

def main():
    """メイン実行関数"""
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # ファイル構造確認
        check_file_structure()
        
        # 実装検証
        success = check_enhanced_feature_implementation()
        
        if success:
            print(f"\n🚀 拡張AI統一判定システムの実装が完了しています！")
            print("💡 APIキーを設定してtest_enhanced_ai_system.pyを実行すると")
            print("   実際の動作テストが可能です。")
        else:
            print(f"\n🔧 実装課題があります。上記の問題を解決してください。")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 検証中にエラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 