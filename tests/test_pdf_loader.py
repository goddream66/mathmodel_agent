import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_pdf_loader_tries_ocr_by_default_and_falls_back(self) -> None:
        with patch("mathagent.io.loaders_v2._extract_text_from_pdf", return_value="base text") as base_mock:
            with patch(
                "mathagent.io.loaders_v2._extract_ocr_text_from_pdf",
                side_effect=RuntimeError("missing ocr deps"),
            ) as ocr_mock:
                result = load_problem_text("problem.pdf")

        self.assertEqual(result, "base text")
        base_mock.assert_called_once()
        ocr_mock.assert_called_once()

    def test_pdf_loader_can_disable_auto_ocr(self) -> None:
        with patch("mathagent.io.loaders_v2._extract_text_from_pdf", return_value="base text") as base_mock:
            with patch("mathagent.io.loaders_v2._extract_ocr_text_from_pdf") as ocr_mock:
                result = load_problem_text("problem.pdf", enable_ocr=False)

        self.assertEqual(result, "base text")
        base_mock.assert_called_once()
        ocr_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
