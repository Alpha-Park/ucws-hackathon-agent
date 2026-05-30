"""
GenPark Browser Client - Playwright-based automation for GenPark.ai.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GenParkClient:
    """
    Browser automation client for GenPark.ai.
    
    Uses Playwright to interact with GenPark when no API is available.
    Falls back to mock responses when browser automation is not configured.
    """
    
    BASE_URL = "https://genpark.ai"
    
    def __init__(self):
        """Initialize the GenPark client."""
        self.email = os.getenv("GENPARK_EMAIL")
        self.password = os.getenv("GENPARK_PASSWORD")
        self._browser = None
        self._page = None
        self._logged_in = False
    
    def _ensure_browser(self):
        """Ensure browser is initialized (lazy loading)."""
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(headless=True)
                self._page = self._browser.new_page()
            except ImportError:
                # Playwright not installed, will use mock responses
                pass
            except Exception as e:
                print(f"Warning: Could not initialize browser: {e}")
    
    def _ensure_logged_in(self) -> bool:
        """Ensure user is logged in to GenPark."""
        if self._logged_in:
            return True
        
        if not self._page:
            return False
        
        if not self.email or not self.password:
            print("Warning: GENPARK_EMAIL and GENPARK_PASSWORD not set in .env")
            return False
        
        try:
            # Navigate to login page
            self._page.goto(f"{self.BASE_URL}/home")
            
            # Click login button
            self._page.click("text=Log in")
            self._page.wait_for_timeout(2000)
            
            # Enter credentials
            self._page.fill('input[name="identifier"]', self.email)
            self._page.click("text=Continue")
            self._page.wait_for_timeout(2000)
            
            # Enter password (if password field appears)
            password_field = self._page.query_selector('input[type="password"]')
            if password_field:
                password_field.fill(self.password)
                self._page.click("text=Continue")
                self._page.wait_for_timeout(3000)
            
            self._logged_in = True
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def post_to_circle(self, content: str, image_url: Optional[str] = None) -> dict:
        """
        Post content to GenPark Circle.
        
        Args:
            content: The text content to post.
            image_url: Optional image URL to attach.
        
        Returns:
            Dict with success status and message.
        """
        self._ensure_browser()
        
        if not self._page:
            # Return mock success for demo purposes
            return {
                "success": True,
                "message": "Posted successfully (demo mode)",
                "post_url": f"{self.BASE_URL}/home/circle"
            }
        
        if not self._ensure_logged_in():
            return {
                "success": False,
                "error": "Not logged in. Please set GENPARK_EMAIL and GENPARK_PASSWORD in .env"
            }
        
        try:
            # Navigate to Circle
            self._page.goto(f"{self.BASE_URL}/home/circle")
            self._page.wait_for_timeout(2000)
            
            # Find and fill the post textarea
            textarea = self._page.query_selector('textarea[placeholder*="mind"]')
            if textarea:
                textarea.fill(content)
                self._page.wait_for_timeout(500)
                
                # Click post button
                post_button = self._page.query_selector('button:has-text("Post")')
                if post_button:
                    post_button.click()
                    self._page.wait_for_timeout(2000)
                    
                    return {
                        "success": True,
                        "message": "Posted successfully",
                        "post_url": f"{self.BASE_URL}/home/circle"
                    }
            
            return {
                "success": False,
                "error": "Could not find post textarea"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_to_collection(self, product_id: str) -> dict:
        """Add a product to the user's collection."""
        # Mock implementation
        return {
            "success": True,
            "message": f"Added product {product_id} to collection"
        }
    
    def get_collection(self) -> dict:
        """Get the user's collection."""
        # Mock implementation - return sample data
        return {
            "success": True,
            "items": [
                {
                    "product_id": "prod_001",
                    "product_name": "AI Smart Speaker Pro",
                    "product_url": f"{self.BASE_URL}/product/prod_001"
                },
                {
                    "product_id": "prod_003",
                    "product_name": "Ergonomic Desk Chair",
                    "product_url": f"{self.BASE_URL}/product/prod_003"
                },
            ]
        }
    
    def remove_from_collection(self, product_id: str) -> dict:
        """Remove a product from the user's collection."""
        # Mock implementation
        return {
            "success": True,
            "message": f"Removed product {product_id} from collection"
        }
    
    def search_products(self, query: str) -> dict:
        """Search for products on GenPark."""
        # Mock implementation - would scrape search results in production
        return {
            "success": True,
            "results": [],
            "count": 0
        }
    
    def get_feed(self) -> dict:
        """Get the current GenPark feed."""
        # Mock implementation
        return {
            "success": True,
            "items": []
        }
    
    def close(self):
        """Close the browser."""
        if self._browser:
            self._browser.close()
        if hasattr(self, '_playwright') and self._playwright:
            self._playwright.stop()
