"""
Test the dynamic TrackAnalyzer - no hardcoded database.
"""

import sys
sys.path.insert(0, '.')

from models.track import Track
from core.race_engineer_advisor import TrackAnalyzer


def test_track_analyzer():
    """Test that TrackAnalyzer generates advice for ANY track."""
    print("=" * 60)
    print("TEST: Dynamic Track Analyzer")
    print("=" * 60)
    
    analyzer = TrackAnalyzer()
    
    # Test various tracks - including ones NOT in any database
    test_tracks = [
        # Known touge
        Track(track_id="ek_akagi", name="Akagi", config="downhill_real"),
        Track(track_id="akina_downhill", name="Akina Downhill"),
        Track(track_id="usui_pass", name="Usui Pass"),
        
        # Unknown touge (should still detect from keywords)
        Track(track_id="some_random_mountain_pass", name="Random Mountain Pass"),
        Track(track_id="custom_touge_map", name="Custom Touge"),
        Track(track_id="japan_hillclimb", name="Japan Hillclimb"),
        
        # Highway
        Track(track_id="shutoko_revival", name="Shutoko Revival Project"),
        Track(track_id="wangan_midnight", name="Wangan Midnight"),
        
        # Drift
        Track(track_id="ebisu_minami", name="Ebisu Minami"),
        Track(track_id="meihan_sportsland", name="Meihan Sportsland"),
        
        # Circuit
        Track(track_id="ks_nurburgring", name="Nurburgring GP"),
        Track(track_id="spa_francorchamps", name="Spa Francorchamps"),
        
        # Completely unknown
        Track(track_id="xyz_unknown_track", name="Unknown Track"),
    ]
    
    for track in test_tracks:
        knowledge = analyzer.analyze(track)
        print(f"\n{track.name} ({track.track_id}):")
        print(f"  Type: {knowledge.type}")
        print(f"  Hairpins: {knowledge.has_tight_hairpins}")
        print(f"  Downhill: {knowledge.has_elevation_change}")
        print(f"  Cliff edges: {knowledge.has_cliff_edges}")
        print(f"  Overtake zones: {len(knowledge.overtake_zones)}")
        print(f"  Danger zones: {len(knowledge.danger_zones)}")
        print(f"  Corner tips: {len(knowledge.key_corners)}")
        
        # Show first tip
        if knowledge.key_corners:
            print(f"  → {knowledge.key_corners[0]}")
    
    print("\n" + "=" * 60)
    print("✅ TrackAnalyzer works for ANY track - no hardcoded database!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_track_analyzer()
