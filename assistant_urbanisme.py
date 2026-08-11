"""
Assistant d'urbanisme basé sur les données PLUi, une recherche vectorielle
MongoDB et un LLM Groq.

Application Gradio permettant de poser une question à propos d'une parcelle
et d'obtenir une réponse basée sur les documents d'urbanisme disponibles.

Configuration via variables d'environnement :
    MONGO_DB_PASSWORD : mot de passe MongoDB
    GROQ_API_KEY      : clé API Groq
    MONGO_USERNAME    : utilisateur MongoDB (défaut : sig_test)
    MONGO_HOST        : hôte MongoDB (défaut : cluster0.rrvhdpu.mongodb.net)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import gradio as gr
import requests
from groq import Groq
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = (
    "https://portail.sigsbaa.fr/arcgis/rest/services/"
    "SIGSBAA/cadplui/FeatureServer"
)

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "sig_test")
MONGO_HOST = os.getenv("MONGO_HOST", "cluster0.rrvhdpu.mongodb.net")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")

DATABASE_NAME = os.getenv("MONGO_DATABASE", "Urbanisme_test_0508")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "Documents")
VECTOR_INDEX = os.getenv("MONGO_VECTOR_INDEX", "vector_index_test_0508")

MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

http = requests.Session()

_embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

_mongo_client: MongoClient | None = None
_collection = None

if not MONGO_DB_PASSWORD:
    logger.warning(
        "MONGO_DB_PASSWORD n'est pas définie. "
        "La recherche MongoDB ne sera pas disponible."
    )
else:
    mongo_uri = (
        f"mongodb+srv://{MONGO_USERNAME}:{MONGO_DB_PASSWORD}"
        f"@{MONGO_HOST}/?appName=Cluster0"
    )
    try:
        _mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=REQUEST_TIMEOUT * 1000,
        )
        _mongo_client.admin.command("ping")
        _collection = _mongo_client[DATABASE_NAME][COLLECTION_NAME]
        logger.info("Connexion à MongoDB réussie.")
    except Exception:
        logger.exception("Impossible de se connecter à MongoDB.")
        _mongo_client = None
        _collection = None


groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise RuntimeError(
        "La variable d'environnement GROQ_API_KEY est absente."
    )

llm_client = Groq(api_key=groq_api_key)


# ---------------------------------------------------------------------------
# PLUi
# ---------------------------------------------------------------------------


def get_plui(commune: str, parcelle: str) -> dict[str, Any] | list[Any]:
    """Récupère les informations PLUi associées à une parcelle."""

    # 1. Trouver l'identifiant de la parcelle.
    url = f"{BASE_URL}/0/query"
    params = {
        "where": f"ident LIKE '%{parcelle}' AND code_comm='{commune}'",
        "outFields": "id_parcelle",
        "returnGeometry": "false",
        "f": "json",
    }

    response = http.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT,
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    data = response.json()

    features = data.get("features", [])
    if not features:
        raise ValueError("Parcelle introuvable.")

    id_parcelle = features[0]["attributes"]["id_parcelle"]

    # 2. Trouver les identifiants des informations PLUi.
    url = f"{BASE_URL}/18/query"
    params = {
        "where": f"id_parcelle={id_parcelle}",
        "outFields": "id_information_plui",
        "returnGeometry": "false",
        "f": "json",
    }

    response = http.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT,
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    data = response.json()

    ids = [
        feature["attributes"]["id_information_plui"]
        for feature in data.get("features", [])
    ]

    if not ids:
        return []

    # 3. Récupérer les informations PLUi.
    url = f"{BASE_URL}/17/query"
    params = {
        "where": f"id_information_plui IN ({','.join(map(str, ids))})",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
    }

    response = http.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT,
        verify=VERIFY_SSL,
    )
    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# Recherche vectorielle
# ---------------------------------------------------------------------------


def generate_embedding(question: str) -> list[float]:
    """Génère l'embedding normalisé d'une question."""

    vector = _embedding_model.encode(
        question,
        normalize_embeddings=True,
    )
    return vector.tolist()


def vector_search(question: str, limit: int = 5) -> list[dict[str, Any]]:
    """Effectue une recherche vectorielle dans MongoDB."""

    if _collection is None:
        logger.error("Connexion MongoDB indisponible.")
        return []

    query_vector = generate_embedding(question)

    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit,
            }
        },
        {
            "$project": {
                "_id": 0,
                "chunk_text": 1,
                "document_name": 1,
                "page_number": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    return list(_collection.aggregate(pipeline))


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
Tu es un assistant spécialisé dans l’analyse des documents d’urbanisme
(PLU, PLUi, règlements écrits, prescriptions graphiques et notes d’urbanisme).

Ta mission est de répondre uniquement à partir :
- des extraits de documents fournis ;
- des informations liées à la parcelle.

Consignes :
- Réponds en français.
- Utilise un ton pédagogique et professionnel.
- Ne mentionne jamais MongoDB ni les scores.
- Ne complète jamais avec des règles générales absentes des documents.
- Cite systématiquement le document et la page lorsque tu utilises un extrait.
- Ne donne jamais de validation administrative définitive.

Structure obligatoire :

1. Contexte de la parcelle
- Numéro de parcelle si disponible.
- Commune.
- Zone PLU/PLUi.
- Prescriptions ou contraintes utiles.

2. Réponse à la question
- Répond directement au projet demandé.
- Indique si le projet semble compatible ou non avec les règles extraites.
- Distingue toujours :
  - compatibilité avec les documents analysés ;
  - validation finale nécessitant une instruction administrative.

3. Règles applicables au projet
Présente uniquement les règles extraites utiles.

4. Points à vérifier avant réalisation
Présente uniquement les vérifications complémentaires nécessaires.

Termine obligatoirement par :

"Ces informations sont données à titre indicatif.
Elles ne remplacent pas un document officiel ou une consultation en mairie."
""".strip()


def ask_llm(
    question: str,
    chunks: list[dict[str, Any]],
    contexte_parcelle: str = "",
) -> str | None:
    """Génère une réponse à partir des documents retrouvés."""

    documents = "\n\n".join(
        (
            f"Document : {chunk.get('document_name', 'N/A')}\n"
            f"Page : {chunk.get('page_number', 'N/A')}\n\n"
            f"Extrait :\n{chunk.get('chunk_text', '')}\n"
            "--------------------------------"
        )
        for chunk in chunks
    )

    prompt = f"""
CONTEXTE PARCELLE :

{contexte_parcelle}

QUESTION UTILISATEUR :

{question}

DOCUMENTS DISPONIBLES :

{documents}

Réponds uniquement à partir des documents fournis.
""".strip()

    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    except Exception:
        logger.exception("Erreur lors de l'appel au LLM.")
        return None


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


def chatbot(commune: str, parcelle: str, question: str) -> str:
    """Pipeline principal appelé par l'interface Gradio."""

    if not commune or not parcelle or not question:
        return "Veuillez renseigner la commune, la parcelle et la question."

    try:
        # 1. Récupération des informations PLUi.
        resultat = get_plui(commune, parcelle)

        # 2. Recherche documentaire.
        chunks = vector_search(question)

        if not chunks:
            return "Aucun document PLUi trouvé pour répondre à cette question."

        # 3. Création du contexte parcellaire.
        contexte = f"""
Commune : {commune}
Parcelle : {parcelle}

Informations PLUi :
{resultat}
""".strip()

        # 4. Génération de la réponse.
        reponse = ask_llm(
            question=question,
            chunks=chunks,
            contexte_parcelle=contexte,
        )

        return reponse or "Impossible de générer une réponse."

    except requests.RequestException as exc:
        logger.exception("Erreur lors de la récupération des données PLUi.")
        return f"Erreur lors de la récupération des données PLUi : {exc}"

    except Exception as exc:
        logger.exception("Erreur dans le chatbot.")
        return f"Erreur : {exc}"


def create_interface() -> gr.Interface:
    """Construit l'interface Gradio."""

    return gr.Interface(
        fn=chatbot,
        inputs=[
            gr.Textbox(
                label="Code commune",
                placeholder="Exemple : 220XXX",
            ),
            gr.Textbox(
                label="Numéro parcelle",
                placeholder="Exemple : AB123",
            ),
            gr.Textbox(
                label="Votre question",
                placeholder="Puis-je construire une piscine ?",
            ),
        ],
        outputs=gr.Textbox(label="Réponse assistant urbanisme"),
        title="Assistant urbanisme",
        description="Assistant IA basé sur le règlement du PLUi de SBAA.",
        theme=gr.themes.Monochrome(),
    )


def main() -> None:
    """Point d'entrée de l'application."""

    demo = create_interface()
    demo.launch()


if __name__ == "__main__":
    main()
