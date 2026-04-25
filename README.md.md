# Plateforme d’Analyse et de Prédiction Immobilière — Ames Housing

## 1. Présentation du projet

Ce projet a pour objectif de concevoir une **plateforme analytique immobilière complète** à partir du dataset **Ames Housing**.  
L’idée directrice n’est pas seulement d’entraîner un modèle de Machine Learning, mais de construire une chaîne cohérente allant :

- de la donnée brute,
- à la préparation et au stockage,
- jusqu’à l’analyse, la prédiction et la restitution visuelle.

Le projet s’inscrit dans un cadre académique Big Data, avec une approche progressive et réaliste.  
Même si le volume de données n’est pas massif au sens industriel, l’architecture mise en place reproduit la logique d’une vraie plateforme data moderne.

---

## 2. Vision produit

Le projet doit être compris comme une **plateforme d’analyse et d’aide à la décision pour l’immobilier**.

Elle vise à permettre :

- la compréhension du marché immobilier,
- l’identification des facteurs influençant les prix,
- la comparaison de plusieurs modèles prédictifs,
- l’analyse des erreurs de prédiction,
- la centralisation des données dans une base structurée,
- la démonstration d’une interface de plateforme analytique.

En plus du pipeline technique, une **démo de plateforme / maquette UI** a été réalisée pour matérialiser la vision produit.  
Ainsi, le projet ne se limite pas à du code ou à des graphiques isolés, mais s’inscrit dans une logique de **plateforme analytique immobilière**.

---

## 3. Problématique métier

Le projet simule un cas d’usage immobilier dans lequel une plateforme pourrait aider :

- une agence immobilière,
- un analyste du marché,
- un investisseur,
- un promoteur,
- un décideur métier.

La valeur métier apportée est double :

1. **Comprendre le marché**  
   Quels sont les quartiers les plus chers ? Quels facteurs font monter les prix ? Quels profils de biens dominent ?

2. **Prédire et expliquer**  
   Quel prix peut-on estimer pour un bien ? Quel modèle est le plus performant ? Dans quels cas le modèle se trompe-t-il ?

---

## 4. Dataset utilisé

Le dataset utilisé est **Ames Housing**.

### Caractéristiques générales

- **Source** : `AmesHousing.tsv`
- **Nombre initial de lignes** : 2930
- **Nombre initial de colonnes** : 82
- **Variable cible** : `SalePrice`

### Pourquoi ce dataset

Le dataset a été choisi car il :

- est reconnu dans les projets académiques de data science,
- contient de nombreuses variables explicatives,
- permet une vraie problématique de régression,
- est suffisamment riche pour produire une analyse métier intéressante,
- constitue un bon compromis entre faisabilité et profondeur analytique.

### Particularité importante

Le dataset recommande de supprimer les observations avec :

```text
Gr Liv Area > 4000
```

Cette règle a été intégrée au pipeline afin de réduire l’influence de cas extrêmes atypiques.

---

## 5. Positionnement du projet dans la logique Big Data

Ce projet est un **mini-projet académique inspiré des architectures Big Data**.

### Ce qu’il est

- une chaîne de traitement de données structurée,
- une architecture modulaire,
- une intégration entre préparation, stockage, traitement et visualisation,
- une démonstration de bonnes pratiques data engineering / analytics.

### Ce qu’il n’est pas

- un système industriel à grande échelle,
- une architecture temps réel,
- un cluster distribué imposé par le volume.

### Pourquoi il reste pertinent

Le projet permet de discuter de notions essentielles :

- Dockerisation,
- HDFS,
- Spark / PySpark,
- PostgreSQL,
- BI / visualisation,
- structuration d’un pipeline analytique complet.

---

## 6. Architecture globale du projet

L’architecture retenue suit la logique suivante :

```text
Dataset brut
    ↓
Préparation Python
    ↓
Dockerisation
    ↓
Stockage HDFS
    ↓
Traitement Spark / PySpark
    ↓
Insertion PostgreSQL
    ↓
Visualisation Python / démo plateforme
```

### Architecture résumée

```text
AmesHousing.tsv
   ↓
Python (préparation)
   ↓
ames_housing_prepared.csv
   ↓
HDFS
   ↓
Spark / MLlib
   ↓
PostgreSQL
   ↓
Graphes analytiques / démo plateforme / 
```

---

## 7. Phases du projet

## Phase 1 — Préparation des données

Un premier pipeline Python a été mis en place pour :

- charger les données brutes,
- nettoyer les colonnes texte,
- gérer les valeurs manquantes,
- supprimer les outliers documentés,
- créer des variables dérivées,
- encoder les variables catégorielles.

### Variables dérivées créées

- `HouseAge`
- `RemodAge`
- `TotalBath`
- `TotalPorchSF`
- `HasGarage`
- `HasFireplace`
- `HasPool`
- `TotalSF`

### Résultat

Production d’un dataset préparé :

```text
data/ames_housing_prepared.csv
```

Après préparation :

- **2925 lignes** conservées
- **environ 283 colonnes** après encodage
- **0 valeur manquante restante**

---

## Phase 2 — Dockerisation

Le projet a ensuite été structuré dans une logique conteneurisée afin de :

- fiabiliser l’environnement,
- rendre l’exécution reproductible,
- préparer une architecture plus réaliste.

Docker a été utilisé pour encapsuler les composants techniques, notamment PostgreSQL et les briques nécessaires au pipeline.

---

## Phase 3 — Stockage dans HDFS

Le dataset préparé a été stocké dans HDFS pour s’inscrire dans une logique Big Data cohérente.

Exemple d’emplacement utilisé dans le projet :

```text
hdfs://namenode:9000/data/ames/ames_housing_prepared.csv
```

Cette étape a permis de montrer :

- l’intégration d’un stockage distribué,
- la continuité entre préparation locale et traitement distribué,
- l’évolution du pipeline vers Spark.

---

## Phase 4 — Traitement Spark / PySpark

Une version distribuée du pipeline a été mise en place avec Spark pour lire les données depuis HDFS, entraîner plusieurs modèles et produire les résultats d’évaluation.

### Modèles considérés dans l’étape Spark

- **Linear Regression**
- **Random Forest Regressor**
- **Gradient Boosting Regressor**

### Objectifs de cette phase

- lire les données depuis HDFS,
- entraîner les modèles avec Spark,
- calculer des métriques de performance,
- préparer les prédictions,
- insérer directement les résultats dans PostgreSQL via JDBC.

Cette phase matérialise la dimension Big Data du projet dans une forme démonstrative mais cohérente.

---

## Phase 5 — Stockage dans PostgreSQL

Une base PostgreSQL a été conçue pour centraliser les données métier, les exécutions de modèles et les prédictions.

### Tables utilisées

- `houses_core`
- `houses_location`
- `houses_structure`
- `houses_sale`
- `model_runs`
- `predictions`

### Rôle de la base

- structurer les données des maisons,
- stocker les résultats des modèles,
- centraliser les prédictions,
- permettre des requêtes analytiques,
- alimenter la couche de visualisation.

### Logique relationnelle

- les tables `houses_*` représentent la maison sous plusieurs dimensions,
- `model_runs` stocke les exécutions et les métriques des modèles,
- `predictions` stocke les prédictions et les erreurs associées.

---

## Phase 6 — Visualisation et restitution

La restitution a été pensée comme une vraie couche analytique, avec deux dimensions :

### 1. Visualisation analytique automatique en Python
Un script dédié lit directement les données depuis PostgreSQL et génère automatiquement les graphiques.

### 2. Démo de plateforme / maquette UI
Une démo de plateforme a été réalisée pour matérialiser le projet sous une forme plus produit / SaaS, afin de montrer la vision finale au-delà du pipeline technique.

### 3. BI / tableau de bord
Power BI a été envisagé comme couche de restitution décisionnelle, avec une logique de dashboard par axes analytiques.

---

## 8. Scripts principaux du projet

### `src/prepare_ames_housing.py`
Préparation, nettoyage, enrichissement et encodage des données.

### `src/train_baseline_model.py`
Entraînement du modèle baseline `LinearRegression` avec validation croisée.

### `src/train_random_forest_optimized.py`
Benchmark avancé avec `RandomForestRegressor` optimisé.

### `train_house_price_model.py`
Pipeline Spark / PostgreSQL pour :

- lire depuis HDFS,
- entraîner plusieurs modèles Spark,
- calculer les métriques,
- insérer `model_runs` et `predictions` dans PostgreSQL.

### `visualization_postgres.py`
Script de visualisation lisant directement PostgreSQL et générant automatiquement des graphiques dans un dossier `output/`.

---

## 9. Résultats de modélisation obtenus

## 9.1. Résultats du modèle baseline `LinearRegression`

Les performances observées sont d’environ :

- **RMSE ≈ 22177**
- **MAE ≈ 15037**
- **R² ≈ 0.919**

Ces résultats montrent qu’un pipeline propre et bien structuré permet déjà d’obtenir une base très crédible.

---

## 9.2. Résultats du modèle `RandomForestOptimized`

Les performances observées sont d’environ :

- **RMSE ≈ 22809**
- **MAE ≈ 14826**
- **R² ≈ 0.915**

Le modèle est sérieux et constitue un bon benchmark, mais il ne dépasse pas globalement la régression linéaire dans ce pipeline.

---

## 9.3. Choix du modèle final

Le modèle principal retenu est :

```text
LinearRegression
```

### Justification

- meilleur RMSE,
- meilleur R²,
- simplicité,
- interprétabilité,
- cohérence avec un mini-projet académique.

Le `RandomForestOptimized` est conservé comme **benchmark méthodologique**.

---

## 10. Structure des sorties générées

## Données et prédictions

- `data/ames_housing_prepared.csv`
- `outputs/ames_predictions_cv_full.csv`
- `outputs/ames_predictions_sample.csv`
- `outputs/ames_predictions_rf_optimized_cv_full.csv`
- `outputs/ames_predictions_rf_optimized_sample.csv`
- `outputs/model_comparison_metrics.csv`

## Visualisations PostgreSQL

Dans :

```text
visualization_postgres/output/
```

on retrouve :

- les graphiques du marché,
- les graphes explicatifs,
- les comparaisons de modèles,
- les analyses d’erreurs,
- les fichiers analytiques auxiliaires.

Exemples :

- `houses_master_enriched.csv`
- `predictions_enriched.csv`
- `model_runs_snapshot.csv`
- `kpi_summary.txt`
- `top_20_errors.csv`
- `top_15_underestimated.csv`
- `top_15_overestimated.csv`

---

## 11. Axes d’analyse produits par la plateforme

La plateforme analytique est structurée autour de **quatre grands axes**.

## Axe 1 — Analyse du marché immobilier

Objectif :

- comprendre la structure du marché avant modélisation.

Visualisations typiques :

- distribution des prix,
- prix moyen / médian,
- prix par quartier,
- surface vs prix,
- qualité vs prix,
- zoning vs prix,
- année de construction vs prix.

---

## Axe 2 — Facteurs influençant le prix

Objectif :

- expliquer la variation des prix.

Visualisations typiques :

- `TotalSF` vs prix,
- `HouseAge` vs prix,
- `TotalBath` vs prix,
- effet du garage,
- effet de la cheminée,
- effet de la piscine,
- heatmap de corrélation,
- boxplots par niveau de qualité.

---

## Axe 3 — Comparaison des modèles ML

Objectif :

- comparer la qualité des modèles de prédiction.

Visualisations typiques :

- RMSE par modèle,
- MAE par modèle,
- R² par modèle,
- synthèse du meilleur modèle.

---

## Axe 4 — Analyse des prédictions et des erreurs

Objectif :

- comprendre dans quels cas le modèle fonctionne bien ou se trompe.

Visualisations typiques :

- réel vs prédit,
- distribution des erreurs absolues,
- top erreurs,
- erreurs par quartier,
- erreurs selon la gamme de prix,
- résidus vs prix réel,
- maisons sous-estimées / surestimées.

---

## 12. Démo plateforme

En plus du pipeline analytique, une **démo de plateforme** a été pensée pour représenter le projet comme un produit.

Cette démonstration sert à montrer que le travail ne se limite pas à :

- des scripts,
- une base,
- quelques courbes,

mais s’inscrit dans une logique de **plateforme data immobilière**, avec :

- navigation analytique,
- tableaux de bord,
- couches de restitution,
- vision produit.

Cette composante renforce fortement la qualité de la soutenance.

---

## 13. Structure de la base PostgreSQL

Le projet ne stocke pas simplement un grand tableau opaque.  
Il adopte une logique plus structurée.

### Tables métier

- `houses_core`
- `houses_location`
- `houses_structure`
- `houses_sale`

### Tables analytiques / ML

- `model_runs`
- `predictions`

### Intérêt

Cette structure permet de séparer :

- les attributs descriptifs,
- les dimensions de localisation,
- les caractéristiques structurelles,
- les informations de vente,
- les résultats des modèles,
- la traçabilité des prédictions.

---

## 14. Lecture du projet comme plateforme complète

Le projet peut être présenté comme un mini-système analytique composé de :

### Couche 1 — Données
Dataset brut + données préparées

### Couche 2 — Traitement
Python + Spark / PySpark

### Couche 3 — Stockage
PostgreSQL via Docker

### Couche 4 — Analyse
Visualisation Python + BI

### Couche 5 — Restitution
Démo plateforme / maquette UI / soutenance

---

## 15. Structure recommandée du dépôt

```text
project/
├─ README.md
├─ data/
│  ├─ AmesHousing.tsv
│  └─ ames_housing_prepared.csv
├─ outputs/
│  ├─ ames_predictions_cv_full.csv
│  ├─ ames_predictions_sample.csv
│  ├─ ames_predictions_rf_optimized_cv_full.csv
│  ├─ ames_predictions_rf_optimized_sample.csv
│  └─ model_comparison_metrics.csv
├─ src/
│  ├─ prepare_ames_housing.py
│  ├─ train_baseline_model.py
│  └─ train_random_forest_optimized.py
├─ sql/
│  ├─ create_tables.sql
│  └─ import_data.sql
├─ phase4_spark/
├─ phase5_postgresql/
├─ visualization_postgres/
│  ├─ visualization_postgres.py
│  └─ output/
├─ dashboards/
├─ docs/
└─ requirements.txt
```

---

## 16. Comment exécuter le projet

## 1. Lancer PostgreSQL Docker

```bash
docker compose up -d
```

dans le dossier PostgreSQL concerné.

## 2. Vérifier les conteneurs

```bash
docker ps
```

## 3. Exécuter les scripts Python de préparation / ML
Exemples :

```bash
python src/prepare_ames_housing.py
python src/train_baseline_model.py
```

## 4. Exécuter le pipeline Spark
Depuis l’environnement Spark préparé.

## 5. Générer les visualisations
Dans `visualization_postgres/` :

```bash
python visualization_postgres.py
```

Les résultats seront enregistrés automatiquement dans :

```text
output/
```

---

## 17. Limites du projet

Le projet reste volontairement académique :

- dataset de taille modérée,
- architecture distribuée partielle,
- pas de temps réel,
- focus sur la cohérence du pipeline plutôt que sur la scalabilité industrielle.

Cependant, cette limite est assumée.  
L’objectif est de proposer une **plateforme crédible, démontrable et bien structurée**.

---

## 18. Perspectives d’amélioration

Extensions possibles :

- intégration complète Power BI sur PostgreSQL,
- enrichissement de la couche UI / UX,
- ajout d’un reporting HTML automatisé,
- historisation plus poussée des modèles,
- ajout d’un troisième niveau de comparaison ML,
- extension vers une API ou une interface web.

---

## 19. Conclusion

Ce projet ne doit pas être présenté comme un simple exercice de régression, mais comme une **plateforme analytique immobilière complète**, construite autour d’un pipeline cohérent :

- préparation des données,
- stockage,
- traitement distribué,
- modélisation,
- centralisation en base,
- visualisation,
- démo produit.

Les éléments les plus importants à retenir sont :

- le dataset Ames Housing a été nettoyé, enrichi et structuré,
- PostgreSQL a été intégré dans une logique Docker,
- Spark a été utilisé pour la lecture HDFS, l’entraînement et l’insertion des résultats,
- `LinearRegression` a été retenu comme modèle principal,
- une couche de visualisation Python a été mise en place,
- une démo de plateforme a été réalisée pour matérialiser la vision du projet.

En conclusion, le projet constitue une **plateforme d’analyse et de prédiction des prix des maisons**, techniquement cohérente, pédagogiquement défendable et visuellement démontrable en soutenance.
