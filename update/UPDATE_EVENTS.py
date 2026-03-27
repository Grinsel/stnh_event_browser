"""
=============================================================================
STNH EVENT BROWSER - FULL UPDATE SCRIPT
=============================================================================

Complete automation of the event data regeneration process.
Run this script whenever the STNH mod is updated.

PREREQUISITES:
- Python 3.8+
- STNH mod at: C:\\Users\\marcj\\git01\\New-Horizons-Development
- ImageMagick installed (optional, for image conversion)

USAGE:
    python UPDATE_EVENTS.py
    python UPDATE_EVENTS.py --skip-images

PHASES:
    1. Validation    - Check paths and dependencies
    2. Localisation  - Parse all 7 languages
    3. GFX Mapping   - Parse sprite definitions
    4. Events        - Parse all event files
    5. Generation    - Generate all JSON assets
    6. Images        - Convert DDS to WebP (optional)
    7. Summary       - Statistics and summary
=============================================================================
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add update directory to path
UPDATE_DIR = Path(__file__).parent
sys.path.insert(0, str(UPDATE_DIR))


def print_banner():
    print("""
=============================================================================
    _____ _____ _   _ _   _   _______     _______ _   _ _____
   /  ___|_   _| \\ | | | | | |  ___\\ \\   / / ____| \\ | |_   _|
   \\ `--. | | |  \\| | |_| | | |__  \\ \\ / /|  _| |  \\| | | |
    `--. \\ | | | . ` |  _  | |  __|  \\ V / | |___| . ` | | |
   /\\__/ / | | | |\\  | | | | | |___   \\ /  |_____|\\  | | | |
   \\____/  \\_/ \\_| \\_\\_| |_| |_____|   \\_/         \\_| \\_/ \\_/

              BROWSER UPDATE SCRIPT v1.0
=============================================================================
    """)


def phase_validation():
    """Phase 1: Validate environment."""
    print("=" * 60)
    print("PHASE 1: VALIDATION")
    print("=" * 60)

    from config import validate_paths, print_config
    try:
        validate_paths()
        print_config()
        return True
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return False


def phase_localisation():
    """Phase 2: Parse localisation."""
    print("\n" + "=" * 60)
    print("PHASE 2: LOCALISATION")
    print("=" * 60)

    from parse_localisation import main as loc_main
    loc_data, stats = loc_main()
    return stats


def phase_gfx():
    """Phase 3: Parse GFX mappings."""
    print("\n" + "=" * 60)
    print("PHASE 3: GFX MAPPINGS")
    print("=" * 60)

    from parse_gfx_mappings import main as gfx_main
    return gfx_main()


def phase_events():
    """Phase 4: Parse events."""
    print("\n" + "=" * 60)
    print("PHASE 4: EVENT PARSING")
    print("=" * 60)

    from parse_events import main as events_main
    events, namespaces, stats = events_main()
    return stats


def phase_generation():
    """Phase 5: Generate all JSON assets."""
    print("\n" + "=" * 60)
    print("PHASE 5: JSON GENERATION")
    print("=" * 60)

    from generate_events_json import generate_all
    return generate_all()


def phase_images(skip=False):
    """Phase 6: Convert images."""
    print("\n" + "=" * 60)
    print("PHASE 6: IMAGE CONVERSION")
    print("=" * 60)

    if skip:
        print("  [SKIPPED] --skip-images flag set")
        return {'skipped': True}

    from convert_images import main as img_main
    return img_main()


def main():
    print_banner()
    start_time = time.time()

    parser = argparse.ArgumentParser(description='STNH Event Browser - Full Update')
    parser.add_argument('--skip-images', action='store_true',
                        help='Skip DDS to WebP image conversion')
    args = parser.parse_args()

    results = {}

    # Phase 1
    if not phase_validation():
        print("\n[ABORT] Validation failed.")
        return 1
    results['validation'] = 'OK'

    # Phase 2
    results['localisation'] = phase_localisation()

    # Phase 3
    results['gfx'] = phase_gfx()

    # Phase 4
    results['events'] = phase_events()

    # Phase 5
    results['generation'] = phase_generation()

    # Phase 6
    results['images'] = phase_images(skip=args.skip_images)

    # Phase 7: Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("PHASE 7: SUMMARY")
    print("=" * 60)
    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"\n  Results written to: {os.path.join(UPDATE_DIR.parent, 'assets')}")

    # Write run log
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'elapsed_seconds': round(elapsed, 1),
        'results': {k: v for k, v in results.items() if isinstance(v, dict)},
    }
    log_path = os.path.join(UPDATE_DIR.parent, 'assets', 'last_update.json')
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2, default=str)
    print(f"  Log written to: {log_path}")

    print("\n  [DONE] Update complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
