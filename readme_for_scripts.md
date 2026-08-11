# Le projet est composé de deux scripts :

| Script | Rôle |
|---|---|
| `documents_plui.ipynb` | Génère un fichier JSON (texte + embeddings) à partir d'un PDF, à importer **manuellement** dans la base vectorielle |
| `app.py` | Application complète : interroge la parcelle, effectue la recherche vectorielle dans MongoDB et génère la réponse via un LLM (Groq) |

version python : python==3.11.x
---

## 1. `documents_plui.ipynb` — Préparation des documents (Google Colab)

Ce notebook prépare les données qui alimenteront la base vectorielle MongoDB. Il ne fait **aucun appel à MongoDB** : il produit un fichier `.json` téléchargeable, à insérer ensuite manuellement dans la collection.

### Étapes du notebook

1. **Installation des dépendances** : `pypdf`, `sentence-transformers`, `tqdm`.
2. **Upload du PDF** via `google.colab.files.upload()`.
3. **Extraction du texte** page par page avec `pypdf` (`PdfReader`), en conservant le numéro de page associé à chaque bloc de texte.
4. **Découpage en chunks (chunking)** :
   - Le texte de chaque page est d'abord normalisé (suppression des sauts de ligne/espaces multiples).
   - Découpage **par nombre de caractères**, avec chevauchement (overlap) pour ne pas perdre le contexte entre deux chunks.
   - **Paramètres utilisés :**
     - `CHUNK_SIZE = 500` caractères
     - `CHUNK_OVERLAP = 100` caractères
   - Dédoublonnage des chunks strictement identiques.
   - Chaque chunk conserve : `document_name`, `page_number`, `chunk_text`.
5. **Génération des embeddings** avec `sentence-transformers` :
   - **Modèle : `all-MiniLM-L6-v2`**
   - Chaque `chunk_text` est encodé en un vecteur (converti en `list` pour la sérialisation JSON) et ajouté au champ `embedding`.
6. **Export JSON** : un fichier `<nom_du_pdf>_chunks_with_embeddings.json` est généré et téléchargé automatiquement, avec la structure suivante par entrée :

```json
{
  "document_name": "reglement_plui.pdf",
  "page_number": 12,
  "chunk_text": "Extrait du texte...",
  "embedding": [0.0123, -0.045, ...]
}
```

### Import manuel dans MongoDB

Ce JSON doit ensuite être importé **manuellement** dans la collection MongoDB (`Documents` par défaut), avec un index vectoriel créé sur le champ `embedding` (via `$vectorSearch` / Atlas Vector Search).

---

## 2. `app.py` — Application RAG (Gradio)

Ce script constitue l'**application de production** : interface Gradio + pipeline complet de bout en bout, sans étape manuelle.

### Pipeline exécuté à chaque question

1. **Récupération des données PLUi de la parcelle** (`get_plui`) :
   - Interroge l'API ArcGIS FeatureServer du portail SIG SBAA en 3 étapes :
     1. Résolution de `id_parcelle` à partir de la commune et du numéro de parcelle (couche `0`).
     2. Récupération des `id_information_plui` liés à la parcelle (couche `18`).
     3. Récupération du détail des informations PLUi (couche `17`).
2. **Recherche vectorielle** (`vector_search`) :
   - La question de l'utilisateur est encodée avec **`fastembed` / `TextEmbedding`**, en utilisant le même modèle que le notebook : `sentence-transformers/all-MiniLM-L6-v2`. (le modèle n'est pas inclus dans le dépôt et sera téléchargé automatiquement)
   - Une agrégation MongoDB `$vectorSearch` est exécutée sur l'index vectoriel (`numCandidates: 100`, `limit: 5` par défaut) pour récupérer les chunks les plus pertinents (`chunk_text`, `document_name`, `page_number`, score de similarité).
3. **Construction du contexte** : les informations de la parcelle (API ArcGIS) et les chunks retrouvés sont assemblés dans un prompt structuré.
4. **Génération de la réponse** (`ask_llm`) via l'API **Groq** :
   - Modèle : `llama-3.3-70b-versatile` (configurable)
   - `temperature=0.1`, `max_tokens=2000`
   - Un **prompt système** strict impose :
     - réponse en français, ton pédagogique ;
     - usage exclusif des extraits fournis (pas de règles générales inventées) ;
     - citation systématique du document et de la page ;
     - structure obligatoire : *Contexte de la parcelle → Réponse à la question → Règles applicables → Points à vérifier* ;
     - une mention de non-validité juridique en fin de réponse.
5. **Restitution** dans l'interface Gradio (`gr.Interface`).

### Interface utilisateur

Formulaire à 3 champs (`gr.Interface`) :
- Code commune
- Numéro de parcelle
- Question libre

Réponse affichée dans une zone de texte unique.

### Variables d'environnement

voir env.example

### Installation & lancement

```bash
pip install gradio requests fastembed groq pymongo

export MONGO_DB_PASSWORD="..."
export GROQ_API_KEY="..."

python app.py
```

---

## Résumé du modèle d'embedding et du chunking

| Paramètre | Valeur | Utilisé dans |
|---|---|---|
| Modèle d'embedding | `sentence-transformers/all-MiniLM-L6-v2` | Indexation (notebook, via `sentence-transformers`) **et** requêtage (`app.py`, via `fastembed`) |
| Taille des chunks | 800 caractères | Notebook d'indexation |
| Chevauchement (overlap) | 110 caractères | Notebook d'indexation |
| Stratégie de découpage | Découpage brut par nombre de caractères, par page, avec dédoublonnage des chunks identiques | Notebook d'indexation |

---

## Architecture globale

```
┌────────────────────────┐        ┌──────────────────────────┐
│  documents_plui.ipynb  │  JSON  │      Import manuel         │
│  (extraction + chunks  │ ─────► │      dans MongoDB          │
│   + embeddings)        │        │  (collection + index      │
└────────────────────────┘        │   vectoriel Atlas)         │
                                   └────────────┬───────────────┘
                                                │
                                                ▼
┌────────────────────────┐    question    ┌──────────────────────────┐
│   Interface Gradio      │ ─────────────► │        app.py             │
│   (commune, parcelle,   │                │  1. API ArcGIS (parcelle) │
│    question)            │                │  2. Recherche vectorielle │
│                          │ ◄───────────── │  3. Génération LLM (Groq) │
└────────────────────────┘    réponse      └──────────────────────────┘
```
Accès réseau requis à l'exécution (pas seulement à l'installation)

Au-delà de l'installation des paquets Python, le script a besoin, à chaque exécution, d'un accès sortant vers les services suivants :

Service	Hôte	Usage
API ArcGIS PLUi	: portail.sigsbaa.fr	: Récupération des données de la parcelle
MongoDB Atlas	: cluster0.rrvhdpu.mongodb.net (ou valeur de MONGO_HOST)	: Recherche vectorielle (protocole SRV/DNS, port habituel 27017)
API Groq	api.groq.com	: Génération de la réponse par le LLM
Hugging Face / hébergement du modèle	(dépend de fastembed)	: Téléchargement du modèle d'embedding
