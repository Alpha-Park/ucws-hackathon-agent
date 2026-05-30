"""
Circle Posting Tool - Post content to GenPark Circle.
"""

from typing import Optional

from ..browser.genpark_client import GenParkClient


def post_to_circle(
    content: str,
    image_url: Optional[str] = None,
) -> dict:
    """
    Post content to the GenPark Circle community feed.
    
    Use this when the user wants to share thoughts, product reviews, 
    or any content with the GenPark community.
    
    Args:
        content: The text content to post. Can include markdown formatting,
                 hashtags, and mentions.
        image_url: Optional URL to an image to attach to the post.
    
    Returns:
        A dict with 'success' (bool) and 'message' (str) indicating the result.
    
    Example:
        post_to_circle("Just discovered this amazing AI gadget! #GenParkAI #TechFinds")
    """
    if not content or not content.strip():
        return {
            "success": False,
            "message": "Content cannot be empty. Please provide some text to post."
        }
    
    if len(content) > 2000:
        return {
            "success": False,
            "message": f"Content is too long ({len(content)} chars). Maximum is 2000 characters."
        }
    
    try:
        client = GenParkClient()
        result = client.post_to_circle(content, image_url)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"✅ Successfully posted to Circle! Your post is now live.",
                "post_url": result.get("post_url", "https://genpark.ai/home/circle")
            }
        else:
            return {
                "success": False,
                "message": f"Failed to post: {result.get('error', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error posting to Circle: {str(e)}"
        }
