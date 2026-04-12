from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any


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


def load_supporting_data(paths: list[str | Path]) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            tables.append(_load_csv_table(path))
            continue
        if suffix == ".json":
            tables.extend(_load_json_tables(path))
            continue
        raise RuntimeError(f"Unsupported data file format: {path}")

    return {
        "tables": tables,
        "table_names": [table["name"] for table in tables],
        "table_count": len(tables),
    }


def _load_csv_table(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [{str(k): _coerce_cell(v) for k, v in row.items()} for row in reader]
        columns = list(reader.fieldnames or [])
    return {
        "name": path.stem,
        "source": str(path),
        "kind": "table",
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }


def _load_json_tables(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables: list[dict[str, Any]] = []

    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        columns = _infer_columns(data)
        tables.append(
            {
                "name": path.stem,
                "source": str(path),
                "kind": "table",
                "columns": columns,
                "rows": [{str(k): _coerce_cell(v) for k, v in row.items()} for row in data],
                "row_count": len(data),
            }
        )
        return tables

    if isinstance(data, dict):
        if "tables" in data and isinstance(data["tables"], list):
            for index, item in enumerate(data["tables"], start=1):
                if not isinstance(item, dict):
                    continue
                rows = item.get("rows")
                if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                    continue
                columns = list(item.get("columns") or _infer_columns(rows))
                tables.append(
                    {
                        "name": str(item.get("name") or f"{path.stem}_{index}"),
                        "source": str(path),
                        "kind": "table",
                        "columns": columns,
                        "rows": [{str(k): _coerce_cell(v) for k, v in row.items()} for row in rows],
                        "row_count": len(rows),
                    }
                )
            return tables

        tables.append(
            {
                "name": path.stem,
                "source": str(path),
                "kind": "json",
                "data": data,
            }
        )
        return tables

    raise RuntimeError(f"Unsupported JSON table structure: {path}")


def _infer_columns(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            key_str = str(key)
            if key_str not in seen:
                seen.add(key_str)
                columns.append(key_str)
    return columns


def _coerce_cell(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return ""
        try:
            if "." in stripped:
                return float(stripped)
            return int(stripped)
        except ValueError:
            return stripped
    return value


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
