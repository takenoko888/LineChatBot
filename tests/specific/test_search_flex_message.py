#!/usr/bin/env python3
"""
検索結果Flex Message化のテスト
"""
import os
import sys
import json
from datetime import datetime

# APIキー設定（テスト用）
os.environ['GEMINI_API_KEY'] = 'test_key'

# パスを追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_search_flex_message_formatting():
    """検索結果のFlex Message形式テスト"""
    print("🎨 検索結果Flex Message化テスト")
    print("=" * 50)
    
    try:
        from services.search_service import SearchResult, SearchService
        
        # テスト用の検索結果データを作成
        test_results = [
            SearchResult(
                title="OpenAI ChatGPT - 人工知能チャットボット",
                snippet="OpenAIが開発した最新の人工知能チャットボット。自然言語での対話が可能で、質問応答、文章作成、翻訳など様々なタスクに対応しています。",
                link="https://www.openai.com/chatgpt",
                type="web",
                image_url="https://www.openai.com/content/images/2022/11/ChatGPT.jpg"
            ),
            SearchResult(
                title="【2024年最新】AI活用法完全ガイド",
                snippet="ビジネスでのAI活用方法を徹底解説。業務効率化から新しいサービス開発まで、実践的な活用例を紹介します。",
                link="https://example.com/ai-guide-2024",
                type="web"
            )
        ]

        # SearchServiceのインスタンスを作成（APIキーなしでテスト）
        search_service = SearchService(api_key="test", search_engine_id="test")

        # テスト1: Flex Message形式
        print("\n🎨 テスト1: Flex Message形式")
        print("-" * 30)
        flex_message = search_service.format_search_results(test_results, format_type='flex_message')
        
        # JSON構造の検証
        assert isinstance(flex_message, dict)
        assert flex_message['type'] == 'carousel'
        assert len(flex_message['contents']) == 2
        
        bubble1 = flex_message['contents'][0]
        assert bubble1['type'] == 'bubble'
        assert bubble1['hero']['url'] == "https://www.openai.com/content/images/2022/11/ChatGPT.jpg"
        assert bubble1['body']['contents'][0]['text'] == "OpenAI ChatGPT - 人工知能チャットボット"
        assert bubble1['footer']['contents'][0]['action']['uri'] == "https://www.openai.com/chatgpt"

        bubble2 = flex_message['contents'][1]
        assert bubble2['hero']['url'] == "https://via.placeholder.com/512x512.png?text=No+Image"

        print("✅ Flex Messageの基本構造は正常です。")
        print("\n生成されたJSON:")
        print(json.dumps(flex_message, indent=2, ensure_ascii=False))

        # テスト2: 結果がない場合
        print("\n🎨 テスト2: 結果がない場合のFlex Message")
        print("-" * 30)
        no_results_flex = search_service.format_search_results([], format_type='flex_message')
        assert no_results_flex['body']['contents'][0]['text'] == "検索結果が見つかりませんでした。"
        print("✅ 結果がない場合のメッセージは正常です。")
        print("\n生成されたJSON:")
        print(json.dumps(no_results_flex, indent=2, ensure_ascii=False))

        print("\n🎉 すべてのFlex Messageテストが完了しました！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_search_flex_message_formatting()
    sys.exit(0 if success else 1)
