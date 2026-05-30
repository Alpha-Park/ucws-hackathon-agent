"""GenPark browser client.

The client is intentionally honest about setup state. When Playwright or
credentials are unavailable, it returns `requires_setup` instead of pretending a
side effect succeeded.
"""

from __future__ import annotations

import os
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - only used before dependencies are installed
    def load_dotenv() -> bool:
        return False


load_dotenv()


class GenParkClient:
    BASE_URL = "https://genpark.ai"

    def __init__(self):
        self.email = os.getenv("GENPARK_EMAIL")
        self.password = os.getenv("GENPARK_PASSWORD")
        self._browser = None
        self._page = None
        self._playwright = None
        self._logged_in = False

    def _ensure_browser(self) -> tuple[bool, str | None]:
        if self._browser is not None:
            return True, None

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return False, "Playwright is not installed. Install requirements and run `playwright install chromium`."

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._page = self._browser.new_page()
            return True, None
        except Exception as exc:  # pragma: no cover - depends on local browser install
            return False, f"Could not initialize browser automation: {exc}"

    def _ensure_logged_in(self) -> tuple[bool, str | None]:
        if self._logged_in:
            return True, None
        if not self.email or not self.password:
            return False, "GENPARK_EMAIL and GENPARK_PASSWORD are not configured."
        if not self._page:
            return False, "Browser page is not initialized."

        try:
            self._page.goto(f"{self.BASE_URL}/home")
            self._page.click("text=Log in", timeout=5000)
            self._page.fill('input[name="identifier"]', self.email)
            self._page.click("text=Continue")

            password_field = self._page.query_selector('input[type="password"]')
            if password_field:
                password_field.fill(self.password)
                self._page.click("text=Continue")

            self._page.wait_for_timeout(3000)
            self._logged_in = True
            return True, None
        except Exception as exc:  # pragma: no cover - depends on GenPark UI
            return False, f"Login failed: {exc}"

    def post_to_circle(self, content: str, image_url: Optional[str] = None) -> dict:
        browser_ready, browser_error = self._ensure_browser()
        if not browser_ready:
            return {
                "success": False,
                "requires_setup": True,
                "mode": "manual_or_configure_browser",
                "message": "Circle post was not published.",
                "error": browser_error,
                "draft": content,
            }

        logged_in, login_error = self._ensure_logged_in()
        if not logged_in:
            return {
                "success": False,
                "requires_setup": True,
                "mode": "manual_or_configure_credentials",
                "message": "Circle post was not published.",
                "error": login_error,
                "draft": content,
            }

        try:
            self._page.goto(f"{self.BASE_URL}/home/circle")
            textarea = self._page.query_selector('textarea[placeholder*="mind"]')
            if not textarea:
                return {
                    "success": False,
                    "requires_setup": False,
                    "message": "Could not find the Circle post textarea.",
                    "draft": content,
                }

            textarea.fill(content)
            if image_url:
                return {
                    "success": False,
                    "requires_setup": False,
                    "message": "Image attachment is not implemented yet.",
                    "draft": content,
                }

            post_button = self._page.query_selector('button:has-text("Post")')
            if not post_button:
                return {
                    "success": False,
                    "requires_setup": False,
                    "message": "Could not find the Circle post button.",
                    "draft": content,
                }

            post_button.click()
            self._page.wait_for_timeout(2000)
            return {
                "success": True,
                "message": "Posted successfully.",
                "post_url": f"{self.BASE_URL}/home/circle",
            }
        except Exception as exc:  # pragma: no cover - depends on GenPark UI
            return {
                "success": False,
                "requires_setup": False,
                "message": "Circle post failed during browser automation.",
                "error": str(exc),
                "draft": content,
            }

    def close(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
