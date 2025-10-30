"""
Weather service implementation
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import os
import logging
import requests
from dataclasses import dataclass
import pytz

@dataclass
class WeatherInfo:
    """天気情報データモデル"""
    location: str
    temperature: float
    humidity: float
    description: str
    wind_speed: float
    timestamp: str
    icon: str
    feels_like: Optional[float] = None
    pressure: Optional[int] = None
    clouds: Optional[int] = None
    rain_1h: Optional[float] = None
    snow_1h: Optional[float] = None
    advice: Optional[str] = None  # AIによる天気アドバイス

@dataclass
class DailyWeatherInfo:
    """日ごとの天気情報データモデル"""
    date: str
    max_temp: float
    min_temp: float
    avg_temp: float
    description: str
    icon: str
    chance_of_rain: int
    chance_of_snow: int
    wind_speed: float

@dataclass
class WeatherForecast:
    """天気予報データモデル"""
    location: str
    forecasts: List[DailyWeatherInfo]

class WeatherService:
    """天気サービス"""

    def __init__(self, api_key: Optional[str] = None, gemini_service: Optional[Any] = None):
        """
        天気サービスの初期化
        
        Args:
            api_key (Optional[str]): Weather APIキー
            gemini_service (Optional[Any]): GeminiService インスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv('WEATHER_API_KEY')
        self.is_available = bool(self.api_key)
        self.gemini_service = gemini_service
        
        if self.is_available:
            self.base_url = "http://api.weatherapi.com/v1"
        else:
            self.logger.warning("Weather APIキーが設定されていません。天気機能は無効です。")
            
        self.jst = pytz.timezone('Asia/Tokyo')
        # 簡易メモリキャッシュ
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl_seconds = 180  # 3分

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

    def _generate_weather_advice(self, weather_info: WeatherInfo) -> str:
        """
        天気情報に基づいてアドバイスを生成
        
        Args:
            weather_info (WeatherInfo): 天気情報
            
        Returns:
            str: 生成されたアドバイス
        """
        if not self.gemini_service:
            return None

        try:
            prompt = f"""
            以下の天気情報に基づいて、その日の過ごし方や注意点についてアドバイスを提供してください。
            簡潔で具体的な1-2文の助言を返してください。絵文字を1-2個使用してOKです。

            場所: {weather_info.location}
            気温: {weather_info.temperature}°C
            湿度: {weather_info.humidity}%
            天気: {weather_info.description}
            風速: {weather_info.wind_speed}m/s
            体感温度: {weather_info.feels_like if weather_info.feels_like else '不明'}°C
            降水量: {weather_info.rain_1h if weather_info.rain_1h else '0'}mm/h

            例えば：
            - 暑い日→「🌞 暑さ対策を忘れずに、こまめな水分補給がおすすめです」
            - 雨の日→「☔ 足元が滑りやすいので、傘と防水の靴があると安心です」
            - 寒い日→「🧣 冷え込むので、マフラーや手袋などの防寒対策をお忘れなく」
            """

            response = self.gemini_service.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
                
        except Exception as e:
            self.logger.error(f"アドバイス生成エラー: {str(e)}")
            
        return None

    def get_current_weather(self, location: str) -> Optional[WeatherInfo]:
        """
        現在または明日の天気を取得
        
        Args:
            location (str): 場所（都市名）
            
        Returns:
            Optional[WeatherInfo]: 天気情報、取得失敗時はNone
        """
        if not self.is_available:
            self.logger.warning("天気機能は利用できません")
            return None
            
        try:
            # location が None や空文字の場合はデフォルトを適用
            if not location:
                location = '東京'

            is_tomorrow = '明日' in location
            cleaned_location = location.replace('明日', '').replace('の天気', '').strip()
            
            if not cleaned_location:
                cleaned_location = '東京'
            
            # キャッシュキー
            cache_key = f"current:{cleaned_location}:{'tmrw' if is_tomorrow else 'now'}"
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

            if is_tomorrow:
                url = f"{self.base_url}/forecast.json"
                params = {'q': f"{cleaned_location},JP", 'key': self.api_key, 'days': 2, 'lang': 'ja'}
            else:
                url = f"{self.base_url}/current.json"
                params = {'q': f"{cleaned_location},JP", 'key': self.api_key, 'lang': 'ja'}
            
            # タイムアウトを明示（デフォルト3秒。環境変数で上書き可）
            timeout_sec = float(os.getenv('WEATHER_HTTP_TIMEOUT', '3'))
            response = requests.get(url, params=params, timeout=timeout_sec)
            response.raise_for_status()
            data = response.json()

            if is_tomorrow:
                tomorrow = data['forecast']['forecastday'][1]
                tomorrow_date = datetime.strptime(tomorrow['date'], '%Y-%m-%d')
                weather_info = WeatherInfo(
                    location=cleaned_location,
                    temperature=tomorrow['day']['avgtemp_c'],
                    humidity=tomorrow['day']['avghumidity'],
                    description=tomorrow['day']['condition']['text'],
                    wind_speed=tomorrow['day']['maxwind_kph'] / 3.6,
                    timestamp=tomorrow_date.strftime('%Y-%m-%d 12:00:00'),
                    icon=tomorrow['day']['condition']['icon'],
                    pressure=tomorrow['hour'][12]['pressure_mb'],
                    clouds=tomorrow['hour'][12]['cloud'],
                    rain_1h=tomorrow['day']['totalprecip_mm'] / 24,
                    snow_1h=None
                )
            else:
                current = data['current']
                weather_info = WeatherInfo(
                    location=cleaned_location,
                    temperature=current['temp_c'],
                    humidity=current['humidity'],
                    description=current['condition']['text'],
                    wind_speed=current['wind_kph'] / 3.6,
                    timestamp=datetime.fromisoformat(current['last_updated']).isoformat(),
                    icon=current['condition']['icon'],
                    feels_like=current['feelslike_c'],
                    pressure=current['pressure_mb'],
                    clouds=current['cloud'],
                    rain_1h=current.get('precip_mm'),
                    snow_1h=None
                )

            if self.gemini_service:
                weather_info.advice = self._generate_weather_advice(weather_info)

            # キャッシュ保存
            self._cache_set(cache_key, weather_info)
            return weather_info
            
        except Exception as e:
            self.logger.error(f"天気情報取得エラー: {str(e)}")
            return None

    def get_weather_forecast(self, location: str, days: int = 7) -> Optional[WeatherForecast]:
        """
        週間天気予報を取得
        
        Args:
            location (str): 場所（都市名）
            days (int): 予報日数（最大10日）
            
        Returns:
            Optional[WeatherForecast]: 天気予報、取得失敗時はNone
        """
        if not self.is_available:
            self.logger.warning("天気機能は利用できません")
            return None
            
        try:
            # キャッシュ
            cache_key = f"forecast:{location}:{days}"
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            url = f"{self.base_url}/forecast.json"
            params = {'q': f"{location},JP", 'key': self.api_key, 'days': min(days, 10), 'lang': 'ja'}
            
            # タイムアウトを明示
            timeout_sec = float(os.getenv('WEATHER_HTTP_TIMEOUT', '3'))
            response = requests.get(url, params=params, timeout=timeout_sec)
            response.raise_for_status()
            data = response.json()
            
            forecast_data = data['forecast']['forecastday']
            forecasts = []

            for day_data in forecast_data:
                day_info = day_data['day']
                forecasts.append(DailyWeatherInfo(
                    date=day_data['date'],
                    max_temp=day_info['maxtemp_c'],
                    min_temp=day_info['mintemp_c'],
                    avg_temp=day_info['avgtemp_c'],
                    description=day_info['condition']['text'],
                    icon=day_info['condition']['icon'],
                    chance_of_rain=day_info.get('daily_chance_of_rain', 0),
                    chance_of_snow=day_info.get('daily_chance_of_snow', 0),
                    wind_speed=day_info['maxwind_kph'] / 3.6
                ))

            result = WeatherForecast(location=location, forecasts=forecasts)
            self._cache_set(cache_key, result)
            return result

        except KeyError as e:
            self.logger.error(f"天気予報データのキーエラー: {e} - 予報データが不足している可能性があります。")
            self.logger.debug(f"受信したデータ: {data}")
            return None
        except Exception as e:
            self.logger.error(f"天気予報取得エラー: {e}")
            return None

    def format_weather_message(self, weather_data: Union[WeatherInfo, WeatherForecast]) -> Optional[Dict[str, Any]]:
        """
        天気情報や予報を適切なFlex Messageに整形する
        
        Args:
            weather_data: WeatherInfoまたはWeatherForecastオブジェクト
            
        Returns:
            Flex Messageの辞書
        """
        if isinstance(weather_data, WeatherInfo):
            return self.create_weather_flex_message(weather_data)
        elif isinstance(weather_data, WeatherForecast):
            return self.format_daily_forecast_flex_message(weather_data)
        return None

    def create_weather_flex_message(self, weather: Optional[WeatherInfo]) -> Optional[Dict[str, Any]]:
        """天気情報のFlex Messageを生成"""
        if not weather:
            return None
        
        weather_emoji = self._get_weather_emoji(weather.description)
        temp_emoji = self._get_temperature_emoji(weather.temperature)

        return {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"🌍 {weather.location}の天気", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": datetime.fromisoformat(weather.timestamp).strftime('%Y/%m/%d %H:%M'), "size": "sm", "color": "#999999"}
                ]
            },
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{weather_emoji} {weather.description}", "size": "3xl", "align": "center", "weight": "bold"},
                    {"type": "text", "text": f"{temp_emoji} {weather.temperature:.1f}°C", "size": "5xl", "align": "center", "weight": "bold"}
                ],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "🌡 体感", "flex": 2, "color": "#999999"}, {"type": "text", "text": f"{weather.feels_like:.1f}°C", "flex": 3, "weight": "bold"}]},
                    {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "💧 湿度", "flex": 2, "color": "#999999"}, {"type": "text", "text": f"{weather.humidity}%", "flex": 3, "weight": "bold"}]},
                    {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "🌪 風速", "flex": 2, "color": "#999999"}, {"type": "text", "text": f"{weather.wind_speed:.1f}m/s", "flex": 3, "weight": "bold"}]},
                    {"type": "separator", "margin": "lg"},
                    {"type": "text", "text": f"💡 {weather.advice}" if weather.advice else "良い一日を！", "wrap": True, "margin": "lg"}
                ]
            }
        }

    def format_daily_forecast_flex_message(self, forecast: Optional[WeatherForecast]) -> Optional[Dict[str, Any]]:
        """週間天気予報のFlex Message（カルーセル）を生成"""
        if not forecast or not forecast.forecasts:
            return None

        bubbles = []
        for daily_data in forecast.forecasts:
            date = datetime.strptime(daily_data.date, '%Y-%m-%d')
            day_of_week = ["月", "火", "水", "木", "金", "土", "日"][date.weekday()]
            
            bubble = {
                "type": "bubble",
                "size": "micro",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": date.strftime('%m/%d'), "color": "#ffffff", "size": "sm"},
                        {"type": "text", "text": f"({day_of_week})", "color": "#ffffff", "size": "xl", "weight": "bold"}
                    ],
                    "paddingAll": "10px",
                    "backgroundColor": "#0367D3"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": self._get_weather_emoji(daily_data.description), "size": "xxl", "align": "center"},
                        {"type": "text", "text": daily_data.description, "size": "sm", "wrap": True, "align": "center"},
                        {"type": "separator", "margin": "md"},
                        {"type": "box", "layout": "vertical", "margin": "md", "contents": [
                            {"type": "text", "text": f"最高: {daily_data.max_temp:.0f}°", "size": "sm", "align": "center", "color": "#E44040"},
                            {"type": "text", "text": f"最低: {daily_data.min_temp:.0f}°", "size": "sm", "align": "center", "color": "#407EE4"}
                        ]},
                        {"type": "box", "layout": "vertical", "margin": "md", "contents": [
                            {"type": "text", "text": "降水確率", "size": "xs", "align": "center", "color": "#aaaaaa"},
                            {"type": "text", "text": f"{daily_data.chance_of_rain}%", "size": "md", "align": "center", "weight": "bold", "color": "#40A0E4"}
                        ]}
                    ]
                }
            }
            bubbles.append(bubble)

        return {"type": "carousel", "contents": bubbles}

    def _get_weather_emoji(self, description: str) -> str:
        """天気に対応する絵文字を取得"""
        emoji_map = {'晴': '☀️', '曇': '☁️', '雨': '🌧', '雪': '❄️',
            '霧': '🌫',
            '曇り時々晴れ': '⛅️',
            '雷': '⚡️'
        }

        for key, emoji in emoji_map.items():
            if key in description:
                return emoji
        return '🌤'

    def _get_temperature_emoji(self, temp: float) -> str:
        """気温に対応する絵文字を取得"""
        if temp >= 30:
            return '🔥'
        elif temp >= 25:
            return '😰'
        elif temp >= 20:
            return '😊'
        elif temp >= 15:
            return '😌'
        elif temp >= 10:
            return '🙂'
        elif temp >= 5:
            return '😕'
        else:
            return '🥶'
