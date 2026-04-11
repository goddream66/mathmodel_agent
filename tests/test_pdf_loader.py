import unittest
from pathlib import Path

from mathagent.io import load_problem_text


class PdfLoaderTest(unittest.TestCase):
    def test_pdf_loader_requires_dependency(self) -> None:
        try:
            __import__("pypdf")
        except ImportError:
            tmp = Path("data/empty.pdf")
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(b"")
            with self.assertRaises(RuntimeError) as ctx:
                load_problem_text(tmp)
            self.assertIn("pypdf", str(ctx.exception))
        else:
            self.skipTest("pypdf installed; skip missing-dependency test")

    def test_ocr_loader_requires_dependency(self) -> None:
        try:
            __import__("pypdf")
        except ImportError:
            self.skipTest("pypdf not installed; cannot reach OCR branch")

        try:
            __import__("rapidocr_onnxruntime")
            __import__("fitz")
            __import__("PIL")
        except ImportError:
            tmp = Path("data/empty.pdf")
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(b"")
            with self.assertRaises(RuntimeError) as ctx:
                load_problem_text(tmp, enable_ocr=True)
            self.assertIn(".[ocr]", str(ctx.exception))
        else:
            self.skipTest("ocr deps installed; skip missing-dependency test")


if __name__ == "__main__":
    unittest.main()
