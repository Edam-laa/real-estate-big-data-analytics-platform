# Real Estate Analytics & Price Prediction Platform

## Présentation

Ce projet consiste à construire une plateforme analytique immobilière basée sur le dataset **Ames Housing**.  
L’objectif n’est pas uniquement de prédire le prix des maisons, mais de mettre en place un pipeline complet allant de la donnée brute jusqu’à l’analyse, la modélisation et la visualisation.

Le projet simule une architecture data moderne intégrant :

- préparation des données avec Python,
- stockage distribué avec HDFS,
- traitement et Machine Learning avec Apache Spark,
- stockage structuré avec PostgreSQL,
- visualisation analytique avec Python,
- démonstration d’une interface de plateforme.

---

## Objectifs du projet

Le projet vise à répondre à quatre objectifs principaux :

1. Comprendre le marché immobilier à partir des données.
2. Identifier les facteurs qui influencent le prix des maisons.
3. Construire et comparer plusieurs modèles de Machine Learning.
4. Analyser les prédictions, les erreurs et les limites du modèle.

---

## Problématique

Dans le domaine immobilier, l’estimation du prix d’un bien dépend de nombreux facteurs : surface, localisation, qualité générale, ancienneté, équipements, etc.

La problématique traitée est donc :

> Comment exploiter des données immobilières pour comprendre le marché, identifier les facteurs déterminants et prédire le prix des maisons à travers une plateforme analytique complète ?

---

## Dataset utilisé

Le projet utilise le dataset **Ames Housing**, un dataset de référence pour les problèmes de régression immobilière.

### Caractéristiques principales

- Dataset : `AmesHousing.tsv`
- Nombre initial de lignes : environ 2930
- Nombre initial de colonnes : 82
- Variable cible : `SalePrice`
- Type de problème : régression supervisée

Ce dataset est particulièrement intéressant car il contient des variables numériques et catégorielles décrivant les maisons, leur localisation, leur structure, leur qualité et leurs conditions de vente.

---

## Architecture globale

Le pipeline global du projet suit la logique suivante :

```text
Dataset brut
   ↓
Préparation Python
   ↓
Dockerisation
   ↓
Stockage HDFS
   ↓
Traitement Spark / Machine Learning
   ↓
Stockage PostgreSQL
   ↓
Visualisation / Démo plateforme
