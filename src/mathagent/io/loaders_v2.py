from __future__ import annotations

import csv
import io
import importlib
import json
from pathlib import Path
from typing import Any

from .tabular import summarize_table


def load_problem_text(
    path: str | Path, *, enable_ocr: bool | None = None, ocr_mode: str = "auto"
) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".txt", ".md"}:
        return p.read_text(encoding="utf-8")

    if suffix == ".pdf":
        base_text = _extract_text_from_pdf(p)
        should_try_ocr = True if enable_ocr is None else enable_ocr
        if not should_try_ocr:
            return base_text

        try:
            ocr_text = _extract_ocr_text_from_pdf(p, base_text=base_text, mode=ocr_mode)
        except RuntimeError:
            if enable_ocr is True:
                raise
            return base_text
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
        if suffix in {".xlsx", ".xlsm"}:
            tables.extend(_load_excel_tables(path))
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
    return _build_table_payload(name=path.stem, source=str(path), columns=columns, rows=rows)


def _load_json_tables(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables: list[dict[str, Any]] = []

    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        rows = [{str(k): _coerce_cell(v) for k, v in row.items()} for row in data]
        columns = _infer_columns(rows)
        tables.append(_build_table_payload(name=path.stem, source=str(path), columns=columns, rows=rows))
        return tables

    if isinstance(data, dict):
        if "tables" in data and isinstance(data["tables"], list):
            for index, item in enumerate(data["tables"], start=1):
                if not isinstance(item, dict):
                    continue
                rows = item.get("rows")
                if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                    continue
                normalized_rows = [
                    {str(k): _coerce_cell(v) for k, v in row.items()}
                    for row in rows
                ]
                columns = list(item.get("columns") or _infer_columns(normalized_rows))
                tables.append(
                    _build_table_payload(
                        name=str(item.get("name") or f"{path.stem}_{index}"),
                        source=str(path),
                        columns=columns,
                        rows=normalized_rows,
                    )
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


def _load_excel_tables(path: Path) -> list[dict[str, Any]]:
    try:
        load_workbook = _import_optional_module("openpyxl").load_workbook
    except ImportError as e:
        raise RuntimeError(
            "Reading XLSX files requires openpyxl. Run: python -m pip install -e .[solver]"
        ) from e

    workbook = load_workbook(filename=path, read_only=True, data_only=True)
    try:
        worksheets = list(workbook.worksheets)
        tables: list[dict[str, Any]] = []
        for worksheet in worksheets:
            raw_rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
            table = _worksheet_to_table(path, worksheet.title, raw_rows, single_sheet=len(worksheets) == 1)
            if table is not None:
                tables.append(table)
        return tables
    finally:
        close = getattr(workbook, "close", None)
        if callable(close):
            close()


def _worksheet_to_table(
    path: Path,
    sheet_name: str,
    raw_rows: list[list[Any]],
    *,
    single_sheet: bool,
) -> dict[str, Any] | None:
    header_index = _find_header_row(raw_rows)
    if header_index is None:
        return None

    headers = _make_unique_headers(raw_rows[header_index])
    rows: list[dict[str, Any]] = []
    for raw_row in raw_rows[header_index + 1 :]:
        if not any(cell not in {None, ""} for cell in raw_row):
            continue
        padded = list(raw_row) + [None] * max(0, len(headers) - len(raw_row))
        row = {headers[index]: _coerce_cell(padded[index]) for index in range(len(headers))}
        rows.append(row)

    table_name = path.stem if single_sheet else f"{path.stem}_{sheet_name}"
    table = _build_table_payload(name=table_name, source=str(path), columns=headers, rows=rows)
    table["sheet_name"] = sheet_name
    return table


def _build_table_payload(
    *,
    name: str,
    source: str,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = summarize_table(columns, rows)
    return {
        "name": name,
        "source": source,
        "kind": "table",
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        **summary,
    }


def _find_header_row(raw_rows: list[list[Any]]) -> int | None:
    for index, row in enumerate(raw_rows):
        if any(cell not in {None, ""} for cell in row):
            return index
    return None


def _make_unique_headers(row: list[Any]) -> list[str]:
    headers: list[str] = []
    seen: dict[str, int] = {}
    for index, value in enumerate(row, start=1):
        base = str(value).strip() if value not in {None, ""} else f"column_{index}"
        count = seen.get(base, 0) + 1
        seen[base] = count
        headers.append(base if count == 1 else f"{base}_{count}")
    return headers


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


def _import_optional_module(module_name: str) -> Any:
    return importlib.import_module(module_name)


def _extract_text_from_pdf(path: Path) -> str:
    try:
        PdfReader = _import_optional_module("pypdf").PdfReader
    except ImportError as e:
        raise RuntimeError(
            "Reading PDF files requires pypdf. Run: python -m pip install -e .[pdf]"
        ) from e

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n\n".join(parts).strip()


def _extract_ocr_text_from_pdf(path: Path, *, base_text: str, mode: str) -> str:
    try:
        import fitz  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "OCR requires pymupdf, pillow, numpy, and rapidocr-onnxruntime. Run: python -m pip install -e .[ocr]"
        ) from e

    try:
        np = _import_optional_module("numpy")
        Image = _import_optional_module("PIL.Image")
        RapidOCR = _import_optional_module("rapidocr_onnxruntime").RapidOCR
    except ImportError as e:
        raise RuntimeError(
            "OCR requires pymupdf, pillow, numpy, and rapidocr-onnxruntime. Run: python -m pip install -e .[ocr]"
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
                for image_index, image in enumerate(images[:10], start=1):
                    extracted = doc.extract_image(image[0])
                    image_bytes = extracted.get("image")
                    if not image_bytes:
                        continue
                    try:
                        pil = Image.open(io.BytesIO(image_bytes))
                    except Exception:
                        continue

                    ocr_text = _filter_ocr_lines(_run_ocr(ocr, np, pil), base_text)
                    if not ocr_text:
                        continue
                    extracted_any = True
                    lines.extend([f"### 第{page_index + 1}页 图片{image_index}", ocr_text, ""])

            if not extracted_any and mode in {"auto", "page"}:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                try:
                    pil = Image.open(io.BytesIO(pix.tobytes("png")))
                except Exception:
                    continue

                ocr_text = _filter_ocr_lines(_run_ocr(ocr, np, pil), base_text)
                if not ocr_text:
                    continue
                lines.extend([f"### 第{page_index + 1}页 整页", ocr_text, ""])

        return "\n".join(lines).strip()
    finally:
        doc.close()


def _run_ocr(ocr, np, pil) -> str:
    arr = np.array(pil.convert("RGB"))
    result, _ = ocr(arr)
    if not result:
        return ""
    return "\n".join([item[1] for item in result if len(item) >= 2 and isinstance(item[1], str)]).strip()


def _filter_ocr_lines(ocr_text: str, base_text: str) -> str:
    if not ocr_text:
        return ""
    base = base_text.replace(" ", "")
    kept: list[str] = []
    for line in [value.strip() for value in ocr_text.splitlines()]:
        if not line:
            continue
        compact = line.replace(" ", "")
        if len(compact) <= 1:
            continue
        if compact in base:
            continue
        kept.append(line)
    return "\n".join(kept).strip()
