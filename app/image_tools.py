"""Image generation tool for Travel Concierge Agent."""

import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-02-547b57b57d29"
BUCKET_NAME = "travel-concierge-public-qwiklabs-gcp-02-547b57b57d29"


async def generate_destination_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates a visual image for a travel destination or attraction using gemini-3.1-flash-lite-image in the global region.

    Saves the image as an artifact in the Dev UI Playground and uploads the image bytes to the public Cloud Storage bucket.

    Args:
        prompt: Detailed image generation prompt (e.g. 'A vibrant twilight scene of Tokyo Tower with cherry blossoms').
        tool_context: ADK ToolContext instance for saving artifacts.

    Returns:
        The public HTTPS URL of the uploaded image in Cloud Storage.
    """
    if not prompt or not prompt.strip():
        return "Please provide a descriptive prompt for image generation."

    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        candidates = getattr(response, "candidates", [])
        if not candidates or not candidates[0].content.parts:
            return "Failed to generate image: No image parts returned from Gemini model."

        part = candidates[0].content.parts[0]
        if not hasattr(part, "inline_data") or not part.inline_data:
            return "Failed to extract inline image data from model response."

        image_bytes = part.inline_data.data
        filename = f"destination_{uuid.uuid4().hex[:8]}.jpg"

        # (1) Save image artifact in Playground Dev UI
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # (2) Upload image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/jpeg")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"🖼️ Image generated successfully!\n• Artifact saved: {filename}\n• Public URL: {public_url}"

    except Exception as e:
        return f"Error generating destination image: {str(e)}"
