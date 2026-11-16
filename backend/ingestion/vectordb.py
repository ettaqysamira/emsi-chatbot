"""Initialisation des collections Qdrant pour le lab EMSI_chatBot."""

from __future__ import annotations

import os
from typing import Literal

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


TEXT_COLLECTION = "emsi_text"
IMAGE_COLLECTION = "emsi_images"


def _create_client() -> QdrantClient:
    """Construit un client Qdrant à partir de QDRANT_URL ou du défaut local."""

    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


def creer_collections(client: QdrantClient | None = None) -> list[str]:
    """Crée les collections nécessaires et renvoie celles nouvellement créées.

    La fonction est idempotente : une collection déjà présente n'est pas recréée.
    Le payload de chaque point doit respecter le format produit par
    :func:`construire_payload`.
    """

    client = client or _create_client()
    existing = {
        collection.name for collection in client.get_collections().collections
    }

    definitions = {
        TEXT_COLLECTION: VectorParams(size=1024, distance=Distance.COSINE),
        IMAGE_COLLECTION: VectorParams(size=512, distance=Distance.COSINE),
    }

    created: list[str] = []
    for name, vectors_config in definitions.items():
        if name in existing:
            continue

        client.create_collection(
            collection_name=name,
            vectors_config=vectors_config,
        )
        created.append(name)

    return created


def construire_payload(
    *,
    source: str,
    page: int,
    type_: Literal["text", "image"],
    contenu: str,
    chunk_id: str,
) -> dict[str, str | int]:
    """Construit le payload standard associé à un point Qdrant."""

    return {
        "source": source,
        "page": page,
        "type": type_,
        "contenu": contenu,
        "chunk_id": chunk_id,
    }


if __name__ == "__main__":
    qdrant = _create_client()
    collections_creees = creer_collections(qdrant)

    if collections_creees:
        print("Collections créées :")
        for collection_name in collections_creees:
            print(f"- {collection_name}")
    else:
        print("Aucune collection créée : elles existent déjà.")

    print("Collections disponibles :")
    for collection in qdrant.get_collections().collections:
        print(f"- {collection.name}")
