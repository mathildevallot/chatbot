# Chatbot - Génération d'embeddings pour question utilisateur

## Description

Ce projet permet de transformer un texte ou une question en morceaux ("chunks") puis de générer des embeddings grâce à un modèle de langage.

Les embeddings obtenus peuvent ensuite être utilisés pour de la recherche sémantique, un système de chatbot ou une architecture RAG (Retrieval Augmented Generation).

## Fonctionnalités

- Découpage automatique du texte en plusieurs morceaux (chunks)
- Nettoyage du texte
- Génération d'embeddings avec le modèle `all-MiniLM-L6-v2`
- Export des résultats au format JSON
- Téléchargement du fichier généré

## Technologies utilisées

- Python
- Google Colab
- Sentence Transformers
- TQDM

## Installation

Installer les dépendances :

```bash
pip install sentence-transformers tqdm
