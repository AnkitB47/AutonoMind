import os
import sys
from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import types

sys.modules.setdefault("google", MagicMock())

# Provide stub GenerativeModel for import
class DummyModel:
    def __init__(self, *a, **k):
        self.called = False
    def generate_content(self, parts):
        self.called = True
        return type("R", (), {"text": "ok"})()

genai_mod = types.SimpleNamespace(configure=lambda **_: None, GenerativeModel=DummyModel)
sys.modules.setdefault("google.generativeai", genai_mod)

os.environ["ENV"] = "dev"
os.environ["GEMINI_API_KEY"] = "testkey"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.gemini_vision import extract_image_text


class TestExtractImageText(unittest.TestCase):
    def create_image(self, fmt: str) -> bytes:
        img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    def test_png_and_jpeg(self):
        for fmt in ("PNG", "JPEG"):
            data = self.create_image(fmt)
            with patch("google.generativeai.GenerativeModel") as M:
                M.return_value = DummyModel()
                text = extract_image_text(data)
                self.assertEqual(text, "ok")
                self.assertTrue(M.return_value.called)

    def test_bad_data(self):
        with self.assertRaises(Exception):
            extract_image_text(b"notanimage")


if __name__ == "__main__":
    unittest.main()
