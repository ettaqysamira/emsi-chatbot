"""Extraction de texte, tableaux et images depuis les documents uploadés."""

from __future__ import annotations

import io
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

import fitz
from PIL import Image


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_IMAGES_DIR = BACKEND_DIR / "data" / "images"
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _slugifier_source(source: str) -> str:
    """Produit un préfixe de fichier sûr à partir du nom de la source."""

    stem = Path(source).stem
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")
    return slug or "document"


def _nom_image(source: str, page: int, image_index: int) -> str:
    identifiant = uuid.uuid4().hex[:8]
    return (
        f"{_slugifier_source(source)}_{identifiant}_"
        f"page{page}_img{image_index}.png"
    )


def _table_en_markdown(table: Any) -> str:
    """Convertit une table PyMuPDF en Markdown avec un fallback simple."""

    if hasattr(table, "to_markdown"):
        markdown = table.to_markdown()
        if markdown:
            return str(markdown).strip()

    rows = table.extract() if hasattr(table, "extract") else []
    if not rows:
        return ""

    normalized_rows = [
        ["" if cell is None else str(cell).replace("\n", " ") for cell in row]
        for row in rows
    ]
    width = max(len(row) for row in normalized_rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in normalized_rows]

    lines = [
        "| " + " | ".join(normalized_rows[0]) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(row) + " |" for row in normalized_rows[1:]
    )
    return "\n".join(lines)


def _sauvegarder_image_pdf(
    document: fitz.Document,
    xref: int,
    destination: Path,
) -> None:
    """Sauvegarde une image PDF au format PNG."""

    image_info = document.extract_image(xref)
    image_bytes = image_info["image"]
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.convert("RGB").save(destination, format="PNG")
    except Exception:
        # Fallback pour les images PDF que Pillow ne sait pas décoder.
        pixmap = fitz.Pixmap(document, xref)
        try:
            if pixmap.alpha:
                rgb_pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
                try:
                    rgb_pixmap.save(destination)
                finally:
                    rgb_pixmap = None
            else:
                pixmap.save(destination)
        finally:
            pixmap = None


def extraire_pdf(
    chemin_pdf: str | Path,
    images_dir: str | Path = DEFAULT_IMAGES_DIR,
    source: str | None = None,
) -> dict[str, Any]:
    """Extrait le contenu textuel, les tableaux et les images d'un PDF."""

    chemin = Path(chemin_pdf)
    source = source or chemin.name
    dossier_images = Path(images_dir)
    dossier_images.mkdir(parents=True, exist_ok=True)

    textes: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []

    with fitz.open(chemin) as document:
        for page_number, page in enumerate(document, start=1):
            texte = page.get_text("text").strip()
            if texte:
                textes.append(
                    {
                        "source": source,
                        "page": page_number,
                        "contenu": texte,
                        "type": "text",
                    }
                )

            try:
                table_finder = page.find_tables()
                tables = getattr(table_finder, "tables", [])
            except Exception:
                # Certaines versions ou certains PDF ne permettent pas la
                # détection de tableaux : le texte de la page reste exploitable.
                tables = []

            for table_index, table in enumerate(tables, start=1):
                tableau = _table_en_markdown(table)
                if tableau:
                    textes.append(
                        {
                            "source": source,
                            "page": page_number,
                            "contenu": tableau,
                            "type": "text",
                            "table_id": f"table_{table_index}",
                        }
                    )

            for image_index, image_ref in enumerate(page.get_images(full=True), start=1):
                xref = image_ref[0]
                chemin_image = dossier_images / _nom_image(
                    source, page_number, image_index
                )
                _sauvegarder_image_pdf(document, xref, chemin_image)
                images.append(
                    {
                        "source": source,
                        "page": page_number,
                        "contenu": str(chemin_image),
                        "type": "image",
                        "chunk_id": (
                            f"{_slugifier_source(source)}_p{page_number}_"
                            f"img{image_index:04d}"
                        ),
                    }
                )

        nombre_pages = document.page_count

    return {"pages": nombre_pages, "textes": textes, "images": images}


def extraire_txt(
    chemin_txt: str | Path,
    source: str | None = None,
) -> dict[str, Any]:
    """Transforme un fichier TXT en une structure d'extraction textuelle."""

    chemin = Path(chemin_txt)
    source = source or chemin.name
    texte = chemin.read_text(encoding="utf-8", errors="replace").strip()
    textes = (
        [
            {
                "source": source,
                "page": 1,
                "contenu": texte,
                "type": "text",
            }
        ]
        if texte
        else []
    )
    return {"pages": 1, "textes": textes, "images": []}


def extraire_image(
    chemin_image: str | Path,
    images_dir: str | Path = DEFAULT_IMAGES_DIR,
    source: str | None = None,
) -> dict[str, Any]:
    """Copie une image uploadée vers data/images au format PNG."""

    chemin = Path(chemin_image)
    source = source or chemin.name
    dossier_images = Path(images_dir)
    dossier_images.mkdir(parents=True, exist_ok=True)
    destination = dossier_images / _nom_image(source, page=1, image_index=1)

    with Image.open(chemin) as image:
        image.convert("RGB").save(destination, format="PNG")

    return {
        "pages": 1,
        "textes": [],
        "images": [
            {
                "source": source,
                "page": 1,
                "contenu": str(destination),
                "type": "image",
                "chunk_id": f"{_slugifier_source(source)}_p1_img0001",
            }
        ],
    }


def extraire_fichier(
    chemin: str | Path,
    images_dir: str | Path = DEFAULT_IMAGES_DIR,
    source: str | None = None,
) -> dict[str, Any]:
    """Route un fichier PDF, TXT ou image vers l'extracteur approprié."""

    chemin = Path(chemin)
    suffixe = chemin.suffix.lower()
    if suffixe == ".pdf":
        return extraire_pdf(chemin, images_dir=images_dir, source=source)
    if suffixe == ".txt":
        return extraire_txt(chemin, source=source)
    if suffixe in SUPPORTED_IMAGE_SUFFIXES:
        return extraire_image(chemin, images_dir=images_dir, source=source)
    raise ValueError(f"Format non supporté : {suffixe or 'sans extension'}")
