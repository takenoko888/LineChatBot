"""Register real bot functions to FunctionRegistry.
This should be called once during app initialization after service instances are ready.
"""
from __future__ import annotations
from typing import Any, Dict, List
from core.function_registry import register_function


def setup_functions(notification_service=None, weather_service=None, search_service=None):
    """Register wrapper functions with actual service instances."""
    if weather_service and getattr(weather_service, 'is_available', False):

        @register_function(name="get_current_weather", description="Get current weather for location")
        def _get_current_weather(location: str) -> Dict[str, Any]:
            weather = weather_service.get_current_weather(location)
            return weather_service.format_weather_message(weather) if weather else {"error": "unavailable"}

        @register_function(name="get_weather_forecast", description="Get weather forecast for location")
        def _get_weather_forecast(location: str, days: int = 7) -> Dict[str, Any]:
            forecast = weather_service.get_weather_forecast(location, days=days)
            return weather_service.format_daily_forecast_flex_message(forecast) if forecast else {"error": "unavailable"}

    if search_service:

        @register_function(name="web_search", description="Search the web and return formatted results")
        def _web_search(query: str, max_results: int = 3) -> str:
            results = search_service.search(query, result_type="web", max_results=max_results)
            return search_service.format_search_results_with_clickable_links(results)

        @register_function(name="web_search_news", description="Search news and return compact results")
        def _web_search_news(query: str, max_results: int = 3) -> str:
            results = search_service.search(query, result_type="news", max_results=max_results)
            return search_service.format_search_results(results, format_type='compact')

        @register_function(name="web_search_images", description="Search images and return simple results")
        def _web_search_images(query: str, max_results: int = 3) -> str:
            results = search_service.search(query, result_type="image", max_results=max_results)
            return search_service.format_search_results(results, format_type='simple')

    if notification_service:

        @register_function(name="add_notification", description="Add a reminder from natural language")
        def _add_notification(user_id: str, text: str) -> str:
            success, msg = notification_service.add_notification_from_text(user_id, text)
            return msg

        @register_function(name="list_notifications", description="List notifications for user")
        def _list_notifications(user_id: str) -> Dict[str, Any]:
            notes = notification_service.get_notifications(user_id)
            return notification_service.format_notification_list(notes, format_type="flex_message") 

        @register_function(name="delete_notification", description="Delete notification by ID")
        def _delete_notification(user_id: str, notification_id: str) -> str:
            ok = notification_service.delete_notification(user_id, notification_id)
            return "deleted" if ok else "not_found"

        @register_function(name="acknowledge_notification", description="Acknowledge notification by ID")
        def _ack_notification(user_id: str, notification_id: str) -> str:
            ok = notification_service.acknowledge_notification(user_id, notification_id)
            return "acknowledged" if ok else "not_found"

        @register_function(name="update_notification", description="Update notification fields")
        def _update_notification(user_id: str, notification_id: str, datetime_str: str = "", repeat: str = "", title: str = "", message: str = "", priority: str = "") -> str:
            updates = {}
            if datetime_str:
                updates['datetime'] = datetime_str
            if repeat:
                updates['repeat'] = repeat
            if title:
                updates['title'] = title
            if message:
                updates['message'] = message
            if priority:
                updates['priority'] = priority
            if not updates:
                return "no_updates"
            ok = notification_service.update_notification(user_id, notification_id, updates)
            return "updated" if ok else "not_found"