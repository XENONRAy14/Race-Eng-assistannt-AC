# 🔧 RÉPONSES AUX QUESTIONS DE L'INGÉNIEUR DE COURSE

**Date:** 28 décembre 2025  
**Sujet:** Analyse technique approfondie du système de génération de setups  
**Version:** 2.1

---

## 🛠️ 1. MÉTHODE D'INJECTION - FLUX DE DONNÉES

### **A. Rechargement du Setup dans AC**

**❌ LIMITATION ACTUELLE:**
```
L'application écrit le fichier .ini sur disque, mais AC ne le recharge PAS automatiquement.
```

**Workflow actuel:**
```python
# 1. Génération setup
setup = engine.generate_setup(car, track, behavior)

# 2. Écriture fichier
path = Documents/Assetto Corsa/setups/{car_id}/{track_id}/rea_setup.ini
write_setup(setup, path)

# 3. ❌ AC ne relit PAS automatiquement
# L'utilisateur DOIT:
# - Être aux stands (Pit/Menu)
# - Cliquer "Setup" → "Load" → Sélectionner le fichier
# - Ou redémarrer la session
```

**Pourquoi l'aileron ne bouge pas:**
- Si tu es **en piste** → AC ne relit jamais les fichiers
- Si tu es **aux stands** → Tu dois cliquer "Load" manuellement
- Si le fichier est dans `generic/` → Visible dans tous les circuits
- Si le fichier est dans `{track_id}/` → Visible uniquement sur ce circuit

**Solutions possibles (NON IMPLÉMENTÉES):**

**Option 1: Script Lua Content Manager**
```lua
-- Nécessite Content Manager + CSP
ac.setSetupValue("PRESSURE_LF", 25)
ac.reloadSetup()
```
❌ Pas implémenté - Nécessite CM + CSP activé

**Option 2: Shared Memory Injection**
```python
# Écriture directe dans mémoire partagée AC
# ❌ IMPOSSIBLE - AC ne permet pas l'écriture
# Shared memory est READ-ONLY
```

**Option 3: Python Plugin AC**
```python
# Plugin Python dans AC (comme apps/)
# ❌ Complexe - Nécessite intégration dans AC
```

**✅ SOLUTION ACTUELLE:**
```
1. Génère setup → Écrit fichier
2. Affiche message: "Setup généré! Retourne aux stands et clique Load"
3. L'utilisateur charge manuellement
```

---

### **B. Formatage des Fichiers**

**Format AC Setup (.ini):**
```ini
[PARAMETER_NAME]
VALUE=123

[ANOTHER_PARAM]
VALUE=456

[CAR]
MODEL=ks_porsche_911_gt3_r_2016
```

**Encodage actuel:**
```python
# setup_writer.py ligne 82, 105
with open(file_path, "w", encoding="utf-8") as f:
    f.write(ini_content)
```

**✅ UTF-8** utilisé (correct pour AC moderne + CSP)

**⚠️ PROBLÈME POTENTIEL:**
- AC vanilla ancien: Parfois UTF-16 LE
- AC + CSP: UTF-8 fonctionne
- Mods: Peuvent nécessiter ANSI (Windows-1252)

**Structure des headers:**

**Voitures Kunos (officielles):**
```ini
[PRESSURE_LF]
VALUE=26

[CAMBER_LF]
VALUE=-35

[TOE_OUT_LF]
VALUE=0
```

**Mods (variables):**
```ini
[WING_0]        # Certains mods
VALUE=5

[REAR_WING]     # Autres mods
VALUE=5

[AERO_REAR]     # Encore d'autres
VALUE=5
```

**❌ PROBLÈME IDENTIFIÉ:**
```python
# setup_writer.py ligne 221-258
# Mapping FIXE pour voitures Kunos uniquement
param_mapping = {
    ("TYRES", "PRESSURE_LF"): "PRESSURE_LF",
    ("ALIGNMENT", "CAMBER_LF"): "CAMBER_LF",
    # ... etc
}

# ❌ Si un mod utilise [WING_1] au lieu de [WING_0]
# → La modification est IGNORÉE
```

---

## 🔍 2. MAPPING DES VARIABLES - PROBLÈME DES MODS

### **A. Dictionnaire de Correspondance**

**État actuel:**
```python
# setup_writer.py ligne 221-258
# ❌ Mapping STATIQUE pour Kunos uniquement
param_mapping = {
    ("SUSPENSION", "RIDE_HEIGHT_LF"): "ROD_LENGTH_LF",
    ("ALIGNMENT", "TOE_LF"): "TOE_OUT_LF",
    # Seulement ~30 paramètres Kunos
}
```

**❌ LIMITATIONS:**
1. **Pas de base de données par voiture**
   - Tous les mods utilisent le même mapping
   - Noms de variables custom ignorés

2. **Pas de détection automatique**
   - Ne lit pas `data.acd` de la voiture
   - Ne parse pas `suspensions.ini`

3. **Aéro non gérée**
   - Pas de mapping pour `[WING_0]`, `[WING_1]`, etc.
   - Aileron non modifiable

**Exemple concret:**

**Porsche GT3 R Kunos:**
```ini
[PRESSURE_LF]
VALUE=26
[CAMBER_LF]
VALUE=-35
```
✅ Fonctionne (mapping connu)

**Mod GT3 Custom:**
```ini
[TYRE_PRESSURE_0]  # ❌ Nom différent
VALUE=26
[CAMBER_ANGLE_FL]  # ❌ Nom différent
VALUE=-35
[WING_REAR_0]      # ❌ Pas mappé
VALUE=5
```
❌ Modifications ignorées

---

### **B. Détection des Paramètres Disponibles**

**Méthode actuelle:**
```python
# setup_writer.py ligne 113-157
def _read_existing_car_setup(car_id):
    """
    Lit un setup existant (last.ini) pour détecter
    les paramètres disponibles.
    """
    # 1. Cherche last.ini dans generic/
    # 2. Parse tous les [PARAM] VALUE=X
    # 3. Retourne dict {param: value}
```

**✅ AVANTAGE:**
- Détecte automatiquement les paramètres disponibles
- S'adapte à chaque voiture

**❌ LIMITATION:**
- Nécessite un setup existant (last.ini)
- Si première utilisation → Pas de référence
- Ne lit PAS `data.acd` (fichiers source voiture)

**Ce qui devrait être fait:**

**Option 1: Parser data.acd**
```python
# Lire suspensions.ini depuis data.acd
import zipfile

def read_car_data(car_id):
    acd_path = f"content/cars/{car_id}/data.acd"
    
    with zipfile.ZipFile(acd_path) as z:
        # Lire suspensions.ini
        susp = z.read("suspensions.ini")
        # Parser [FRONT] SPRINGS=...
        
        # Lire tyres.ini
        tyres = z.read("tyres.ini")
        # Parser [FRONT] PRESSURE_IDEAL=...
```
❌ Non implémenté

**Option 2: Base de données par voiture**
```json
{
  "ks_porsche_911_gt3_r_2016": {
    "pressure": "PRESSURE_LF",
    "camber": "CAMBER_LF",
    "wing_rear": "WING_0"
  },
  "mod_gt3_custom": {
    "pressure": "TYRE_PRESSURE_0",
    "camber": "CAMBER_ANGLE_FL",
    "wing_rear": "WING_REAR_0"
  }
}
```
❌ Non implémenté

---

## 📐 3. CONVERSION PHYSIQUE ↔ CLICKS

### **A. Gestion des Steps**

**Problème:**
```
Calcul physique: k_spring = 154,687 N/m
AC setup: [SPRING_RATE_LF] VALUE=10 (click index)

Comment convertir 154,687 N/m → Click 10 ?
```

**Système actuel:**

**Détection Click-based vs Absolute:**
```python
# setup_engine.py ligne 682-690
def _is_click_based_setup(setup):
    """
    Détecte si setup utilise clicks (race) ou valeurs absolues (street).
    """
    spring_rate = setup.get_value("SUSPENSION", "SPRING_RATE_LF")
    
    if spring_rate < 1000:
        return True  # Click-based (1-30)
    else:
        return False  # Absolute (40000-200000 N/m)
```

**Conversion dans setup_writer.py:**
```python
# ligne 325-380
def _convert_value_for_ac(param_name, our_value, existing_value):
    """
    Convertit notre valeur physique en index AC.
    """
    
    # Pression: Direct (PSI)
    if "PRESSURE" in param_name:
        return int(round(our_value))  # 26.5 → 26
    
    # Camber: Degrés × 10
    if "CAMBER" in param_name:
        return int(round(our_value * 10))  # -3.5° → -35
    
    # Toe: Degrés × 100 ou × 10 (détection auto)
    if "TOE" in param_name:
        if abs(existing_value) > 50:
            return int(round(our_value * 100))
        else:
            return int(round(our_value * 10))
    
    # Dampers: ❌ PROBLÈME ICI
    if "DAMP" in param_name:
        if our_value > 100:
            return int(round(our_value / 500))  # Heuristique
        return int(round(our_value))
    
    # ARB: N/mm ou index (détection auto)
    if "ARB" in param_name:
        if existing_value > 1000:
            return int(round(our_value * 1000))
        return int(round(our_value))
```

**❌ PROBLÈMES IDENTIFIÉS:**

**1. Springs (Ressorts):**
```python
# V2 calcule: k_spring = 154,687 N/m
# Conversion actuelle: AUCUNE pour springs!

# setup_writer.py ne gère PAS SPRING_RATE
# → Valeur physique écrite directement
# → AC rejette si > max click
```

**2. Dampers (Amortisseurs):**
```python
# V2 calcule: c = 2100 N/m/s
# Conversion: c / 500 = 4.2 → Click 4

# ❌ Heuristique arbitraire
# Devrait lire steps depuis suspensions.ini
```

**3. Pas de validation steps:**
```python
# Si voiture permet clicks 0-15
# Et on écrit VALUE=20
# → AC remet à défaut (souvent click 7-8)
```

---

### **B. Clamping (Limites)**

**Système actuel:**
```python
# setup_engine.py ligne 377-450
VALUE_LIMITS = {
    "TYRES": {
        "PRESSURE_LF": (20.0, 35.0),
        "PRESSURE_RF": (20.0, 35.0),
        # ...
    },
    "ALIGNMENT": {
        "CAMBER_LF": (-8.0, 0.0),
        "CAMBER_RF": (-8.0, 0.0),
        # ...
    }
}

# ligne 1093-1127
def _clamp_values(setup):
    """
    Clamp toutes les valeurs dans les limites.
    """
    for section, limits in VALUE_LIMITS.items():
        for param, (min_val, max_val) in limits.items():
            current = setup.get_value(section, param)
            if current is not None:
                clamped = max(min_val, min(max_val, current))
                setup.set_value(section, param, clamped)
```

**✅ AVANTAGE:**
- Valeurs toujours dans limites génériques AC

**❌ LIMITATION:**
- Limites FIXES pour toutes les voitures
- Ne lit PAS les limites spécifiques de chaque voiture

**Exemple problème:**

**Calcul V2:**
```python
camber_front = -4.0°  # Cible GT3
```

**Voiture A (GT3 Kunos):**
```ini
# suspensions.ini
[FRONT]
CAMBER_MIN=-5.0
CAMBER_MAX=-1.0
```
✅ -4.0° accepté

**Voiture B (Mod street):**
```ini
# suspensions.ini
[FRONT]
CAMBER_MIN=-3.5
CAMBER_MAX=0.0
```
❌ -4.0° rejeté → AC remet -3.5°

**Solution idéale:**
```python
def read_car_limits(car_id):
    """Lit limites depuis data.acd"""
    limits = parse_suspensions_ini(car_id)
    return {
        "camber_min": limits["CAMBER_MIN"],
        "camber_max": limits["CAMBER_MAX"],
        # ...
    }

def clamp_to_car_limits(setup, car_id):
    """Clamp selon limites spécifiques voiture"""
    limits = read_car_limits(car_id)
    # Clamp avec limites réelles
```
❌ Non implémenté

---

## 📊 4. SENSIBILITÉ DES SLIDERS - L'UI

### **A. Multiplicateurs d'Impact**

**Sliders utilisateur (6 au total):**
```python
# models/driver_profile.py
class DriverProfile:
    rotation: float = 0.5      # 0.0 → 1.0
    slide: float = 0.5         # 0.0 → 1.0
    aggression: float = 0.5    # 0.0 → 1.0
    drift: float = 0.0         # 0.0 → 1.0
    performance: float = 0.5   # 0.0 → 1.0
    # + 1 slider "Sous-virage" dans UI
```

**Impact actuel (DOUBLÉ en V2):**

**1. Rotation (0→1):**
```python
# setup_engine.py ligne 934-946
strength = (rotation - 0.5) * 2  # -1.0 → +1.0

# Toe arrière
toe_rear += strength × 0.4°  # Max ±0.4°

# ARB arrière
arb_rear × (1 + strength × 0.3)  # Max ±30%

# Diff coast
diff_coast += strength × 15%  # Max ±15%
```

**Exemple concret:**
```
Rotation = 0.0 (sous-virage)
  → toe_rear = base + (-0.5 × 2) × 0.4° = base - 0.4°
  → arb_rear × 0.7 (-30%)
  → diff_coast - 15%

Rotation = 1.0 (survirage)
  → toe_rear = base + (+0.5 × 2) × 0.4° = base + 0.4°
  → arb_rear × 1.3 (+30%)
  → diff_coast + 15%
```

**2. Slide (0→1):**
```python
# ligne 955-971
strength = (slide - 0.5) * 2

# Toe avant
toe_front += strength × 0.3°  # Max ±0.3°

# Camber arrière
camber_rear += strength × -1.0°  # Max ±1.0°

# Diff power
diff_power += strength × 20%  # Max ±20%
```

**3. Aggression (0→1):**
```python
# ligne 980-992
strength = aggression

# Springs
springs × (1 + strength × 0.25)  # Max +25%

# Ride height
ride_height -= strength × 10mm  # Max -10mm

# Brake power
brake_power × (1 + strength × 0.2)  # Max +20%

# Damping
damping × (1 + strength × 0.3)  # Max +30%
```

**4. Drift (0→1):**
```python
# ligne 1002-1009
# Diff très lockant
diff_power += drift × 50%  # Max +50%
diff_coast += drift × 40%  # Max +40%

# Brake bias avant
brake_bias += drift × 5%  # Max +5%

# Camber arrière réduit
camber_rear += drift × 1.5°  # Max +1.5° (moins négatif)
```

**5. Performance (0→1):**
```python
# ligne 1018-1028
# Damping raide
damping × (1 + performance × 0.4)  # Max +40%

# Ride height bas
ride_height -= performance × 8mm  # Max -8mm
```

---

### **B. Différence Street vs GT3**

**Détection automatique:**
```python
# setup_engine.py ligne 682-690
is_click_based = spring_rate < 1000

# Si click-based (GT3/Race):
#   → Petits ajustements (précision)
# Si absolute (Street):
#   → Gros ajustements (impact visible)
```

**Exemples d'ajustements:**

**Suspension stiffness (behavior):**
```python
# ligne 699-711
if is_click_based:  # GT3
    adjustment = behavior.suspension_stiffness × 2  # ±2 clicks
else:  # Street
    adjustment = behavior.suspension_stiffness × 10000  # ±10k N/m
```

**Camber (behavior):**
```python
# ligne 768-778
if is_click_based:  # GT3
    adjustment = behavior.camber_front × -0.3°  # ±0.3°
else:  # Street
    adjustment = behavior.camber_front × -1.0°  # ±1.0°
```

**Toe (behavior):**
```python
# ligne 781-791
if is_click_based:  # GT3
    adjustment = behavior.toe_rear × 0.05°  # ±0.05°
else:  # Street
    adjustment = behavior.toe_rear × 0.15°  # ±0.15°
```

**Différentiel (behavior):**
```python
# ligne 752-765
if is_click_based:  # GT3
    adjustment = behavior.diff_power × 10%  # ±10%
else:  # Street
    adjustment = behavior.diff_power × 25%  # ±25%
```

**✅ CONCLUSION:**
- GT3: Ajustements fins (±0.3°, ±2 clicks)
- Street: Ajustements larges (±1.0°, ±10k N/m)
- Impact **2-3x plus fort** pour street cars

---

### **C. Interdépendance des Paramètres**

**Slider "Appui" (Aéro):**

**❌ NON IMPLÉMENTÉ ACTUELLEMENT**

Le système ne modifie PAS:
- Aileron avant/arrière
- Ride height pour compenser rake
- Balance aéro

**Ce qui devrait être fait:**
```python
def apply_aero_slider(setup, aero_level):
    """
    aero_level: 0.0 (low downforce) → 1.0 (high downforce)
    """
    # Aileron arrière
    wing_rear = 0 + aero_level × 10  # 0 → 10 clicks
    
    # Aileron avant (balance 50%)
    wing_front = wing_rear × 0.5
    
    # Compenser rake (plus d'appui = plus bas)
    ride_height_front -= aero_level × 5mm
    ride_height_rear -= aero_level × 3mm  # Maintenir rake
    
    # Springs plus raides (supporter appui)
    springs × (1 + aero_level × 0.15)
```

**Autres interdépendances manquantes:**

**1. Rotation ↔ Brake Bias:**
```python
# Si rotation élevée (survirage)
# → Devrait réduire brake bias avant
# ❌ Non implémenté
```

**2. Aggression ↔ Fuel:**
```python
# Si aggression élevée (sprint)
# → Devrait réduire fuel (moins de poids)
# ❌ Non implémenté
```

**3. Drift ↔ Suspension:**
```python
# Si drift élevé
# → Devrait assouplir suspension arrière
# ❌ Partiellement implémenté (seulement diff + camber)
```

---

## 🧠 5. SYSTÈME ADAPTATIF - DEBUG LOGGING

### **A. Logs d'Exportation Actuels**

**❌ PAS DE DEBUG LOG DÉTAILLÉ**

Actuellement:
```python
# setup_writer.py ligne 104-108
with open(file_path, "w", encoding="utf-8") as f:
    f.write(ini_content)

return True, f"Setup saved: {file_path}", file_path
```

Pas de log de:
- Valeurs calculées vs valeurs écrites
- Conversions appliquées
- Paramètres ignorés
- Clamping effectué

---

### **B. Système de Debug Logging à Implémenter**

**Proposition:**

```python
class SetupDebugLogger:
    """
    Logger détaillé pour debug setup generation.
    """
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.entries = []
    
    def log_calculation(self, param, calculated_value, unit):
        """Log valeur calculée par physique."""
        self.entries.append({
            "stage": "calculation",
            "param": param,
            "value": calculated_value,
            "unit": unit,
            "timestamp": datetime.now()
        })
    
    def log_conversion(self, param, from_value, to_value, reason):
        """Log conversion physique → AC."""
        self.entries.append({
            "stage": "conversion",
            "param": param,
            "from": from_value,
            "to": to_value,
            "reason": reason
        })
    
    def log_clamp(self, param, original, clamped, limit):
        """Log clamping."""
        self.entries.append({
            "stage": "clamp",
            "param": param,
            "original": original,
            "clamped": clamped,
            "limit": limit
        })
    
    def log_ignored(self, param, reason):
        """Log paramètre ignoré."""
        self.entries.append({
            "stage": "ignored",
            "param": param,
            "reason": reason
        })
    
    def export(self):
        """Export log complet."""
        with open(self.log_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("SETUP GENERATION DEBUG LOG\n")
            f.write("=" * 80 + "\n\n")
            
            for entry in self.entries:
                if entry["stage"] == "calculation":
                    f.write(f"[CALC] {entry['param']}: "
                           f"{entry['value']:.2f} {entry['unit']}\n")
                
                elif entry["stage"] == "conversion":
                    f.write(f"[CONV] {entry['param']}: "
                           f"{entry['from']:.2f} → {entry['to']} "
                           f"({entry['reason']})\n")
                
                elif entry["stage"] == "clamp":
                    f.write(f"[CLAMP] {entry['param']}: "
                           f"{entry['original']:.2f} → {entry['clamped']:.2f} "
                           f"(limit: {entry['limit']})\n")
                
                elif entry["stage"] == "ignored":
                    f.write(f"[IGNORE] {entry['param']}: "
                           f"{entry['reason']}\n")
                
                f.write("\n")
```

**Utilisation:**
```python
# Dans generate_setup()
logger = SetupDebugLogger("debug_setup.log")

# Calcul physique
k_spring = calculate_spring_rate(freq, mass)
logger.log_calculation("SPRING_RATE_LF", k_spring, "N/m")

# Correction MR
k_corrected = k_spring / (MR ** 2)
logger.log_conversion("SPRING_RATE_LF", k_spring, k_corrected, 
                     f"Motion ratio {MR}")

# Conversion clicks
click_value = convert_to_clicks(k_corrected, car_data)
logger.log_conversion("SPRING_RATE_LF", k_corrected, click_value,
                     "N/m to click index")

# Clamping
if click_value > max_clicks:
    logger.log_clamp("SPRING_RATE_LF", click_value, max_clicks,
                    f"max={max_clicks}")
    click_value = max_clicks

# Export
logger.export()
```

**Exemple de log généré:**
```
================================================================================
SETUP GENERATION DEBUG LOG
================================================================================

[CALC] SPRING_RATE_LF: 93000.00 N/m

[CONV] SPRING_RATE_LF: 93000.00 → 114815.00 (Motion ratio 0.9)

[CONV] SPRING_RATE_LF: 114815.00 → 12 (N/m to click index)

[CLAMP] SPRING_RATE_LF: 12.00 → 10.00 (limit: max=10)

[CALC] PRESSURE_LF: 27.50 PSI

[CONV] PRESSURE_LF: 27.50 → 25.20 (Cold for hot target, road_temp=22°C)

[CONV] PRESSURE_LF: 25.20 → 25 (PSI to integer)

[CALC] CAMBER_LF: -4.00 deg

[CONV] CAMBER_LF: -4.00 → -40 (degrees × 10)

[CLAMP] CAMBER_LF: -40.00 → -35.00 (limit: max=-35)

[IGNORE] WING_REAR: Parameter not found in car setup

[IGNORE] DAMP_FAST_BUMP_LF: Parameter not found in car setup
```

---

## 📋 RÉSUMÉ DES PROBLÈMES IDENTIFIÉS

### **🔴 CRITIQUES (Bloquants):**

1. **Rechargement setup**
   - AC ne relit pas automatiquement
   - Utilisateur doit charger manuellement
   - Pas de script Lua/CM

2. **Mapping variables mods**
   - Mapping fixe Kunos uniquement
   - Mods avec noms custom ignorés
   - Aileron non géré

3. **Conversion physique → clicks**
   - Pas de lecture steps depuis data.acd
   - Heuristiques arbitraires
   - Springs non convertis

### **🟡 IMPORTANTS (Limitants):**

4. **Limites par voiture**
   - Limites fixes génériques
   - Ne lit pas limites spécifiques
   - Clamping approximatif

5. **Debug logging**
   - Pas de log détaillé
   - Impossible de tracer conversions
   - Pas de diagnostic erreurs

### **🟢 MINEURS (Améliorations):**

6. **Interdépendances**
   - Slider aéro non implémenté
   - Pas de compensation rake
   - Manque liens rotation↔brake

7. **Encodage fichiers**
   - UTF-8 uniquement
   - Peut poser problème mods anciens
   - Pas de détection auto

---

## 🔧 PLAN D'ACTION RECOMMANDÉ

### **Phase 1: Debug & Diagnostic (Priorité 1)**
```
✅ Implémenter SetupDebugLogger
✅ Logger toutes conversions
✅ Identifier paramètres ignorés
→ Permet de diagnostiquer pourquoi aileron ne bouge pas
```

### **Phase 2: Mapping Variables (Priorité 1)**
```
✅ Créer base données mapping par voiture
✅ Parser last.ini pour détecter noms
✅ Ajouter support [WING_0], [WING_1], etc.
→ Résout problème mods
```

### **Phase 3: Conversion Clicks (Priorité 2)**
```
✅ Lire steps depuis suspensions.ini
✅ Convertir N/m → clicks correctement
✅ Valider limites par voiture
→ Améliore précision
```

### **Phase 4: Rechargement Auto (Priorité 3)**
```
⚠️ Nécessite Content Manager + CSP
✅ Script Lua pour reload auto
✅ Ou message clair utilisateur
→ Améliore UX
```

---

## 📞 QUESTIONS POUR L'INGÉNIEUR

**Sur la conversion clicks:**
1. As-tu des données réelles de steps par voiture ?
2. Quelle est la formule exacte N/m → click pour GT3 ?

**Sur les limites:**
3. Devrions-nous parser data.acd systématiquement ?
4. Ou créer une base de données manuelle ?

**Sur l'aéro:**
5. Quelle balance aéro avant/arrière pour GT3 ?
6. Comment compenser rake avec downforce ?

**Sur les priorités:**
7. Quel problème résoudre en premier ?
8. Debug logging suffit pour diagnostiquer ?

---

**Ce document identifie tous les problèmes techniques actuels et propose des solutions concrètes.** 🏁
