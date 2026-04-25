# Plateforme d’Analyse et de Prédiction Immobilière — Ames Housing

## Présentation du projet

Ce projet consiste à construire une plateforme analytique immobilière basée sur le dataset **Ames Housing**.

L’objectif n’est pas uniquement de prédire le prix des maisons, mais de mettre en place un pipeline complet allant de la donnée brute jusqu’à l’analyse, la modélisation, le stockage et la visualisation.

Le projet s’inscrit dans un contexte Big Data académique et simule une architecture data moderne composée de plusieurs couches :

- préparation des données,
- stockage distribué,
- traitement Spark,
- Machine Learning,
- stockage PostgreSQL,
- visualisation analytique,
- démonstration d’une plateforme.

---

## Objectifs

Les objectifs principaux du projet sont :

- comprendre le marché immobilier,
- identifier les facteurs qui influencent le prix des maisons,
- construire et comparer plusieurs modèles de Machine Learning,
- analyser les prédictions et les erreurs,
- centraliser les résultats dans une base PostgreSQL,
- produire des visualisations exploitables,
- proposer une vision de plateforme analytique immobilière.

---

## Problématique

Dans le domaine immobilier, le prix d’un bien dépend de plusieurs facteurs : surface, localisation, qualité générale, ancienneté, équipements, etc.

La problématique traitée est donc :

> Comment exploiter des données immobilières afin de comprendre le marché, identifier les facteurs déterminants et prédire le prix des maisons à travers une plateforme analytique complète ?

---

## Dataset utilisé

Le projet utilise le dataset **Ames Housing**, un dataset de référence pour les problèmes de régression immobilière.

### Caractéristiques principales

- Fichier source : `AmesHousing.tsv`
- Nombre initial de lignes : environ 2930
- Nombre initial de colonnes : 82
- Variable cible : `SalePrice`
- Type de problème : régression supervisée

Ce dataset contient des variables numériques et catégorielles décrivant les maisons, leur localisation, leur structure, leur qualité, leurs équipements et leurs conditions de vente.

---

## Architecture globale

Le pipeline global du projet suit la logique suivante :

```text
AmesHousing.tsv
      ↓
Python — Nettoyage & Feature Engineering
      ↓
Docker — Environnement reproductible
      ↓
HDFS — Stockage distribué
      ↓
Spark / PySpark — Traitement & Machine Learning
      ↓
PostgreSQL — Stockage structuré
      ↓
Python — Visualisation analytique
      ↓
Démo plateforme — Interface analytique
```

Cette architecture permet de représenter une chaîne complète de traitement de données, proche d’une plateforme data réelle.

---

## Technologies utilisées

| Technologie | Rôle dans le projet |
|---|---|
| Python | Nettoyage, préparation, feature engineering et visualisation |
| Docker | Conteneurisation et orchestration des environnements |
| HDFS | Stockage distribué des données préparées |
| Apache Spark / PySpark | Traitement distribué et Machine Learning |
| PostgreSQL | Stockage structuré des données et résultats |
| Pandas / Matplotlib | Analyse et génération automatique des graphes |
| Canva / UI Mockup | Démonstration visuelle de la plateforme |

---

## Structure du dépôt

```text
.
├── README.md
├── docs/
│
├── phase2_docker/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── data/
│   ├── output/
│   └── src/
│
├── phase3_hdfs/
│   └── docker-compose.yml
│
├── phase4_spark/
│   ├── docker-compose.yml
│   └── app/
│       └── train_house_price_model.py
│
├── phase5_postgresql/
│   ├── docker-compose.yml
│   ├── import_houses.py
│   ├── data/
│   └── init/
│       └── create_tables.sql
│
├── phase6_visualisation/
│   ├── visualization_postgres.py
│   ├── texte_soutenance_visualisations_ames.md
│   └── output/
│
└── phase7_platform/
```

---

## Description des phases

### Phase 1 — Préparation et nettoyage des données

La première étape consiste à préparer le dataset brut afin de le rendre exploitable.

Les traitements réalisés incluent :

- chargement du fichier `AmesHousing.tsv`,
- nettoyage des colonnes,
- gestion des valeurs manquantes,
- suppression des outliers documentés,
- préparation des variables pour l’analyse et la modélisation.

Cette étape permet d’obtenir un dataset propre et cohérent.

---

### Phase 2 — Dockerisation

La dockerisation permet de rendre l’environnement du projet plus stable et reproductible.

Elle facilite :

- l’isolation des dépendances,
- la portabilité du projet,
- la structuration du pipeline,
- la préparation d’une architecture plus proche d’un environnement réel.

---

### Phase 3 — Stockage HDFS

Le dataset préparé est stocké dans HDFS afin de simuler une logique Big Data.

Cette phase permet de faire le lien entre la préparation locale des données et leur traitement distribué avec Spark.

---

### Phase 4 — Traitement Spark et Machine Learning

Spark / PySpark est utilisé pour traiter les données et entraîner les modèles de prédiction.

Les modèles utilisés sont :

- Linear Regression,
- Random Forest Regressor,
- Gradient Boosting Regressor.

Les métriques utilisées pour comparer les modèles sont :

- RMSE,
- MAE,
- R².

L’objectif est de comparer plusieurs approches et de sélectionner le modèle le plus pertinent selon un compromis entre performance, simplicité et interprétabilité.

---

### Phase 5 — Stockage PostgreSQL

PostgreSQL est utilisé comme base analytique pour centraliser les données et les résultats.

Les principales tables sont :

- `houses_core`
- `houses_location`
- `houses_structure`
- `houses_sale`
- `model_runs`
- `predictions`

Cette structuration permet de séparer les informations descriptives, géographiques, structurelles, commerciales et analytiques.

---

### Phase 6 — Visualisation analytique

Les visualisations sont générées automatiquement depuis PostgreSQL grâce au script :

```text
phase6_visualisation/visualization_postgres.py
```

Les graphes sont enregistrés dans :

```text
phase6_visualisation/output/
```

Les visualisations couvrent quatre axes :

1. Analyse du marché immobilier
2. Analyse des facteurs influençant le prix
3. Comparaison des modèles Machine Learning
4. Analyse des prédictions et des erreurs

---

### Phase 7 — Démo plateforme

Une maquette de plateforme analytique a été réalisée afin de matérialiser la vision produit du projet.

Cette partie illustre :

- la consultation des maisons,
- les filtres analytiques,
- les prédictions de prix,
- les indicateurs clés,
- la comparaison des modèles,
- la visualisation des erreurs.

Les captures de la plateforme sont disponibles dans :

```text
phase7_platform/
```

---

## Visualisations produites

Le projet génère plusieurs graphes analytiques, notamment :

```text
01_distribution_prix.png
02_kpis_marche.png
03_prix_moyen_par_quartier.png
04_surface_vs_prix.png
05_qualite_vs_prix.png
14_heatmap_correlations.png
16_rmse_test_par_modele.png
17_mae_test_par_modele.png
18_r2_test_par_modele.png
20_reel_vs_predit.png
25_residus_vs_prix_reel.png
```

Ces visualisations permettent de comprendre le marché, d’expliquer les facteurs influents et d’évaluer les performances des modèles.

---

## Axes d’analyse

### Axe 1 — Analyse du marché immobilier

Cet axe permet de comprendre la structure globale du marché.

Exemples d’analyses :

- distribution des prix,
- prix moyen et médian,
- prix par quartier,
- surface vs prix,
- qualité vs prix.

---

### Axe 2 — Facteurs influençant le prix

Cet axe vise à expliquer pourquoi certains biens sont plus chers que d’autres.

Exemples d’analyses :

- impact de la surface totale,
- impact de l’âge de la maison,
- impact du nombre de salles de bain,
- effet du garage,
- effet de la cheminée,
- effet de la piscine,
- corrélations entre variables.

---

### Axe 3 — Comparaison des modèles ML

Cet axe compare les performances des modèles de Machine Learning.

Les métriques utilisées sont :

- RMSE : mesure l’erreur globale,
- MAE : mesure l’erreur moyenne absolue,
- R² : mesure la capacité explicative du modèle.

---

### Axe 4 — Analyse des prédictions et erreurs

Cet axe permet d’évaluer en détail les prédictions du modèle.

Exemples d’analyses :

- prix réel vs prix prédit,
- distribution des erreurs,
- top erreurs,
- erreurs par gamme de prix,
- résidus selon le prix réel.

---

## Exécution rapide

### 1. Cloner le dépôt

```bash
git clone https://github.com/USERNAME/real-estate-big-data-analytics-platform.git
cd real-estate-big-data-analytics-platform
```

Remplacer `USERNAME` par le nom d’utilisateur GitHub.

---

### 2. Lancer les services Docker

Exécuter les commandes Docker dans les dossiers concernés.

Exemple :

```bash
cd phase5_postgresql
docker compose up -d
```

Pour HDFS et Spark :

```bash
cd phase3_hdfs
docker compose up -d
```

```bash
cd phase4_spark
docker compose up -d
```

---

### 3. Préparer les données

Depuis le dossier de préparation :

```bash
cd phase2_docker
python src/prepare_ames_housing.py
```

---

### 4. Exécuter le pipeline Spark / ML

Depuis le dossier Spark :

```bash
cd phase4_spark/app
python train_house_price_model.py
```

---

### 5. Importer les données dans PostgreSQL

Depuis le dossier PostgreSQL :

```bash
cd phase5_postgresql
python import_houses.py
```

---

### 6. Générer les visualisations

Depuis le dossier de visualisation :

```bash
cd phase6_visualisation
python visualization_postgres.py
```

Les résultats seront générés dans :

```text
phase6_visualisation/output/
```

---

## Résultats attendus

À la fin de l’exécution, le projet permet d’obtenir :

- un dataset préparé,
- des modèles entraînés,
- des métriques de performance,
- des prédictions stockées en base,
- des visualisations analytiques,
- une démo visuelle de plateforme.

---

## Limites du projet

Ce projet est académique et démonstratif.

Ses principales limites sont :

- volume de données modéré,
- absence de traitement temps réel,
- architecture distribuée simulée,
- démo UI non connectée à une application complète,
- optimisation ML encore améliorable.

Cependant, ces limites sont assumées : l’objectif est de démontrer une démarche complète de data engineering, machine learning et visualisation.

---

## Perspectives d’amélioration

Plusieurs améliorations peuvent être envisagées :

- connecter Power BI directement à PostgreSQL,
- développer une vraie application web,
- exposer le modèle via une API,
- automatiser l’exécution du pipeline,
- enrichir les données avec des sources externes,
- ajouter un suivi historique des modèles,
- tester des modèles plus avancés.

---

## Conclusion

Ce projet représente une plateforme complète d’analyse et de prédiction immobilière.

Il combine :

- préparation des données,
- stockage distribué,
- traitement Spark,
- modélisation Machine Learning,
- base PostgreSQL,
- visualisation analytique,
- démonstration de plateforme.

L’intérêt du projet réside dans sa vision globale : il ne s’agit pas seulement d’un modèle prédictif, mais d’un pipeline complet capable de transformer des données brutes en informations exploitables pour l’aide à la décision immobilière.

---

## Auteurs

- Maaoui Siwar
- Laadhar Edam
