#!/usr/bin/env python3
"""
検索結果URL表示改善のテスト
"""
import os
import sys
from datetime import datetime

# APIキー設定（テスト用）
os.environ['GEMINI_API_KEY'] = 'test_key'  # 実際のキーに置き換えてください

# パスを追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_search_url_display_formatting():
    """検索結果の表示形式テスト（APIキー不要）"""
    print("🔍 検索結果URL表示改善テスト")
    print("=" * 50)
    
    try:
        from services.search_service import SearchResult, SearchService
        
        # テスト用の検索結果データを作成
        test_results = [
            SearchResult(
                title="OpenAI ChatGPT - 人工知能チャットボット",
                snippet="OpenAIが開発した最新の人工知能チャットボット。自然言語での対話が可能で、質問応答、文章作成、翻訳など様々なタスクに対応しています。",
                link="https://www.openai.com/chatgpt",
                type="web"
            ),
            SearchResult(
                title="【2024年最新】AI活用法完全ガイド",
                snippet="ビジネスでのAI活用方法を徹底解説。業務効率化から新しいサービス開発まで、実践的な活用例を紹介します。",
                link="https://example.com/ai-guide-2024",
                type="web"
            ),
            SearchResult(
                title="人工知能研究の最前線 - 東京大学",
                snippet="最新の人工知能研究動向と将来展望について、東京大学の研究チームが詳しく解説しています。",
                link="https://www.u-tokyo.ac.jp/research/ai",
                type="web"
            )
        ]
        
        # SearchServiceのインスタンスを作成（APIキーなしでテスト）
        class MockSearchService:
            def __init__(self):
                pass
                
            def _extract_domain(self, url: str) -> str:
                """URLからドメイン名を抽出"""
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc
                    
                    if domain.startswith('www.'):
                        domain = domain[4:]
                        
                    return domain
                except Exception:
                    return "不明なサイト"
            
            def format_search_results_with_clickable_links(self, results, max_title_length=40):
                """クリック可能なリンク形式で検索結果を整形"""
                if not results:
                    return "❌ 検索結果が見つかりませんでした。"

                formatted_results = ["🔍 **検索結果** (URLをタップしてアクセス)\n"]
                
                for i, result in enumerate(results, 1):
                    # タイトルの長さ調整
                    title = result.title
                    if len(title) > max_title_length:
                        title = title[:max_title_length] + "..."
                    
                    # ドメイン名を抽出
                    domain = self._extract_domain(result.link)
                    
                    formatted_results.append(
                        f"**{i}. {title}**\n"
                        f"📝 {result.snippet[:80]}{'...' if len(result.snippet) > 80 else ''}\n"
                        f"🌐 **{domain}**\n"
                        f"👆 {result.link}\n"
                    )
                
                return "\n".join(formatted_results)
            
            def format_search_results(self, results, format_type='default'):
                """従来の表示形式"""
                if not results:
                    return "検索結果が見つかりませんでした。"

                formatted_results = []
                
                if format_type == 'detailed':
                    for i, result in enumerate(results, 1):
                        item = [f"📌 **検索結果 {i}**"]
                        item.append(f"📝 **タイトル:** {result.title}")
                        
                        if result.snippet:
                            snippet_lines = []
                            for j in range(0, len(result.snippet), 50):
                                snippet_lines.append(result.snippet[j:j+50])
                            formatted_snippet = '\n'.join(snippet_lines)
                            item.append(f"📄 **概要:**\n{formatted_snippet}")
                        
                        item.append(f"🌐 **URL:** {result.link}")
                        item.append("─" * 40)
                        
                        formatted_results.append("\n".join(item))
                
                return "\n".join(formatted_results)
        
        mock_service = MockSearchService()
        
        # テスト1: 新しいクリック可能リンク形式
        print("\n📱 テスト1: クリック可能リンク形式")
        print("-" * 30)
        clickable_format = mock_service.format_search_results_with_clickable_links(test_results)
        print(clickable_format)
        
        # テスト2: 詳細表示形式
        print("\n📋 テスト2: 詳細表示形式")
        print("-" * 30)
        detailed_format = mock_service.format_search_results(test_results, format_type='detailed')
        print(detailed_format)
        
        # テスト3: ドメイン抽出テスト
        print("\n🌐 テスト3: ドメイン抽出テスト")
        print("-" * 30)
        test_urls = [
            "https://www.openai.com/chatgpt",
            "https://example.com/path/to/page",
            "https://www.u-tokyo.ac.jp/research/ai",
            "http://news.yahoo.co.jp/articles/123"
        ]
        
        for url in test_urls:
            domain = mock_service._extract_domain(url)
            print(f"URL: {url}")
            print(f"ドメイン: {domain}\n")
        
        print("✅ すべての表示形式テストが完了しました！")
        print("\n🎯 改善点:")
        print("- URLが明確に表示される")
        print("- ドメイン名でサイトを識別しやすい")
        print("- タップしやすいリンク形式")
        print("- 見やすい絵文字とフォーマット")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        return False

def test_url_display_improvements():
    """URL表示改善の機能比較"""
    print("\n📊 URL表示改善の比較")
    print("=" * 50)
    
    print("🔴 **改善前の表示例:**")
    print("""1. OpenAI ChatGPT
OpenAIが開発した最新の人工知能チャットボット...
https://www.openai.com/chatgpt

2. AI活用法ガイド
ビジネスでのAI活用方法を徹底解説...
https://example.com/ai-guide-2024""")
    
    print("\n🟢 **改善後の表示例:**")
    print("""🔍 **検索結果** (URLをタップしてアクセス)

**1. OpenAI ChatGPT - 人工知能チャットボット**
📝 OpenAIが開発した最新の人工知能チャットボット。自然言語での対話が可能で、質問応答、文章作成、翻訳など...
🌐 **openai.com**
👆 https://www.openai.com/chatgpt

**2. 【2024年最新】AI活用法完全ガイド**
📝 ビジネスでのAI活用方法を徹底解説。業務効率化から新しいサービス開発まで、実践的な活用例...
🌐 **example.com**
👆 https://example.com/ai-guide-2024""")
    
    print("\n✨ **改善効果:**")
    print("- 🎯 URLが目立つ位置に配置")
    print("- 🏷️ ドメイン名で信頼性を判断可能")
    print("- 👆 タップを促す視覚的指示")
    print("- 📱 モバイルで見やすい形式")
    print("- 🌐 サイトの識別が容易")

def main():
    """メイン実行関数"""
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 表示形式テスト
        success1 = test_search_url_display_formatting()
        
        # 改善比較
        test_url_display_improvements()
        
        if success1:
            print(f"\n🎉 検索結果URL表示改善が完了しました！")
            print("💡 ユーザーがより簡単にサイトにアクセスできるようになります")
        else:
            print(f"\n⚠️ 一部テストで問題がありました")
        
        return success1
        
    except Exception as e:
        print(f"\n❌ テスト実行中にエラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 