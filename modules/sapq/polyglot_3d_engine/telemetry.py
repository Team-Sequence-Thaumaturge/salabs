import sys
import json
import time

def start_telemetry_daemon():
    """
    Python Telemetry Daemon (Phase 5.2).
    Listens to standard input for JSON telemetry (e.g., 18-DoF Humanoid joint angles)
    and processes the data to maintain a real-time feedback loop.
    """
    print("Telemetry daemon started. Listening on stdin...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                # Sleep briefly if no data to prevent high CPU usage,
                # but typically stdin will block until EOF or data.
                time.sleep(0.01)
                continue

            # Parse the JSON telemetry data
            data = json.loads(line)

            # For Phase 5.2: We just print/acknowledge the received 18-DoF tensor
            # In a full implementation, this could write to a pipe or DB.
            if "Head" in data or "Spine" in data:
                print(f"[TELEMETRY_ACK] Received 18-DoF Skeleton Kinematics Update: {len(data)} joints.")
            else:
                print(f"[TELEMETRY_ACK] Received generic telemetry update.")

        except json.JSONDecodeError:
            # Ignore malformed lines to prevent daemon crash
            pass
        except KeyboardInterrupt:
            print("Telemetry daemon stopping...")
            break
        except Exception as e:
            print(f"Telemetry error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    start_telemetry_daemon()
