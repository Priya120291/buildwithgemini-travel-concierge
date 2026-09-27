"""Firestore database integration and function tools for Travel Concierge Agent."""

from typing import Optional
from google.cloud import firestore

# Hardcoded GCP Project ID (crucial for Agent Platform compatibility)
PROJECT_ID = "qwiklabs-gcp-02-547b57b57d29"


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with the hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def get_destinations(city: Optional[str] = None, category: Optional[str] = None) -> str:
    """Retrieves travel destinations from the Firestore catalog, optionally filtered by city or category.

    Args:
        city: Optional city name to filter destinations (e.g. 'Tokyo', 'Paris', 'Kyoto', 'New York', 'Rome').
        category: Optional category filter (e.g. 'Culture & Shopping', 'Nature & History', 'Art & Architecture', 'Parks & Recreation').

    Returns:
        A summary string of matching destinations found in the catalog.
    """
    db = get_firestore_client()
    collection_ref = db.collection("destinations")

    query = collection_ref

    if city and city.strip():
        # Case-insensitive check helper via client-side filtering if needed, or exact match
        query = query.where("city", "==", city.strip())

    docs = query.stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        if category and category.strip():
            if category.lower() not in data.get("category", "").lower():
                continue

        results.append(
            f"• [{data.get('id')}] {data.get('name')} ({data.get('city')}, {data.get('country')})\n"
            f"  Category: {data.get('category')} | Rating: ⭐{data.get('rating')} | Avg Cost: ${data.get('average_cost_usd')}\n"
            f"  Description: {data.get('description')}\n"
            f"  Tags: {', '.join(data.get('tags', []))}"
        )

    if not results:
        filters = []
        if city:
            filters.append(f"city='{city}'")
        if category:
            filters.append(f"category='{category}'")
        filter_str = f" with {', '.join(filters)}" if filters else ""
        return f"No destinations found in the catalog{filter_str}."

    return f"Found {len(results)} destination(s) in catalog:\n\n" + "\n\n".join(results)


def add_destination(
    id: str,
    name: str,
    city: str,
    country: str,
    category: str,
    description: str,
    average_cost_usd: float = 0.0,
    rating: float = 5.0
) -> str:
    """Adds a new travel destination or updates an existing destination in the Firestore catalog.

    Args:
        id: Unique identifier string for the destination (e.g., 'tokyo-shibuya', 'london-big-ben').
        name: Full name of the destination/attraction.
        city: City where the destination is located.
        country: Country where the destination is located.
        category: Category/type of destination.
        description: Detailed summary of what to experience.
        average_cost_usd: Estimated average cost per visitor in USD.
        rating: Visitor rating score out of 5.0.

    Returns:
        Confirmation message of addition/update in Firestore.
    """
    db = get_firestore_client()
    doc_ref = db.collection("destinations").document(id.strip().lower())

    destination_data = {
        "id": id.strip().lower(),
        "name": name.strip(),
        "city": city.strip(),
        "country": country.strip(),
        "category": category.strip(),
        "description": description.strip(),
        "average_cost_usd": float(average_cost_usd),
        "rating": float(rating),
        "tags": [city.lower(), category.lower()]
    }

    doc_ref.set(destination_data)
    return f"Successfully added/updated destination '{name}' ({id}) in Firestore catalog."
