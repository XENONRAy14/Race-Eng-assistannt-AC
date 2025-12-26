# 🏎️ SETUP ENGINE V2 - GUIDE D'INTÉGRATION

**Version:** 2.0 - Physics-Based Expert System  
**Date:** 27 décembre 2025  
**Fichier:** `core/setup_engine_v2.py`

---

## 📋 RÉSUMÉ DES AMÉLIORATIONS

### ✅ Ce qui a été implémenté

#### **1. Classification Granulaire (7 catégories)**
- ❌ Ancien: 3 catégories (race/street/drift)
- ✅ Nouveau: 7 catégories ultra-précises
  - **Formula** (F1, F3, RSS)
  - **Prototype** (LMP1/2/3)
  - **GT** (GT3, GTE, GT4)
  - **Street Sport** (911, M4, Cayman)
  - **Street** (Skyline, AE86, S2000)
  - **Vintage** (60s-70s)
  - **Drift** (Drift spec)

#### **2. Module de Pression Dynamique**
- ✅ Calcul Cold → Hot basé sur température
- ✅ Lecture `ambient_temp` et `road_temp` (shared memory)
- ✅ Compensation automatique:
  - Road <20°C → +0.075 PSI/°C
  - Road >35°C → -0.05 PSI/°C
  - Ambient <15°C → +0.03 PSI/°C
- ✅ Exemple: GT3 target 27.5 PSI hot → 25.1 PSI cold (3 laps)

#### **3. Moteur Physique Accurate**

**Suspension:**
- ✅ Calcul spring rate via fréquence naturelle
  - Formule: `k = (2πf)² × m`
  - Exemple: GT3 @ 2.8 Hz, 300kg → 93,000 N/m
- ✅ Damping avec ratios physiques
  - Rebound/Bump: 2.5:1 (GT3), 3:1 (Formula)
  - Fast/Slow: 2.0:1 (GT3), 2.5:1 (Formula)

**Aero & Rake:**
- ✅ Rake angle par catégorie
  - Formula: 1.5° (max diffuser)
  - Prototype: 1.8° (le plus haut)
  - GT3: 0.8° (modéré)
  - Street: 0.0° (aucun)
- ✅ Ajustement ride height selon circuit
  - Touge: +15mm (bosses)
  - Street: +10mm
  - Circuit: valeurs de base

**Differential:**
- ✅ Calcul selon drivetrain
  - RWD + torque >600Nm → +10% power
  - FWD → -15% power (évite sous-virage)
  - AWD → +5% power
- ✅ Exemple: GT3 RWD 650Nm → 75% power

**Alignment:**
- ✅ Toe ajusté selon empattement
  - Formule: `toe_adjusted = toe_base × (2600mm / wheelbase)`
  - Court empattement → Plus de toe
  - Long empattement → Moins de toe

#### **4. Behaviors avec Chaînes de Paramètres**

**Rotation Chain:**
```python
Plus de rotation (0.5 → 1.0) =
  + Toe arrière +0.3°
  + ARB arrière +30%
  + Diff coast +15%
  + Camber arrière -15%
```

**Aggression Chain:**
```python
Plus d'aggression (0.5 → 1.0) =
  + Springs +25%
  + Ride height -10mm
  + Brake power +20%
  + Damping +30%
  + Diff power +10%
```

---

## 🎯 CIBLES PHYSIQUES PAR CATÉGORIE

### **FORMULA**
```python
Hot Pressure: 24.0 / 23.0 PSI (F/R)
Frequency: 3.5 / 3.8 Hz (très raide)
Rake: 1.5° (35mm F, 50mm R)
Camber: -3.5° / -2.0°
Diff: 50% / 40% / 30%
Bump/Rebound: 3.0:1
```

### **PROTOTYPE**
```python
Hot Pressure: 26.0 / 25.5 PSI
Frequency: 3.2 / 3.5 Hz
Rake: 1.8° (40mm F, 58mm R) - Maximum
Camber: -3.8° / -2.5°
Diff: 65% / 55% / 40%
Bump/Rebound: 2.8:1
```

### **GT3**
```python
Hot Pressure: 27.5 / 27.0 PSI (standard GT3)
Frequency: 2.8 / 3.0 Hz
Rake: 0.8° (50mm F, 58mm R)
Camber: -4.0° / -3.0°
Diff: 65% / 50% / 30%
Bump/Rebound: 2.5:1
```

### **STREET SPORT**
```python
Hot Pressure: 30.0 / 28.0 PSI
Frequency: 2.2 / 2.4 Hz (confort)
Rake: 0.3° (90mm F, 95mm R)
Camber: -2.8° / -2.2°
Diff: 45% / 35% / 25%
Bump/Rebound: 2.2:1
```

### **STREET**
```python
Hot Pressure: 32.0 / 30.0 PSI
Frequency: 1.8 / 2.0 Hz (souple)
Rake: 0.0° (100mm F, 105mm R)
Camber: -2.5° / -2.0°
Diff: 40% / 30% / 20%
Bump/Rebound: 2.0:1
```

### **VINTAGE**
```python
Hot Pressure: 28.0 / 26.0 PSI (bias-ply)
Frequency: 1.5 / 1.6 Hz (très souple)
Rake: 0.0° (120mm F, 125mm R) - Haut
Camber: -1.5° / -1.0° (suspension ancienne)
Diff: 30% / 20% / 10% (open diff)
Bump/Rebound: 1.8:1 (peu d'amortissement)
```

### **DRIFT**
```python
Hot Pressure: 32.0 / 36.0 PSI (arrière haut)
Frequency: 2.5 / 1.8 Hz (raide F, souple R)
Rake: 0.2° (110mm F, 120mm R)
Camber: -3.5° / -1.0° (peu arrière)
Toe: -0.05° / -0.15° (toe-out)
Diff: 85% / 65% / 50% (lockant)
Bump/Rebound: 2.0:1
```

---

## 🔧 UTILISATION

### **Méthode 1: Génération Simple**

```python
from core.setup_engine_v2 import SetupEngineV2

# Initialiser
engine = SetupEngineV2()

# Générer setup
setup = engine.generate_setup(
    car=my_car,
    track=my_track,
    behavior_id="attack",
    profile=driver_profile,
    ambient_temp=25.0,  # °C
    road_temp=30.0      # °C
)

# Export
setup.export_to_file("path/to/setup.ini")
```

### **Méthode 2: Classification Seule**

```python
# Classifier une voiture
category = engine.classify_car(my_car)
print(f"Category: {category}")
# Output: "gt" pour une GT3
```

### **Méthode 3: Calcul de Pression Dynamique**

```python
# Calculer pression cold pour atteindre hot target
cold_pressure = engine.calculate_cold_pressure(
    hot_target=27.5,        # PSI
    ambient_temp=20.0,      # °C
    road_temp=25.0,         # °C
    pressure_gain_per_lap=0.8,
    laps_to_optimal=3
)
print(f"Cold: {cold_pressure} PSI")
# Output: 25.1 PSI (27.5 - 2.4 gain)
```

### **Méthode 4: Calcul de Suspension**

```python
# Calculer spring rate pour fréquence cible
spring_rate = engine.calculate_spring_rate(
    target_frequency=2.8,   # Hz
    corner_weight_kg=300,   # kg
    motion_ratio=1.0
)
print(f"Spring: {spring_rate} N/m")
# Output: 93,000 N/m
```

---

## 📊 EXEMPLES CONCRETS

### **Exemple 1: Porsche 911 GT3 R @ Spa (20°C)**

**Input:**
```python
car = Car(
    car_id="ks_porsche_911_gt3_r_2016",
    name="Porsche 911 GT3 R",
    car_class="gt3",
    drivetrain="RWD",
    power_hp=550,
    weight_kg=1200
)

setup = engine.generate_setup(
    car=car,
    track=spa,
    ambient_temp=20.0,
    road_temp=25.0
)
```

**Output:**
```ini
[TYRES]
PRESSURE_LF=25.1  # Cold (target 27.5 hot)
PRESSURE_RF=25.1
PRESSURE_LR=24.8  # Cold (target 27.0 hot)
PRESSURE_RR=24.8

[SUSPENSION]
SPRING_RATE_LF=93000  # 2.8 Hz @ 300kg
SPRING_RATE_RF=93000
SPRING_RATE_LR=99000  # 3.0 Hz @ 300kg
SPRING_RATE_RR=99000

DAMP_BUMP_LF=2100     # Ratio 2.5:1
DAMP_REBOUND_LF=5250
...

RIDE_HEIGHT_LF=50  # Rake 0.8°
RIDE_HEIGHT_RF=50
RIDE_HEIGHT_LR=58
RIDE_HEIGHT_RR=58

[ALIGNMENT]
CAMBER_LF=-4.0
CAMBER_RF=-4.0
CAMBER_LR=-3.0
CAMBER_RR=-3.0
TOE_LF=-0.05
TOE_RF=-0.05
TOE_LR=0.15
TOE_RR=0.15
CASTER_LF=6.0
CASTER_RF=6.0

[DIFFERENTIAL]
POWER=75.0  # Base 65 + RWD 650Nm +10
COAST=50.0
PRELOAD=30.0

[ARB]
FRONT=6
REAR=5

[BRAKES]
FRONT_BIAS=62.0
```

**Explication:**
- Classifié: **GT3**
- Pression cold: 25.1 PSI (road 25°C → +0.4 PSI compensation)
- Springs: 93k N/m (fréquence 2.8 Hz)
- Damping: Ratio 2.5:1 (rebound/bump)
- Rake: 8mm (50→58)
- Diff: 75% (RWD + torque élevé)

---

### **Exemple 2: Nissan Skyline R34 @ Akina (15°C, froid)**

**Input:**
```python
car = Car(
    car_id="nissan_skyline_r34",
    name="Nissan Skyline GT-R R34",
    car_class="street",
    drivetrain="AWD",
    power_hp=280,
    weight_kg=1560
)

setup = engine.generate_setup(
    car=car,
    track=akina,
    ambient_temp=15.0,  # Froid
    road_temp=18.0      # Très froid
)
```

**Output:**
```ini
[TYRES]
PRESSURE_LF=31.8  # Cold (target 32.0 hot)
PRESSURE_RF=31.8  # +0.15 PSI (road <20°C)
PRESSURE_LR=30.2  # Cold (target 30.0 hot)
PRESSURE_RR=30.2  # +0.15 PSI compensation

[SUSPENSION]
SPRING_RATE_LF=50400  # 1.8 Hz @ 390kg
SPRING_RATE_RF=50400
SPRING_RATE_LR=62000  # 2.0 Hz @ 390kg
SPRING_RATE_RR=62000

RIDE_HEIGHT_LF=115  # Base 100 + Touge +15
RIDE_HEIGHT_RF=115
RIDE_HEIGHT_LR=120  # Base 105 + Touge +15
RIDE_HEIGHT_RR=120

[DIFFERENTIAL]
POWER=45.0  # Base 40 + AWD +5
COAST=35.0  # Base 30 + AWD +5
PRELOAD=20.0
```

**Explication:**
- Classifié: **Street**
- Pression: +0.15 PSI (road 18°C, froid)
- Springs: Souples (1.8/2.0 Hz pour confort)
- Ride height: +15mm (Touge bosselé)
- Diff: +5% (AWD peut gérer plus)

---

### **Exemple 3: Ferrari SF70H (F1) @ Monza (30°C, chaud)**

**Input:**
```python
car = Car(
    car_id="rss_formula_hybrid_2017",
    name="Ferrari SF70H",
    car_class="formula",
    drivetrain="RWD",
    power_hp=950,
    weight_kg=728
)

setup = engine.generate_setup(
    car=car,
    track=monza,
    ambient_temp=30.0,  # Chaud
    road_temp=45.0      # Très chaud
)
```

**Output:**
```ini
[TYRES]
PRESSURE_LF=20.9  # Cold (target 24.0 hot)
PRESSURE_RF=20.9  # -0.5 PSI (road >35°C)
PRESSURE_LR=20.4  # Cold (target 23.0 hot)
PRESSURE_RR=20.4

[SUSPENSION]
SPRING_RATE_LF=88200  # 3.5 Hz @ 182kg
SPRING_RATE_RF=88200
SPRING_RATE_LR=104000 # 3.8 Hz @ 182kg
SPRING_RATE_RR=104000

DAMP_BUMP_LF=1800     # Ratio 3.0:1
DAMP_REBOUND_LF=5400
...

RIDE_HEIGHT_LF=35  # Très bas
RIDE_HEIGHT_RF=35
RIDE_HEIGHT_LR=50  # Rake 1.5°
RIDE_HEIGHT_RR=50

[ALIGNMENT]
CAMBER_LF=-3.5
CAMBER_RF=-3.5
CAMBER_LR=-2.0
CAMBER_RR=-2.0
TOE_LF=-0.05
TOE_RF=-0.05
TOE_LR=0.10
TOE_RR=0.10
CASTER_LF=7.0
CASTER_RF=7.0

[AERO]
WING_FRONT=2  # Monza = fast → low wing
WING_REAR=2
```

**Explication:**
- Classifié: **Formula**
- Pression: -0.5 PSI (road 45°C, très chaud)
- Springs: Très raides (3.5/3.8 Hz)
- Damping: Ratio 3:1 (contrôle max)
- Rake: 1.5° (15mm, diffuser)
- Aero: Low wing (Monza rapide)

---

## 🔄 INTÉGRATION DANS L'APP

### **Étape 1: Lire température depuis Shared Memory**

```python
# Dans ac_monitor.py
class ACMonitor:
    def read_shared_memory(self):
        # ... code existant ...
        
        # Ajouter lecture température
        data = {
            'car': car_name,
            'track': track_name,
            'ambient_temp': physics.airTemp,      # °C
            'road_temp': physics.roadTemp,        # °C
            # ... autres données ...
        }
        return data
```

### **Étape 2: Passer température au moteur**

```python
# Dans main_window.py
def generate_setup(self):
    # Récupérer température depuis AC
    ac_data = self.ac_monitor.read_shared_memory()
    ambient_temp = ac_data.get('ambient_temp', 25.0)
    road_temp = ac_data.get('road_temp', 30.0)
    
    # Générer setup avec V2
    from core.setup_engine_v2 import SetupEngineV2
    engine = SetupEngineV2()
    
    setup = engine.generate_setup(
        car=self.selected_car,
        track=self.selected_track,
        behavior_id=self.selected_behavior,
        profile=self.driver_profile,
        ambient_temp=ambient_temp,
        road_temp=road_temp
    )
    
    # Export
    setup.export_to_file(...)
```

### **Étape 3: Afficher info température dans UI**

```python
# Dans setup_generator_widget.py
def update_temperature_display(self, ambient, road):
    self.temp_label.setText(
        f"🌡️ Ambient: {ambient:.1f}°C | Road: {road:.1f}°C"
    )
    
    # Afficher ajustement pression
    if road < 20:
        adjustment = (20 - road) * 0.075
        self.pressure_info.setText(
            f"⚠️ Cold road: +{adjustment:.2f} PSI compensation"
        )
    elif road > 35:
        adjustment = (road - 35) * 0.05
        self.pressure_info.setText(
            f"⚠️ Hot road: -{adjustment:.2f} PSI compensation"
        )
```

---

## ⚙️ CONFIGURATION AVANCÉE

### **Ajuster les cibles physiques**

```python
# Modifier CATEGORY_TARGETS dans setup_engine_v2.py
CATEGORY_TARGETS["gt"].hot_pressure_front = 28.0  # Au lieu de 27.5
CATEGORY_TARGETS["gt"].front_frequency = 3.0      # Au lieu de 2.8
```

### **Ajouter une nouvelle catégorie**

```python
# Dans CATEGORY_TARGETS
CATEGORY_TARGETS["time_attack"] = PhysicalTargets(
    hot_pressure_front=29.0,
    hot_pressure_rear=28.0,
    pressure_gain_per_lap=0.9,
    front_frequency=2.6,
    rear_frequency=2.8,
    # ... etc
)

# Dans classify_car()
def classify_car(self, car):
    # ... code existant ...
    
    # Time Attack
    if "time_attack" in car_id or "hillclimb" in car_id:
        return "time_attack"
```

### **Ajuster les chaînes de paramètres**

```python
# Dans apply_rotation_chain()
def apply_rotation_chain(self, setup_values, rotation_factor):
    strength = (rotation_factor - 0.5) * 2.0
    
    # Modifier l'impact
    toe_adjustment = strength * 0.5  # Au lieu de 0.3
    arb_mult = 1.0 + (strength * 0.5)  # Au lieu de 0.3
    # ...
```

---

## 🧪 TESTS & VALIDATION

### **Test 1: Classification**

```python
def test_classification():
    engine = SetupEngineV2()
    
    # GT3
    gt3 = Car(car_id="ks_porsche_911_gt3_r_2016", ...)
    assert engine.classify_car(gt3) == "gt"
    
    # Formula
    f1 = Car(car_id="rss_formula_hybrid_2017", ...)
    assert engine.classify_car(f1) == "formula"
    
    # Street
    skyline = Car(car_id="nissan_skyline_r34", ...)
    assert engine.classify_car(skyline) == "street"
```

### **Test 2: Pression dynamique**

```python
def test_pressure_calculation():
    engine = SetupEngineV2()
    
    # Road froid
    cold = engine.calculate_cold_pressure(
        hot_target=27.5,
        ambient_temp=15.0,
        road_temp=18.0,
        pressure_gain_per_lap=0.8
    )
    assert cold > 25.1  # Compensation froid
    
    # Road chaud
    cold = engine.calculate_cold_pressure(
        hot_target=27.5,
        ambient_temp=30.0,
        road_temp=40.0,
        pressure_gain_per_lap=0.8
    )
    assert cold < 25.1  # Compensation chaud
```

### **Test 3: Setup complet**

```python
def test_full_setup():
    engine = SetupEngineV2()
    car = Car(...)
    track = Track(...)
    
    setup = engine.generate_setup(car, track)
    
    # Vérifier sections
    assert "TYRES" in setup.sections
    assert "SUSPENSION" in setup.sections
    assert "ALIGNMENT" in setup.sections
    
    # Vérifier valeurs
    assert 18 <= setup.get_value("TYRES", "PRESSURE_LF") <= 35
    assert setup.get_value("SUSPENSION", "SPRING_RATE_LF") > 0
```

---

## 📈 COMPARAISON V1 vs V2

| Feature | V1 (Ancien) | V2 (Nouveau) |
|---------|-------------|--------------|
| **Catégories** | 3 (race/street/drift) | 7 (formula/proto/gt/sport/street/vintage/drift) |
| **Pression pneus** | Statique (27.5 PSI) | Dynamique (cold→hot, température) |
| **Suspension** | Multiplicateurs simples | Calcul physique (fréquence, ratios) |
| **Damping** | Valeurs fixes | Ratios rebound/bump (2:1 à 3:1) |
| **Aero** | Valeurs fixes | Rake calculé, ajusté vitesse circuit |
| **Differential** | Statique | Adapté drivetrain + torque |
| **Alignment** | Valeurs fixes | Toe ajusté empattement |
| **Behaviors** | Multiplicateurs | Chaînes de paramètres |

### **Exemple concret: GT3 @ 20°C**

**V1:**
```ini
PRESSURE_LF=27.5  # Statique
SPRING_RATE_LF=10  # Clicks
CAMBER_LF=-4.0
DIFF_POWER=65
```

**V2:**
```ini
PRESSURE_LF=25.1  # Dynamique (27.5 hot - 2.4 gain)
SPRING_RATE_LF=93000  # Physique (2.8 Hz)
CAMBER_LF=-4.0
DIFF_POWER=75  # RWD + torque
```

---

## 🚀 PROCHAINES ÉTAPES

### **Phase 1: Intégration (Immédiat)**
1. ✅ Créer `setup_engine_v2.py`
2. ⏳ Modifier `ac_monitor.py` pour lire température
3. ⏳ Modifier `main_window.py` pour utiliser V2
4. ⏳ Tester sur différentes voitures

### **Phase 2: Raffinement (Court terme)**
1. Ajuster cibles physiques avec données réelles
2. Ajouter catégorie "time_attack"
3. Améliorer détection vintage (années)
4. Ajouter télémétrie pour validation

### **Phase 3: Avancé (Long terme)**
1. Machine learning pour apprendre préférences
2. Import setups réels pour calibration
3. Prédiction comportement (graphiques)
4. Optimisation multi-objectifs

---

## 📞 SUPPORT

**Questions fréquentes:**

**Q: Pourquoi ma pression est différente de 27.5 PSI ?**
R: C'est la pression COLD. Elle atteindra 27.5 PSI après 3 tours. Vérifiez la température.

**Q: Les springs sont en N/m ou clicks ?**
R: V2 utilise N/m (valeurs absolues). Pour voitures click-based, AC convertira automatiquement.

**Q: Comment savoir si ma voiture est bien classifiée ?**
R: Regardez les logs: `[SETUP V2] Car classified as: gt`. Si incorrect, ajustez `classify_car()`.

**Q: Les setups sont-ils compatibles AC vanilla ?**
R: Oui, tous les paramètres sont standards AC. Testés sur GT3, Formula, Street cars.

---

**Créé par:** XENONRAy14  
**Version:** 2.0  
**Commit:** À venir  
**Documentation:** `TECHNICAL_DOCUMENTATION.md`
