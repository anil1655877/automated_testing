"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
AI Module: Self-Healing Locator
============================================================
Automatically finds elements when primary locators fail,
using fuzzy matching and alternative selector strategies.
100% OFFLINE — no AI API required.
============================================================
"""
from __future__ import annotations
import re
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from fuzzywuzzy import fuzz
from config.config import AI_ENABLED, SELF_HEALING_ENABLED
from utilities.logger import get_logger

logger = get_logger(__name__)

Locator = tuple[str, str]


class SelfHealingLocator:
    """
    Self-healing element locator that recovers from broken selectors.

    CONCEPT (Interview Answer):
        Traditional automation breaks when locators change (e.g., ID changes,
        CSS class renamed). Self-healing locators try multiple fallback strategies
        to find the same element without requiring manual maintenance.

    HOW IT WORKS:
        1. Try the PRIMARY locator (as coded by developer)
        2. If fails → try ALTERNATIVE locators (ID from CSS, CSS from ID, etc.)
        3. If fails → try FUZZY TEXT matching (finds button with similar text)
        4. If fails → try ATTRIBUTE scanning (name, placeholder, aria-label, data-*)
        5. Log the healing event so developer can update primary locator

    USAGE:
        healer = SelfHealingLocator(driver)
        element = healer.find(
            primary=(By.ID, "submit-btn"),
            fallbacks=[
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(),'Submit')]"),
            ],
            element_description="Submit button",
        )
    """

    # Healing event log (in-memory for session)
    _healing_log: list[dict] = []

    def __init__(self, driver: WebDriver):
        self.driver = driver
        logger.debug("SelfHealingLocator initialized")

    def find(
        self,
        primary: Locator,
        fallbacks: Optional[list[Locator]] = None,
        element_description: str = "",
        fuzzy_text: Optional[str] = None,
    ) -> WebElement:
        """
        Find element with self-healing capability.

        Args:
            primary: Primary locator (By.*, selector)
            fallbacks: List of fallback locators to try if primary fails
            element_description: Human-readable element name for logging
            fuzzy_text: If provided, also try fuzzy text matching

        Returns:
            WebElement: The found element

        Raises:
            NoSuchElementException: If all strategies fail
        """
        if not (AI_ENABLED and SELF_HEALING_ENABLED):
            # Self-healing disabled — use primary locator only
            return self.driver.find_element(*primary)

        name = element_description or str(primary)

        # ── Strategy 1: Primary Locator ───────────────────────
        element = self._try_locator(primary)
        if element:
            return element

        logger.warning("Primary locator failed for '%s': %s", name, primary)

        # ── Strategy 2: Fallback Locators ─────────────────────
        for fallback in (fallbacks or []):
            element = self._try_locator(fallback)
            if element:
                self._log_healing(name, primary, fallback, "fallback_locator")
                logger.info("🔧 Self-healed '%s' using fallback: %s", name, fallback)
                return element

        # ── Strategy 3: Auto-generated Alternatives ───────────
        auto_alternatives = self._generate_alternatives(primary)
        for alt in auto_alternatives:
            element = self._try_locator(alt)
            if element:
                self._log_healing(name, primary, alt, "auto_alternative")
                logger.info("🔧 Self-healed '%s' via auto-alternative: %s", name, alt)
                return element

        # ── Strategy 4: Fuzzy Text Matching ───────────────────
        if fuzzy_text:
            element = self._fuzzy_find(fuzzy_text)
            if element:
                found_locator = (By.XPATH, f"//*[contains(text(),'{fuzzy_text[:20]}')]")
                self._log_healing(name, primary, found_locator, "fuzzy_text")
                logger.info("🔧 Self-healed '%s' via fuzzy text match: '%s'", name, fuzzy_text)
                return element

        # ── Strategy 5: Attribute Scan ────────────────────────
        element = self._attribute_scan(primary)
        if element:
            self._log_healing(name, primary, ("attribute_scan", str(primary)), "attribute_scan")
            logger.info("🔧 Self-healed '%s' via attribute scan", name)
            return element

        # All strategies exhausted
        logger.error("❌ Self-healing FAILED for '%s'. All %d strategies exhausted.",
                     name, 4 + len(fallbacks or []))
        raise NoSuchElementException(
            f"Element '{name}' not found after self-healing attempts.\n"
            f"Primary: {primary}\n"
            f"Tried {len(auto_alternatives)} auto-alternatives + {len(fallbacks or [])} fallbacks\n"
            f"Check healing_log.json for update suggestions."
        )

    def _try_locator(self, locator: Locator) -> Optional[WebElement]:
        """Attempt to find element with given locator. Returns None on failure."""
        try:
            return self.driver.find_element(*locator)
        except (NoSuchElementException, Exception):
            return None

    def _generate_alternatives(self, primary: Locator) -> list[Locator]:
        """
        Generate alternative locators from the primary locator.

        EXAMPLES:
            (By.ID, "login-btn") →
                (By.CSS_SELECTOR, "#login-btn")
                (By.XPATH, "//*[@id='login-btn']")
                (By.NAME, "login-btn")

            (By.CSS_SELECTOR, ".btn-primary") →
                (By.XPATH, "//*[@class='btn-primary']")
                (By.CSS_SELECTOR, "[class*='btn-primary']")
        """
        by, value = primary
        alternatives = []

        if by == By.ID:
            alternatives.extend([
                (By.CSS_SELECTOR, f"#{value}"),
                (By.XPATH, f"//*[@id='{value}']"),
                (By.NAME, value),
                (By.CSS_SELECTOR, f"[data-testid='{value}']"),
                (By.CSS_SELECTOR, f"[data-id='{value}']"),
            ])
        elif by == By.CSS_SELECTOR:
            if value.startswith("#"):
                # CSS ID selector → try as ID
                id_val = value.lstrip("#")
                alternatives.extend([
                    (By.ID, id_val),
                    (By.XPATH, f"//*[@id='{id_val}']"),
                ])
            elif value.startswith("."):
                class_val = value.lstrip(".")
                alternatives.extend([
                    (By.CLASS_NAME, class_val),
                    (By.XPATH, f"//*[@class='{class_val}']"),
                    (By.XPATH, f"//*[contains(@class,'{class_val}')]"),
                ])
            else:
                # Generic CSS → try partial match
                alternatives.append((By.XPATH, f"//*[@{value.split('[')[0]}]") if "[" in value else
                                    (By.XPATH, f"//*[contains(@class,'{value}')]"))
        elif by == By.XPATH:
            # Extract text from xpath and try CSS
            text_match = re.search(r"text\(\)='([^']+)'", value)
            if text_match:
                text = text_match.group(1)
                alternatives.extend([
                    (By.LINK_TEXT, text),
                    (By.PARTIAL_LINK_TEXT, text[:10]),
                    (By.XPATH, f"//*[contains(text(),'{text}')]"),
                ])
        elif by == By.NAME:
            alternatives.extend([
                (By.CSS_SELECTOR, f"[name='{value}']"),
                (By.XPATH, f"//*[@name='{value}']"),
                (By.ID, value),
            ])

        return alternatives

    def _fuzzy_find(self, target_text: str, min_score: int = 70) -> Optional[WebElement]:
        """
        Find element using fuzzy text matching.
        Finds the element whose text is most similar to target_text.

        Args:
            target_text: Text to match against
            min_score: Minimum fuzzy match score (0-100)
        """
        candidates = []
        try:
            all_elements = self.driver.find_elements(
                By.XPATH, "//*[string-length(normalize-space(text())) > 0]"
            )
            for el in all_elements[:100]:  # Limit to avoid performance issues
                try:
                    text = el.text.strip()
                    if text:
                        score = fuzz.ratio(target_text.lower(), text.lower())
                        if score >= min_score:
                            candidates.append((score, el, text))
                except Exception:
                    continue
        except Exception as e:
            logger.debug("Fuzzy search error: %s", e)
            return None

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_el, best_text = candidates[0]
            logger.debug("Fuzzy match: '%s' ≈ '%s' (score=%d)", target_text, best_text, best_score)
            return best_el
        return None

    def _attribute_scan(self, primary: Locator) -> Optional[WebElement]:
        """
        Scan elements by common attributes related to the primary locator value.

        Tries aria-label, placeholder, title, data-testid with the selector value.
        """
        _, value = primary
        # Extract meaningful keyword from the selector
        keyword = re.sub(r'[#.\[\]>*=\'"]', "", value).strip().split()[0]
        if not keyword or len(keyword) < 2:
            return None

        attribute_selectors = [
            f"[aria-label*='{keyword}']",
            f"[placeholder*='{keyword}']",
            f"[title*='{keyword}']",
            f"[data-testid*='{keyword}']",
            f"[data-cy*='{keyword}']",
            f"[alt*='{keyword}']",
        ]
        for selector in attribute_selectors:
            el = self._try_locator((By.CSS_SELECTOR, selector))
            if el:
                return el
        return None

    def _log_healing(
        self, element_name: str, primary: Locator, healed: Locator, strategy: str
    ) -> None:
        """Log healing event to file for developer review."""
        event = {
            "element": element_name,
            "primary_locator": str(primary),
            "healed_locator": str(healed),
            "strategy": strategy,
        }
        self.__class__._healing_log.append(event)
        try:
            from config.config import LOG_DIR
            import json
            log_file = LOG_DIR / "self_healing_log.json"
            with open(log_file, "w") as f:
                json.dump(self.__class__._healing_log, f, indent=2)
        except Exception:
            pass

    @classmethod
    def get_healing_report(cls) -> list[dict]:
        """Get all self-healing events from current session."""
        return cls._healing_log.copy()
