"""Seed Firestore database for Travel Concierge Agent."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-547b57b57d29"

SEED_DESTINATIONS = [
    {
        "id": "tokyo-shibuya",
        "name": "Shibuya Crossing & Harajuku",
        "city": "Tokyo",
        "country": "Japan",
        "category": "Culture & Shopping",
        "description": "World-famous scramble crossing, trendy fashion boutiques, and street food in Harajuku.",
        "average_cost_usd": 65.0,
        "rating": 4.9,
        "tags": ["landmark", "shopping", "culture", "street-food"]
    },
    {
        "id": "kyoto-arashiyama",
        "name": "Arashiyama Bamboo Grove & Tenryu-ji",
        "city": "Kyoto",
        "country": "Japan",
        "category": "Nature & History",
        "description": "Serene bamboo forest path leading to UNESCO World Heritage Zen temple and monkey park.",
        "average_cost_usd": 30.0,
        "rating": 4.8,
        "tags": ["nature", "temple", "scenic", "photography"]
    },
    {
        "id": "paris-montmartre",
        "name": "Montmartre & Sacré-Cœur Basilica",
        "city": "Paris",
        "country": "France",
        "category": "Art & Architecture",
        "description": "Historic bohemian hilltop neighborhood known for artist studios, cobblestone streets, and panoramic city views.",
        "average_cost_usd": 45.0,
        "rating": 4.7,
        "tags": ["art", "views", "historic", "romantic"]
    },
    {
        "id": "nyc-central-park",
        "name": "Central Park & Bethesda Terrace",
        "city": "New York",
        "country": "United States",
        "category": "Parks & Recreation",
        "description": "Iconic urban green space featuring rowing lakes, walking trails, Bethesda Fountain, and seasonal events.",
        "average_cost_usd": 25.0,
        "rating": 4.9,
        "tags": ["park", "outdoors", "scenic", "family"]
    },
    {
        "id": "kerala-backwaters",
        "name": "Alleppey Backwaters & Houseboats",
        "city": "Alleppey (Alappuzha)",
        "country": "India",
        "category": "Nature & Relaxation",
        "description": "User's favorite destination. Tranquil palm-fringed backwaters, traditional luxury houseboats, and authentic Ayurvedic wellness.",
        "average_cost_usd": 50.0,
        "rating": 5.0,
        "tags": ["favorite", "backwaters", "nature", "relaxation", "kerala"]
    }
]


def seed_database():
    """Populates the destinations collection with initial seed items."""
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")

    print(f"Seeding Firestore collection 'destinations' in project '{PROJECT_ID}'...")

    for item in SEED_DESTINATIONS:
        doc_ref = collection_ref.document(item["id"])
        doc_ref.set(item)
        print(f"  ✓ Seeded document: {item['id']} ({item['name']})")

    print("Seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
