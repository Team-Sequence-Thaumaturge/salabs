import os
import threading
import http.server
import socketserver
import time
import logging

class SAPQSandboxProxy:
    """
    SAPQ Phase 18.2: Local Mirroring Sandbox Proxy
    - Spins up a local HTTP server in a background thread to bypass external live domain security blocks.
    - Allows the AI Agent (via Playwright) to test external logic locally without triggering security sandbox policies.
    """
    def __init__(self, directory=".", port=8000):
        self.directory = os.path.abspath(directory)
        self.port = port
        self.httpd = None
        self.thread = None
        self.logger = logging.getLogger("SAPQSandboxProxy")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)

    def start(self):
        """Starts the proxy server in a background thread."""
        if self.httpd is not None:
            self.logger.warning("Sandbox Proxy is already running.")
            return

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, directory=None, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

            def log_message(self, format, *args):
                # Suppress standard HTTP logs for clarity unless debugging
                pass

        # Allow port reuse
        socketserver.TCPServer.allow_reuse_address = True

        try:
            self.httpd = socketserver.TCPServer(("", self.port), lambda *args, **kwargs: Handler(*args, directory=self.directory, **kwargs))
        except OSError as e:
            self.logger.error(f"Failed to bind to port {self.port}: {e}")
            raise

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.logger.info(f"Sandbox Proxy started at http://localhost:{self.port} serving {self.directory}")

        # Give the server a moment to start
        time.sleep(0.5)

    def stop(self):
        """Stops the proxy server."""
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.thread.join()
            self.httpd = None
            self.thread = None
            self.logger.info("Sandbox Proxy stopped.")

    def get_url(self, filepath=None):
        """Returns the local URL for a given filepath relative to the proxy directory."""
        base_url = f"http://localhost:{self.port}"
        if not filepath:
            return base_url

        rel_path = os.path.relpath(os.path.abspath(filepath), self.directory)
        # Ensure forward slashes for URLs
        rel_path = rel_path.replace("\\", "/")
        if rel_path.startswith(".."):
            self.logger.warning(f"File {filepath} is outside the served directory {self.directory}")

        return f"{base_url}/{rel_path}"

if __name__ == "__main__":
    proxy = SAPQSandboxProxy(port=8080)
    proxy.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        proxy.stop()
