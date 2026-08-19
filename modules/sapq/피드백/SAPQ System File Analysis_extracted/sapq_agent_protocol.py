import json
from .sapq_dom_relay import SAPQDOMRelay
from .sapq_sandbox_proxy import SAPQSandboxProxy

class SAPQAgentProtocol:
    """
    SAPQ Phase 18.3: Agent Bidirectional Feedback Protocol
    - Standardizes communication between the AI Agent and the SAPQ DOM Relay.
    - Consumes raw actions and returns structured JSON responses.
    """
    def __init__(self, target_filepath, proxy_port=8000):
        self.proxy = SAPQSandboxProxy(port=proxy_port)
        self.proxy.start()

        url = self.proxy.get_url(target_filepath)
        self.relay = SAPQDOMRelay(url)

    def __del__(self):
        if hasattr(self, 'proxy'):
            self.proxy.stop()

    def request_navigation_map(self):
        """Returns the available interactive elements on the page."""
        try:
            nav_map = self.relay.generate_navigation_map()
            return self._format_response("success", data={"navigation_map": nav_map})
        except Exception as e:
            return self._format_response("error", errors=[str(e)])

    def dispatch_action(self, selector, action="click"):
        """Dispatches an action and returns the delta and any errors."""
        try:
            result = self.relay.dispatch_event_and_capture(selector, event_type=action)
            if result.get("success"):
                return self._format_response("success", data={
                    "delta": result.get("dom_delta"),
                    "console_messages": result.get("console_messages"),
                    "page_errors": result.get("page_errors")
                })
            else:
                return self._format_response("error", errors=[result.get("error")])
        except Exception as e:
            return self._format_response("error", errors=[str(e)])

    def _format_response(self, status, data=None, errors=None):
        return json.dumps({
            "protocol": "SAPQ_AGENT_FEEDBACK_V1",
            "status": status,
            "data": data or {},
            "errors": errors or []
        }, indent=2)

    def shutdown(self):
        """Manually shuts down the proxy server."""
        self.proxy.stop()
