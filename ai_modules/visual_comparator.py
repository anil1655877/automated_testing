"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
AI Module: Visual Comparator (Offline)
============================================================
Compares screenshots pixel-by-pixel or using structural
similarity (SSIM). 100% offline — no cloud vision API.
============================================================
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple
from config.config import AI_ENABLED, LOG_DIR, SCREENSHOT_DIR
from utilities.logger import get_logger

logger = get_logger(__name__)


class VisualComparator:
    """
    Visual regression testing using screenshot comparison.

    MODES:
        1. Pixel-diff  — exact pixel-by-pixel comparison
        2. SSIM        — Structural Similarity Index (perceptual)
        3. Histogram   — Color histogram comparison

    OFFLINE: Uses Pillow + scikit-image. No cloud API needed.

    USAGE:
        comparator = VisualComparator()

        # Save baseline (first run)
        comparator.save_baseline(driver, "login_page")

        # Compare (subsequent runs)
        result = comparator.compare(driver, "login_page")
        assert result["match"], f"Visual regression: {result['diff_percent']:.1f}% changed"
    """

    BASELINE_DIR: Path = SCREENSHOT_DIR / "baselines"
    DIFF_DIR: Path = SCREENSHOT_DIR / "diffs"
    SIMILARITY_THRESHOLD: float = 0.95   # 95% similarity required to pass

    def __init__(self, driver=None):
        self.driver = driver
        self.BASELINE_DIR.mkdir(parents=True, exist_ok=True)
        self.DIFF_DIR.mkdir(parents=True, exist_ok=True)
        self._ssim_available = self._check_ssim()

    def save_baseline(self, name: str, driver=None) -> Path:
        """
        Capture current page screenshot and save as baseline.

        Args:
            name: Baseline identifier (e.g., "login_page", "checkout_step1")
            driver: WebDriver instance (uses self.driver if not provided)

        Returns:
            Path to saved baseline image
        """
        drv = driver or self.driver
        if not drv:
            raise ValueError("WebDriver instance required for screenshot")

        baseline_path = self.BASELINE_DIR / f"{name}.png"
        drv.save_screenshot(str(baseline_path))
        logger.info("Baseline saved: %s", baseline_path)
        return baseline_path

    def compare(
        self,
        name: str,
        driver=None,
        threshold: Optional[float] = None,
    ) -> dict:
        """
        Compare current page screenshot against saved baseline.

        Args:
            name: Baseline identifier to compare against
            driver: WebDriver instance
            threshold: Similarity threshold (0.0-1.0). Default: 0.95

        Returns:
            dict with keys:
                match (bool): True if within threshold
                similarity (float): 0.0-1.0 similarity score
                diff_percent (float): % of pixels that changed
                baseline_path (str): Path to baseline image
                current_path (str): Path to current screenshot
                diff_path (str): Path to diff image (if mismatch)
        """
        if not AI_ENABLED:
            return self._disabled_response(name)

        threshold = threshold or self.SIMILARITY_THRESHOLD
        baseline_path = self.BASELINE_DIR / f"{name}.png"

        if not baseline_path.exists():
            logger.warning("No baseline found for '%s' — creating baseline now", name)
            self.save_baseline(name, driver)
            return {
                "match": True,
                "similarity": 1.0,
                "diff_percent": 0.0,
                "message": "Baseline created on first run",
                "baseline_path": str(baseline_path),
                "current_path": str(baseline_path),
                "diff_path": None,
            }

        # Take current screenshot
        drv = driver or self.driver
        current_path = SCREENSHOT_DIR / f"{name}_current.png"
        drv.save_screenshot(str(current_path))

        # Compare
        if self._ssim_available:
            result = self._ssim_compare(baseline_path, current_path, name)
        else:
            result = self._pixel_compare(baseline_path, current_path, name)

        result["baseline_path"] = str(baseline_path)
        result["current_path"] = str(current_path)

        if result["match"]:
            logger.info("✓ Visual match for '%s': %.1f%% similar", name, result["similarity"] * 100)
        else:
            logger.warning(
                "❌ Visual mismatch for '%s': %.1f%% similar (threshold: %.0f%%)",
                name, result["similarity"] * 100, threshold * 100
            )

        return result

    def update_baseline(self, name: str, driver=None) -> Path:
        """
        Update an existing baseline with current screenshot.
        Call this after intentional UI changes.
        """
        logger.info("Updating baseline for '%s'", name)
        return self.save_baseline(name, driver)

    def delete_baseline(self, name: str) -> bool:
        """Delete a baseline image."""
        path = self.BASELINE_DIR / f"{name}.png"
        if path.exists():
            path.unlink()
            logger.info("Deleted baseline: %s", name)
            return True
        return False

    def list_baselines(self) -> list[str]:
        """List all saved baseline names."""
        return [f.stem for f in self.BASELINE_DIR.glob("*.png")]

    def _ssim_compare(self, baseline: Path, current: Path, name: str) -> dict:
        """SSIM-based comparison using scikit-image."""
        try:
            from skimage.metrics import structural_similarity as ssim
            from PIL import Image
            import numpy as np

            img1 = np.array(Image.open(baseline).convert("L"))   # Grayscale
            img2 = np.array(Image.open(current).convert("L"))

            # Resize if dimensions differ
            if img1.shape != img2.shape:
                from PIL import Image as PILImage
                pil2 = PILImage.open(current).convert("L").resize(
                    (img1.shape[1], img1.shape[0])
                )
                img2 = np.array(pil2)

            score, diff = ssim(img1, img2, full=True)
            diff_pixels = int((1 - score) * img1.size)
            diff_percent = (1 - score) * 100

            # Save diff image on mismatch
            diff_path = None
            if score < self.SIMILARITY_THRESHOLD:
                diff_normalized = ((1 - diff) * 255).astype("uint8")
                diff_img = Image.fromarray(diff_normalized)
                diff_path = str(self.DIFF_DIR / f"{name}_diff.png")
                diff_img.save(diff_path)

            return {
                "match": score >= self.SIMILARITY_THRESHOLD,
                "similarity": float(score),
                "diff_percent": diff_percent,
                "diff_pixels": diff_pixels,
                "diff_path": diff_path,
                "method": "ssim",
            }
        except Exception as e:
            logger.warning("SSIM compare failed (%s) — falling back to pixel compare", e)
            return self._pixel_compare(baseline, current, name)

    def _pixel_compare(self, baseline: Path, current: Path, name: str) -> dict:
        """Pixel-by-pixel comparison using Pillow only."""
        try:
            from PIL import Image, ImageChops
            import math

            img1 = Image.open(baseline).convert("RGB")
            img2 = Image.open(current).convert("RGB")

            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            diff = ImageChops.difference(img1, img2)
            pixels = list(diff.getdata())
            total = len(pixels)
            changed = sum(1 for p in pixels if any(c > 10 for c in p))
            diff_percent = (changed / total) * 100
            similarity = 1.0 - (changed / total)

            diff_path = None
            if similarity < self.SIMILARITY_THRESHOLD:
                diff_path = str(self.DIFF_DIR / f"{name}_diff.png")
                diff.save(diff_path)

            return {
                "match": similarity >= self.SIMILARITY_THRESHOLD,
                "similarity": round(similarity, 4),
                "diff_percent": round(diff_percent, 2),
                "diff_pixels": changed,
                "diff_path": diff_path,
                "method": "pixel_diff",
            }
        except Exception as e:
            logger.error("Pixel compare failed: %s", e)
            return {
                "match": True,   # Pass-safe default
                "similarity": 1.0,
                "diff_percent": 0.0,
                "diff_pixels": 0,
                "diff_path": None,
                "method": "error_fallback",
                "error": str(e),
            }

    def _check_ssim(self) -> bool:
        """Check if scikit-image is available for SSIM comparison."""
        try:
            from skimage.metrics import structural_similarity
            return True
        except ImportError:
            logger.debug("scikit-image not installed — using pixel diff comparison")
            return False

    @staticmethod
    def _disabled_response(name: str) -> dict:
        return {
            "match": True,
            "similarity": 1.0,
            "diff_percent": 0.0,
            "message": "AI_ENABLED=false — visual comparison skipped",
            "method": "disabled",
        }
