# 🏎️ RACE ENGINEER ASSISTANT - DOCUMENTATION TECHNIQUE COMPLÈTE

**Version:** 1.0 (26 décembre 2025)  
**Auteur:** XENONRAy14  
**Objectif:** Génération automatique de setups Assetto Corsa adaptés au type de voiture et au style de conduite

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble du système](#vue-densemble-du-système)
2. [Architecture de l'application](#architecture-de-lapplication)
3. [Flux de détection automatique](#flux-de-détection-automatique)
4. [Système de classification des voitures](#système-de-classification-des-voitures)
5. [Génération de setups](#génération-de-setups)
6. [Valeurs de base par type de voiture](#valeurs-de-base-par-type-de-voiture)
7. [Behaviors (Styles de conduite)](#behaviors-styles-de-conduite)
8. [Profile Tuning (Ajustements utilisateur)](#profile-tuning-ajustements-utilisateur)
9. [Exemples concrets](#exemples-concrets)
10. [Points d'amélioration potentiels](#points-damélioration-potentiels)

---

## 1. VUE D'ENSEMBLE DU SYSTÈME

### Concept principal
L'application génère automatiquement des setups de voiture pour Assetto Corsa en combinant :
- **Détection automatique** de la voiture et du circuit en cours
- **Classification intelligente** du type de voiture (Race/Street/Drift)
- **Valeurs de base adaptées** au type de voiture
- **Behaviors prédéfinis** (Safe/Balanced/Attack/Drift)
- **Ajustements utilisateur** via sliders (rotation, aggression, drift, etc.)

### Workflow utilisateur
```
1. Lancer Assetto Corsa
2. Sélectionner voiture + circuit
3. L'app détecte automatiquement → Affiche dans l'interface
4. Utilisateur choisit un behavior (ex: "Attack Touge")
5. Utilisateur ajuste les sliders selon ses préférences
6. Clic "Generate Setup" → Setup créé et exporté
7. Charger le setup dans AC → Conduire
```

---

## 2. ARCHITECTURE DE L'APPLICATION

### Modules principaux

```
race_engineer_assistant/
├── core/
│   ├── setup_engine.py        # Moteur de génération de setups
│   ├── behavior_engine.py     # Définition des behaviors
│   ├── ac_monitor.py          # Détection AC via shared memory
│   └── rules_engine.py        # Règles de validation
├── ui/
│   ├── main_window.py         # Interface principale
│   ├── car_track_selector.py # Sélection voiture/circuit
│   └── setup_editor.py        # Éditeur de setup
├── models/
│   ├── car.py                 # Modèle de données voiture
│   ├── track.py               # Modèle de données circuit
│   └── setup.py               # Modèle de données setup
└── data/
    ├── cars.json              # Base de données voitures
    └── tracks.json            # Base de données circuits
```

### Technologies utilisées
- **Python 3.14**
- **PySide6** (Qt) pour l'interface
- **mmap** pour lire la shared memory d'AC
- **configparser** pour lire/écrire les fichiers .ini de setups

---

## 3. FLUX DE DÉTECTION AUTOMATIQUE

### Étape 1: Lecture de la Shared Memory AC
```python
# ac_monitor.py
class ACMonitor:
    def read_shared_memory(self):
        # Lit la mémoire partagée d'AC (struct C)
        # Extrait: car_name, track_name, track_config
        return {
            'car': 'ks_porsche_911_gt3_r_2016',
            'track': 'ks_brands_hatch',
            'config': 'gp'
        }
```

**Fréquence:** Toutes les 500ms  
**Données extraites:**
- Nom de la voiture (car_id)
- Nom du circuit (track_id)
- Configuration du circuit (config)
- Vitesse, RPM, position (pour détection en piste)

### Étape 2: Recherche dans la base de données
```python
# main_window.py - _auto_select_car_track()
def _auto_select_car_track(self, car_name, track_name, track_config):
    # 1. Cherche la voiture dans cars.json
    car = self.car_manager.find_car_by_id(car_name)
    
    # 2. Cherche le circuit dans tracks.json
    track = self.track_manager.find_track(track_name, track_config)
    
    # 3. Met à jour l'interface
    self.car_track_selector.select_car_by_id(car.car_id)
    self.car_track_selector.select_track_by_id(track.track_id, track.config)
```

### Étape 3: Synchronisation UI
```python
# car_track_selector.py
def select_car_by_id(self, car_id):
    # Trouve l'index dans le QComboBox
    for i in range(self.car_combo.count()):
        car = self.car_combo.itemData(i)
        if car and car.car_id == car_id:
            self.car_combo.setCurrentIndex(i)
            self._on_car_changed(i)  # Force signal
            break
```

---

## 4. SYSTÈME DE CLASSIFICATION DES VOITURES

### Fonction de détection: `_detect_car_type()`

```python
def _detect_car_type(self, car: Car) -> str:
    """
    Détecte le type de voiture pour sélectionner les bonnes valeurs de base.
    Returns: "race", "drift", or "street"
    """
    
    # 1. DRIFT CARS (priorité haute)
    if car.is_drift_car():  # Flag dans cars.json
        return "drift"
    
    if "drift" in car.car_id.lower() or "drift" in car.name.lower():
        return "drift"
    
    # 2. RACE CARS
    # Check car_class
    car_class = car.car_class.lower()
    if car_class in ["gt3", "gt2", "gt4", "gte", "lmp", "lmp1", "lmp2", "dtm", "formula"]:
        return "race"
    
    # Check car_id patterns
    if any(pattern in car.car_id.lower() for pattern in ["_gt3", "_gt2", "_lmp", "_f1"]):
        return "race"
    
    # Check power-to-weight ratio
    if car.power_hp and car.weight_kg:
        power_to_weight = car.power_hp / car.weight_kg
        if power_to_weight > 0.4:  # >400hp/ton = race car
            return "race"
    
    # 3. DEFAULT: STREET
    return "street"
```

### Exemples de classification

| Voiture | Type détecté | Raison |
|---------|--------------|--------|
| Porsche 911 GT3 R | **race** | car_class = "gt3" |
| BMW M3 E30 Drift | **drift** | "drift" in car_id |
| Nissan Skyline R34 | **street** | Pas de pattern race/drift |
| McLaren 720S | **street** | Voiture de rue sportive |
| Ferrari 488 GTE | **race** | car_class = "gte" |
| Toyota AE86 (Touge) | **street** | Voiture de montagne |

---

## 5. GÉNÉRATION DE SETUPS

### Pipeline complet

```
1. _create_base_setup()
   ↓ Sélectionne GT3_BASE / STREET_BASE / DRIFT_BASE
   
2. _apply_behavior_modifiers()
   ↓ Applique Safe/Balanced/Attack/Drift behavior
   
3. _apply_profile_tuning()
   ↓ Applique les sliders utilisateur (rotation, aggression, etc.)
   
4. _apply_track_adjustments()
   ↓ Ajuste selon le circuit (aero pour circuits rapides, etc.)
   
5. _clamp_values()
   ↓ Limite les valeurs aux ranges AC valides
   
6. Export vers .ini
   ↓ Sauvegarde dans Documents/Assetto Corsa/setups/
```

### Méthode 1: `_create_base_setup()`

```python
def _create_base_setup(self, car, track, name, behavior_id) -> Setup:
    # Détecte le type
    car_type = self._detect_car_type(car)
    
    # Sélectionne les valeurs de base appropriées
    if car_type == "race":
        # Essaie de charger le setup par défaut d'AC
        ac_setup = self._load_ac_default_setup(car)
        if ac_setup:
            return ac_setup  # Utilise le setup AC officiel
        else:
            base_values = self.GT3_BASE_VALUES  # Fallback
    
    elif car_type == "drift":
        base_values = self.DRIFT_BASE_VALUES
    
    else:  # street
        base_values = self.STREET_BASE_VALUES
    
    # Initialise le setup avec ces valeurs
    setup = Setup(name=name, car_id=car.car_id, track_id=track.full_id)
    for section, values in base_values.items():
        setup.sections[section] = SetupSection(section, values.copy())
    
    return setup
```

### Méthode 2: `_apply_behavior_modifiers()`

```python
def _apply_behavior_modifiers(self, setup, behavior) -> Setup:
    # Récupère les modifiers du behavior (-1.0 à +1.0)
    modifiers = {
        'suspension_stiffness': behavior.suspension_stiffness,  # ex: 0.7 pour Attack
        'diff_power': behavior.diff_power,                      # ex: 0.7 pour Attack
        'camber_front': behavior.camber_front,                  # ex: 0.7 pour Attack
        # ... etc
    }
    
    # Détecte si setup click-based (race) ou absolute (street)
    is_click_based = self._is_click_based_setup(setup)
    
    # Applique les modifiers
    if is_click_based:
        # Race cars: ajuste par clicks
        spring_clicks = int(modifiers['suspension_stiffness'] * 5)  # ±5 clicks max
        for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", ...]:
            current = setup.get_value("SUSPENSION", key, 10)
            setup.set_value("SUSPENSION", key, current + spring_clicks)
    
    else:
        # Street cars: ajuste par pourcentage
        spring_mult = 1.0 + modifiers['suspension_stiffness'] * 0.4  # ±40%
        for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", ...]:
            current = setup.get_value("SUSPENSION", key, 70000)
            setup.set_value("SUSPENSION", key, int(current * spring_mult))
    
    # Differential (toujours en %)
    diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
    diff_adj = modifiers['diff_power'] * 30  # ±30%
    setup.set_value("DIFFERENTIAL", "POWER", diff_power + diff_adj)
    
    # Camber (toujours en degrés)
    camber_mult = 1.0 + modifiers['camber_front'] * 0.5  # ±50%
    for key in ["CAMBER_LF", "CAMBER_RF"]:
        current = setup.get_value("ALIGNMENT", key, -3.0)
        setup.set_value("ALIGNMENT", key, current * camber_mult)
    
    return setup
```

### Méthode 3: `_apply_profile_tuning()`

```python
def _apply_profile_tuning(self, setup, profile) -> Setup:
    factors = profile.get_all_factors()  # Dict de 0.0 à 1.0
    
    # ROTATION slider (0 = stable, 1 = rotationnel)
    rotation = factors["rotation"]
    if rotation > 0.5:
        # Plus de rotation = toe-out arrière
        rear_toe_adj = (rotation - 0.5) * 0.8  # Max +0.4°
        for key in ["TOE_LR", "TOE_RR"]:
            current = setup.get_value("ALIGNMENT", key, 0.1)
            setup.set_value("ALIGNMENT", key, current + rear_toe_adj)
        
        # ARB arrière plus souple
        rear_arb = setup.get_value("ARB", "REAR", 4)
        setup.set_value("ARB", "REAR", rear_arb * (1.0 - (rotation - 0.5) * 0.6))
    
    # AGGRESSION slider (0 = safe, 1 = agressif)
    aggression = factors["aggression"]
    if aggression > 0.5:
        # Suspension plus raide
        stiffness_mult = 1.0 + (aggression - 0.5) * 0.6  # Max +30%
        for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", ...]:
            current = setup.get_value("SUSPENSION", key, 70000)
            setup.set_value("SUSPENSION", key, int(current * stiffness_mult))
        
        # Diff plus lockant
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
        setup.set_value("DIFFERENTIAL", "POWER", diff_power * (1.0 + (aggression - 0.5) * 0.8))
    
    # DRIFT slider (0 = grip, 1 = drift)
    drift = factors["drift"]
    if drift > 0.3:
        # Diff très lockant
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
        setup.set_value("DIFFERENTIAL", "POWER", min(100, diff_power + drift * 60))
        
        # Brake bias vers l'arrière
        brake_bias = setup.get_value("BRAKES", "FRONT_BIAS", 60)
        setup.set_value("BRAKES", "FRONT_BIAS", brake_bias - drift * 15)
    
    return setup
```

---

## 6. VALEURS DE BASE PAR TYPE DE VOITURE

### GT3_BASE_VALUES (Race Cars)

**Philosophie:** Setup agressif, click-based, optimisé pour la performance pure

```python
GT3_BASE_VALUES = {
    "TYRES": {
        "PRESSURE_LF": 27.5,      # PSI - Pression optimale GT3
        "PRESSURE_RF": 27.5,
        "PRESSURE_LR": 27.0,      # Légèrement moins à l'arrière
        "PRESSURE_RR": 27.0,
    },
    "ALIGNMENT": {
        "CAMBER_LF": -4.0,        # Camber agressif pour grip en virage
        "CAMBER_RF": -4.0,
        "CAMBER_LR": -3.0,
        "CAMBER_RR": -3.0,
        "TOE_LF": -0.05,          # Léger toe-out avant pour turn-in
        "TOE_RF": -0.05,
        "TOE_LR": 0.15,           # Toe-in arrière pour stabilité
        "TOE_RR": 0.15,
    },
    "DIFFERENTIAL": {
        "POWER": 65.0,            # Assez lockant pour traction
        "COAST": 50.0,            # Lockant en décélération
        "PRELOAD": 30.0,
    },
    "SUSPENSION": {
        "SPRING_RATE_LF": 10,     # CLICKS (pas N/m)
        "SPRING_RATE_RF": 10,
        "SPRING_RATE_LR": 9,
        "SPRING_RATE_RR": 9,
        "RIDE_HEIGHT_LF": 50,     # mm - Bas pour aero
        "RIDE_HEIGHT_RF": 50,
        "RIDE_HEIGHT_LR": 55,
        "RIDE_HEIGHT_RR": 55,
    },
    "ARB": {
        "FRONT": 6,               # Raide pour réactivité
        "REAR": 5,
    },
    "BRAKES": {
        "BIAS": 62.0,             # Bias avant pour GT3
        "FRONT_BIAS": 62.0,
    },
    "AERO": {
        "WING_FRONT": 2,          # Aero équilibrée
        "WING_REAR": 3,
    },
}
```

**Utilisé pour:**
- GT3, GT2, GT4, GTE
- LMP1, LMP2, LMP3
- DTM, TCR
- Formula cars
- Voitures >400hp/ton

---

### STREET_BASE_VALUES (Street/Touge Cars)

**Philosophie:** Setup équilibré, valeurs absolues, confort + performance

```python
STREET_BASE_VALUES = {
    "TYRES": {
        "PRESSURE_LF": 32.0,      # PSI - Pression route normale
        "PRESSURE_RF": 32.0,
        "PRESSURE_LR": 30.0,      # Moins à l'arrière pour grip
        "PRESSURE_RR": 30.0,
    },
    "ALIGNMENT": {
        "CAMBER_LF": -2.5,        # Camber modéré
        "CAMBER_RF": -2.5,
        "CAMBER_LR": -2.0,
        "CAMBER_RR": -2.0,
        "TOE_LF": 0.05,           # Léger toe-in pour stabilité
        "TOE_RF": 0.05,
        "TOE_LR": 0.15,
        "TOE_RR": 0.15,
    },
    "DIFFERENTIAL": {
        "POWER": 40.0,            # Peu lockant pour confort
        "COAST": 30.0,
        "PRELOAD": 20.0,
    },
    "SUSPENSION": {
        "SPRING_RATE_LF": 75000,  # N/m (valeurs absolues)
        "SPRING_RATE_RF": 75000,
        "SPRING_RATE_LR": 65000,  # Plus souple arrière
        "SPRING_RATE_RR": 65000,
        "RIDE_HEIGHT_LF": 100,    # mm - Plus haut pour routes
        "RIDE_HEIGHT_RF": 100,
        "RIDE_HEIGHT_LR": 105,
        "RIDE_HEIGHT_RR": 105,
    },
    "ARB": {
        "FRONT": 5,               # Équilibré
        "REAR": 4,
    },
    "BRAKES": {
        "BIAS": 58.0,             # Bias neutre
        "FRONT_BIAS": 58.0,
    },
}
```

**Utilisé pour:**
- Voitures de rue (M3, Skyline, Supra, etc.)
- Voitures Touge (AE86, S2000, etc.)
- Sportives routières (911 Carrera, Cayman, etc.)
- Par défaut si type inconnu

---

### DRIFT_BASE_VALUES (Drift Cars)

**Philosophie:** Setup pour glisse contrôlée, diff lockant, instabilité arrière

```python
DRIFT_BASE_VALUES = {
    "TYRES": {
        "PRESSURE_LF": 32.0,      # PSI - Normale avant
        "PRESSURE_RF": 32.0,
        "PRESSURE_LR": 35.0,      # HAUTE arrière pour glisse
        "PRESSURE_RR": 35.0,
    },
    "ALIGNMENT": {
        "CAMBER_LF": -3.5,        # Camber avant pour grip
        "CAMBER_RF": -3.5,
        "CAMBER_LR": -1.0,        # PEU de camber arrière (glisse)
        "CAMBER_RR": -1.0,
        "TOE_LF": -0.05,          # Léger toe-out avant
        "TOE_RF": -0.05,
        "TOE_LR": -0.15,          # TOE-OUT arrière (instabilité)
        "TOE_RR": -0.15,
    },
    "DIFFERENTIAL": {
        "POWER": 85.0,            # TRÈS lockant pour drift
        "COAST": 65.0,            # Lockant aussi en coast
        "PRELOAD": 50.0,          # Preload élevé
    },
    "SUSPENSION": {
        "SPRING_RATE_LF": 85000,  # N/m - Raide avant
        "SPRING_RATE_RF": 85000,
        "SPRING_RATE_LR": 70000,  # SOUPLE arrière (glisse)
        "SPRING_RATE_RR": 70000,
        "RIDE_HEIGHT_LF": 110,    # mm - Assez haut
        "RIDE_HEIGHT_RF": 110,
        "RIDE_HEIGHT_LR": 120,    # Plus haut arrière
        "RIDE_HEIGHT_RR": 120,
    },
    "ARB": {
        "FRONT": 7,               # TRÈS raide avant
        "REAR": 3,                # TRÈS souple arrière
    },
    "BRAKES": {
        "BIAS": 54.0,             # Bias arrière pour initiation
        "FRONT_BIAS": 54.0,
    },
    "ELECTRONICS": {
        "TC": 0,                  # PAS de TC
        "ABS": 0,                 # PAS d'ABS
    },
}
```

**Utilisé pour:**
- Voitures avec flag `is_drift_car: true`
- Voitures avec "drift" dans le nom/ID
- Pack drift spécifiques

---

## 7. BEHAVIORS (STYLES DE CONDUITE)

### 4 Behaviors prédéfinis

Chaque behavior a des **modifiers** de -1.0 à +1.0 qui s'appliquent sur les valeurs de base.

---

#### **SAFE TOUGE** - Stabilité maximale

**Objectif:** Setup très stable, prévisible, idéal pour apprendre ou conduire relax

```python
Behavior(
    suspension_stiffness = -0.6,   # Suspension TRÈS souple
    diff_power = -0.7,             # Diff PEU lockant
    camber_front = -0.4,           # Camber modéré
    toe_rear = 0.4,                # Toe-in arrière prononcé (stabilité)
    arb_front = -0.5,              # ARB souples
    ride_height = 0.3,             # Plus haut (confort)
    tyre_pressure = -0.3,          # Pression basse (grip)
)
```

**Effet sur GT3 (base: -4.0° camber, 65% diff):**
- Camber: -4.0° → **-3.2°** (moins agressif)
- Diff power: 65% → **45%** (moins lockant)
- Toe arrière: 0.15° → **0.55°** (très stable)

**Effet sur Street (base: -2.5° camber, 40% diff):**
- Camber: -2.5° → **-2.0°**
- Diff power: 40% → **28%**
- Toe arrière: 0.15° → **0.55°**

---

#### **BALANCED TOUGE** - Équilibré

**Objectif:** Setup neutre, bon compromis

```python
Behavior(
    suspension_stiffness = 0.0,    # Neutre
    diff_power = 0.0,              # Neutre
    camber_front = 0.0,            # Neutre
    toe_rear = 0.1,                # Légèrement stable
    # ... tous à 0 ou proche
)
```

**Effet:** Garde les valeurs de base presque intactes, juste quelques ajustements mineurs.

---

#### **ATTACK TOUGE** - Performance maximale

**Objectif:** Setup agressif, grip maximal, turn-in rapide

```python
Behavior(
    suspension_stiffness = 0.7,    # Suspension TRÈS raide
    diff_power = 0.7,              # Diff TRÈS lockant
    camber_front = 0.7,            # Camber TRÈS agressif
    toe_front = -0.3,              # Toe-out avant (turn-in)
    arb_front = 0.6,               # ARB raides
    ride_height = -0.5,            # Très bas (aero)
    tyre_pressure = 0.3,           # Pression haute (réactivité)
)
```

**Effet sur GT3 (base: -4.0° camber, 65% diff):**
- Camber: -4.0° → **-5.4°** (très agressif)
- Diff power: 65% → **86%** (très lockant)
- Toe avant: -0.05° → **-0.35°** (turn-in rapide)
- Ride height: 50mm → **40mm** (très bas)

**Effet sur Street (base: -2.5° camber, 40% diff):**
- Camber: -2.5° → **-3.25°**
- Diff power: 40% → **61%**
- Springs: 75000 → **95000 N/m** (+27%)

---

#### **DRIFT TOUGE** - Glisse contrôlée

**Objectif:** Setup pour drifter facilement

```python
Behavior(
    suspension_stiffness = 0.3,    # Assez raide (réactivité)
    diff_power = 1.0,              # MAXIMUM lockant
    camber_rear = -0.6,            # MOINS de camber arrière (glisse)
    toe_rear = -0.3,               # Toe-out arrière (instabilité)
    arb_front = 0.7,               # ARB avant TRÈS raide
    arb_rear = -0.5,               # ARB arrière TRÈS souple
    brake_bias = -0.5,             # Bias arrière (initiation)
    tyre_pressure = 0.5,           # Pression haute arrière
)
```

**Effet sur Street (base: -2.5° camber, 40% diff):**
- Camber arrière: -2.0° → **-1.4°** (moins de grip)
- Diff power: 40% → **70%** (lockant)
- Toe arrière: 0.15° → **-0.15°** (toe-out = instable)
- Brake bias: 58% → **53%** (plus arrière)

**Effet sur Drift Base (base: -1.0° camber, 85% diff):**
- Camber arrière: -1.0° → **-0.7°** (encore moins)
- Diff power: 85% → **100%** (maximum)
- Toe arrière: -0.15° → **-0.45°** (très instable)

---

## 8. PROFILE TUNING (AJUSTEMENTS UTILISATEUR)

### Sliders disponibles (0.0 à 1.0)

L'utilisateur peut affiner le setup avec 6 sliders principaux :

---

#### **1. ROTATION** (0 = Stable, 1 = Rotationnel)

**Impact:**
- **Rotation > 0.5:**
  - Toe arrière: +0.4° max (rotation)
  - ARB arrière: -30% (plus souple)
  
- **Rotation < 0.5:**
  - ARB arrière: +20% (plus raide = stable)

**Exemple (Street base, Rotation = 100%):**
- Toe arrière: 0.15° → **0.55°** (rotation)
- ARB arrière: 4 → **2.8** (souple)

---

#### **2. AGGRESSION** (0 = Safe, 1 = Agressif)

**Impact:**
- **Aggression > 0.5:**
  - Springs: +30% max
  - Diff power: +40% max
  
- **Aggression < 0.5:**
  - Diff power: -20% max

**Exemple (Street base, Aggression = 100%):**
- Springs: 75000 → **97500 N/m** (+30%)
- Diff power: 40% → **56%** (+40%)

---

#### **3. DRIFT** (0 = Grip, 1 = Drift)

**Impact (si > 30%):**
- Diff power: +60 max
- Diff coast: +50 max
- Brake bias: -15% max (vers arrière)

**Exemple (Street base, Drift = 100%):**
- Diff power: 40% → **100%** (clamped)
- Diff coast: 30% → **80%**
- Brake bias: 58% → **43%** (arrière)

---

#### **4. SLIDE** (0 = Max Grip, 1 = Glisse)

**Impact:**
- **Slide > 0.5:**
  - Pression pneus: -2 PSI max
  - Camber: -30% (moins agressif)
  
- **Slide < 0.5:**
  - Camber avant: +15% (plus agressif)

**Exemple (Street base, Slide = 100%):**
- Pression: 32 → **30 PSI** (-2)
- Camber: -2.5° → **-1.75°** (-30%)

---

#### **5. PERFORMANCE** (0 = Confort, 1 = Performance)

**Impact:**
- **Performance > 0.5:**
  - Damping: +40% max
  - Ride height: -10mm max
  
- **Performance < 0.5:**
  - Damping: -10% (confort)

**Exemple (Street base, Performance = 100%):**
- Damping: 2800 → **3920** (+40%)
- Ride height: 100mm → **90mm** (-10mm)

---

#### **6. GRIP** (0 = Confort, 1 = Grip Max)

**Impact:**
- Camber avant: +15% max
- Pression pneus: optimale

**Exemple (Street base, Grip = 100%):**
- Camber avant: -2.5° → **-2.875°** (+15%)

---

### Combinaisons typiques

**Setup Touge Agressif:**
- Rotation: 70%
- Aggression: 80%
- Performance: 90%
- → Setup très réactif, turn-in rapide, raide

**Setup Drift:**
- Drift: 100%
- Slide: 80%
- Rotation: 60%
- → Diff lockant, toe-out, facile à glisser

**Setup Confort:**
- Tous les sliders: 50%
- → Setup neutre, prévisible

---

## 9. EXEMPLES CONCRETS

### Exemple 1: Porsche 911 GT3 R sur Brands Hatch GP

**Détection:**
```
Car detected: ks_porsche_911_gt3_r_2016
Track detected: ks_brands_hatch (gp)
Car type: RACE (car_class = "gt3")
```

**Setup généré (Behavior: Attack Touge, Aggression 80%):**

```ini
[TYRES]
PRESSURE_LF=28.1    # Base 27.5 + Attack +0.3 + Aggression +0.3
PRESSURE_RF=28.1
PRESSURE_LR=27.6
PRESSURE_RR=27.6

[ALIGNMENT]
CAMBER_LF=-5.4      # Base -4.0 + Attack +0.7 (×1.35) + Aggression +0.3
CAMBER_RF=-5.4
CAMBER_LR=-3.9
CAMBER_RR=-3.9
TOE_LF=-0.35        # Base -0.05 + Attack -0.3
TOE_RF=-0.35
TOE_LR=0.15
TOE_RR=0.15

[DIFFERENTIAL]
POWER=86            # Base 65 + Attack +21
COAST=58            # Base 50 + Attack +8
PRELOAD=38          # Base 30 + Attack +8

[SUSPENSION]
SPRING_RATE_LF=14   # Base 10 clicks + Attack +4 clicks
SPRING_RATE_RF=14
SPRING_RATE_LR=12
SPRING_RATE_RR=12
RIDE_HEIGHT_LF=40   # Base 50 + Attack -10mm
RIDE_HEIGHT_RF=40
RIDE_HEIGHT_LR=45
RIDE_HEIGHT_RR=45

[ARB]
FRONT=9             # Base 6 + Attack +3
REAR=6              # Base 5 + Attack +1

[BRAKES]
FRONT_BIAS=62       # Base 62 (neutre pour Attack)
```

**Résultat:** Setup très agressif, camber prononcé, diff lockant, bas, raide → Performance maximale

---

### Exemple 2: Nissan Skyline R34 sur Akina Downhill

**Détection:**
```
Car detected: nissan_skyline_r34
Track detected: akina_downhill
Car type: STREET (pas de pattern race/drift)
```

**Setup généré (Behavior: Balanced Touge, Rotation 70%):**

```ini
[TYRES]
PRESSURE_LF=32.0    # Base 32.0 (Balanced neutre)
PRESSURE_RF=32.0
PRESSURE_LR=30.0
PRESSURE_RR=30.0

[ALIGNMENT]
CAMBER_LF=-2.5      # Base -2.5 (Balanced neutre)
CAMBER_RF=-2.5
CAMBER_LR=-2.0
CAMBER_RR=-2.0
TOE_LF=0.05
TOE_RF=0.05
TOE_LR=0.31         # Base 0.15 + Rotation +0.16 (70% × 0.4 × 0.5)
TOE_RR=0.31

[DIFFERENTIAL]
POWER=40            # Base 40 (Balanced neutre)
COAST=30
PRELOAD=20

[SUSPENSION]
SPRING_RATE_LF=75000  # Base 75000 (Balanced neutre)
SPRING_RATE_RF=75000
SPRING_RATE_LR=65000
SPRING_RATE_RR=65000
RIDE_HEIGHT_LF=100
RIDE_HEIGHT_RF=100
RIDE_HEIGHT_LR=105
RIDE_HEIGHT_RR=105

[ARB]
FRONT=5             # Base 5 (Balanced neutre)
REAR=3.4            # Base 4 - Rotation -15% (70% × 0.6 × 0.5)

[BRAKES]
FRONT_BIAS=58       # Base 58 (neutre)
```

**Résultat:** Setup équilibré avec plus de rotation arrière pour Touge, confortable

---

### Exemple 3: BMW M3 E30 Drift sur Ebisu

**Détection:**
```
Car detected: bmw_m3_e30_drift
Track detected: ebisu_circuit
Car type: DRIFT ("drift" in car_id)
```

**Setup généré (Behavior: Drift Touge, Drift slider 100%):**

```ini
[TYRES]
PRESSURE_LF=32.0    # Base 32.0
PRESSURE_RF=32.0
PRESSURE_LR=37.5    # Base 35.0 + Drift behavior +2.5
PRESSURE_RR=37.5

[ALIGNMENT]
CAMBER_LF=-4.55     # Base -3.5 + Drift behavior +0.3 (×1.3)
CAMBER_RF=-4.55
CAMBER_LR=-0.7      # Base -1.0 + Drift behavior -0.6 (×0.7)
CAMBER_RR=-0.7
TOE_LF=-0.35        # Base -0.05 + Drift behavior -0.3
TOE_RF=-0.35
TOE_LR=-0.45        # Base -0.15 + Drift behavior -0.3
TOE_RR=-0.45

[DIFFERENTIAL]
POWER=100           # Base 85 + Drift behavior +15 + Drift slider +60 (clamped)
COAST=100           # Base 65 + Drift behavior +13 + Drift slider +50 (clamped)
PRELOAD=85          # Base 50 + Drift behavior +35

[SUSPENSION]
SPRING_RATE_LF=95500   # Base 85000 + Drift behavior +10500
SPRING_RATE_RF=95500
SPRING_RATE_LR=70000   # Base 70000 (souple arrière)
SPRING_RATE_RR=70000
RIDE_HEIGHT_LF=110
RIDE_HEIGHT_RF=110
RIDE_HEIGHT_LR=120
RIDE_HEIGHT_RR=120

[ARB]
FRONT=11            # Base 7 + Drift behavior +4 (très raide)
REAR=2              # Base 3 + Drift behavior -1 (très souple)

[BRAKES]
FRONT_BIAS=39       # Base 54 + Drift behavior -15 (arrière)

[ELECTRONICS]
TC=0                # Désactivé pour drift
ABS=0               # Désactivé pour drift
```

**Résultat:** Setup extrême pour drift, diff 100%, toe-out, peu de camber arrière, brake bias arrière

---

## 10. POINTS D'AMÉLIORATION POTENTIELS

### Pour discussion avec ingénieur de course

---

#### **A. Valeurs de base**

**Questions:**
1. Les valeurs GT3_BASE sont-elles réalistes pour un GT3 réel ?
   - Camber -4.0° avant est-il approprié ?
   - Diff 65% power est-il correct pour un GT3 ?
   - Pression 27.5 PSI est-elle optimale ?

2. Les valeurs STREET_BASE sont-elles adaptées pour Touge ?
   - Springs 75000 N/m est-ce trop raide pour une voiture de rue ?
   - Diff 40% power est-ce trop faible ?

3. Les valeurs DRIFT_BASE sont-elles correctes ?
   - Diff 85% power est-ce suffisant pour drifter ?
   - Toe-out -0.15° arrière est-ce trop/pas assez ?
   - Camber arrière -1.0° est-ce optimal pour glisse ?

---

#### **B. Behaviors - Amplitudes des modifiers**

**Questions:**
1. Les modifiers Attack sont-ils trop extrêmes ?
   - +0.7 sur camber = +35% → -4.0° devient -5.4°
   - Est-ce réaliste ou trop agressif ?

2. Les modifiers Safe sont-ils assez prononcés ?
   - -0.6 sur stiffness = -30%
   - Est-ce suffisant pour un setup "safe" ?

3. Les modifiers Drift sont-ils appropriés ?
   - 1.0 sur diff_power = +30% → peut atteindre 100%
   - Est-ce correct pour un setup drift ?

---

#### **C. Profile Tuning - Impact des sliders**

**Questions:**
1. Le slider Rotation est-il assez impactant ?
   - Max +0.4° toe arrière
   - Est-ce suffisant pour sentir la différence ?

2. Le slider Aggression est-il trop puissant ?
   - Max +30% springs, +40% diff
   - Peut-il rendre le setup inconduisible ?

3. Le slider Drift est-il bien calibré ?
   - +60 diff power max
   - Est-ce la bonne approche pour un setup drift ?

---

#### **D. Détection du type de voiture**

**Questions:**
1. La détection power/weight >0.4 est-elle pertinente ?
   - Une Caterham 620R (313hp, 545kg = 0.57) serait "race"
   - Est-ce correct ou devrait-elle être "street_sport" ?

2. Faut-il ajouter une catégorie "street_sport" ?
   - Pour 911 Carrera, Cayman GT4, M2, etc.
   - Valeurs entre street et race ?

3. La détection drift est-elle fiable ?
   - Basée sur flag + nom
   - Faut-il ajouter d'autres critères ?

---

#### **E. Ajustements par circuit**

**Actuellement minimal:**
```python
def _apply_track_adjustments(self, setup, track):
    # Seulement aero pour circuits rapides
    if track.avg_speed > 180:
        # Plus d'aero
        pass
```

**Questions:**
1. Faut-il ajuster selon le type de circuit ?
   - Circuit lent/technique → Setup souple, rotation
   - Circuit rapide → Setup raide, aero
   - Circuit bosselé → Setup souple, ride height

2. Faut-il ajuster selon la météo ?
   - Pluie → Moins de camber, pression basse
   - Chaud → Pression haute

3. Faut-il ajuster selon la longueur de course ?
   - Sprint → Setup agressif
   - Endurance → Setup conservateur, moins d'usure

---

#### **F. Validation physique**

**Questions:**
1. Les setups générés respectent-ils les lois physiques ?
   - Balance aero avant/arrière
   - Distribution de poids
   - Fréquences de suspension

2. Y a-t-il des combinaisons dangereuses ?
   - Diff 100% + toe-out + camber faible = spin ?
   - Springs trop raides + damping faible = instable ?

3. Faut-il ajouter des règles de validation ?
   - "Si diff > 80%, alors toe arrière > 0"
   - "Si camber < -5°, alors pression > 27 PSI"

---

#### **G. Feedback utilisateur**

**Actuellement manquant:**
- Pas d'explication des choix
- Pas de prédiction du comportement
- Pas de comparaison avant/après

**Questions:**
1. Faut-il afficher des explications ?
   - "Setup agressif : turn-in rapide mais moins stable"
   - "Diff lockant : meilleure traction mais sous-virage"

2. Faut-il prédire le comportement ?
   - Graphique oversteer/understeer
   - Note de stabilité/performance

3. Faut-il permettre des ajustements manuels ?
   - Éditeur de setup intégré
   - Comparaison avec setup de base

---

#### **H. Données réelles**

**Actuellement basé sur:**
- Expérience personnelle
- Valeurs AC par défaut
- Logique générale de setup

**Questions:**
1. Faut-il intégrer des données de setups réels ?
   - Setups pro de GT3 réels
   - Setups de championnat AC
   - Telemetry data

2. Faut-il permettre l'import de setups ?
   - Analyser un setup existant
   - Apprendre des patterns
   - Suggérer des améliorations

3. Faut-il ajouter un mode "apprentissage" ?
   - L'utilisateur note les setups
   - L'app apprend ses préférences
   - Génération personnalisée

---

## 📊 RÉSUMÉ POUR INGÉNIEUR

### Ce qui fonctionne bien

✅ **Détection automatique** - Fiable via shared memory  
✅ **Classification des voitures** - 3 types distincts (race/street/drift)  
✅ **Valeurs de base adaptées** - Différentes selon le type  
✅ **Behaviors marqués** - Différences perceptibles (2-3x amplifiées)  
✅ **Sliders impactants** - Ajustements utilisateur visibles (2x amplifiés)  
✅ **Export automatique** - Setups prêts à charger dans AC

### Ce qui pourrait être amélioré

⚠️ **Validation physique** - Pas de vérification des lois physiques  
⚠️ **Ajustements circuit** - Très basiques actuellement  
⚠️ **Feedback utilisateur** - Pas d'explication des choix  
⚠️ **Données réelles** - Basé sur expérience, pas telemetry  
⚠️ **Catégories intermédiaires** - Manque "street_sport", "time_attack", etc.  
⚠️ **Météo/conditions** - Pas pris en compte

### Questions principales pour l'ingénieur

1. **Les valeurs de base sont-elles réalistes ?** (camber, diff, pression)
2. **Les amplitudes des behaviors sont-elles appropriées ?** (trop/pas assez)
3. **Les sliders ont-ils le bon impact ?** (perceptible mais pas dangereux)
4. **Faut-il ajouter des règles de validation physique ?**
5. **Faut-il intégrer des données de setups réels ?**
6. **Quelles améliorations prioritaires ?**

---

**Document créé le:** 26 décembre 2025  
**Version app:** 1.0 (commit ea56e53)  
**Contact:** XENONRAy14

---

## 📎 ANNEXES

### Fichiers clés à consulter

- `core/setup_engine.py` - Logique de génération (1150 lignes)
- `core/behavior_engine.py` - Définition des behaviors (312 lignes)
- `models/car.py` - Structure de données voiture
- `models/setup.py` - Structure de données setup
- `SETUP_ANALYSIS.md` - Analyse détaillée des améliorations

### Ressources externes

- [Assetto Corsa Setup Guide](https://www.assettocorsa.net/forum/)
- [Real GT3 Setup Data](https://www.gt-world-challenge.com/)
- [AC Modding Documentation](https://www.assettocorsa.net/modding/)
