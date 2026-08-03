# Chatbot IA pour une application d'urbanisme

## Présentation

Ce projet a pour objectif de développer un **chatbot basé sur l'intelligence artificielle** capable de répondre aux questions des utilisateurs à partir de documents d'urbanisme (PLUi, règlements, documents techniques, etc.).

L'objectif est de permettre une consultation plus intuitive de ces documents en utilisant un modèle de langage (LLM) enrichi par une base documentaire.

---

## Architecture envisagé 

Après avoir étudié plusieurs approches pour intégrer un modèle de langage à une base documentaire (modèle affiné, modèle entraîné, ingénierie rapide avec contexte), notre choix s'est porté sur une architecture **RAG (Retrieval-Augmented Generation)**, de type séquence.

Cette approche présente plusieurs avantages :

* les réponses sont générées à partir des documents du projet plutôt que des seules connaissances du modèle ;
* les documents peuvent être mis à jour sans avoir à réentraîner le modèle ;
* les réponses sont plus pertinentes et davantage contextualisées ;
* le coût de mise en œuvre est réduit par rapport à un fine-tuning complet ;
* il est possible de citer les passages utilisés pour générer la réponse, améliorant ainsi la traçabilité.

---

## Architecture générale

Le schéma ci-dessous présente une idée de fonctionnement.

![Architecture RAG](architecture_rag.png)

## État actuel du projet

À ce stade, l'objectif est de valider expérimentalement le fonctionnement d'un système RAG.

Les tests sont réalisés de manière manuelle afin d'évaluer la qualité des réponses produites avant toute intégration dans une application d'urbanisme.

---

## Contenu du projet

Le dépôt contient actuellement deux scripts principaux permettant de préparer les données textuelles nécessaires au système RAG :

Ces scripts constituent la première étape de la chaîne de traitement avant l'interrogation par le modèle de langage.

---

## Travaux en cours

Les travaux actuels visent à améliorer la pertinence des réponses générées. Plusieurs pistes sont explorées :

* amélioration du prompt envoyé au LLM ;
* augmentation du nombre d'échantillons récupérés (paramétrage de la pipeline RAG) ;
* comparaison de différents modèles d'embeddings ;
* expérimentation de différentes tailles de chunks et stratégies de découpage ;
* optimisation des paramètres de recherche dans la base vectorielle ;
* évaluation qualitative des réponses obtenues.
