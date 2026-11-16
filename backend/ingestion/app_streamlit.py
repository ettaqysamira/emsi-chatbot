"""Interface Streamlit de l'ingestion multimodale vers Qdrant."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

import streamlit as st
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ingestion.chunking import chunker_textes  # noqa: E402
from ingestion.embeddings import embedding_images, embedding_texte  # noqa: E402
from ingestion.extraction import DEFAULT_IMAGES_DIR, extraire_fichier  # noqa: E402
from ingestion.vectordb import (  # noqa: E402
    IMAGE_COLLECTION,
    TEXT_COLLECTION,
    construire_payload,
    creer_collections,
)


load_dotenv(BACKEND_DIR / ".env")


def _identifiant_point(collection: str, source: str, key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{collection}:{source}:{key}"))


def _inserer_textes(
    client: QdrantClient,
    chunks: Iterable[Mapping[str, Any]],
    vecteurs: Iterable[list[float]],
) -> int:
    points = [
        PointStruct(
            id=_identifiant_point(TEXT_COLLECTION, str(chunk["source"]), str(chunk["chunk_id"])),
            vector=vector,
            payload=construire_payload(
                source=str(chunk["source"]),
                page=int(chunk["page"]),
                type_="text",
                contenu=str(chunk["contenu"]),
                chunk_id=str(chunk["chunk_id"]),
            ),
        )
        for chunk, vector in zip(chunks, vecteurs, strict=True)
    ]
    if points:
        client.upsert(collection_name=TEXT_COLLECTION, points=points, wait=True)
    return len(points)


def _inserer_images(
    client: QdrantClient,
    images: Iterable[Mapping[str, Any]],
    vecteurs: Iterable[list[float]],
) -> int:
    points = [
        PointStruct(
            id=_identifiant_point(IMAGE_COLLECTION, str(image["source"]), str(image["chunk_id"])),
            vector=vector,
            payload=construire_payload(
                source=str(image["source"]),
                page=int(image["page"]),
                type_="image",
                contenu=str(image["contenu"]),
                chunk_id=str(image["chunk_id"]),
            ),
        )
        for image, vector in zip(images, vecteurs, strict=True)
    ]
    if points:
        client.upsert(collection_name=IMAGE_COLLECTION, points=points, wait=True)
    return len(points)


def _ingester(uploaded_file: Any, progress: Any) -> dict[str, int]:
    """Exécute l'extraction, le chunking, les embeddings et l'indexation."""

    temporary_directory = Path(tempfile.mkdtemp(prefix="emsi_ingestion_"))
    try:
        temporary_file = temporary_directory / uploaded_file.name
        temporary_file.write_bytes(uploaded_file.getbuffer())
        progress.progress(10, text="Fichier uploadé")

        extraction = extraire_fichier(
            temporary_file,
            images_dir=DEFAULT_IMAGES_DIR,
            source=uploaded_file.name,
        )
        textes = extraction["textes"]
        images = extraction["images"]
        progress.progress(30, text="Extraction terminée")

        chunks = chunker_textes(textes)
        progress.progress(45, text="Chunking terminé")

        vecteurs_textes = embedding_texte(
            [str(chunk["contenu"]) for chunk in chunks]
        )
        progress.progress(60, text="Embeddings texte terminés")

        vecteurs_images = embedding_images(
            [str(image["contenu"]) for image in images]
        )
        progress.progress(75, text="Embeddings images terminés")

        client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333")
        )
        creer_collections(client)
        nombre_textes = _inserer_textes(client, chunks, vecteurs_textes)
        nombre_images = _inserer_images(client, images, vecteurs_images)
        progress.progress(100, text="Insertion Qdrant terminée")

        return {
            "pages": int(extraction["pages"]),
            "chunks": nombre_textes,
            "images": nombre_images,
        }
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)


def main() -> None:
    st.set_page_config(page_title="EMSI ChatBot — Ingestion", page_icon="📚")
    st.title("EMSI ChatBot — Pipeline d'ingestion")
    st.caption("Extraction → Chunking → Embeddings → Qdrant")

    uploaded_file = st.file_uploader(
        "Importer une brochure PDF, un fichier TXT ou une image",
        type=["pdf", "txt", "png", "jpg", "jpeg", "webp", "bmp", "gif"],
    )

    lancer = st.button(
        "Lancer l'ingestion",
        type="primary",
        disabled=uploaded_file is None,
    )
    if not lancer or uploaded_file is None:
        return

    progress = st.progress(0, text="Préparation de l'ingestion")
    try:
        resultat = _ingester(uploaded_file, progress)
    except Exception as exc:
        progress.empty()
        st.error("L'ingestion a échoué.")
        st.exception(exc)
        return

    st.success("Ingestion terminée avec succès.")
    col_pages, col_chunks, col_images = st.columns(3)
    col_pages.metric("Pages", resultat["pages"])
    col_chunks.metric("Chunks texte", resultat["chunks"])
    col_images.metric("Images indexées", resultat["images"])


if __name__ == "__main__":
    main()
