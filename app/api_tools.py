"""Public API integration tools for Travel Concierge Agent."""

import json
import os
import urllib.parse
import urllib.request


def get_live_city_info(city_name: str) -> str:
    """Fetches real-time geographical data and live weather conditions for any city worldwide using the Open-Meteo public API.

    Args:
        city_name: Name of the target city (e.g. 'Tokyo', 'Paris', 'New York', 'Rome', 'Sydney').

    Returns:
        Formatted summary with country, region, timezone, population, elevation, temperature, and wind speed.
    """
    if not city_name or not city_name.strip():
        return "Please provide a valid city name."

    encoded_city = urllib.parse.quote(city_name.strip())
    api_key = os.environ.get("OPEN_METEO_API_KEY", "").strip()

    # Step 1: Geocoding search
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1"
    if api_key:
        geo_url += f"&apikey={api_key}"

    headers = {"User-Agent": "TravelConciergeAgent/1.0"}

    try:
        req = urllib.request.Request(geo_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())

        results = geo_data.get("results")
        if not results:
            return f"Could not find location information for '{city_name}'."

        loc = results[0]
        name = loc.get("name", city_name)
        country = loc.get("country", "Unknown Country")
        admin1 = loc.get("admin1", "")
        population = loc.get("population", 0)
        timezone = loc.get("timezone", "N/A")
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        elevation = loc.get("elevation", 0)

        # Step 2: Fetch current weather
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        )
        if api_key:
            weather_url += f"&apikey={api_key}"

        req_w = urllib.request.Request(weather_url, headers=headers)
        with urllib.request.urlopen(req_w, timeout=5) as resp_w:
            w_data = json.loads(resp_w.read().decode())

        current = w_data.get("current", {})
        temp_c = current.get("temperature_2m", "N/A")
        temp_f = round(temp_c * 9 / 5 + 32, 1) if isinstance(temp_c, (int, float)) else "N/A"
        humidity = current.get("relative_humidity_2m", "N/A")
        wind_speed = current.get("wind_speed_10m", "N/A")

        region_str = f" ({admin1})" if admin1 else ""
        pop_str = f"{population:,}" if population else "N/A"

        return (
            f"🌍 Live City Information for {name}, {country}{region_str}:\n"
            f"• Timezone: {timezone}\n"
            f"• Population: {pop_str}\n"
            f"• Elevation: {elevation}m\n"
            f"• Coordinates: {lat:.4f}°N, {lon:.4f}°E\n"
            f"----------------------------------------\n"
            f"🌤️ Current Weather:\n"
            f"• Temperature: {temp_c}°C ({temp_f}°F)\n"
            f"• Humidity: {humidity}%\n"
            f"• Wind Speed: {wind_speed} km/h"
        )
    except Exception as e:
        return f"Error fetching live city info for '{city_name}': {str(e)}"


def get_live_exchange_rates(base_currency: str = "USD", target_currency: str = "JPY") -> str:
    """Fetches real-time foreign exchange currency rates using the free Open Exchange Rates public API.

    Args:
        base_currency: Three-letter ISO currency code to convert from (e.g. 'USD', 'EUR', 'GBP').
        target_currency: Optional three-letter ISO currency code to convert to (e.g. 'JPY', 'EUR', 'GBP', 'CAD', 'AUD').

    Returns:
        Formatted string showing the latest exchange rate and conversion factor.
    """
    base = base_currency.strip().upper()
    target = target_currency.strip().upper() if target_currency else ""
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY", "").strip()

    url = f"https://open.er-api.com/v6/latest/{base}"
    if api_key:
        url += f"?app_id={api_key}"

    headers = {"User-Agent": "TravelConciergeAgent/1.0"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if data.get("result") != "success":
            return f"Could not retrieve exchange rates for base currency '{base}'."

        rates = data.get("rates", {})
        update_time = data.get("time_last_update_utc", "N/A")

        if target:
            if target not in rates:
                return f"Currency symbol '{target}' not found in exchange rate data."
            rate = rates[target]
            return (
                f"🔱 Live Currency Exchange Rate:\n"
                f"• 1 {base} = {rate:,.4f} {target}\n"
                f"• Last Updated: {update_time}"
            )

        # Return major travel currencies if no specific target requested
        major_symbols = ["EUR", "JPY", "GBP", "CAD", "AUD", "CHF", "CNY"]
        summary = [f"🔱 Live Currency Exchange Rates (Base: {base}):"]
        for sym in major_symbols:
            if sym in rates and sym != base:
                summary.append(f"• 1 {base} = {rates[sym]:,.4f} {sym}")

        summary.append(f"• Last Updated: {update_time}")
        return "\n".join(summary)

    except Exception as e:
        return f"Error fetching exchange rates for '{base}': {str(e)}"


def get_public_holidays(country_code: str = "JP", year: int = 2026) -> str:
    """Fetches upcoming national public holidays for a destination country using Nager.Date Public API.

    Args:
        country_code: Two-letter ISO country code (e.g. 'JP', 'FR', 'US', 'IT', 'GB', 'ES').
        year: Target year for public holidays (e.g. 2026).

    Returns:
        Formatted summary of national public holidays in the destination country.
    """
    code = country_code.strip().upper()
    api_key = os.environ.get("HOLIDAYS_API_KEY", "").strip()

    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{code}"
    if api_key:
        url += f"?key={api_key}"

    headers = {"User-Agent": "TravelConciergeAgent/1.0"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if not isinstance(data, list) or not data:
            return f"No public holidays found for country code '{code}' in year {year}."

        holidays_list = []
        for item in data[:10]:  # Limit top 10 for clean summary
            d = item.get("date", "")
            name = item.get("name", "")
            local_name = item.get("localName", "")
            local_str = f" ({local_name})" if local_name and local_name != name else ""
            holidays_list.append(f"• {d}: {name}{local_str}")

        return (
            f"📅 National Public Holidays in {code} ({year}):\n" +
            "\n".join(holidays_list)
        )

    except Exception as e:
        return f"Error fetching public holidays for country '{code}': {str(e)}"


