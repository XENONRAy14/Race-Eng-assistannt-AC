# 🔧 SETUP ENGINE V2.1 - GUIDE D'INTÉGRATION COMPLET

**Version:** 2.1 - Physics Refiner + Thermal Monitor  
**Date:** 27 décembre 2025  
**Nouveaux modules:** `physics_refiner.py`, `ac_monitor_v2.py`

---

## 📋 RÉSUMÉ DES NOUVEAUTÉS V2.1

### ✅ Modules créés

1. **`core/physics_refiner.py`** (600+ lignes)
   - Correction Motion Ratio
   - Anti-bottoming pour voitures à appui
   - Cap Fast Damping pour circuits bosselés

2. **`core/ac_monitor_v2.py`** (500+ lignes)
   - Lecture température temps réel (airTemp, roadTemp)
   - Extraction données dynamiques (pression pneus, suspension)
   - Structure ctypes complète pour shared memory AC

3. **`data/cars_enriched_example.json`**
   - Base de données enrichie avec données physiques
   - Wheelbase, max_torque, motion_ratios par voiture

---

## 🎯 PROBLÈMES RÉSOLUS

### **Problème 1: Motion Ratio ignoré**

**Avant (V2.0):**
```python
# SetupEngineV2 calcule k_wheel
k_wheel = (2πf)² × m = 99,000 N/m

# Mais ignore le Motion Ratio !
# Spring rate exporté = 99,000 N/m (INCORRECT)
```

**Après (V2.1):**
```python
# SetupEngineV2 calcule k_wheel
k_wheel = 99,000 N/m

# PhysicsRefiner corrige avec MR
MR_rear = 0.8 (GT3)
k_spring = k_wheel / MR² = 99,000 / 0.64 = 154,687 N/m

# Spring rate exporté = 154,687 N/m (CORRECT)
```

**Impact:** Springs 56% plus raides pour GT3 arrière !

---

### **Problème 2: Bottoming sur Formula/LMP**

**Avant:**
```python
# Formula avec rake 1.5°
# Front ride height = 35mm
# Sous appui aéro → Compression 20mm
# Résultat: 35 - 20 = 15mm → BOTTOMING !
```

**Après:**
```python
# PhysicsRefiner détecte:
# - Category = "formula"
# - Rake = 1.5° (>1.0°)
# → Augmente springs +15%

# Nouvelle compression sous appui:
# Springs +15% → Compression 17mm (au lieu de 20mm)
# Résultat: 35 - 17 = 18mm → SAFE
```

---

### **Problème 3: Rebonds sur Touge**

**Avant:**
```python
# Fast bump = 6000 (2x slow bump)
# Roue frappe bosse → Compression rapide
# Fast damping trop raide → Rebond violent
# Perte de contact avec route
```

**Après:**
```python
# PhysicsRefiner détecte track_type = "touge"
# Cap fast bump à 50% de slow bump
# Fast bump = 1500 (au lieu de 6000)
# Roue absorbe bosse sans rebondir
```

---

## 🔌 INTÉGRATION ÉTAPE PAR ÉTAPE

### **Étape 1: Importer les nouveaux modules**

```python
# Dans main_window.py ou setup_generator.py
from core.setup_engine_v2 import SetupEngineV2
from core.physics_refiner import PhysicsRefiner
from core.ac_monitor_v2 import ACMonitorV2
```

---

### **Étape 2: Initialiser les modules**

```python
class SetupGenerator:
    def __init__(self):
        # Moteur de setup V2
        self.setup_engine = SetupEngineV2()
        
        # Raffineur physique V2.1
        self.physics_refiner = PhysicsRefiner()
        
        # Moniteur AC V2
        self.ac_monitor = ACMonitorV2()
        
        # Connecter au démarrage
        self.ac_monitor.connect()
```

---

### **Étape 3: Charger données enrichies**

```python
import json
from pathlib import Path

def load_car_data(car_id: str) -> dict:
    """
    Charge les données enrichies d'une voiture.
    
    Returns:
        Dict avec wheelbase_mm, max_torque_nm, motion_ratios, etc.
    """
    # Charger JSON enrichi
    json_path = Path("data/cars_enriched.json")
    
    if not json_path.exists():
        print(f"[WARNING] Enriched data not found, using defaults")
        return {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Chercher la voiture
    for car in data.get("cars", []):
        if car["car_id"] == car_id:
            return car
    
    print(f"[WARNING] Car {car_id} not found in enriched data")
    return {}
```

---

### **Étape 4: Fonction de génération complète V2.1**

```python
def generate_setup_v21(
    self,
    car: Car,
    track: Track,
    behavior_id: str = "balanced",
    profile: Optional[DriverProfile] = None
) -> Setup:
    """
    Génération de setup V2.1 avec raffinement physique.
    
    Pipeline:
    1. Récupérer température temps réel (AC Monitor V2)
    2. Charger données enrichies voiture
    3. Générer setup base (Setup Engine V2)
    4. Raffiner physique (Physics Refiner)
    5. Exporter
    
    Args:
        car: Objet Car
        track: Objet Track
        behavior_id: ID du behavior
        profile: Profil conducteur
    
    Returns:
        Setup raffiné prêt à exporter
    """
    print("\n" + "="*70)
    print("SETUP GENERATION V2.1 - COMPLETE PIPELINE")
    print("="*70)
    
    # ─────────────────────────────────────────────────────────────────
    # STEP 1: Récupérer température temps réel
    # ─────────────────────────────────────────────────────────────────
    print("\n[STEP 1] Reading thermal data from AC...")
    
    thermal_data = self.ac_monitor.get_thermal_data()
    ambient_temp = thermal_data["ambient_temp"]
    road_temp = thermal_data["road_temp"]
    
    print(f"  Ambient: {ambient_temp:.1f}°C")
    print(f"  Road: {road_temp:.1f}°C")
    
    # Fallback si AC non connecté
    if not self.ac_monitor.is_connected:
        print("  [WARNING] AC not connected, using defaults (25°C / 30°C)")
        ambient_temp = 25.0
        road_temp = 30.0
    
    # ─────────────────────────────────────────────────────────────────
    # STEP 2: Charger données enrichies
    # ─────────────────────────────────────────────────────────────────
    print("\n[STEP 2] Loading enriched car data...")
    
    car_data = load_car_data(car.car_id)
    
    if car_data:
        print(f"  Wheelbase: {car_data.get('wheelbase_mm', 'N/A')} mm")
        print(f"  Max Torque: {car_data.get('max_torque_nm', 'N/A')} Nm")
        print(f"  Motion Ratio F/R: {car_data.get('motion_ratio_front', 'N/A')} / {car_data.get('motion_ratio_rear', 'N/A')}")
    else:
        print("  [WARNING] No enriched data, using category defaults")
    
    # ─────────────────────────────────────────────────────────────────
    # STEP 3: Générer setup base (V2)
    # ─────────────────────────────────────────────────────────────────
    print("\n[STEP 3] Generating base setup (V2)...")
    
    setup = self.setup_engine.generate_setup(
        car=car,
        track=track,
        behavior_id=behavior_id,
        profile=profile,
        ambient_temp=ambient_temp,
        road_temp=road_temp
    )
    
    # Classifier la voiture
    category = self.setup_engine.classify_car(car)
    print(f"  Category: {category}")
    
    # ─────────────────────────────────────────────────────────────────
    # STEP 4: Raffiner physique (V2.1)
    # ─────────────────────────────────────────────────────────────────
    print("\n[STEP 4] Applying physics refinement (V2.1)...")
    
    # Déterminer rake angle (depuis les cibles)
    from core.setup_engine_v2 import CATEGORY_TARGETS
    targets = CATEGORY_TARGETS.get(category)
    rake_angle = targets.rake_angle if targets else 0.0
    
    # Déterminer type de circuit
    track_type = "circuit"  # Default
    if "touge" in track.name.lower() or "akina" in track.name.lower():
        track_type = "touge"
    elif "street" in track.name.lower():
        track_type = "street"
    
    print(f"  Rake angle: {rake_angle:.1f}°")
    print(f"  Track type: {track_type}")
    
    # Appliquer raffinement
    setup = self.physics_refiner.refine(
        setup=setup,
        category=category,
        rake_angle=rake_angle,
        track_type=track_type,
        car_data=car_data
    )
    
    # ─────────────────────────────────────────────────────────────────
    # STEP 5: Export
    # ─────────────────────────────────────────────────────────────────
    print("\n[STEP 5] Setup ready for export")
    print("="*70 + "\n")
    
    return setup
```

---

### **Étape 5: Utilisation dans l'UI**

```python
# Dans le bouton "Generate Setup"
def on_generate_setup_clicked(self):
    """Handler pour le bouton de génération."""
    
    # Récupérer sélections
    car = self.car_track_selector.get_selected_car()
    track = self.car_track_selector.get_selected_track()
    behavior_id = self.behavior_selector.get_selected_behavior()
    profile = self.driver_profile
    
    if not car or not track:
        QMessageBox.warning(self, "Error", "Please select car and track")
        return
    
    # Générer setup V2.1
    try:
        setup = self.generate_setup_v21(car, track, behavior_id, profile)
        
        # Exporter
        export_path = self.get_export_path(car, track)
        setup.export_to_file(export_path)
        
        QMessageBox.information(
            self, 
            "Success", 
            f"Setup generated and exported to:\n{export_path}"
        )
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Setup generation failed:\n{e}")
```

---

## 📊 EXEMPLE COMPLET: GT3 @ SPA

### **Input:**
```python
car = Car(
    car_id="ks_porsche_911_gt3_r_2016",
    name="Porsche 911 GT3 R",
    car_class="gt3",
    drivetrain="RWD",
    power_hp=550,
    weight_kg=1200
)

track = Track(
    track_id="ks_spa",
    name="Spa-Francorchamps",
    length_km=7.0
)

# AC conditions
ambient_temp = 18.0°C
road_temp = 22.0°C
```

---

### **Pipeline V2.1:**

#### **1. Setup Engine V2 génère:**
```ini
[TYRES]
PRESSURE_LF=24.8  # Cold (target 27.5 hot, road 22°C)
PRESSURE_RF=24.8
PRESSURE_LR=24.5  # Cold (target 27.0 hot)
PRESSURE_RR=24.5

[SUSPENSION]
SPRING_RATE_LF=93000   # k_wheel @ 2.8 Hz
SPRING_RATE_RF=93000
SPRING_RATE_LR=99000   # k_wheel @ 3.0 Hz
SPRING_RATE_RR=99000

RIDE_HEIGHT_LF=50
RIDE_HEIGHT_RF=50
RIDE_HEIGHT_LR=58  # Rake 0.8°
RIDE_HEIGHT_RR=58
```

#### **2. Physics Refiner corrige:**

**Motion Ratio (GT3: F=0.9, R=0.8):**
```
Front:
  k_wheel = 93,000 N/m
  MR = 0.9
  k_spring = 93,000 / 0.9² = 93,000 / 0.81 = 114,815 N/m
  
Rear:
  k_wheel = 99,000 N/m
  MR = 0.8
  k_spring = 99,000 / 0.8² = 99,000 / 0.64 = 154,687 N/m
```

**Anti-bottoming (rake 0.8° < 1.0°):**
```
Rake OK, pas d'ajustement
```

**Fast Damping (circuit lisse):**
```
Track type = "circuit"
Pas de cap, fast damping OK
```

#### **3. Setup final exporté:**
```ini
[TYRES]
PRESSURE_LF=24.8
PRESSURE_RF=24.8
PRESSURE_LR=24.5
PRESSURE_RR=24.5

[SUSPENSION]
SPRING_RATE_LF=114815  # Corrigé MR 0.9
SPRING_RATE_RF=114815
SPRING_RATE_LR=154687  # Corrigé MR 0.8
SPRING_RATE_RR=154687

RIDE_HEIGHT_LF=50
RIDE_HEIGHT_RF=50
RIDE_HEIGHT_LR=58
RIDE_HEIGHT_RR=58
```

---

## 🧪 TESTS & VALIDATION

### **Test 1: Motion Ratio**

```python
def test_motion_ratio_correction():
    """Vérifie que la correction MR fonctionne."""
    from core.physics_refiner import PhysicsRefiner, calculate_spring_correction
    
    # Test calcul correction
    assert calculate_spring_correction(1.0) == 1.0    # Pas de correction
    assert calculate_spring_correction(0.9) == 1.23   # +23%
    assert calculate_spring_correction(0.8) == 1.56   # +56%
    assert calculate_spring_correction(0.7) == 2.04   # +104%
    
    print("[TEST] Motion ratio correction: PASS")
```

### **Test 2: Anti-bottoming**

```python
def test_anti_bottoming():
    """Vérifie que l'anti-bottoming s'active correctement."""
    from core.physics_refiner import PhysicsRefiner
    from models.setup import Setup
    
    refiner = PhysicsRefiner()
    setup = Setup(name="Test")
    
    # Ajouter springs de base
    setup.set_value("SUSPENSION", "SPRING_RATE_LF", 90000)
    
    # Test Formula avec rake agressif
    setup_refined = refiner.apply_anti_bottoming(setup, "formula", rake_angle=1.5)
    
    # Vérifier augmentation 15%
    new_spring = setup_refined.get_value("SUSPENSION", "SPRING_RATE_LF")
    assert new_spring == 103500  # 90000 × 1.15
    
    print("[TEST] Anti-bottoming: PASS")
```

### **Test 3: Fast Damping Cap**

```python
def test_fast_damping_cap():
    """Vérifie que le cap fast damping fonctionne."""
    from core.physics_refiner import PhysicsRefiner
    from models.setup import Setup
    
    refiner = PhysicsRefiner()
    setup = Setup(name="Test")
    
    # Ajouter damping
    setup.set_value("SUSPENSION", "DAMP_BUMP_LF", 3000)
    setup.set_value("SUSPENSION", "DAMP_FAST_BUMP_LF", 6000)  # 2x
    
    # Appliquer cap pour Touge
    setup_refined = refiner.cap_fast_damping(setup, track_type="touge")
    
    # Vérifier cap à 50%
    fast_bump = setup_refined.get_value("SUSPENSION", "DAMP_FAST_BUMP_LF")
    assert fast_bump == 1500  # 3000 × 0.5
    
    print("[TEST] Fast damping cap: PASS")
```

### **Test 4: AC Monitor**

```python
def test_ac_monitor():
    """Teste la connexion au moniteur AC."""
    from core.ac_monitor_v2 import ACMonitorV2
    
    monitor = ACMonitorV2()
    
    if monitor.connect():
        data = monitor.get_thermal_data()
        
        assert "ambient_temp" in data
        assert "road_temp" in data
        assert data["ambient_temp"] > 0
        
        print(f"[TEST] AC Monitor: PASS")
        print(f"  Ambient: {data['ambient_temp']:.1f}°C")
        print(f"  Road: {data['road_temp']:.1f}°C")
        
        monitor.disconnect()
    else:
        print("[TEST] AC Monitor: SKIP (AC not running)")
```

---

## 🔧 CONFIGURATION AVANCÉE

### **Ajuster Motion Ratios**

```python
# Dans physics_refiner.py
MOTION_RATIOS["gt"]["rear"] = 0.75  # Au lieu de 0.8

# Ou dans cars_enriched.json
{
  "car_id": "ks_porsche_911_gt3_r_2016",
  "motion_ratio_front": 0.92,  # Custom
  "motion_ratio_rear": 0.78    # Custom
}
```

### **Ajuster seuil Anti-bottoming**

```python
# Dans apply_anti_bottoming()
if rake_angle > 1.2:  # Au lieu de 1.0
    spring_multiplier = 1.20  # Au lieu de 1.15
```

### **Ajuster cap Fast Damping**

```python
# Dans cap_fast_damping()
max_ratio = 0.6  # Au lieu de 0.5 (60% au lieu de 50%)
```

---

## 📚 DOCUMENTATION TECHNIQUE

### **Formules physiques utilisées**

#### **1. Motion Ratio**
```
k_spring = k_wheel / MR²

Où:
- k_wheel = Raideur à la roue (N/m)
- MR = Motion Ratio (wheel travel / spring travel)
- k_spring = Raideur réelle du ressort (N/m)

Exemple:
  k_wheel = 100,000 N/m
  MR = 0.8
  k_spring = 100,000 / 0.64 = 156,250 N/m
```

#### **2. Fréquence naturelle**
```
f = (1/2π) × √(k/m)

Où:
- f = Fréquence naturelle (Hz)
- k = Raideur (N/m)
- m = Masse (kg)

Inversée:
  k = (2πf)² × m
```

#### **3. Amortissement critique**
```
c_critical = 2 × √(k × m)

Où:
- c_critical = Coefficient d'amortissement critique
- k = Raideur ressort (N/m)
- m = Masse (kg)

Utilisation typique: 70% du critique
  c = 0.7 × c_critical
```

---

## 🚀 MIGRATION V2.0 → V2.1

### **Changements requis:**

1. **Importer nouveaux modules**
   ```python
   from core.physics_refiner import PhysicsRefiner
   from core.ac_monitor_v2 import ACMonitorV2
   ```

2. **Initialiser refiner**
   ```python
   self.physics_refiner = PhysicsRefiner()
   ```

3. **Appeler refine() après generate_setup()**
   ```python
   setup = engine.generate_setup(...)
   setup = refiner.refine(setup, category, rake_angle, track_type, car_data)
   ```

4. **Utiliser AC Monitor V2**
   ```python
   monitor = ACMonitorV2()
   monitor.connect()
   thermal = monitor.get_thermal_data()
   ```

### **Rétrocompatibilité:**

✅ V2.1 est **100% compatible** avec V2.0  
✅ Si `physics_refiner` n'est pas utilisé, setup V2.0 fonctionne  
✅ Si `car_data` manque, utilise defaults par catégorie  
✅ Si AC non connecté, utilise températures par défaut

---

## 📊 RÉSULTATS ATTENDUS

### **Avant V2.1:**
- Springs incorrects (MR ignoré)
- Bottoming sur Formula/LMP
- Rebonds sur Touge

### **Après V2.1:**
- ✅ Springs corrects (+23% à +104% selon MR)
- ✅ Pas de bottoming (anti-bottoming actif)
- ✅ Absorption bosses (fast damping cappé)
- ✅ Pression adaptée température réelle

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Tester sur différentes voitures
2. ✅ Valider avec télémétrie AC
3. ⏳ Enrichir `cars.json` avec toutes les voitures
4. ⏳ Ajouter UI pour afficher corrections appliquées
5. ⏳ Ajouter export rapport de raffinement

---

**Version:** 2.1  
**Créé par:** XENONRAy14  
**Date:** 27 décembre 2025  
**Modules:** `physics_refiner.py`, `ac_monitor_v2.py`
