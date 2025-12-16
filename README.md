# Race Engineer Assistant

**Ingénieur de course virtuel pour Assetto Corsa**

Application desktop Python pour générer automatiquement des setups de voiture optimisés pour le touge (routes de montagne) dans Assetto Corsa.

## Fonctionnalités

### 🎯 Génération automatique de setups
- Génère des setups complets basés sur votre style de conduite
- 4 comportements prédéfinis : Safe, Balanced, Attack, Drift
- Écriture directe dans le dossier setups d'Assetto Corsa

### 🧠 IA basée sur règles
- Moteur de règles pour ajuster les réglages
- Scoring et pondération des paramètres
- Recommandations intelligentes

### 👤 Profil pilote personnalisable
- 5 sliders de préférences :
  - Stabilité ↔ Rotation
  - Grip ↔ Glisse
  - Sécurité ↔ Agressivité
  - Drift ↔ Grip
  - Confort ↔ Performance

### 🔧 Paramètres de setup
- Suspensions (ressorts, amortisseurs, hauteur)
- Différentiel (power, coast, preload)
- Géométrie (carrossage, pincement)
- Freinage (répartition)
- Barres anti-roulis
- Pression des pneus

## Installation

### Prérequis
- Python 3.11 ou supérieur
- Assetto Corsa installé
- Windows 10/11

### Installation des dépendances

```bash
cd race_engineer_assistant
pip install -r requirements.txt
```

### Lancement

```bash
python main.py
```

## Structure du projet

```
race_engineer_assistant/
├── main.py                 # Point d'entrée
├── ui/                     # Interface utilisateur PySide6
│   ├── main_window.py
│   ├── car_track_selector.py
│   ├── behavior_selector.py
│   └── sliders_panel.py
├── core/                   # Logique métier
│   ├── setup_engine.py     # Génération de setups
│   ├── behavior_engine.py  # Comportements prédéfinis
│   ├── rules_engine.py     # Moteur de règles IA
│   └── scoring_engine.py   # Scoring des setups
├── ai/                     # Intelligence artificielle
│   ├── decision_engine.py  # Décisions et recommandations
│   └── feedback_engine.py  # Apprentissage par feedback
├── assetto/                # Intégration Assetto Corsa
│   ├── ac_detector.py      # Détection installation
│   ├── setup_writer.py     # Écriture fichiers .ini
│   └── ac_connector.py     # Interface haut niveau
├── data/                   # Persistance
│   ├── database.db         # Base SQLite
│   ├── setup_repository.py # Repository pattern
│   └── setup_scraper_stub.py
├── models/                 # Modèles de données
│   ├── car.py
│   ├── track.py
│   ├── setup.py
│   └── driver_profile.py
└── config/
    └── settings.json       # Configuration
```

## Utilisation

1. **Lancez l'application** - Elle détecte automatiquement Assetto Corsa
2. **Sélectionnez une voiture** - Filtrez par RWD si souhaité
3. **Sélectionnez une piste** - Filtrez par type Touge
4. **Choisissez un comportement** - Safe, Balanced, Attack ou Drift
5. **Ajustez vos préférences** - Utilisez les sliders
6. **Générez le setup** - Cliquez sur "Générer et Appliquer"

Le setup sera automatiquement sauvegardé dans :
```
Documents/Assetto Corsa/setups/<voiture>/<piste>/
```

## Comportements

| Comportement | Description |
|--------------|-------------|
| **Safe Touge** | Stabilité maximale, setup prévisible et tolérant |
| **Balanced Touge** | Équilibre entre grip, rotation et stabilité |
| **Attack Touge** | Setup agressif pour performance maximale |
| **Drift Touge** | Optimisé pour le drift et les glisses contrôlées |

## Règles IA

L'IA utilise un système de règles pour ajuster les paramètres :

- **Stabilité > 70%** → Suspensions plus souples, différentiel progressif
- **Rotation > 60%** → Barre anti-roulis avant plus rigide
- **Grip > 70%** → Plus de carrossage négatif
- **Drift > 50%** → Différentiel plus agressif
- **Débutant** → Réglages plus tolérants

## Limitations

- ✅ Lecture des dossiers Assetto Corsa
- ✅ Écriture des fichiers setup.ini
- ❌ Pas d'injection mémoire
- ❌ Pas de modification du jeu en runtime
- ❌ Pas de deep learning (règles + scoring uniquement)

## Extensibilité future

Le projet est conçu pour permettre :
- Intégration télémétrie (SharedMemory AC)
- Apprentissage par feedback utilisateur
- Import de setups communautaires
- Analyse de données de conduite

## Licence

Projet personnel - Usage non commercial

## Auteur

Race Engineer Assistant - Touge Engineering
