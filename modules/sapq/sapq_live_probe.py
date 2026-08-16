import requests
import socket

class LiveProbeEngine:
    """
    Phase 17.2: Active Runtime Probe & Integration Prober
    - Verify live cloud infrastructure states (API status verification).
    - Flag dynamic connection errors (API/auth key expirations or network connectivity cuts).
    """
    @staticmethod
    def ping_api(url, timeout=5, expected_status=200):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code != expected_status:
                return {
                    "url": url,
                    "status": "FAIL",
                    "issue": f"LIVE_PROBE_ERROR: Expected status {expected_status}, got {response.status_code}"
                }
            return {"url": url, "status": "OK"}
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status": "FAIL",
                "issue": f"LIVE_PROBE_ERROR: Connection failed - {str(e)}"
            }

    @staticmethod
    def check_local_listener(host, port, timeout=2):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return {"host": host, "port": port, "status": "OK"}
        except OSError as e:
            return {
                "host": host,
                "port": port,
                "status": "FAIL",
                "issue": f"LIVE_PROBE_ERROR: Port {port} on {host} is unreachable - {str(e)}"
            }
