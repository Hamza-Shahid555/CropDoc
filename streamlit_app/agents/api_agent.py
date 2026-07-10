"""API Agent: external HTTP tool-calls exposed to the Response Agent. Uses
Open-Meteo (no API key required) so weather-aware agronomic advice ("should
I spray before the rain?") works out of the box in a demo deployment."""

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(location: str) -> dict:
    try:
        geo = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=8).json()
        results = geo.get("results") or []
        if not results:
            return {"error": f"Could not find a location matching '{location}'."}
        place = results[0]
        lat, lon = place["latitude"], place["longitude"]

        forecast = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "daily": "precipitation_probability_max,temperature_2m_max,temperature_2m_min",
                "forecast_days": 3,
                "timezone": "auto",
            },
            timeout=8,
        ).json()

        return {
            "location": f"{place.get('name')}, {place.get('country', '')}".strip(", "),
            "current": forecast.get("current"),
            "next_3_days": forecast.get("daily"),
        }
    except requests.RequestException as e:
        return {"error": f"Weather lookup failed: {e}"}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get current conditions and a 3-day forecast for a location, useful "
                "for agronomic advice such as spray timing, irrigation, or disease "
                "spread risk (many fungal diseases spread faster in humid/wet conditions)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or place name, e.g. 'Lahore' or 'Fresno, California'.",
                    }
                },
                "required": ["location"],
            },
        },
    },
]

TOOL_FUNCTIONS = {"get_weather": get_weather}
