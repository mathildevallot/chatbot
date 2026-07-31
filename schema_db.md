# Schéma : database

Document représentant un chunk de texte issu d'un document d'urbanisme, avec son embedding vectoriel (pipeline RAG / recherche sémantique).

## Champs requis

- **`_id`** (`ObjectId`) — identifiant MongoDB
- **`document_name`** (`string`) — nom du document source
- **`page_number`** (`integer`) — numéro de page
- **`chunk_text`** (`string`) — extrait de texte
- **`embedding`** (`array<Double>`) — vecteur représentant `chunk_text`

## Types personnalisés

### ObjectId

Chaîne hexadécimale de 24 caractères exactement :

\`\`\`
{ "$oid": "507f1f77bcf86cd799439011" }
\`\`\`

### Double

Soit un nombre JSON classique (`0.0234`), soit un wrapper Extended JSON MongoDB pour les valeurs spéciales :

\`\`\`
{ "$numberDouble": "Infinity" }
{ "$numberDouble": "-Infinity" }
{ "$numberDouble": "NaN" }
\`\`\`

## Points d'attention

- Format Extended JSON MongoDB (`$oid`, `$numberDouble`) — visible surtout en JSON brut exporté (mongoexport), pas via un driver natif (pymongo, mongoose...).
- Aucune contrainte de dimension sur `embedding`.
- `additionalProperties: false` uniquement sur `ObjectId`, pas sur le document racine.
- Aucun format imposé pour `document_name`.
