import os
import json
import logging
from playwright.sync_api import sync_playwright

class SAPQDOMRelay:
    """
    SAPQ Phase 18: DOM Relay Middleware (sapq_dom_relay.py)
    - Generates a static/dynamic Navigation Map of interactive elements.
    - Dispatches logical DOM events to bypass pixel offset errors.
    - Captures DOM state delta and console errors.
    """
    def __init__(self, target_url):
        self.target = target_url
        self.logger = logging.getLogger("SAPQDOMRelay")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)

    def _get_page(self, playwright):
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        # Convert local path to file:// if not a URL
        url = self.target if self.target.startswith(('http://', 'https://', 'file://')) else f"file://{os.path.abspath(self.target)}"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
        except Exception as e:
            self.logger.warning(f"Page load timeout or error: {e}")

        return browser, page

    def generate_navigation_map(self):
        """
        Extracts interactive elements and their handler references into a JSON-friendly map.
        """
        with sync_playwright() as p:
            browser, page = self._get_page(p)

            nav_map = page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('button, a, input, select, [onclick]'));
                return elements.map((el, index) => {
                    // Create a unique CSS selector for targeting
                    let selector = el.tagName.toLowerCase();
                    if (el.id) {
                        selector = `#${el.id}`;
                    } else if (el.className && typeof el.className === 'string') {
                        selector += `.${el.className.trim().replace(/\\s+/g, '.')}`;
                    }

                    return {
                        id: el.id || null,
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText ? el.innerText.trim().substring(0, 50) : null,
                        onclick: el.getAttribute('onclick') || null,
                        href: el.getAttribute('href') || null,
                        selector: selector
                    };
                });
            }""")

            browser.close()
            return nav_map

    def dispatch_event_and_capture(self, selector, event_type="click", wait_ms=500):
        """
        Logically dispatches an event on a selector and captures the before/after state.
        """
        with sync_playwright() as p:
            browser, page = self._get_page(p)

            console_messages = []
            page_errors = []

            page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # Capture initial DOM
            before_html = page.content()

            try:
                locator = page.locator(selector).first
                # Use dispatch_event to trigger logically, bypassing UI pixel issues
                locator.dispatch_event(event_type)
                # Wait briefly for synchronous mutations or short async
                page.wait_for_timeout(wait_ms)
            except Exception as e:
                browser.close()
                return {"error": str(e), "success": False}

            after_html = page.content()
            dom_changed = before_html != after_html

            # To provide meaningful delta without huge strings, we can just say if it changed and by how much length
            delta_info = {
                "changed": dom_changed,
                "length_diff": len(after_html) - len(before_html)
            }

            browser.close()

            return {
                "success": True,
                "selector": selector,
                "event_type": event_type,
                "dom_delta": delta_info,
                "console_messages": console_messages,
                "page_errors": page_errors
            }

    def execute_scenario(self, scenario_steps):
        """
        Phase 22: Playwright Relay E2E Multi-Step Scenario Macro
        Executes a sequence of actions (click, fill, wait, assert_text, assert_style).
        scenario_steps format:
        [
            {"action": "fill", "selector": "#input1", "value": "test"},
            {"action": "click", "selector": "#btn1"},
            {"action": "wait", "ms": 1000},
            {"action": "assert_text", "selector": "#res", "expected": "Success"}
        ]
        """
        with sync_playwright() as p:
            browser, page = self._get_page(p)

            console_messages = []
            page_errors = []

            page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            initial_html = page.content()
            step_results = []

            for step_idx, step in enumerate(scenario_steps):
                action = step.get("action")
                selector = step.get("selector")
                result = {"step": step_idx, "action": action, "success": True, "error": None}

                try:
                    if action == "click":
                        locator = page.locator(selector).first
                        locator.dispatch_event("click")
                    elif action == "fill":
                        # Range sliders often fail with fill, so we use evaluate + dispatchEvent
                        value = step.get("value")
                        locator = page.locator(selector).first
                        locator.evaluate(f"(el) => {{ el.value = '{value}'; }}")
                        locator.dispatch_event("input")
                        locator.dispatch_event("change")
                    elif action == "wait":
                        page.wait_for_timeout(step.get("ms", 500))
                    elif action == "assert_text":
                        locator = page.locator(selector).first
                        text = locator.inner_text()
                        if text != step.get("expected"):
                            result["success"] = False
                            result["error"] = f"Expected text '{step.get('expected')}', got '{text}'"
                    elif action == "assert_style":
                        locator = page.locator(selector).first
                        prop = step.get("property")
                        expected = step.get("expected")
                        actual = locator.evaluate(f"(el) => window.getComputedStyle(el).getPropertyValue('{prop}')")
                        if actual != expected:
                            result["success"] = False
                            result["error"] = f"Expected style {prop}='{expected}', got '{actual}'"
                    else:
                        result["success"] = False
                        result["error"] = f"Unknown action: {action}"

                except Exception as e:
                    result["success"] = False
                    result["error"] = str(e)

                step_results.append(result)

                # Halt scenario if an assertion or action fails
                if not result["success"]:
                    break

            final_html = page.content()
            delta_info = {
                "changed": initial_html != final_html,
                "length_diff": len(final_html) - len(initial_html)
            }

            browser.close()

            return {
                "scenario_completed": all(r["success"] for r in step_results),
                "steps": step_results,
                "dom_delta": delta_info,
                "console_messages": console_messages,
                "page_errors": page_errors
            }
