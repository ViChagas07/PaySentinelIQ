from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz  # type: ignore[import-untyped]
from PIL import Image, ImageFilter

from app.synthetic.records import SyntheticDocument

FOOTER = "DOCUMENTO FICTICIO / SYNTHETIC SAMPLE"
VARIANTS = ("native", "scanned_clean", "scanned_rot", "scanned_blur", "image_png")


def _page_lines(document: SyntheticDocument) -> list[str]:
    return list(document.lines)


def _draw_native(
    document: SyntheticDocument,
    path: Path,
    lines: list[str],
) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    font_size = 9.5
    y = 45.0
    max_width = 530.0
    for line in lines:
        text = line
        while fitz.get_text_length(text, fontname="helv", fontsize=font_size) > max_width:
            cut = len(text) - 1
            while cut > 0 and fitz.get_text_length(
                text[:cut], fontname="helv", fontsize=font_size
            ) > max_width:
                cut -= 1
            page.insert_text((32, y), text[:cut], fontname="helv", fontsize=font_size)
            y += 13
            text = text[cut:]
        page.insert_text((32, y), text, fontname="helv", fontsize=font_size)
        y += 13
    page.insert_text((32, 825), FOOTER, fontname="helv", fontsize=8)
    doc.set_metadata(
        {
            "title": f"Synthetic {document.doc_kind} {document.id}",
            "author": "PaySentinelIQ Synthetic Generator",
            "subject": "Documento ficticio para avaliacao",
            "keywords": "synthetic, documento ficticio",
            "creator": "PaySentinelIQ Synthetic Generator",
            "producer": "PaySentinelIQ Synthetic Generator",
            "creationDate": "D:20260101000000Z",
            "modDate": "D:20260101000000Z",
        }
    )
    doc.save(str(path), garbage=4, deflate=1, no_new_id=1)
    doc.close()


def _edit_pdf(document: SyntheticDocument, path: Path) -> None:
    if not document.pdf_edit:
        return
    before = document.pdf_edit.get("before_text")
    after = document.pdf_edit.get("after_text")
    if not before or not after:
        return
    doc = fitz.open(str(path))
    page = doc[0]
    rects = page.search_for(before)
    if not rects:
        doc.close()
        return
    rect = rects[0]
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
    page.insert_text(
        (rect.x0, rect.y1 - 1),
        after,
        fontname="times-roman",
        fontsize=9.5,
        color=(0, 0, 0),
    )
    doc.set_metadata(
        {
            "title": f"Synthetic {document.doc_kind} {document.id}",
            "author": "PaySentinelIQ Synthetic Generator",
            "subject": "Documento ficticio para avaliacao",
            "keywords": "synthetic, documento ficticio",
            "creator": "Adobe Acrobat Pro",
            "producer": "Adobe PDF Library 23.6",
            "creationDate": "D:20260101000000Z",
            "modDate": "D:20260102000000Z",
        }
    )
    doc.save(
        str(path),
        incremental=True,
        encryption=fitz.PDF_ENCRYPT_KEEP,
        no_new_id=1,
    )
    doc.close()


def _rasterize(path: Path) -> Image.Image:
    doc = fitz.open(str(path))
    page = doc[0]
    pix = page.get_pixmap(dpi=200, alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return image


def _save_image_pdf(
    image: Image.Image,
    path: Path,
    document: SyntheticDocument,
    jpeg_quality: int | None = None,
) -> None:
    buffer = BytesIO()
    image = image.convert("L")
    if jpeg_quality is None:
        image.save(buffer, format="PNG")
    else:
        image.save(buffer, format="JPEG", quality=jpeg_quality)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(
        fitz.Rect(0, 0, 595, 842),
        stream=buffer.getvalue(),
        keep_proportion=True,
    )
    doc.set_metadata(
        {
            "title": f"Synthetic {document.doc_kind} {document.id}",
            "author": "PaySentinelIQ Synthetic Generator",
            "subject": "Documento ficticio para avaliacao",
            "keywords": "synthetic, documento ficticio",
            "creator": "PaySentinelIQ Synthetic Generator",
            "producer": "PaySentinelIQ Synthetic Generator",
            "creationDate": "D:20260101000000Z",
            "modDate": "D:20260101000000Z",
        }
    )
    doc.save(str(path), garbage=4, deflate=1, no_new_id=1)
    doc.close()


def render_variant(
    document: SyntheticDocument,
    variant: str,
    out_path: str | Path,
) -> str:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if variant not in VARIANTS:
        raise ValueError(f"Unknown render variant: {variant}")

    if variant == "native":
        lines = list(document.lines)
        if document.pdf_edit and document.original_lines:
            _draw_native(document, path, document.original_lines)
            _edit_pdf(document, path)
        else:
            _draw_native(document, path, lines)
        return "\n".join(lines)

    if variant == "image_png":
        native_path = path.with_suffix(".native.pdf")
        _draw_native(document, native_path, document.lines)
        image = _rasterize(native_path)
        image.save(str(path), format="PNG")
        native_path.unlink(missing_ok=True)
        return "\n".join(document.lines)

    native_path = path.with_suffix(".native.pdf")
    _draw_native(document, native_path, document.lines)
    image = _rasterize(native_path)
    native_path.unlink(missing_ok=True)
    if variant == "scanned_rot":
        image = image.rotate(2, expand=True, fillcolor="white")
    elif variant == "scanned_blur":
        image = image.filter(ImageFilter.GaussianBlur(1))
    _save_image_pdf(
        image,
        path,
        document,
        jpeg_quality=40 if variant == "scanned_blur" else 50,
    )
    return "\n".join(document.lines)


def render_all(
    document: SyntheticDocument,
    out_dir: str | Path,
    variants: tuple[str, ...] = VARIANTS,
) -> dict[str, dict[str, str]]:
    root = Path(out_dir)
    paths: dict[str, dict[str, str]] = {}
    for variant in variants:
        suffix = ".png" if variant == "image_png" else ".pdf"
        path = root / variant / f"{document.id}{suffix}"
        text = render_variant(document, variant, path)
        paths[variant] = {
            "path": str(path),
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "text": text,
        }
    return paths


def edit_target(document: SyntheticDocument) -> dict[str, Any] | None:
    if not document.pdf_edit:
        return None
    return dict(document.pdf_edit)
