"""
Test script to simulate the case where AC is NOT detected automatically.
This simulates what happens on friends' PCs.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from assetto.ac_detector import ACDetector, ACInstallation
from assetto.ac_connector import ACConnector

def test_no_ac_detected():
    """Simulate the case where AC is not detected automatically."""
    
    print("=" * 60)
    print("SIMULATION: AC NON DÉTECTÉ (cas des amis)")
    print("=" * 60)
    print()
    
    # Step 1: Create a detector with no auto-detection
    print("1. Création d'un détecteur sans auto-détection:")
    detector = ACDetector()
    
    # Override the installation to simulate "not found"
    detector._installation = ACInstallation(
        documents_path=None,
        game_path=None
    )
    
    installation = detector.get_installation()
    print(f"   Documents path: {installation.documents_path}")
    print(f"   Game path: {installation.game_path}")
    print(f"   Is valid: {installation.is_valid}")
    print(f"   ❌ AC non détecté (comme chez tes amis)")
    print()
    
    # Step 2: Test connector with no installation
    print("2. Test du connecteur sans installation:")
    connector = ACConnector()
    connector.detector = detector  # Use our fake detector
    
    status = connector.connect()
    print(f"   is_connected: {status.is_connected}")
    print(f"   game_found: {status.game_found}")
    print(f"   documents_found: {status.documents_found}")
    print(f"   cars_count: {status.cars_count}")
    print(f"   tracks_count: {status.tracks_count}")
    print()
    
    # Step 3: Try to get cars/tracks
    print("3. Tentative de chargement des voitures/pistes:")
    
    print("   connector.is_connected():", connector.is_connected())
    
    cars = connector.get_cars()
    print(f"   get_cars() retourne: {len(cars) if cars else 0} voitures")
    
    tracks = connector.get_tracks()
    print(f"   get_tracks() retourne: {len(tracks) if tracks else 0} pistes")
    print()
    
    # Step 4: Simulate user selecting AC folder manually
    print("4. Simulation: L'utilisateur sélectionne le dossier AC manuellement:")
    
    # Find the real AC path
    real_detector = ACDetector()
    real_installation = real_detector.detect_installation()
    
    if real_installation.is_valid:
        print(f"   Chemin sélectionné: {real_installation.game_path}")
        
        # Set the installation manually
        detector._installation = real_installation
        
        # Reconnect
        print("   Reconnexion...")
        status = connector.connect()
        
        print(f"   is_connected: {status.is_connected}")
        print(f"   cars_count: {status.cars_count}")
        print(f"   tracks_count: {status.tracks_count}")
        print()
        
        # Try loading again
        print("5. Nouvelle tentative de chargement:")
        cars = connector.get_cars()
        print(f"   ✅ {len(cars)} voitures chargées")
        
        tracks = connector.get_tracks()
        print(f"   ✅ {len(tracks)} pistes chargées")
        print()
    else:
        print("   ❌ Impossible de trouver AC même manuellement")
        print()
    
    # Step 5: Summary
    print("=" * 60)
    print("RÉSUMÉ DU TEST")
    print("=" * 60)
    
    if status.is_connected and cars and tracks:
        print("✅ SUCCÈS - Après sélection manuelle, tout fonctionne!")
        print(f"   - Voitures: {len(cars)}")
        print(f"   - Pistes: {len(tracks)}")
        print()
        print("CONCLUSION:")
        print("Si tes amis voient 'Connecté' mais pas de voitures/pistes,")
        print("c'est probablement que:")
        print("1. Le chemin AC est sauvegardé mais invalide")
        print("2. OU les dossiers content/cars et content/tracks sont vides/inaccessibles")
    else:
        print("❌ ÉCHEC - Même après sélection manuelle")
    
    print()

if __name__ == "__main__":
    try:
        test_no_ac_detected()
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
