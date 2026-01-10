"""
Race Engineer Advisor V1.0
Provides real, accurate driving advice based on:
1. Car characteristics (power, weight, drivetrain, turbo)
2. Track configuration (touge type, corners, elevation)
3. Generated setup values (diff, brakes, suspension, etc.)

All advice is based on real racing physics and driving techniques.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum

from models.car import Car
from models.track import Track
from models.setup import Setup


# ═══════════════════════════════════════════════════════════════════════════
# ADVICE CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

class AdviceType(Enum):
    STRENGTH = "strength"      # Point fort
    WARNING = "warning"        # Point faible / danger
    STRATEGY = "strategy"      # Stratégie de course
    SETUP = "setup"            # Lié au setup injecté
    OVERTAKE = "overtake"      # Conseil de dépassement


@dataclass
class Advice:
    """A single piece of driving advice."""
    type: AdviceType
    title: str
    description: str
    priority: int = 1  # 1 = haute, 2 = moyenne, 3 = basse
    icon: str = "💡"


# ═══════════════════════════════════════════════════════════════════════════
# CAR CHARACTERISTICS ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CarCharacteristics:
    """Analyzed car characteristics."""
    power_hp: int = 0
    weight_kg: int = 0
    drivetrain: str = "RWD"  # RWD, FWD, AWD
    power_to_weight: float = 0.0  # kg per hp
    is_turbo: bool = False
    is_lightweight: bool = False  # < 1100kg
    is_powerful: bool = False     # > 350hp
    is_heavy: bool = False        # > 1500kg
    category: str = "street"      # street, drift, gt, formula


class CarAnalyzer:
    """Analyzes car characteristics from AC data."""
    
    # Known turbo cars (partial list - expand as needed)
    TURBO_KEYWORDS = [
        "turbo", "gt-r", "gtr", "supra", "rx7", "rx-7", "evo", "wrx", "sti",
        "rs6", "m3_e30", "m5", "rs4", "rs3", "amg", "911_turbo", "918",
        "f40", "288", "delta", "cosworth", "sierra", "escort_rs"
    ]
    
    # Known NA high-rev cars
    NA_HIGHREV_KEYWORDS = [
        "s2000", "nsx", "vtec", "ae86", "miata", "mx5", "mx-5", "86", "brz",
        "gt86", "elise", "exige", "seven", "caterham", "atom", "f1", "v10", "v12"
    ]
    
    def analyze(self, car: Car) -> CarCharacteristics:
        """Analyze car and return characteristics."""
        chars = CarCharacteristics()
        
        # Basic data
        chars.power_hp = car.power_hp if car.power_hp > 0 else self._estimate_power(car)
        chars.weight_kg = car.weight_kg if car.weight_kg > 0 else self._estimate_weight(car)
        chars.drivetrain = car.drivetrain.upper() if car.drivetrain else "RWD"
        
        # Calculated values
        if chars.power_hp > 0:
            chars.power_to_weight = chars.weight_kg / chars.power_hp
        
        # Flags
        chars.is_turbo = self._detect_turbo(car)
        chars.is_lightweight = chars.weight_kg < 1100
        chars.is_powerful = chars.power_hp > 350
        chars.is_heavy = chars.weight_kg > 1500
        
        # Category
        chars.category = self._detect_category(car)
        
        return chars
    
    def _estimate_power(self, car: Car) -> int:
        """Estimate power from car name if not provided."""
        name_lower = car.car_id.lower()
        
        # GT3/GT cars
        if "gt3" in name_lower or "gt2" in name_lower:
            return 550
        if "gt4" in name_lower:
            return 400
        
        # Formula
        if "f1" in name_lower or "formula" in name_lower:
            return 900
        
        # Known cars
        if "ae86" in name_lower:
            return 130
        if "gtr" in name_lower or "gt-r" in name_lower:
            return 550
        if "supra" in name_lower:
            return 320
        if "rx7" in name_lower or "rx-7" in name_lower:
            return 280
        if "evo" in name_lower:
            return 300
        if "m3" in name_lower:
            return 340
        if "911" in name_lower:
            return 380
        
        # Default
        return 250
    
    def _estimate_weight(self, car: Car) -> int:
        """Estimate weight from car name if not provided."""
        name_lower = car.car_id.lower()
        
        # Lightweight
        if "ae86" in name_lower or "miata" in name_lower or "mx5" in name_lower:
            return 950
        if "elise" in name_lower or "exige" in name_lower:
            return 900
        if "s2000" in name_lower:
            return 1250
        
        # GT cars
        if "gt3" in name_lower:
            return 1300
        if "gtr" in name_lower or "gt-r" in name_lower:
            return 1750
        
        # Default
        return 1350
    
    def _detect_turbo(self, car: Car) -> bool:
        """Detect if car is turbocharged."""
        name_lower = car.car_id.lower() + " " + car.name.lower()
        return any(kw in name_lower for kw in self.TURBO_KEYWORDS)
    
    def _detect_category(self, car: Car) -> str:
        """Detect car category."""
        name_lower = car.car_id.lower()
        
        if "drift" in name_lower:
            return "drift"
        if "gt3" in name_lower or "gt2" in name_lower or "gte" in name_lower:
            return "gt"
        if "f1" in name_lower or "formula" in name_lower:
            return "formula"
        if "lmp" in name_lower or "prototype" in name_lower:
            return "prototype"
        
        return "street"


# ═══════════════════════════════════════════════════════════════════════════
# TRACK KNOWLEDGE DATABASE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TrackKnowledge:
    """Knowledge about a specific track."""
    track_id: str
    name: str
    type: str  # touge_downhill, touge_uphill, circuit, drift
    
    # Characteristics
    has_tight_hairpins: bool = False
    has_high_speed_sections: bool = False
    has_elevation_change: bool = False
    is_narrow: bool = False
    has_cliff_edges: bool = False  # Touge danger
    
    # Overtaking zones (description)
    overtake_zones: List[str] = field(default_factory=list)
    danger_zones: List[str] = field(default_factory=list)
    
    # Key corners advice
    key_corners: List[str] = field(default_factory=list)


class TrackDatabase:
    """Database of known tracks with specific advice."""
    
    TRACKS: Dict[str, TrackKnowledge] = {
        # ═══════════════════════════════════════════════════════════════
        # AKINA (Initial D)
        # ═══════════════════════════════════════════════════════════════
        "akina": TrackKnowledge(
            track_id="akina",
            name="Akina (Mt. Haruna)",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=True,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Longue ligne droite après les 5 virages consécutifs",
                "Sortie du tunnel - 200m de ligne droite",
                "Section rapide avant les épingles finales"
            ],
            danger_zones=[
                "Épingles serrées - pas de dépassement ici",
                "Virage aveugle après le tunnel",
                "Dernière épingle avant la ligne d'arrivée"
            ],
            key_corners=[
                "5 virages consécutifs : garde ta vitesse, pas de freinage brusque",
                "Épingle du milieu : freine TÔT, la pente accélère la voiture",
                "Sortie tunnel : attention au changement de grip (humidité)"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # USUI
        # ═══════════════════════════════════════════════════════════════
        "usui": TrackKnowledge(
            track_id="usui",
            name="Usui Pass",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=False,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Rare ! Seulement dans les sections plus larges",
                "Après une épingle si tu as une meilleure sortie"
            ],
            danger_zones=[
                "Presque tout le circuit - très technique",
                "Enchaînements serrés sans visibilité"
            ],
            key_corners=[
                "Circuit ultra-technique : la régularité bat la vitesse pure",
                "Épingles constantes : trouve ton rythme de freinage",
                "Pas de place pour l'erreur - reste concentré"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # IROHAZAKA
        # ═══════════════════════════════════════════════════════════════
        "irohazaka": TrackKnowledge(
            track_id="irohazaka",
            name="Irohazaka",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=False,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Très difficile - circuit d'épingles",
                "Seule option : meilleure sortie d'épingle → attaque sur la courte ligne droite"
            ],
            danger_zones=[
                "Chaque épingle - le mur est proche",
                "Transitions entre épingles - facile de perdre l'arrière"
            ],
            key_corners=[
                "48 épingles ! Économise tes freins",
                "Technique > Puissance ici",
                "Utilise le frein moteur en descente"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # HARUNA (Mt. Haruna / Akina original)
        # ═══════════════════════════════════════════════════════════════
        "haruna": TrackKnowledge(
            track_id="haruna",
            name="Mt. Haruna",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=True,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Sections rapides entre les épingles",
                "Ligne droite principale"
            ],
            danger_zones=[
                "Épingles avec dévers négatif",
                "Virages aveugles en descente"
            ],
            key_corners=[
                "Similaire à Akina - même approche",
                "Freinage anticipé en descente obligatoire"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # HAPPOGAHARA
        # ═══════════════════════════════════════════════════════════════
        "happogahara": TrackKnowledge(
            track_id="happogahara",
            name="Happogahara",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=True,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Longue ligne droite du milieu",
                "Section rapide avant le pont"
            ],
            danger_zones=[
                "Pont étroit - pas de dépassement",
                "Épingles en aveugle"
            ],
            key_corners=[
                "Section rapide : garde ta vitesse, les virages s'enchaînent",
                "Pont : reste au centre, les bords sont piégeux"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # SADAMINE
        # ═══════════════════════════════════════════════════════════════
        "sadamine": TrackKnowledge(
            track_id="sadamine",
            name="Sadamine Pass",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=True,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Sections fluides entre les épingles",
                "Sortie des virages rapides"
            ],
            danger_zones=[
                "Épingles serrées avec mur intérieur",
                "Changements de direction rapides"
            ],
            key_corners=[
                "Mix technique/rapide : adapte ton style",
                "Les sections rapides récompensent le courage"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # AKAGI (Ek_Akagi mod)
        # ═══════════════════════════════════════════════════════════════
        "akagi": TrackKnowledge(
            track_id="ek_akagi",
            name="Mt. Akagi",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=True,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Longue ligne droite après la série de virages",
                "Section rapide avant les épingles",
                "Sortie des virages moyens si meilleure traction"
            ],
            danger_zones=[
                "Épingles serrées - garde ta ligne",
                "Virages en aveugle avec dénivelé",
                "Bord de route sans barrière"
            ],
            key_corners=[
                "Série de virages rapides : garde le rythme, pas de freinage brusque",
                "Épingles : freine tôt, la descente accélère la voiture",
                "Utilise le frein moteur pour préserver les freins"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # MYOGI
        # ═══════════════════════════════════════════════════════════════
        "myogi": TrackKnowledge(
            track_id="myogi",
            name="Myogi",
            type="touge_downhill",
            has_tight_hairpins=True,
            has_high_speed_sections=True,
            has_elevation_change=True,
            is_narrow=True,
            has_cliff_edges=True,
            overtake_zones=[
                "Ligne droite principale",
                "Sections fluides"
            ],
            danger_zones=[
                "Virages en aveugle",
                "Épingles avec dénivelé"
            ],
            key_corners=[
                "Rythme régulier > attaques ponctuelles",
                "La descente accélère la voiture - anticipe"
            ]
        ),
        
        # ═══════════════════════════════════════════════════════════════
        # SHUTOKO (Highway)
        # ═══════════════════════════════════════════════════════════════
        "shutoko": TrackKnowledge(
            track_id="shutoko",
            name="Shutoko Expressway",
            type="highway",
            has_tight_hairpins=False,
            has_high_speed_sections=True,
            has_elevation_change=False,
            is_narrow=False,
            has_cliff_edges=False,
            overtake_zones=[
                "Partout si tu as la puissance",
                "Lignes droites entre les courbes",
                "Intérieur des grandes courbes"
            ],
            danger_zones=[
                "Murs de béton des deux côtés",
                "Trafic (si activé)",
                "Jonctions avec changement de voie"
            ],
            key_corners=[
                "Grandes courbes à haute vitesse : reste smooth",
                "Puissance = roi ici",
                "Aérodynamique compte beaucoup à 250+ km/h"
            ]
        ),
    }
    
    def get_track_knowledge(self, track: Track) -> Optional[TrackKnowledge]:
        """Get knowledge for a track, matching by keywords."""
        track_lower = track.track_id.lower() + " " + track.name.lower()
        
        for key, knowledge in self.TRACKS.items():
            if key in track_lower:
                return knowledge
        
        # Try to detect type from name
        return self._create_generic_knowledge(track)
    
    def _create_generic_knowledge(self, track: Track) -> TrackKnowledge:
        """Create generic knowledge based on track name."""
        track_lower = track.track_id.lower() + " " + track.name.lower()
        
        # Detect type
        if any(kw in track_lower for kw in ["touge", "pass", "mountain", "downhill", "uphill"]):
            track_type = "touge_downhill" if "downhill" in track_lower else "touge"
        elif any(kw in track_lower for kw in ["drift", "ebisu", "meihan"]):
            track_type = "drift"
        elif any(kw in track_lower for kw in ["shutoko", "highway", "wangan", "expressway"]):
            track_type = "highway"
        else:
            track_type = "circuit"
        
        return TrackKnowledge(
            track_id=track.track_id,
            name=track.name,
            type=track_type,
            has_tight_hairpins="touge" in track_type,
            has_high_speed_sections=track_type in ["highway", "circuit"],
            has_elevation_change="touge" in track_type,
            is_narrow="touge" in track_type,
            has_cliff_edges="touge" in track_type,
            overtake_zones=["Analyse le circuit pour trouver les zones de dépassement"],
            danger_zones=["Reste prudent dans les zones inconnues"],
            key_corners=["Apprends le circuit tour par tour"]
        )


# ═══════════════════════════════════════════════════════════════════════════
# SETUP ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class SetupAnalyzer:
    """Analyzes setup values and generates driving advice."""
    
    def analyze(self, setup: Setup) -> List[Advice]:
        """Analyze setup and return advice list."""
        advice_list = []
        
        # ═══════════════════════════════════════════════════════════════
        # DIFFERENTIAL ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 50)
        diff_coast = setup.get_value("DIFFERENTIAL", "COAST", 30)
        
        if diff_power is not None:
            if diff_power > 75:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Différentiel serré (Power)",
                    description=f"Diff à {diff_power:.0f}% : l'arrière va pousser fort en sortie de virage. "
                               f"Attends d'être DROIT avant d'accélérer à fond, sinon survirage garanti.",
                    priority=1,
                    icon="⚙️"
                ))
            elif diff_power > 60:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Différentiel équilibré",
                    description=f"Diff à {diff_power:.0f}% : bon compromis traction/contrôle. "
                               f"Tu peux attaquer en sortie mais reste progressif sur l'accélérateur.",
                    priority=2,
                    icon="⚙️"
                ))
            elif diff_power < 40:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Différentiel ouvert",
                    description=f"Diff à {diff_power:.0f}% : facile à contrôler mais moins de traction. "
                               f"Accélère progressivement, la roue intérieure peut patiner.",
                    priority=2,
                    icon="⚙️"
                ))
        
        if diff_coast is not None and diff_coast > 60:
            advice_list.append(Advice(
                type=AdviceType.SETUP,
                title="Diff Coast élevé",
                description=f"Coast à {diff_coast:.0f}% : l'arrière va se bloquer au lever de pied. "
                           f"Utilise ça pour initier les drifts, mais attention au snap oversteer !",
                priority=1,
                icon="⚠️"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # BRAKE BIAS ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        brake_bias = setup.get_value("BRAKES", "FRONT_BIAS", None)
        if brake_bias is None:
            brake_bias = setup.get_value("BRAKES", "BIAS", 58)
        
        if brake_bias is not None:
            if brake_bias > 62:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Freinage avant dominant",
                    description=f"Bias à {brake_bias:.0f}% avant : risque de blocage des roues avant. "
                               f"Freine UNIQUEMENT en ligne droite. En courbe = sous-virage immédiat.",
                    priority=1,
                    icon="🛑"
                ))
            elif brake_bias < 52:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Freinage arrière fort",
                    description=f"Bias à {brake_bias:.0f}% avant : l'arrière peut décrocher au freinage. "
                               f"Parfait pour le trail-braking, mais dangereux en descente !",
                    priority=1,
                    icon="⚠️"
                ))
            else:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Freinage équilibré",
                    description=f"Bias à {brake_bias:.0f}% : setup neutre, la voiture reste stable au freinage. "
                               f"Tu peux freiner un peu en courbe si nécessaire.",
                    priority=3,
                    icon="✅"
                ))
        
        # ═══════════════════════════════════════════════════════════════
        # SUSPENSION / ARB ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        arb_front = setup.get_value("ARB", "FRONT", 5)
        arb_rear = setup.get_value("ARB", "REAR", 3)
        
        if arb_front is not None and arb_rear is not None:
            if arb_rear > arb_front:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="ARB arrière plus rigide",
                    description=f"ARB F:{arb_front:.0f} / R:{arb_rear:.0f} : la voiture va survier naturellement. "
                               f"Parfait pour le drift ! En grip, attention en entrée de virage.",
                    priority=2,
                    icon="🔄"
                ))
            elif arb_front > arb_rear + 3:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="ARB avant rigide",
                    description=f"ARB F:{arb_front:.0f} / R:{arb_rear:.0f} : tendance au sous-virage. "
                               f"Freine tôt et tourne, la voiture est stable mais moins vive.",
                    priority=2,
                    icon="🔄"
                ))
        
        # ═══════════════════════════════════════════════════════════════
        # CAMBER ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        camber_front = setup.get_value("ALIGNMENT", "CAMBER_LF", -3.0)
        
        if camber_front is not None:
            # Handle both degrees and degrees*10 format
            if abs(camber_front) > 10:
                camber_front = camber_front / 10  # Convert from AC format
            
            if camber_front < -4.0:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Camber agressif",
                    description=f"Camber à {camber_front:.1f}° : grip max en virage mais moins en ligne droite. "
                               f"Évite les gros freinages en courbe, le pneu travaille déjà beaucoup.",
                    priority=2,
                    icon="📐"
                ))
            elif camber_front > -2.0:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Camber conservateur",
                    description=f"Camber à {camber_front:.1f}° : stable au freinage, moins de grip en virage. "
                               f"Compense en freinant plus tôt et en étant smooth.",
                    priority=2,
                    icon="📐"
                ))
        
        # ═══════════════════════════════════════════════════════════════
        # TIRE PRESSURE ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        pressure_front = setup.get_value("TYRES", "PRESSURE_LF", 26)
        pressure_rear = setup.get_value("TYRES", "PRESSURE_LR", 26)
        
        if pressure_front is not None:
            if pressure_front < 24:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Pression basse",
                    description=f"Pneus à {pressure_front:.0f} PSI : grip max mais réponse lente. "
                               f"La voiture sera 'molle' en entrée de virage. Anticipe tes corrections.",
                    priority=2,
                    icon="🔵"
                ))
            elif pressure_front > 28:
                advice_list.append(Advice(
                    type=AdviceType.SETUP,
                    title="Pression élevée",
                    description=f"Pneus à {pressure_front:.0f} PSI : réponse vive mais moins de grip. "
                               f"La voiture sera nerveuse. Sois précis sur tes inputs.",
                    priority=2,
                    icon="🔴"
                ))
        
        return advice_list


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ADVISOR CLASS
# ═══════════════════════════════════════════════════════════════════════════

class RaceEngineerAdvisor:
    """
    Main advisor class that combines all analysis sources.
    Generates real, accurate driving advice.
    """
    
    def __init__(self):
        self.car_analyzer = CarAnalyzer()
        self.track_database = TrackDatabase()
        self.setup_analyzer = SetupAnalyzer()
    
    def generate_advice(
        self,
        car: Car,
        track: Track,
        setup: Optional[Setup] = None
    ) -> List[Advice]:
        """
        Generate complete advice list for car + track + setup combination.
        
        Returns advice sorted by priority (1 = highest).
        """
        all_advice: List[Advice] = []
        
        # 1. Analyze car characteristics
        car_chars = self.car_analyzer.analyze(car)
        all_advice.extend(self._generate_car_advice(car_chars))
        
        # 2. Get track knowledge
        track_knowledge = self.track_database.get_track_knowledge(track)
        if track_knowledge:
            all_advice.extend(self._generate_track_advice(track_knowledge, car_chars))
        
        # 3. Analyze setup (if provided)
        if setup:
            all_advice.extend(self.setup_analyzer.analyze(setup))
        
        # 4. Generate combined strategy advice
        all_advice.extend(self._generate_strategy_advice(car_chars, track_knowledge))
        
        # Sort by priority
        all_advice.sort(key=lambda a: a.priority)
        
        return all_advice
    
    def _generate_car_advice(self, chars: CarCharacteristics) -> List[Advice]:
        """Generate advice based on car characteristics."""
        advice_list = []
        
        # ═══════════════════════════════════════════════════════════════
        # DRIVETRAIN ADVICE
        # ═══════════════════════════════════════════════════════════════
        if chars.drivetrain == "RWD":
            advice_list.append(Advice(
                type=AdviceType.WARNING,
                title="Propulsion (RWD)",
                description="L'arrière peut décrocher en sortie de virage. "
                           "Dose l'accélérateur progressivement, surtout sur route froide.",
                priority=1,
                icon="⚠️"
            ))
            if chars.is_powerful:
                advice_list.append(Advice(
                    type=AdviceType.STRENGTH,
                    title="Puissance en sortie",
                    description=f"{chars.power_hp}ch aux roues arrière = accélération brutale. "
                               f"Ton avantage : les sorties de virage et les lignes droites.",
                    priority=1,
                    icon="💪"
                ))
        
        elif chars.drivetrain == "FWD":
            advice_list.append(Advice(
                type=AdviceType.WARNING,
                title="Traction (FWD)",
                description="Sous-virage probable en entrée si tu accélères trop tôt. "
                           "Technique : freine, tourne, PUIS accélère pour 'tirer' la voiture.",
                priority=1,
                icon="⚠️"
            ))
            advice_list.append(Advice(
                type=AdviceType.STRENGTH,
                title="Stabilité au freinage",
                description="L'avant est lourd = stable au freinage. "
                           "Tu peux freiner tard et en courbe sans perdre l'arrière.",
                priority=2,
                icon="💪"
            ))
        
        elif chars.drivetrain == "AWD":
            advice_list.append(Advice(
                type=AdviceType.STRENGTH,
                title="4 roues motrices (AWD)",
                description="Grip excellent en accélération. "
                           "Tu peux attaquer plus tôt en sortie de virage.",
                priority=1,
                icon="💪"
            ))
            if chars.is_heavy:
                advice_list.append(Advice(
                    type=AdviceType.WARNING,
                    title="Inertie élevée",
                    description=f"{chars.weight_kg}kg + AWD = voiture lourde. "
                               f"Anticipe les freinages, tu mets plus de temps à t'arrêter.",
                    priority=1,
                    icon="⚠️"
                ))
        
        # ═══════════════════════════════════════════════════════════════
        # TURBO ADVICE
        # ═══════════════════════════════════════════════════════════════
        if chars.is_turbo:
            advice_list.append(Advice(
                type=AdviceType.WARNING,
                title="Turbo lag",
                description="Délai avant que la puissance arrive. "
                           "En épingle, accélère AVANT l'apex pour avoir le boost en sortie.",
                priority=1,
                icon="🌀"
            ))
            advice_list.append(Advice(
                type=AdviceType.STRATEGY,
                title="Gestion du turbo",
                description="Garde les tours hauts entre les virages pour minimiser le lag. "
                           "Rétrograde tôt pour rester dans la zone de boost.",
                priority=2,
                icon="🎯"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # POWER TO WEIGHT ADVICE
        # ═══════════════════════════════════════════════════════════════
        if chars.power_to_weight < 4:
            advice_list.append(Advice(
                type=AdviceType.STRENGTH,
                title="Rapport poids/puissance excellent",
                description=f"{chars.power_to_weight:.1f} kg/ch : tu as plus de chevaux que de grip ! "
                           f"Gère la traction, c'est ta limite, pas la puissance.",
                priority=1,
                icon="🚀"
            ))
        elif chars.power_to_weight > 8:
            advice_list.append(Advice(
                type=AdviceType.STRATEGY,
                title="Voiture légère/peu puissante",
                description=f"{chars.power_to_weight:.1f} kg/ch : tu perds en ligne droite. "
                           f"Compense en gardant ta vitesse en virage. Ne freine pas trop !",
                priority=1,
                icon="🎯"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # WEIGHT ADVICE
        # ═══════════════════════════════════════════════════════════════
        if chars.is_lightweight:
            advice_list.append(Advice(
                type=AdviceType.STRENGTH,
                title="Voiture légère",
                description=f"{chars.weight_kg}kg : tu freines plus court que les autres. "
                           f"Freine plus tard, c'est ton avantage en dépassement.",
                priority=2,
                icon="💪"
            ))
        
        return advice_list
    
    def _generate_track_advice(
        self,
        track: TrackKnowledge,
        car_chars: CarCharacteristics
    ) -> List[Advice]:
        """Generate advice based on track knowledge."""
        advice_list = []
        
        # ═══════════════════════════════════════════════════════════════
        # TRACK TYPE SPECIFIC
        # ═══════════════════════════════════════════════════════════════
        if "touge" in track.type:
            if track.has_cliff_edges:
                advice_list.append(Advice(
                    type=AdviceType.WARNING,
                    title="Route de montagne - Falaises",
                    description="Pas de barrières de sécurité. Une erreur = chute mortelle. "
                               "Reste concentré, pas de prise de risque inutile.",
                    priority=1,
                    icon="☠️"
                ))
            
            if "downhill" in track.type:
                advice_list.append(Advice(
                    type=AdviceType.WARNING,
                    title="Descente - Freins sous pression",
                    description="La gravité accélère la voiture. Freine PLUS TÔT que tu ne le penses. "
                               "Tes freins vont chauffer, utilise le frein moteur.",
                    priority=1,
                    icon="🔥"
                ))
                
                if car_chars.is_powerful:
                    advice_list.append(Advice(
                        type=AdviceType.STRATEGY,
                        title="Puissance en descente",
                        description="Ta puissance est moins utile ici - tout le monde va vite en descente. "
                                   "Concentre-toi sur les freinages et les trajectoires.",
                        priority=2,
                        icon="🎯"
                    ))
        
        if track.type == "highway":
            advice_list.append(Advice(
                type=AdviceType.STRENGTH,
                title="Autoroute - Vitesse max",
                description="Puissance et aéro sont rois ici. "
                           "Les grandes courbes se prennent à fond si tu as le grip.",
                priority=1,
                icon="🏎️"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # OVERTAKING ZONES
        # ═══════════════════════════════════════════════════════════════
        if track.overtake_zones:
            zones_text = "\n• ".join(track.overtake_zones[:3])
            advice_list.append(Advice(
                type=AdviceType.OVERTAKE,
                title=f"Zones de dépassement - {track.name}",
                description=f"• {zones_text}",
                priority=1,
                icon="🏁"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # DANGER ZONES
        # ═══════════════════════════════════════════════════════════════
        if track.danger_zones:
            zones_text = "\n• ".join(track.danger_zones[:2])
            advice_list.append(Advice(
                type=AdviceType.WARNING,
                title="Zones dangereuses",
                description=f"• {zones_text}",
                priority=1,
                icon="⛔"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # KEY CORNERS
        # ═══════════════════════════════════════════════════════════════
        if track.key_corners:
            for i, corner in enumerate(track.key_corners[:2]):
                advice_list.append(Advice(
                    type=AdviceType.STRATEGY,
                    title=f"Conseil circuit #{i+1}",
                    description=corner,
                    priority=2,
                    icon="📍"
                ))
        
        return advice_list
    
    def _generate_strategy_advice(
        self,
        car_chars: CarCharacteristics,
        track: Optional[TrackKnowledge]
    ) -> List[Advice]:
        """Generate combined strategy advice."""
        advice_list = []
        
        # ═══════════════════════════════════════════════════════════════
        # OVERTAKING STRATEGY BASED ON CAR
        # ═══════════════════════════════════════════════════════════════
        if car_chars.is_powerful and car_chars.drivetrain == "RWD":
            advice_list.append(Advice(
                type=AdviceType.OVERTAKE,
                title="Stratégie de dépassement",
                description="Tes points forts : sortie de virage et ligne droite. "
                           "Colle l'adversaire en virage, puis attaque à l'accélération.",
                priority=1,
                icon="🎯"
            ))
        
        elif car_chars.is_lightweight:
            advice_list.append(Advice(
                type=AdviceType.OVERTAKE,
                title="Stratégie de dépassement",
                description="Ton avantage : le freinage. "
                           "Freine plus tard que l'adversaire dans les épingles.",
                priority=1,
                icon="🎯"
            ))
        
        elif car_chars.drivetrain == "AWD":
            advice_list.append(Advice(
                type=AdviceType.OVERTAKE,
                title="Stratégie de dépassement",
                description="Ton avantage : la traction. "
                           "Attaque dans les virages serrés où tu peux accélérer plus tôt.",
                priority=1,
                icon="🎯"
            ))
        
        # ═══════════════════════════════════════════════════════════════
        # TOUGE SPECIFIC STRATEGY
        # ═══════════════════════════════════════════════════════════════
        if track and "touge" in track.type:
            if car_chars.is_turbo:
                advice_list.append(Advice(
                    type=AdviceType.STRATEGY,
                    title="Turbo en touge",
                    description="Le turbo lag est ton ennemi en épingle. "
                               "Garde les tours hauts, rétrograde agressivement.",
                    priority=2,
                    icon="🌀"
                ))
            
            if car_chars.category == "drift":
                advice_list.append(Advice(
                    type=AdviceType.STRATEGY,
                    title="Drift car en touge",
                    description="Utilise le drift pour les épingles serrées. "
                               "En section rapide, reste en grip pour la vitesse.",
                    priority=2,
                    icon="🔄"
                ))
        
        return advice_list
    
    def get_advice_summary(
        self,
        car: Car,
        track: Track,
        setup: Optional[Setup] = None,
        max_items: int = 8
    ) -> str:
        """Get a formatted summary of advice for display."""
        advice_list = self.generate_advice(car, track, setup)
        
        if not advice_list:
            return "Aucun conseil disponible pour cette configuration."
        
        lines = []
        for advice in advice_list[:max_items]:
            lines.append(f"{advice.icon} **{advice.title}**")
            lines.append(f"   {advice.description}")
            lines.append("")
        
        return "\n".join(lines)
