import os
from io import BytesIO
import unittest
from unittest.mock import patch
from PIL import Image

os.environ["ENV"] = "dev"
os.environ["GEMINI_API_KEY"] = "dummy"

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.gemini_vision import extract_image_text


class TestExtractImageText(unittest.TestCase):
    def create_image(self, fmt: str) -> bytes:
        img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    def mock_response(self):
        class R:
            status_code = 200
            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        return R()

    def test_png_mime(self):
        data = self.create_image("PNG")
        with patch("requests.post", return_value=self.mock_response()) as mock_post:
            extract_image_text(data)
            payload = mock_post.call_args.kwargs["json"]
            mime = payload["contents"][0]["parts"][1]["inlineData"]["mimeType"]
            self.assertEqual(mime, "image/png")

    def test_jpeg_mime(self):
        data = self.create_image("JPEG")
        with patch("requests.post", return_value=self.mock_response()) as mock_post:
            extract_image_text(data)
            payload = mock_post.call_args.kwargs["json"]
            mime = payload["contents"][0]["parts"][1]["inlineData"]["mimeType"]
            self.assertEqual(mime, "image/jpeg")


if __name__ == "__main__":
    unittest.main()
