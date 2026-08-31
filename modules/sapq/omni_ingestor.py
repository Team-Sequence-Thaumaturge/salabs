import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from omni_adapters import TextTensorState, BinaryTensorState, ControlMapTensorState, VideoTensorState

class OmniIngestor:
    @staticmethod
    def ingest(data, mime_type):
        """
        Determines MIME/format and routes to the correct adapter,
        returning the computed S_matrix and invariants dictionary.
        """
        if mime_type == "text/plain":
            adapter = TextTensorState(data)
        elif mime_type == "application/base64" or mime_type.startswith("image/"):
            adapter = BinaryTensorState(data)
        elif mime_type == "application/x-control-map":
            adapter = ControlMapTensorState(data)
        elif mime_type.startswith("video/"):
            adapter = VideoTensorState(data)
        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")

        return adapter.S_matrix, adapter.invariants
