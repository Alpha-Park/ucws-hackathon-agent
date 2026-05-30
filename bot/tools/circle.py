"""Circle Posting Tool - draft and publish content to GenPark Circle."""

from typing import Optional

from bot.browser.genpark_client import GenParkClient


def post_to_circle(
    content: str,
    image_url: Optional[str] = None,
) -> dict:
    """
    Post content to GenPark Circle.

    This function never returns a fake success. If browser automation or
    credentials are missing, it returns a setup-required result so the agent can
    keep product authenticity clear during evaluation.
    """
    if not content or not content.strip():
        return {
            "success": False,
            "message": "Content cannot be empty. Please provide some text to post.",
        }

    if len(content) > 2000:
        return {
            "success": False,
            "message": f"Content is too long ({len(content)} chars). Maximum is 2000 characters.",
        }

    client = GenParkClient()
    try:
        return client.post_to_circle(content, image_url)
    finally:
        client.close()
