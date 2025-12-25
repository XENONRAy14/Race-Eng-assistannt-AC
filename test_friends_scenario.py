"""
Test script to simulate EXACTLY what happens on friends' PCs.
Scenario: AC path is saved but points to wrong location OR content folders are empty.
"""

import sys
from pathlib import Path
import tempfile

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from assetto.ac_detector import ACDetector, ACInstallation
from assetto.ac_connector import ACConnector

def test_friends_scenario():
    """Simulate the exact scenario friends are experiencing."""
    
    print("=" * 60)
    print("SIMULATION: SCÉNARIO DES AMIS")
    print("Cas: AC 'connecté' mais pas de voitures/pistes")
    print("=" * 60)
    print()
    
    # Scenario 1: Invalid game path (exists but no content)
    print("SCÉNARIO 1: Chemin AC invalide (dossier existe mais pas de content)")
    print("-" * 60)
    
    # Create a fake AC folder
    fake_ac_path = Path(tempfile.gettempdir()) / "fake_assettocorsa"
    fake_ac_path.mkdir(exist_ok=True)
    
    # Create installation with fake path
    fake_installation = ACInstallation(
        documents_path=Path.home() / "Documents" / "Assetto Corsa",
        game_path=fake_ac_path
    )
    
    print(f"Chemin AC (fake): {fake_ac_path}")
    print(f"Existe: {fake_ac_path.exists()}")
    print(f"Installation valide: {fake_installation.is_valid}")
    print(f"Cars path: {fake_installation.cars_path}")
    print(f"Cars path existe: {fake_installation.cars_path.exists() if fake_installation.cars_path else False}")
    print()
    
    # Create detector with fake installation
    detector = ACDetector()
    detector._installation = fake_installation
    
    # Create connector
    connector = ACConnector()
    connector.detector = detector
    
    # Try to connect
    print("Tentative de connexion...")
    status = connector.connect()
    
    print(f"is_connected: {status.is_connected}")
    print(f"game_found: {status.game_found}")
    print(f"cars_count: {status.cars_count}")
    print(f"tracks_count: {status.tracks_count}")
    print()
    
    # Try to load cars/tracks
    print("Tentative de chargement des voitures/pistes...")
    print(f"connector.is_connected(): {connector.is_connected()}")
    
    cars = connector.get_cars()
    tracks = connector.get_tracks()
    
    print(f"Voitures chargées: {len(cars)}")
    print(f"Pistes chargées: {len(tracks)}")
    print()
    
    if status.is_connected and (not cars or not tracks):
        print("❌ PROBLÈME REPRODUIT!")
        print("   L'app dit 'Connecté' mais pas de voitures/pistes")
        print("   C'est exactement ce que vivent tes amis!")
    else:
        print("✅ Pas de problème dans ce scénario")
    
    print()
    print()
    
    # Scenario 2: Empty content folders
    print("SCÉNARIO 2: Dossiers content vides")
    print("-" * 60)
    
    # Create fake AC with empty content folders
    fake_ac_path2 = Path(tempfile.gettempdir()) / "fake_ac_empty_content"
    fake_ac_path2.mkdir(exist_ok=True)
    (fake_ac_path2 / "content").mkdir(exist_ok=True)
    (fake_ac_path2 / "content" / "cars").mkdir(exist_ok=True)
    (fake_ac_path2 / "content" / "tracks").mkdir(exist_ok=True)
    
    fake_installation2 = ACInstallation(
        documents_path=Path.home() / "Documents" / "Assetto Corsa",
        game_path=fake_ac_path2
    )
    
    print(f"Chemin AC: {fake_ac_path2}")
    print(f"Installation valide: {fake_installation2.is_valid}")
    print(f"Cars path existe: {fake_installation2.cars_path.exists()}")
    print(f"Tracks path existe: {fake_installation2.tracks_path.exists()}")
    print()
    
    detector2 = ACDetector()
    detector2._installation = fake_installation2
    
    connector2 = ACConnector()
    connector2.detector = detector2
    
    print("Tentative de connexion...")
    status2 = connector2.connect()
    
    print(f"is_connected: {status2.is_connected}")
    print(f"cars_count: {status2.cars_count}")
    print(f"tracks_count: {status2.tracks_count}")
    print()
    
    print("Tentative de chargement...")
    cars2 = connector2.get_cars()
    tracks2 = connector2.get_tracks()
    
    print(f"Voitures chargées: {len(cars2)}")
    print(f"Pistes chargées: {len(tracks2)}")
    print()
    
    if status2.is_connected and (not cars2 or not tracks2):
        print("❌ PROBLÈME REPRODUIT!")
        print("   L'app dit 'Connecté' mais dossiers vides")
    else:
        print("✅ Pas de problème dans ce scénario")
    
    print()
    print()
    
    # Summary
    print("=" * 60)
    print("DIAGNOSTIC")
    print("=" * 60)
    print()
    print("Si tes amis voient 'Connecté' mais pas de voitures/pistes:")
    print()
    print("CAUSES POSSIBLES:")
    print("1. Le chemin AC sauvegardé pointe vers un dossier invalide")
    print("2. Les dossiers content/cars ou content/tracks n'existent pas")
    print("3. Les dossiers existent mais sont vides (AC mal installé)")
    print("4. Problème de permissions (pas d'accès aux dossiers)")
    print()
    print("SOLUTION:")
    print("Demande-leur de:")
    print("1. Aller dans Paramètres")
    print("2. Cliquer sur 'Sélectionner le dossier AC'")
    print("3. Sélectionner le VRAI dossier AC (celui avec AssettoCorsa.exe)")
    print("4. Vérifier que le message dit 'X voitures, Y pistes' après")
    print()
    print("Les logs de debug dans la version actuelle vont montrer:")
    print("- Le chemin exact scanné")
    print("- Si le chemin existe")
    print("- Combien de voitures/pistes sont trouvées")
    print()
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(fake_ac_path)
        shutil.rmtree(fake_ac_path2)
    except:
        pass

if __name__ == "__main__":
    try:
        test_friends_scenario()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
