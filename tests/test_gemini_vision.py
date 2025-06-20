import os
import sys
from io import BytesIO
import unittest

from PIL import Image
import types
import tempfile
import importlib

sys.modules["google"] = types.ModuleType("google")

# Provide stub GenerativeModel for import
class DummyModel:
    def __init__(self, *a, **k):
        self.called = False
    def generate_content(self, parts):
        self.called = True
        return type("R", (), {"text": "ok"})()

genai_mod = types.SimpleNamespace(configure=lambda **_: None, GenerativeModel=DummyModel)
sys.modules["google.generativeai"] = genai_mod

os.environ["ENV"] = "dev"
os.environ["GEMINI_API_KEY"] = "testkey"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import models.gemini_vision as gv
importlib.reload(gv)
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
            with tempfile.NamedTemporaryFile(suffix=f".{fmt.lower()}", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                text = extract_image_text(tmp_path)
                self.assertEqual(text, "ok")
            finally:
                os.remove(tmp_path)

    def test_bad_data(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"notanimage")
            bad_path = tmp.name
        try:
            with self.assertRaises(Exception):
                extract_image_text(bad_path)
        finally:
            os.remove(bad_path)


if __name__ == "__main__":
    unittest.main()
