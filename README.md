# PLUi RAG – Extraction et Embeddings

Ce projet contient deux notebooks Google Colab permettant de préparer des données textuelles pour un système de RAG (Retrieval Augmented Generation) appliqué à un règlement de Plan Local d'Urbanisme intercommunal (PLUi). Chaque script découpe du texte en morceaux (chunks) et génère un embedding vectoriel pour chacun via le modèle `all-MiniLM-L6-v2` (`sentence-transformers`), puis exporte le résultat au format JSON.

## Contenu du dépôt

| Fichier | Description |
|---|---|
| `reglement_plui` | Extrait le texte d'un document PDF, le découpe en chunks, génère les embeddings et exporte le tout en JSON. |
| `question_utilisateur` | Découpe une question ou un texte saisi manuellement par l'utilisateur, génère les embeddings et exporte le résultat en JSON. |

Les bibliothèques Python sont installées automatiquement dans la première cellule de chaque notebook :

- `pypdf` (uniquement pour `documents_plui.ipynb`)
- `sentence-transformers`
- `tqdm`

## 1. `reglement_plui` : Ingestion d'un document PDF

**Étapes du script :**

1. Installation des bibliothèques nécessaires (`pypdf`, `sentence-transformers`, `tqdm`).
2. Chargement d'un fichier PDF depuis votre ordinateur (via `files.upload()`).
3. Extraction du texte de chaque page du PDF.
4. Découpage en chunks : texte segmenté en morceaux de 500 caractères avec un chevauchement de 100 caractères, afin de préserver le contexte entre les segments.
5. Génération des embeddings pour chaque chunk avec le modèle `all-MiniLM-L6-v2`.
6. Export JSON : création et téléchargement d'un fichier `<nom_du_pdf>_chunks_with_embeddings.json`.

**Utilisation :**

1. Ouvrir le notebook dans Google Colab.
2. Exécuter les cellules dans l'ordre.
3. À l'étape 2, sélectionner le fichier PDF à charger lorsque demandé.
4. Le fichier JSON final se télécharge automatiquement en fin d'exécution.

**Format de sortie :**

```json
[
  {
    "document_name": "200069409_reglement_20250626.pdf",
    "page_number": 1,
    "chunk_text": "Plan Local d'Urbanisme intercommunal (PLUi)...",
    "embedding": [-0.0256, -0.0119, 0.0952, ...]
  }
]
```

## 2. `question_utilisateur` : Traitement d'une question / d'un texte libre

**Étapes du script :**

1. Installation des bibliothèques nécessaires (`sentence-transformers`, `tqdm`).
2. Chargement du modèle d'embeddings `all-MiniLM-L6-v2`.
3. Saisie interactive d'une question ou d'un texte via `input()`.
4. Découpage en chunks (mêmes paramètres : 500 caractères, chevauchement de 100).
5. Génération des embeddings pour chaque chunk.
6. Export JSON : création et téléchargement d'un fichier `question_chunks_with_embeddings_<horodatage>.json`.

**Utilisation :**

1. Ouvrir le notebook dans Google Colab.
2. Exécuter la cellule (fonction `process_question()` appelée automatiquement).
3. Saisir le texte ou la question dans le champ interactif.
4. Le fichier JSON se télécharge automatiquement.
5. Pour traiter plusieurs questions, appeler à nouveau `process_question()` dans une nouvelle cellule.

**Format de sortie :**

```json
[
  {
    "chunk_text": "Texte de la question ou du chunk...",
    "embedding": [-0.0256, -0.0119, 0.0952, ...]
  }
]
```

## Notes

### Modèles d'embeddings et paramètres de chunking

| Script | Traitement | Modèle d'embeddings | Dimensions | Taille de chunk | Chevauchement |
|---|---|---|---|---|---|
| `documents_plui.ipynb` | Texte extrait du PDF (page par page) | `all-MiniLM-L6-v2` | 384 | 500 caractères | 100 caractères |
| `Untitled0.ipynb` | Question / texte saisi par l'utilisateur | `all-MiniLM-L6-v2` | 384 | 500 caractères | 100 caractères |

- Les deux scripts utilisent le **même modèle** (`all-MiniLM-L6-v2`, bibliothèque `sentence-transformers`) et la **même stratégie de chunking**, ce qui garantit que les embeddings du document et ceux des questions sont comparables dans le même espace vectoriel (similarité cosinus, produit scalaire...).
- Paramètres de découpage par défaut : `CHUNK_SIZE = 500` caractères, `CHUNK_OVERLAP = 100` caractères. Ils sont modifiables en tête de chaque notebook — **si vous les changez, faites-le dans les deux scripts** pour garder une granularité cohérente entre base documentaire et requêtes.
- `all-MiniLM-L6-v2` est un modèle léger (~80 Mo, rapide même sur CPU). Pour une meilleure qualité sémantique, `all-mpnet-base-v2` (768 dimensions) est une alternative, à condition de régénérer les embeddings des deux côtés avec le même modèle.
- Les fichiers JSON générés peuvent alimenter une base vectorielle (FAISS, ChromaDB, Pinecone...) pour une application RAG.
