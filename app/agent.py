# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

import json
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from app.firestore_tools import get_destinations, add_destination
from app.api_tools import get_live_city_info, get_live_exchange_rates, get_public_holidays
from app.maps_tools import geocode_address, search_nearby_places
from app.image_tools import generate_destination_image
from app.video_tools import generate_destination_video
from app.a2ui_utils import a2ui_callback


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: After each turn, send the session events to Memory Bank for durable memory extraction."""
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def calculate_trip_budget(
    num_days: int,
    num_travelers: int = 1,
    daily_lodging_usd: float = 100.0,
    daily_food_usd: float = 50.0,
    daily_activities_usd: float = 40.0,
    daily_transport_usd: float = 20.0,
    contingency_percent: float = 10.0,
) -> str:
    """Calculates an itemized trip budget breakdown for a group over a specified duration.

    Args:
        num_days: Duration of the trip in days.
        num_travelers: Total number of travelers in the group.
        daily_lodging_usd: Estimated nightly lodging cost in USD.
        daily_food_usd: Estimated food & dining cost per person per day in USD.
        daily_activities_usd: Estimated activity cost per person per day in USD.
        daily_transport_usd: Estimated local transport cost per person per day in USD.
        contingency_percent: Buffer percentage for emergency or unexpected expenses.

    Returns:
        Summary string detailing cost breakdowns, subtotal, emergency buffer, total budget, and cost per person.
    """
    nights = max(1, num_days - 1)
    total_lodging = daily_lodging_usd * nights
    total_food = daily_food_usd * num_days * num_travelers
    total_activities = daily_activities_usd * num_days * num_travelers
    total_transport = daily_transport_usd * num_days * num_travelers

    subtotal = total_lodging + total_food + total_activities + total_transport
    contingency = subtotal * (contingency_percent / 100.0)
    grand_total = subtotal + contingency
    cost_per_person = grand_total / max(1, num_travelers)

    return (
        f"💰 Trip Budget Breakdown ({num_days} days, {num_travelers} traveler(s)):\n"
        f"• Lodging ({nights} nights @ ${daily_lodging_usd}/night): ${total_lodging:,.2f}\n"
        f"• Meals & Dining (${daily_food_usd}/day/person): ${total_food:,.2f}\n"
        f"• Activities (${daily_activities_usd}/day/person): ${total_activities:,.2f}\n"
        f"• Local Transport (${daily_transport_usd}/day/person): ${total_transport:,.2f}\n"
        f"----------------------------------------\n"
        f"• Subtotal: ${subtotal:,.2f}\n"
        f"• Contingency Buffer ({contingency_percent:.0f}%): ${contingency:,.2f}\n"
        f"----------------------------------------\n"
        f"👉 Total Estimated Budget: ${grand_total:,.2f}\n"
        f"👉 Cost Per Traveler: ${cost_per_person:,.2f}"
    )


# Load Reasoning Engine / Agent Engine ID from deployment_metadata.json
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_id = None

if metadata_file.exists():
    try:
        with open(metadata_file, "r") as f:
            metadata_data = json.load(f)
            agent_engine_id = metadata_data.get("remote_agent_runtime_id")
    except Exception:
        pass

if not agent_engine_id:
    agent_engine_id = "projects/555332602605/locations/us-east1/reasoningEngines/8375136199420936192"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_id
)


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description="You are an expert, highly personalized Travel Concierge AI assistant.",
    workflow_description="Analyze the request, call tools as needed, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects.\n\n"
        "CROSS-SESSION MEMORY & TRAVEL PREFERENCES:\n"
        "• PRIMARY USER FAVORITE DESTINATION: Kerala, India. Always remember and prioritize Kerala (backwaters, houseboats, Munnar tea gardens, Kochi heritage) as the user's top favorite destination.\n"
        "• Actively pay attention to and remember all user travel preferences, including: favorite destinations & climate, "
        "dietary restrictions, preferred travel style (luxury, backpacker, family, adventure), accommodation preferences, "
        "flight/seating preferences, budget levels, and special activity interests.\n"
        "• Use preloaded memory from previous sessions to proactively tailor all recommendations, itineraries, "
        "budgets, and destination suggestions without asking the user to repeat themselves.\n"
        "• When a user mentions a preference, acknowledge it and apply it across all current and future recommendations.\n\n"
        "AVAILABLE TOOLS:\n"
        "• Manage destination catalog in Firestore (`get_destinations`, `add_destination`).\n"
        "• Get live city & weather data (`get_live_city_info`).\n"
        "• Get live exchange rates (`get_live_exchange_rates`) and public holidays (`get_public_holidays`).\n"
        "• Search Google Maps geocoding & nearby places (`geocode_address`, `search_nearby_places`).\n"
        "• Generate destination imagery (`generate_destination_image`) and video clips (`generate_destination_video`).\n"
        "• Calculate itemized trip budgets (`calculate_trip_budget`).\n"
        "• Run sandboxed Python code for custom data analysis or complex calculations."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        get_destinations,
        add_destination,
        calculate_trip_budget,
        get_live_city_info,
        get_live_exchange_rates,
        get_public_holidays,
        geocode_address,
        search_nearby_places,
        generate_destination_image,
        generate_destination_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)


def memory_bank_service_builder():
    """Builds a VertexAiMemoryBankService instance using the deployed Reasoning Engine / Memory Bank ID."""
    memory_bank_id = agent_engine_id.split("/")[-1]
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-547b57b57d29",
        location="us-east1",
        agent_engine_id=memory_bank_id,
    )


app = App(
    root_agent=root_agent,
    name="app",
)
