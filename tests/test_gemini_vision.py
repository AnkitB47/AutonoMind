import os
import sys
from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

sys.modules.setdefault("google", MagicMock())
sys.modules.setdefault("google.generativeai", MagicMock())

os.environ["ENV"] = "dev"
os.environ["GEMINI_API_KEY"] = "dummy"
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

    def test_bad_mime(self):
        with patch("requests.post") as mock_post:
            result = extract_image_text(b"notanimage")
            self.assertIn("Unsupported image type", result)
            mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
