from __future__ import annotations

import io
from pathlib import Path


def load_problem_text(
    path: str | Path, *, enable_ocr: bool = False, ocr_mode: str = "auto"
) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".txt", ".md"}:
        return p.read_text(encoding="utf-8")

    if suffix == ".pdf":
        base_text = _extract_text_from_pdf(p)
        if not enable_ocr:
            return base_text

        ocr_text = _extract_ocr_text_from_pdf(p, base_text=base_text, mode=ocr_mode)
        if not ocr_text:
            return base_text

        if base_text:
            return "\n\n".join([base_text, "## OCR（图片文字识别）", ocr_text]).strip()
        return "\n\n".join(["## OCR（图片文字识别）", ocr_text]).strip()

    return p.read_text(encoding="utf-8")


def _extract_text_from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError(
            "读取 PDF 需要额外依赖：pypdf。请先运行：python -m pip install -e .[pdf]"
        ) from e

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n\n".join(parts).strip()


def _extract_ocr_text_from_pdf(path: Path, *, base_text: str, mode: str) -> str:
    try:
        import fitz  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "启用 OCR 需要额外依赖：pymupdf、pillow、rapidocr-onnxruntime。请先运行：python -m pip install -e .[ocr]"
        ) from e

    try:
        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as e:
        raise RuntimeError(
            "启用 OCR 需要额外依赖：pymupdf、pillow、rapidocr-onnxruntime。请先运行：python -m pip install -e .[ocr]"
        ) from e

    ocr = RapidOCR()
    doc = fitz.open(str(path))
    try:
        lines: list[str] = []

        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            extracted_any = False
            if mode in {"auto", "images"}:
                images = page.get_images(full=True)
                for img_index, img in enumerate(images[:10], start=1):
                    xref = img[0]
                    extracted = doc.extract_image(xref)
                    image_bytes = extracted.get("image")
                    if not image_bytes:
                        continue

                    try:
                        pil = Image.open(io.BytesIO(image_bytes))
                    except Exception:
                        continue

                    ocr_text = _run_ocr(ocr, np, pil)
                    ocr_text = _filter_ocr_lines(ocr_text, base_text)
                    if not ocr_text:
                        continue
                    extracted_any = True
                    lines.extend([f"### 第{page_index + 1}页-图片{img_index}", ocr_text, ""])

            if not extracted_any and mode in {"auto", "page"}:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                try:
                    pil = Image.open(io.BytesIO(pix.tobytes("png")))
                except Exception:
                    continue

                ocr_text = _run_ocr(ocr, np, pil)
                ocr_text = _filter_ocr_lines(ocr_text, base_text)
                if not ocr_text:
                    continue
                lines.extend([f"### 第{page_index + 1}页-整页", ocr_text, ""])

        return "\n".join(lines).strip()
    finally:
        doc.close()


def _run_ocr(ocr, np, pil) -> str:
    arr = np.array(pil.convert("RGB"))
    result, _ = ocr(arr)
    if not result:
        return ""
    return "\n".join([r[1] for r in result if len(r) >= 2 and isinstance(r[1], str)]).strip()


def _filter_ocr_lines(ocr_text: str, base_text: str) -> str:
    if not ocr_text:
        return ""
    base = base_text.replace(" ", "")
    kept: list[str] = []
    for line in [x.strip() for x in ocr_text.splitlines()]:
        if not line:
            continue
        compact = line.replace(" ", "")
        if len(compact) <= 1:
            continue
        if compact in base:
            continue
        kept.append(line)
    return "\n".join(kept).strip()
