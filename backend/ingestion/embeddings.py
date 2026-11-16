"""Embeddings multimodaux pour le pipeline EMSI_chatBot.

Pipeline : Chunking -> Tokenisation -> Embedding -> Vector DB.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Sequence

from PIL import Image
from sentence_transformers import SentenceTransformer


MODELE_TEXTE = "BAAI/bge-m3"
MODELE_IMAGES = "clip-ViT-B-32"


@lru_cache(maxsize=1)
def _modele_texte() -> SentenceTransformer:
    """Charge le modèle texte une seule fois par processus."""

    return SentenceTransformer(MODELE_TEXTE)


@lru_cache(maxsize=1)
def _modele_images() -> SentenceTransformer:
    """Charge le modèle image une seule fois par processus."""

    return SentenceTransformer(MODELE_IMAGES)


def embedding_texte(liste_de_textes: Sequence[str]) -> list[list[float]]:
    """Transforme une liste de textes en vecteurs de dimension 1024."""

    if not liste_de_textes:
        return []

    vecteurs = _modele_texte().encode(
        list(liste_de_textes),
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vecteurs.tolist()


def embedding_images(
    liste_de_chemins: Sequence[str | Path],
) -> list[list[float]]:
    """Transforme des chemins d'images en vecteurs de dimension 512."""

    if not liste_de_chemins:
        return []

    images: list[Image.Image] = []
    for chemin in liste_de_chemins:
        with Image.open(chemin) as image:
            images.append(image.convert("RGB"))

    vecteurs = _modele_images().encode(
        images,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vecteurs.tolist()
