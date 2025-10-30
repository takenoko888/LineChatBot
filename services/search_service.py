"""
Search service implementation
"""
from typing import List, Dict, Any, Optional
import os
import logging
import json
from dataclasses import dataclass
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

@dataclass
class SearchResult:
    """検索結果データモデル"""
    title: str
    snippet: str
    link: str
    type: str = 'web'  # web, image, news, etc.
    image_url: Optional[str] = None
    published_date: Optional[str] = None
    source: Optional[str] = None

from services.gemini_service import GeminiService

class SearchService:
    """検索サービス"""

    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None, gemini_service: Optional[GeminiService] = None):
        """
        検索サービスの初期化
        
        Args:
            api_key (Optional[str]): Google Custom Search APIキー
            search_engine_id (Optional[str]): カスタム検索エンジンID
        """
        self.logger = logging.getLogger(__name__)
        
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = search_engine_id or os.getenv('SEARCH_ENGINE_ID')
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("Google APIキーまたは検索エンジンIDが設定されていません")

        try:
            # 既存のGeminiServiceが渡された場合は再利用
            self.gemini_service = gemini_service or GeminiService()
            # 遅延初期化（ネットワーク依存を回避）
            self.service = None
            self.logger.info("検索サービスの初期化が完了しました（遅延起動）")
        except Exception as e:
            self.logger.error(f"検索サービスの初期化エラー: {str(e)}")
            raise

        # 簡易メモリキャッシュ
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds = 120  # 2分

    def _cache_get(self, key: str) -> Optional[Any]:
        try:
            item = self._cache.get(key)
            if not item:
                return None
            if (datetime.utcnow().timestamp() - item['ts']) > self._cache_ttl_seconds:
                del self._cache[key]
                return None
            return item['value']
        except Exception:
            return None

    def _cache_set(self, key: str, value: Any) -> None:
        try:
            self._cache[key] = {"ts": datetime.utcnow().timestamp(), "value": value}
        except Exception:
            pass

    def search(
        self,
        query: str,
        result_type: str = 'web',
        max_results: int = 5,
        japan_only: bool = True
    ) -> List[SearchResult]:
        """
        検索を実行（日本サイト優先対応）
        
        Args:
            query (str): 検索クエリ
            result_type (str): 結果タイプ（web, image, news）
            max_results (int): 最大結果数
            japan_only (bool): 日本のサイトのみに限定するか
            
        Returns:
            List[SearchResult]: 検索結果リスト
        """
        try:
            # キャッシュキー
            cache_key = json.dumps({
                'q': query, 'type': result_type, 'num': max_results, 'jp': japan_only
            }, ensure_ascii=False)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            # サービスの遅延初期化
            if self.service is None:
                self.service = build(
                    "customsearch", "v1",
                    developerKey=self.api_key,
                    cache_discovery=False
                )

            # 検索パラメータの設定
            search_params = {
                'q': query,
                'cx': self.search_engine_id,
                'num': max_results
            }
            
            # 日本サイト限定設定
            if japan_only:
                search_params['gl'] = 'jp'  # 地域を日本に限定
                search_params['lr'] = 'lang_ja'  # 言語を日本語に限定
                # クエリに日本関連のキーワードを追加（より日本のサイトを優先）
                if not any(jp_word in query for jp_word in ['site:co.jp', 'site:jp', '日本']):
                    search_params['q'] = f"{query} (site:co.jp OR site:jp OR 日本)"
            
            # 結果タイプに応じたパラメータを追加
            if result_type == 'image':
                search_params['searchType'] = 'image'
            elif result_type == 'news':
                search_params['dateRestrict'] = 'd7'  # 過去7日間
                if japan_only:
                    # ニュース検索でも日本サイトを優先
                    search_params['q'] = f"{query} (site:nhk.or.jp OR site:asahi.com OR site:mainichi.jp OR site:yomiuri.co.jp)"
                
            # 検索実行
            result = self.service.cse().list(**search_params).execute()
            
            # 結果の処理
            search_results = []
            if 'items' in result:
                for item in result['items']:
                    search_result = SearchResult(
                        title=item.get('title', ''),
                        snippet=item.get('snippet', ''),
                        link=item.get('link', ''),
                        type=result_type
                    )
                    
                    # 画像検索の場合
                    if result_type == 'image':
                        search_result.image_url = item.get('link')
                        
                    # ニュース検索の場合
                    elif result_type == 'news':
                        search_result.published_date = item.get('pagemap', {}).get(
                            'metatags', [{}]
                        )[0].get('article:published_time')
                        search_result.source = item.get('displayLink', '')
                        
                    search_results.append(search_result)
                    
            # キャッシュ保存
            self._cache_set(cache_key, search_results)
            return search_results
            
        except HttpError as e:
            self.logger.error(f"Google API検索エラー: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"検索実行エラー: {str(e)}")
            return []
    
    def summarize_results(self, results: List[SearchResult], max_length: int = 300) -> Optional[str]:
        """
        検索結果を要約（LINEメッセージ文字数制限対応）
        
        Args:
            results (List[SearchResult]): 検索結果リスト
            max_length (int): 要約の最大文字数
            
        Returns:
            Optional[str]: 要約された検索結果、エラー時はNone
        """
        if not results:
            return None
        
        # 要約用のコンテンツを制限された長さで準備
        content_for_summary = ""
        total_content_length = 0
        max_content_length = 800  # Gemini APIに送る内容の最大長
        
        for result in results:
            # タイトルと概要を制限された長さで追加
            title = result.title[:100] if len(result.title) > 100 else result.title
            snippet = result.snippet[:150] if len(result.snippet) > 150 else result.snippet
            
            entry = f"タイトル: {title}\n概要: {snippet}\n\n"
            
            if total_content_length + len(entry) > max_content_length:
                break
                
            content_for_summary += entry
            total_content_length += len(entry)
            
        # より簡潔で的確な要約を生成するプロンプト
        prompt = f"""
以下の検索結果を非常に簡潔に要約してください。

要約のルール:
1. 最大{max_length}文字以内
2. 箇条書きで2-3点に要約
3. 重要なポイントのみを抽出
4. 「〜について」「〜に関して」などの冗長な表現は避ける
5. 絵文字は使用しない

検索結果:
{content_for_summary}

簡潔な要約:
"""
        
        try:
            response = self.gemini_service.model.generate_content(prompt)
            if response and response.text:
                summary = response.text.strip()
                
                # 文字数制限をチェック
                if len(summary) > max_length:
                    # 文字数超過の場合は短縮
                    summary = summary[:max_length-3] + "..."
                
                # 空の応答や不適切な応答をチェック
                if len(summary) < 10 or "申し訳ありません" in summary:
                    return None
                
                return summary
            else:
                return None
        except Exception as e:
            self.logger.error(f"要約エラー: {str(e)}")
            return None

    def format_search_results(
        self,
        results: List[SearchResult],
        format_type: str = 'default'
    ) -> Any:
        """
        検索結果を整形（URL表示改善版）
        
        Args:
            results (List[SearchResult]): 検索結果リスト
            format_type (str): 整形タイプ ('default', 'simple', 'detailed', 'compact', 'url_focused', 'flex_message')
            
        Returns:
            Any: 整形された検索結果（format_typeによりstrまたはdict）
        """
        try:
            if not results:
                if format_type == 'flex_message':
                    return {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "検索結果が見つかりませんでした。",
                                    "wrap": True
                                }
                            ]
                        }
                    }
                return "検索結果が見つかりませんでした。"

            if format_type == 'flex_message':
                bubbles = []
                for result in results:
                    # サムネイル画像のURLを取得（存在しない場合はプレースホルダー）
                    thumbnail_url = result.image_url or "https://via.placeholder.com/512x512.png?text=No+Image"
                    
                    bubble = {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": thumbnail_url,
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover",
                            "action": {"type": "uri", "uri": result.link}
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": result.title,
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "lg",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "box",
                                            "layout": "baseline",
                                            "spacing": "sm",
                                            "contents": [
                                                {
                                                    "type": "text",
                                                    "text": "概要",
                                                    "color": "#aaaaaa",
                                                    "size": "sm",
                                                    "flex": 1
                                                },
                                                {
                                                    "type": "text",
                                                    "text": result.snippet,
                                                    "wrap": True,
                                                    "color": "#666666",
                                                    "size": "sm",
                                                    "flex": 5
                                                }
                                            ]
                                        },
                                        {
                                            "type": "box",
                                            "layout": "baseline",
                                            "spacing": "sm",
                                            "contents": [
                                                {
                                                    "type": "text",
                                                    "text": "元サイト",
                                                    "color": "#aaaaaa",
                                                    "size": "sm",
                                                    "flex": 1
                                                },
                                                {
                                                    "type": "text",
                                                    "text": self._extract_domain(result.link),
                                                    "wrap": True,
                                                    "color": "#666666",
                                                    "size": "sm",
                                                    "flex": 5
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "uri",
                                        "label": "詳しく見る",
                                        "uri": result.link
                                    }
                                },
                                {
                                    "type": "spacer"
                                }
                            ],
                            "flex": 0
                        }
                    }
                    bubbles.append(bubble)
                
                return {
                    "type": "carousel",
                    "contents": bubbles
                }

            formatted_results = []
            
            if format_type == 'simple':
                # シンプルな表示形式（タイトルとURLのみ）
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. 📄 {result.title}\n"
                        f"   🔗 {result.link}\n"
                    )
                    
            elif format_type == 'detailed':
                # 詳細な表示形式（改善版）
                for i, result in enumerate(results, 1):
                    item = [f"📌 **検索結果 {i}**"]
                    item.append(f"📝 **タイトル:** {result.title}")
                    
                    # ニュース固有の情報
                    if result.type == 'news':
                        if result.published_date:
                            item.append(f"📅 **公開日:** {result.published_date}")
                        if result.source:
                            item.append(f"📰 **情報源:** {result.source}")
                    
                    # 概要（50文字で改行）
                    if result.snippet:
                        snippet_lines = []
                        for i in range(0, len(result.snippet), 50):
                            snippet_lines.append(result.snippet[i:i+50])
                        formatted_snippet = '\n'.join(snippet_lines)
                        item.append(f"📄 **概要:**\n{formatted_snippet}")
                    
                    # URLを目立つように表示
                    item.append(f"🌐 **URL:** {result.link}")
                    item.append("─" * 40)  # 区切り線
                    
                    formatted_results.append("\n".join(item))
                    
            elif format_type == 'compact':
                # コンパクトな表示形式（新規追加）
                for i, result in enumerate(results, 1):
                    # タイトルを30文字に制限
                    title = result.title[:30] + "..." if len(result.title) > 30 else result.title
                    formatted_results.append(
                        f"{i}. {title}\n"
                        f"🔗 {result.link}\n"
                    )
                    
            elif format_type == 'url_focused':
                # URL重視の表示形式（新規追加）
                formatted_results.append("🔍 **検索結果一覧 (URL付き)**\n")
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**{i}. {result.title}**\n"
                        f"📋 {result.snippet[:100]}{'...' if len(result.snippet) > 100 else ''}\n"
                        f"🌐 **アクセス:** {result.link}\n"
                        f"📊 **サイト:** {self._extract_domain(result.link)}\n"
                    )
                    
            else:
                # デフォルトの表示形式（改善版）
                formatted_results.append("🔍 **検索結果**\n")
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**{i}. {result.title}**\n"
                        f"📝 {result.snippet}\n"
                        f"🔗 **リンク:** {result.link}\n"
                        f"🏷️ **サイト:** {self._extract_domain(result.link)}\n"
                    )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            self.logger.error(f"検索結果整形エラー: {str(e)}")
            return "検索結果の表示中にエラーが発生しました。"

    def _extract_domain(self, url: str) -> str:
        """
        URLからドメイン名を抽出
        
        Args:
            url (str): URL
            
        Returns:
            str: ドメイン名
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # wwwを除去
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain
        except Exception:
            return "不明なサイト"

    def format_search_results_with_clickable_links(
        self,
        results: List[SearchResult],
        max_title_length: int = 40
    ) -> str:
        """
        クリック可能なリンク形式で検索結果を整形
        
        Args:
            results (List[SearchResult]): 検索結果リスト
            max_title_length (int): タイトルの最大文字数
            
        Returns:
            str: 整形された検索結果
        """
        try:
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
            
        except Exception as e:
            self.logger.error(f"クリック可能リンク形式整形エラー: {str(e)}")
            return "検索結果の表示中にエラーが発生しました。"

    def get_enhanced_results(
        self,
        query: str,
        include_news: bool = True,
        include_images: bool = False,
        japan_only: bool = True
    ) -> Dict[str, List[SearchResult]]:
        """
        拡張検索結果を取得（日本サイト優先対応）
        
        Args:
            query (str): 検索クエリ
            include_news (bool): ニュース検索を含めるか
            include_images (bool): 画像検索を含めるか
            japan_only (bool): 日本のサイトのみに限定するか
            
        Returns:
            Dict[str, List[SearchResult]]: 種類別の検索結果
        """
        try:
            results = {
                'web': self.search(query, 'web', 3, japan_only=japan_only)  # ウェブ検索は常に実行
            }
            
            if include_news:
                results['news'] = self.search(query, 'news', 2, japan_only=japan_only)
                
            if include_images:
                results['images'] = self.search(query, 'image', 3, japan_only=japan_only)
                
            return results
            
        except Exception as e:
            self.logger.error(f"拡張検索実行エラー: {str(e)}")
            return {'web': [], 'news': [], 'images': []}

    def format_enhanced_results(
        self,
        results: Dict[str, List[SearchResult]],
        max_message_length: int = 1800
    ) -> str:
        """
        拡張検索結果を整形（LINEメッセージ文字数制限対応）
        
        Args:
            results (Dict[str, List[SearchResult]]): 種類別の検索結果
            max_message_length (int): メッセージの最大文字数
            
        Returns:
            str: 整形された検索結果
        """
        try:
            if not any(results.values()):
                return "検索結果が見つかりませんでした。"

            formatted_sections = []
            current_length = 0

            # ウェブ検索結果（優先度：高）
            if results.get('web') and current_length < max_message_length * 0.7:
                web_results = self.format_search_results_with_clickable_links(
                    results['web'], max_title_length=30
                )
                section = f"🌐 **ウェブ検索結果:**\n{web_results}"
                
                if current_length + len(section) < max_message_length * 0.7:
                    formatted_sections.append(section)
                    current_length += len(section)

                    # AI要約を追加（残り文字数を考慮）
                    remaining_length = max_message_length - current_length - 100
                    if remaining_length > 100:
                        summary = self.summarize_results(results['web'], max_length=min(remaining_length, 250))
                        if summary and len(summary) > 10:
                            summary_section = f"🤖 **AI要約:**\n{summary}"
                            if current_length + len(summary_section) < max_message_length:
                                formatted_sections.append(summary_section)
                                current_length += len(summary_section)

            # ニュース検索結果（優先度：中）
            if results.get('news') and current_length < max_message_length * 0.9:
                news_results = self.format_search_results(
                    results['news'], 'compact'
                )
                section = f"📰 **ニュース検索結果:**\n{news_results}"
                
                if current_length + len(section) < max_message_length:
                    formatted_sections.append(section)
                    current_length += len(section)

            # 画像検索結果（優先度：低）
            if results.get('images') and current_length < max_message_length * 0.95:
                images_results = self.format_search_results(
                    results['images'], 'simple'
                )
                section = f"🖼 **画像検索結果:**\n{images_results}"
                
                if current_length + len(section) < max_message_length:
                    formatted_sections.append(section)

            # 結果が空の場合のフォールバック
            if not formatted_sections:
                return "検索結果が見つかりませんでした。"

            final_result = "\n\n".join(formatted_sections)
            
            # 最終的な文字数チェック
            if len(final_result) > max_message_length:
                # 文字数超過の場合は最初のセクションのみ返す
                if formatted_sections:
                    return formatted_sections[0]
                else:
                    return "検索結果が見つかりませんでした。"
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"拡張検索結果整形エラー: {str(e)}")
            return "検索結果の表示中にエラーが発生しました。"

    def close(self):
        """リソースのクリーンアップ"""
        try:
            if hasattr(self, 'service'):
                self.service.close()
        except Exception as e:
            self.logger.error(f"検索サービスのクリーンアップエラー: {str(e)}")