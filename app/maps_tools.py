"""Google Maps Geocoding and Places (New) tools for Travel Concierge Agent."""

import json
import os
import urllib.parse
import urllib.request


def geocode_address(address: str) -> str:
    """Converts a location name or address into geographical coordinates (latitude and longitude).

    Args:
        address: Location query or full address (e.g. 'Shibuya Crossing, Tokyo' or 'Eiffel Tower, Paris').

    Returns:
        Formatted string containing latitude, longitude, and official formatted address.
    """
    if not address or not address.strip():
        return "Please provide a valid address or location query."

    maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not maps_api_key or maps_api_key == "PASTE_KEY_HERE":
        return "Error: GOOGLE_MAPS_API_KEY is not configured in environment."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={maps_api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}': {data.get('status', 'NO_RESULTS')}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        loc = result.get("geometry", {}).get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")

        return (
            f"📍 Geocoding Result for '{address}':\n"
            f"• Formatted Address: {formatted_address}\n"
            f"• Coordinates: Latitude {lat}, Longitude {lng}"
        )
    except Exception as e:
        return f"Error geocoding address '{address}': {str(e)}"


def search_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
) -> str:
    """Finds nearby points of interest or places of a given type around coordinates using Google Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g. 'tourist_attraction', 'restaurant', 'museum', 'cafe', 'park').

    Returns:
        Formatted summary listing nearby places with their display name, formatted address, and coordinates.
    """
    maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not maps_api_key or maps_api_key == "PASTE_KEY_HERE":
        return "Error: GOOGLE_MAPS_API_KEY is not configured in environment."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": maps_api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating",
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": 5000.0,
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found around ({latitude}, {longitude})."

        results = [f"🏢 Nearby Places ({place_type.replace('_', ' ').title()}) around ({latitude:.4f}, {longitude:.4f}):"]
        for p in places:
            name = p.get("displayName", {}).get("text", "Unknown Place")
            address = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            rating = p.get("rating", "N/A")
            p_lat = loc.get("latitude")
            p_lng = loc.get("longitude")
            results.append(f"• {name} (Rating: {rating})\n  Address: {address}\n  Location: ({p_lat}, {p_lng})")

        return "\n".join(results)
    except Exception as e:
        return f"Error searching nearby places: {str(e)}"
