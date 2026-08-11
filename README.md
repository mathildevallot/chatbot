# Chatbot IA pour une application d'urbanisme

## Présentation

Ce projet a pour objectif de développer un **chatbot basé sur l'intelligence artificielle** capable de répondre aux questions des utilisateurs à partir de documents d'urbanisme (PLUi, règlements, documents techniques, etc.).

L'objectif est de permettre une consultation plus intuitive de ces documents en utilisant un modèle de langage (LLM) enrichi par une base documentaire.

---

## Architecture envisagée 

Après avoir vu plusieurs approches pour intégrer un modèle de langage à une base documentaire (modèle affiné, modèle entraîné, ingénierie rapide avec contexte), nous étudions pour le moment l'architecture **RAG (Retrieval-Augmented Generation)**, de type séquence.

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
Depuis les premiers tests manuels, une partie de la chaîne a été automatisée : l'extraction, le découpage, la génération des embeddings et la recherche vectorielle sont désormais scriptés, et une application (assistant_urbanisme.py) permet d'interroger le système de bout en bout via une interface simple, sans intervention manuelle sur la partie recherche/réponse.

L'application s'appuie sur une interface Gradio et est actuellement hébergée sur Render, ce qui permet de la mettre à disposition pour des tests sans nécessiter d'installation locale.
https://chatbot-gati.onrender.com/

À noter concernant la lenteur au démarrage : l'hébergement étant sur l'offre gratuite de Render, le service se met en veille après 15 minutes d'inactivité. Lors de la première requête suivant une période d'inactivité, un délai de 30 à 60 secondes (redémarrage à froid, "cold start") est donc à prévoir avant d'obtenir une réponse. Les requêtes suivantes sont ensuite normales tant que l'application reste active.

---

## Contenu du projet

Le dépôt contient actuellement : 

- 2 scripts principaux :
un script de préparation des données textuelles (extraction, découpage, embeddings), disponible en documents_plui.py et en notebook ;
le script applicatif : assistant_urbanisme.py, qui automatise la récupération des données parcellaires, la recherche vectorielle et la génération de la réponse par le LLM ;
le paramétrage de la pipeline d'agrégation ;
les éléments de connexion à la DB (sauf mot de passe), via un fichier .env.example ;
un README dédié aux scripts, détaillant leur fonctionnement respectif : readme_for_scripts.md ;
les éléments liés à 2 parcelles test, servant d'éléments de contexte : contexte_parcelle-test.json et contexte_parcelle-test1.json ;
le paramétrage de l'index vectoriel utilisé pour la DB ;
le schéma de la DB.
---

## Travaux en cours

Le projet est actuellement en phase de transmission pour test, avant une éventuelle mise en benchmark. Les pistes de travail restent les suivantes :

amélioration du prompt envoyé au LLM ;
augmentation du nombre d'échantillons récupérés (paramétrage de la pipeline RAG) ;
expérimentation de différentes tailles de chunks et stratégies de découpage ;
optimisation des paramètres de recherche dans la base vectorielle ;
évaluation qualitative des réponses obtenues, notamment en comparaison avec les retours des projets menés par les villes d'Istres et de Houilles sur des chatbots d'urbanisme similaires.
