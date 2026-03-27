"""
Configuration for STNH Event Browser Data Pipeline

Reads mod data from git01/New-Horizons-Development/ (READ-ONLY)
Writes generated data to git10/stnh_event_browser/assets/
"""

import os
from pathlib import Path

# ==========================================
# PATH CONFIGURATION
# ==========================================

STNH_MOD_ROOT = r"C:\Users\marcj\git01\New-Horizons-Development"
EVENT_BROWSER_ROOT = r"C:\Users\marcj\git10\stnh_event_browser"

# ==========================================
# SOURCE PATHS (READ-ONLY)
# ==========================================

MOD_EVENTS_DIR = os.path.join(STNH_MOD_ROOT, "events")
MOD_LOCALISATION_DIR = os.path.join(STNH_MOD_ROOT, "localisation")
MOD_ON_ACTIONS_DIR = os.path.join(STNH_MOD_ROOT, "common", "on_actions")
MOD_EVENT_CHAINS_DIR = os.path.join(STNH_MOD_ROOT, "common", "event_chains")
MOD_INTERFACE_DIR = os.path.join(STNH_MOD_ROOT, "interface")
MOD_GFX_EVENT_PICTURES = os.path.join(STNH_MOD_ROOT, "gfx", "event_pictures")

# ==========================================
# OUTPUT PATHS (WRITE)
# ==========================================

OUTPUT_ASSETS_DIR = os.path.join(EVENT_BROWSER_ROOT, "assets")
OUTPUT_EVENTS_DETAIL_DIR = os.path.join(OUTPUT_ASSETS_DIR, "events_detail")
OUTPUT_LOCALISATION_DIR = os.path.join(OUTPUT_ASSETS_DIR, "localisation")
OUTPUT_PICTURES_DIR = os.path.join(EVENT_BROWSER_ROOT, "pictures")

# ==========================================
# LANGUAGES
# ==========================================

LANGUAGES = [
    "english",
    "german",
    "french",
    "spanish",
    "russian",
    "polish",
    "braz_por",
]

LANGUAGE_SUFFIXES = {
    "english": "l_english",
    "german": "l_german",
    "french": "l_french",
    "spanish": "l_spanish",
    "russian": "l_russian",
    "polish": "l_polish",
    "braz_por": "l_braz_por",
}

# ==========================================
# EVENT TYPES
# ==========================================

EVENT_TYPES = [
    "country_event",
    "planet_event",
    "fleet_event",
    "ship_event",
    "pop_event",
    "observer_event",
    "situation_event",
]

# ==========================================
# VALIDATION
# ==========================================

def validate_paths():
    errors = []
    if not os.path.exists(STNH_MOD_ROOT):
        errors.append(f"STNH Mod root not found: {STNH_MOD_ROOT}")
    if not os.path.exists(MOD_EVENTS_DIR):
        errors.append(f"Events directory not found: {MOD_EVENTS_DIR}")
    if not os.path.exists(MOD_LOCALISATION_DIR):
        errors.append(f"Localisation directory not found: {MOD_LOCALISATION_DIR}")

    # Create output dirs
    for d in [OUTPUT_ASSETS_DIR, OUTPUT_EVENTS_DETAIL_DIR, OUTPUT_LOCALISATION_DIR, OUTPUT_PICTURES_DIR]:
        os.makedirs(d, exist_ok=True)

    if errors:
        raise FileNotFoundError("\n".join(errors))
    return True


def print_config():
    print("=" * 60)
    print("STNH Event Browser - Configuration")
    print("=" * 60)
    print(f"\nMod Source (READ-ONLY):")
    print(f"  Root:       {STNH_MOD_ROOT}")
    print(f"  Events:     {MOD_EVENTS_DIR}")
    print(f"  Loc:        {MOD_LOCALISATION_DIR}")
    print(f"  On-Actions: {MOD_ON_ACTIONS_DIR}")
    print(f"  Chains:     {MOD_EVENT_CHAINS_DIR}")
    print(f"\nOutput (WRITE):")
    print(f"  Assets:     {OUTPUT_ASSETS_DIR}")
    print(f"  Pictures:   {OUTPUT_PICTURES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        validate_paths()
        print_config()
        print("\n[OK] Configuration validated successfully!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        exit(1)
