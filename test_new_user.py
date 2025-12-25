"""
Test script to simulate a new user experience.
This will test the app as if it's the first time running it.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.user_settings import get_user_settings
from assetto.ac_detector import ACDetector
from assetto.ac_connector import ACConnector

def test_new_user_flow():
    """Simulate a new user starting the app for the first time."""
    
    print("=" * 60)
    print("SIMULATION: NOUVEL UTILISATEUR")
    print("=" * 60)
    print()
    
    # Step 1: Check if config exists
    settings = get_user_settings()
    config_path = settings._config_path
    
    print(f"1. Vérification du fichier de config:")
    print(f"   Chemin: {config_path}")
    print(f"   Existe: {config_path.exists()}")
    
    if config_path.exists():
        print(f"   ⚠️  Config trouvée - pas vraiment un nouvel utilisateur")
        saved_path = settings.get_ac_game_path()
        print(f"   Chemin AC sauvegardé: {saved_path}")
    else:
        print(f"   ✅ Pas de config - vraiment un nouvel utilisateur")
    print()
    
    # Step 2: Test AC detection
    print("2. Détection automatique d'Assetto Corsa:")
    detector = ACDetector()
    installation = detector.detect_installation()
    
    print(f"   Documents path: {installation.documents_path}")
    print(f"   Game path: {installation.game_path}")
    print(f"   Is valid: {installation.is_valid}")
    print(f"   Can write setups: {installation.can_write_setups}")
    print()
    
    if installation.is_valid:
        print("   ✅ AC détecté automatiquement!")
        print(f"   Cars path: {installation.cars_path}")
        print(f"   Tracks path: {installation.tracks_path}")
        print(f"   Setups path: {installation.setups_path}")
    else:
        print("   ❌ AC non détecté - l'utilisateur devra sélectionner manuellement")
        print()
        return
    print()
    
    # Step 3: Test connector
    print("3. Test du connecteur AC:")
    connector = ACConnector()
    status = connector.connect()
    
    print(f"   is_connected: {status.is_connected}")
    print(f"   game_found: {status.game_found}")
    print(f"   documents_found: {status.documents_found}")
    print(f"   can_write: {status.can_write}")
    print(f"   cars_count: {status.cars_count}")
    print(f"   tracks_count: {status.tracks_count}")
    print()
    
    if not status.is_connected:
        print("   ❌ Connexion échouée")
        print(f"   Erreur: {status.error_message}")
        return
    
    print("   ✅ Connecté avec succès!")
    print()
    
    # Step 4: Test car/track loading
    print("4. Chargement des voitures et pistes:")
    
    print("   Chargement des voitures...")
    cars = connector.get_cars()
    print(f"   ✅ {len(cars)} voitures chargées")
    
    if cars:
        print(f"   Exemples (5 premières):")
        for car in cars[:5]:
            print(f"      - {car.name} ({car.car_id})")
    print()
    
    print("   Chargement des pistes...")
    tracks = connector.get_tracks()
    print(f"   ✅ {len(tracks)} pistes chargées")
    
    if tracks:
        print(f"   Exemples (5 premières):")
        for track in tracks[:5]:
            config_str = f" ({track.config})" if track.config else ""
            print(f"      - {track.name}{config_str}")
    print()
    
    # Step 5: Summary
    print("=" * 60)
    print("RÉSUMÉ DU TEST")
    print("=" * 60)
    
    if status.is_connected and cars and tracks:
        print("✅ SUCCÈS - L'app fonctionnerait pour un nouvel utilisateur!")
        print(f"   - AC détecté: OUI")
        print(f"   - Voitures: {len(cars)}")
        print(f"   - Pistes: {len(tracks)}")
        print(f"   - Peut écrire setups: {status.can_write}")
    else:
        print("❌ ÉCHEC - Problèmes détectés:")
        if not status.is_connected:
            print("   - AC non connecté")
        if not cars:
            print("   - Aucune voiture chargée")
        if not tracks:
            print("   - Aucune piste chargée")
    
    print()

if __name__ == "__main__":
    try:
        test_new_user_flow()
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
