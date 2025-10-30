#!/usr/bin/env python3
"""
天気予報Flex Message化のテスト
"""
import os
import sys
import json
from datetime import datetime, timedelta

# APIキー設定（テスト用）
os.environ['GEMINI_API_KEY'] = 'test_key'

# パスを追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_weather_flex_message_formatting():
    """天気予報のFlex Message形式テスト"""
    print("☀️ 天気予報Flex Message化テスト")
    print("=" * 50)
    
    try:
        from services.weather_service import WeatherService, WeatherInfo, WeatherForecast, DailyWeatherInfo
        
        # Mock GeminiService for advice generation
        class MockGeminiService:
            def __init__(self):
                self.model = self
            def generate_content(self, prompt):
                class MockResponse:
                    def __init__(self, text):
                        self.text = text
                if "暑い" in prompt: return MockResponse("🌞 暑い一日になりそうです。水分補給を忘れずに！")
                if "雨" in prompt: return MockResponse("☔ 傘を忘れずに、足元に注意してくださいね。")
                return MockResponse("良い一日を！")

        mock_gemini_service = MockGeminiService()
        weather_service = WeatherService(api_key="test_key", gemini_service=mock_gemini_service)

        # テスト1: 現在の天気 (WeatherInfo) のFlex Message
        print("\n☀️ テスト1: 現在の天気Flex Message")
        print("-" * 30)
        current_weather = WeatherInfo(
            location="東京",
            temperature=28.5,
            humidity=70,
            description="晴れ",
            wind_speed=3.2,
            timestamp=datetime.now().isoformat(),
            icon="01d",
            feels_like=30.1,
            advice="🌞 暑い一日になりそうです。水分補給を忘れずに！"
        )
        current_flex_message = weather_service.format_weather_message(current_weather)
        
        assert isinstance(current_flex_message, dict)
        assert current_flex_message['type'] == 'bubble'
        assert "東京" in current_flex_message['header']['contents'][0]['text']
        assert "晴れ" in current_flex_message['hero']['contents'][0]['text']
        assert "28.5°C" in current_flex_message['hero']['contents'][1]['text']
        assert "水分補給を忘れずに" in current_flex_message['body']['contents'][4]['text']
        print("✅ 現在の天気Flex Messageの基本構造は正常です。")
        print("\n生成されたJSON:")
        print(json.dumps(current_flex_message, indent=2, ensure_ascii=False))

        # テスト2: 週間天気予報 (WeatherForecast) のFlex Message (カルーセル)
        print("\n📅 テスト2: 週間天気予報Flex Message (カルーセル)")
        print("-" * 30)
        forecast_list = []
        for i in range(5):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            forecast_list.append(DailyWeatherInfo(
                date=date,
                max_temp=25 + i,
                min_temp=15 + i,
                avg_temp=20 + i,
                description="晴れ" if i % 2 == 0 else "曇り",
                icon="01d" if i % 2 == 0 else "02d",
                chance_of_rain=10 + i * 5,
                chance_of_snow=0,
                wind_speed=2.0
            ))
        weekly_forecast = WeatherForecast(location="大阪", forecasts=forecast_list)
        weekly_flex_message = weather_service.format_weather_message(weekly_forecast)

        assert isinstance(weekly_flex_message, dict)
        assert weekly_flex_message['type'] == 'carousel'
        assert len(weekly_flex_message['contents']) == 5
        
        # 最初のバブルの検証
        first_bubble = weekly_flex_message['contents'][0]
        assert first_bubble['type'] == 'bubble'
        assert "晴れ" in first_bubble['body']['contents'][1]['text']
        assert "最高: 25°" in first_bubble['body']['contents'][3]['contents'][0]['text']
        assert "最低: 15°" in first_bubble['body']['contents'][3]['contents'][1]['text']
        assert "10%" in first_bubble['body']['contents'][4]['contents'][1]['text']

        print("✅ 週間天気予報Flex Messageの基本構造は正常です。")
        print("\n生成されたJSON:")
        print(json.dumps(weekly_flex_message, indent=2, ensure_ascii=False))

        # テスト3: データがない場合
        print("\n❌ テスト3: データがない場合")
        print("-" * 30)
        no_data_flex = weather_service.format_weather_message(None)
        assert no_data_flex is None
        print("✅ データがない場合はNoneを返します。")

        print("\n🎉 すべての天気予報Flex Messageテストが完了しました！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_weather_flex_message_formatting()
    sys.exit(0 if success else 1)
