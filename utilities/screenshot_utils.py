"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Screenshot Utilities
============================================================
Captures, stores, and manages test screenshots with
timestamped filenames, failure detection hooks, and
archiving capabilities for reporting.
============================================================
"""
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from PIL import Image, ImageDraw, ImageFont
import base64

from config.config import SCREENSHOT_DIR, SCREENSHOT_ON_FAILURE
from utilities.logger import get_logger

logger = get_logger(__name__)


class ScreenshotUtils:
    """
    Manages screenshot capture and storage for Selenium tests.

    FEATURES:
        - Timestamped filenames (no overwrite collisions)
        - Full-page screenshot via JS scroll-capture
        - Annotated screenshots (add text labels on image)
        - Base64 encoding for embedding in HTML reports
        - Auto-archive by test name and date

    USAGE:
        ss = ScreenshotUtils(driver)
        path = ss.capture("login_failed")
        path = ss.capture_on_failure("test_login_invalid_password")
    """

    def __init__(self, driver: WebDriver, base_dir: Optional[Path] = None):
        self.driver = driver
        self.base_dir = base_dir or SCREENSHOT_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, name: str, subfolder: str = "") -> Path:
        """
        Capture a screenshot and save it with a timestamped filename.

        Args:
            name: Descriptive name for the screenshot
            subfolder: Optional subdirectory (e.g., test class name)

        Returns:
            Path: Absolute path to saved screenshot
        """
        save_dir = self.base_dir / subfolder if subfolder else self.base_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{name}_{timestamp}.png"
        filepath = save_dir / filename

        try:
            self.driver.save_screenshot(str(filepath))
            logger.info("📸 Screenshot saved: %s", filepath)
            return filepath
        except Exception as e:
            logger.error("Failed to capture screenshot: %s", e)
            raise

    def capture_on_failure(self, test_name: str) -> Optional[Path]:
        """
        Capture screenshot only if SCREENSHOT_ON_FAILURE is enabled.
        Used in test teardown / conftest hooks.

        Args:
            test_name: Name of the failing test

        Returns:
            Optional[Path]: Path to screenshot, or None if disabled
        """
        if not SCREENSHOT_ON_FAILURE:
            logger.debug("Screenshot on failure is disabled")
            return None

        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in test_name)
        return self.capture(
            name=f"FAILURE_{safe_name}",
            subfolder="failures",
        )

    def capture_with_annotation(
        self, name: str, annotation: str, subfolder: str = ""
    ) -> Path:
        """
        Capture screenshot and add a text annotation overlay.

        Useful for debugging — annotates the image with a message
        (e.g., "Expected: button visible, Got: button hidden")

        Args:
            name: Screenshot name
            annotation: Text to overlay on the screenshot
            subfolder: Optional subdirectory

        Returns:
            Path: Path to annotated screenshot
        """
        filepath = self.capture(name, subfolder)
        try:
            img = Image.open(filepath)
            draw = ImageDraw.Draw(img)

            # Draw semi-transparent red banner at top
            banner_height = 40
            draw.rectangle([(0, 0), (img.width, banner_height)], fill=(220, 50, 50, 200))

            # Write annotation text
            try:
                font = ImageFont.truetype("arial.ttf", 18)
            except (IOError, OSError):
                font = ImageFont.load_default()

            draw.text((10, 10), f"⚠ {annotation}", fill=(255, 255, 255), font=font)
            img.save(str(filepath))
            logger.debug("Screenshot annotated: %s", annotation)
        except Exception as e:
            logger.warning("Could not annotate screenshot: %s", e)

        return filepath

    def capture_element(self, element, name: str) -> Path:
        """
        Capture a screenshot cropped to a specific WebElement.

        Args:
            element: Selenium WebElement to capture
            name: Screenshot name

        Returns:
            Path: Path to element screenshot
        """
        filepath = self.capture(name, subfolder="elements")
        try:
            img = Image.open(filepath)
            location = element.location
            size = element.size
            left = location["x"]
            top = location["y"]
            right = left + size["width"]
            bottom = top + size["height"]
            cropped = img.crop((left, top, right, bottom))
            cropped.save(str(filepath))
            logger.debug("Element screenshot cropped: %s", name)
        except Exception as e:
            logger.warning("Could not crop element screenshot: %s", e)

        return filepath

    def get_screenshot_as_base64(self) -> str:
        """
        Get current screenshot as Base64 string.
        Used for embedding screenshots directly in HTML/Allure reports.

        Returns:
            str: Base64-encoded PNG image string
        """
        return self.driver.get_screenshot_as_base64()

    def get_screenshot_bytes(self) -> bytes:
        """
        Get current screenshot as raw PNG bytes.

        Returns:
            bytes: PNG image bytes
        """
        return self.driver.get_screenshot_as_png()

    @staticmethod
    def archive_screenshots(archive_name: str = "") -> Path:
        """
        Archive all screenshots into a dated zip file.
        Called at end of test run for reporting.

        Args:
            archive_name: Custom archive name prefix

        Returns:
            Path: Path to the created zip archive
        """
        import zipfile
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = archive_name or f"screenshots_{timestamp}"
        archive_path = SCREENSHOT_DIR / f"{name}.zip"

        screenshots = list(SCREENSHOT_DIR.glob("**/*.png"))
        if not screenshots:
            logger.info("No screenshots to archive")
            return archive_path

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for ss_path in screenshots:
                zf.write(ss_path, ss_path.name)

        logger.info("✓ Archived %d screenshots → %s", len(screenshots), archive_path)
        return archive_path
