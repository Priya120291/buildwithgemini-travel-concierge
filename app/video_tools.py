"""Video generation tool for Travel Concierge Agent."""

import uuid
import base64
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-02-547b57b57d29"
BUCKET_NAME = "travel-concierge-public-qwiklabs-gcp-02-547b57b57d29"


async def generate_destination_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short promotional or scenic travel video for a destination, landmark, or attraction using gemini-omni-flash-preview in the global region.

    Saves the video as an artifact in the Dev UI Playground and uploads the video bytes to the public Cloud Storage bucket.

    Args:
        prompt: Detailed video description (e.g. 'A 3-second aerial video of Kerala backwaters with houseboats and palm trees').
        tool_context: ADK ToolContext instance for saving artifacts.

    Returns:
        The public HTTPS URL of the uploaded MP4 video in Cloud Storage (https://storage.googleapis.com/<bucket>/<object>).
    """
    if not prompt or not prompt.strip():
        return "Please provide a descriptive prompt for video generation."

    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        if not hasattr(interaction, "output_video") or not interaction.output_video:
            return "Failed to generate video: No video output returned from model."

        data_attr = getattr(interaction.output_video, "data", None)
        if not data_attr:
            return "Failed to extract video bytes from model output."

        video_bytes = base64.b64decode(data_attr)
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"

        # (1) Save video artifact in Playground Dev UI
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # (2) Upload video bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url

    except Exception as e:
        return f"Error generating destination video: {str(e)}"
