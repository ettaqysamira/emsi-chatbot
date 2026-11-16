"""Recherche multimodale Qdrant et fusion Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ingestion.embeddings import MODELE_IMAGES, embedding_texte  # noqa: E402
from ingestion.vectordb import IMAGE_COLLECTION, TEXT_COLLECTION  # noqa: E402


TOP_K = 5
RRF_K = 60


def _creer_client() -> QdrantClient:
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


@lru_cache(maxsize=1)
def _modele_clip() -> SentenceTransformer:
    """Charge le modèle CLIP une seule fois pour les requêtes texte-image."""

    return SentenceTransformer(MODELE_IMAGES)


def _embedding_question_clip(question: str) -> list[float]:
    """Encode une question texte dans l'espace vectoriel CLIP de dimension 512."""

    vecteurs = _modele_clip().encode(
        [question],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vecteurs[0].tolist()


def _interroger_qdrant(
    client: QdrantClient,
    collection: str,
    vecteur: Sequence[float],
    top_k: int = TOP_K,
) -> list[Any]:
    """Interroge Qdrant avec l'API récente, avec fallback API historique."""

    if hasattr(client, "query_points"):
        try:
            reponse = client.query_points(
                collection_name=collection,
                query=list(vecteur),
                limit=top_k,
                with_payload=True,
            )
            return list(reponse.points)
        except TypeError:
            # Compatibilité avec des versions où la signature diffère.
            pass

    return list(
        client.search(
            collection_name=collection,
            query_vector=list(vecteur),
            limit=top_k,
            with_payload=True,
        )
    )


def _normaliser_resultat(
    point: Any,
    *,
    collection: str,
    type_attendu: str,
    rang: int,
) -> dict[str, Any]:
    payload = dict(point.payload or {})
    contenu = str(payload.get("contenu", ""))
    type_resultat = str(payload.get("type", type_attendu))
    source = str(payload.get("source", "source inconnue"))
    page = payload.get("page", "?")
    point_id = str(point.id)
    chunk_id = str(payload.get("chunk_id", point_id))

    return {
        "id": point_id,
        "collection": collection,
        "score": 0.0,
        "qdrant_score": float(point.score),
        "rang": rang,
        "source": source,
        "page": page,
        "type": type_resultat,
        "chunk_id": chunk_id,
        "reference": f"{source}, page {page}",
        "contenu": contenu,
        "texte": contenu if type_resultat == "text" else "",
        "chemin_image": contenu if type_resultat == "image" else "",
    }


def fusionner_rrf(
    resultats_textes: Sequence[Mapping[str, Any]],
    resultats_images: Sequence[Mapping[str, Any]],
    k: int = RRF_K,
) -> list[dict[str, Any]]:
    """Fusionne deux classements avec Reciprocal Rank Fusion."""

    if k <= 0:
        raise ValueError("La constante k de RRF doit être strictement positive.")

    fusion: dict[tuple[str, str], dict[str, Any]] = {}
    for resultats in (resultats_textes, resultats_images):
        for resultat in resultats:
            cle = (str(resultat["collection"]), str(resultat["id"]))
            if cle not in fusion:
                fusion[cle] = dict(resultat)
            fusion[cle]["score"] += 1 / (k + int(resultat["rang"]))

    return sorted(
        fusion.values(),
        key=lambda resultat: (-float(resultat["score"]), int(resultat["rang"])),
    )


def rechercher_contexte(
    question: str,
    client: QdrantClient | None = None,
) -> list[dict[str, Any]]:
    """Recherche les meilleurs contextes texte et image, puis les fusionne."""

    question = question.strip()
    if not question:
        raise ValueError("La question ne peut pas être vide.")

    client = client or _creer_client()

    # (2) La question utilisateur est encodée dans les deux espaces utiles.
    vecteur_texte = embedding_texte([question])[0]
    vecteur_image = _embedding_question_clip(question)

    # (3) Recherche top 5 dans les deux collections Qdrant.
    points_textes = _interroger_qdrant(
        client,
        TEXT_COLLECTION,
        vecteur_texte,
        top_k=TOP_K,
    )
    points_images = _interroger_qdrant(
        client,
        IMAGE_COLLECTION,
        vecteur_image,
        top_k=TOP_K,
    )

    # (4) Récupération du contexte puis fusion des deux classements.
    resultats_textes = [
        _normaliser_resultat(
            point,
            collection=TEXT_COLLECTION,
            type_attendu="text",
            rang=rang,
        )
        for rang, point in enumerate(points_textes, start=1)
    ]
    resultats_images = [
        _normaliser_resultat(
            point,
            collection=IMAGE_COLLECTION,
            type_attendu="image",
            rang=rang,
        )
        for rang, point in enumerate(points_images, start=1)
    ]
    return fusionner_rrf(resultats_textes, resultats_images, k=RRF_K)


if __name__ == "__main__":
    question_utilisateur = input("Question : ").strip()
    try:
        resultats = rechercher_contexte(question_utilisateur)
    except Exception as exc:
        print(f"Erreur pendant la recherche : {exc}")
        raise SystemExit(1) from exc

    if not resultats:
        print("Aucun résultat trouvé.")
        raise SystemExit(0)

    print("\nMeilleurs résultats :")
    for index, resultat in enumerate(resultats, start=1):
        print(
            f"\n{index}. score={resultat['score']:.6f} | "
            f"{resultat['reference']} | type={resultat['type']}"
        )
        if resultat["type"] == "image":
            print(f"   image : {resultat['chemin_image']}")
        else:
            extrait = resultat["texte"].replace("\n", " ").strip()
            if len(extrait) > 300:
                extrait = f"{extrait[:300]}..."
            print(f"   texte : {extrait}")
