"""
Convert DDS event pictures to WebP format using ImageMagick.
Only converts pictures that are actually referenced by events.
"""

import os
import json
import subprocess
import time
from config import (
    MOD_GFX_EVENT_PICTURES, OUTPUT_ASSETS_DIR, OUTPUT_PICTURES_DIR
)


def get_referenced_pictures(events_index_path, pictures_map_path):
    """Get set of texture names that are actually used by events."""
    referenced = set()

    # Load index
    with open(events_index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # Collect all picture references
    pic_refs = set()
    for ev in index:
        pic = ev.get('pic')
        if pic and isinstance(pic, str):
            pic_refs.add(pic)

    # Load GFX mappings
    with open(pictures_map_path, 'r', encoding='utf-8') as f:
        gfx_map = json.load(f)

    # Map GFX names to texture filenames
    for pic_ref in pic_refs:
        if pic_ref in gfx_map:
            referenced.add(gfx_map[pic_ref]['texture_name'])

    return referenced


def convert_images(force=False):
    """Convert DDS files to WebP. Returns stats dict."""
    stats = {'total': 0, 'converted': 0, 'skipped': 0, 'failed': 0, 'errors': []}

    events_index_path = os.path.join(OUTPUT_ASSETS_DIR, 'events_index.json')
    pictures_map_path = os.path.join(OUTPUT_ASSETS_DIR, 'pictures_map.json')

    if not os.path.exists(events_index_path) or not os.path.exists(pictures_map_path):
        print("  [ERROR] Run generate_events_json.py first!")
        return stats

    referenced = get_referenced_pictures(events_index_path, pictures_map_path)
    print(f"  Referenced pictures: {len(referenced)}")

    if not os.path.isdir(MOD_GFX_EVENT_PICTURES):
        print(f"  [ERROR] Event pictures directory not found: {MOD_GFX_EVENT_PICTURES}")
        return stats

    os.makedirs(OUTPUT_PICTURES_DIR, exist_ok=True)

    for fn in sorted(os.listdir(MOD_GFX_EVENT_PICTURES)):
        if not fn.endswith('.dds'):
            continue
        base_name = fn[:-4]

        if base_name not in referenced:
            continue

        stats['total'] += 1
        output_path = os.path.join(OUTPUT_PICTURES_DIR, f"{base_name}.webp")

        if not force and os.path.exists(output_path):
            stats['skipped'] += 1
            continue

        input_path = os.path.join(MOD_GFX_EVENT_PICTURES, fn)
        try:
            result = subprocess.run(
                ['magick', input_path, '-resize', '480x300!', '-quality', '80', output_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                stats['converted'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append(f"{fn}: {result.stderr[:200]}")
        except FileNotFoundError:
            print("  [ERROR] ImageMagick not found. Install it to convert images.")
            stats['failed'] += 1
            break
        except Exception as e:
            stats['failed'] += 1
            stats['errors'].append(f"{fn}: {e}")

    return stats


def main():
    print("=== Converting Event Pictures (DDS -> WebP) ===")
    start = time.time()
    stats = convert_images()
    elapsed = time.time() - start
    print(f"\n  Total referenced: {stats['total']}")
    print(f"  Converted: {stats['converted']}")
    print(f"  Skipped (exists): {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Elapsed: {elapsed:.1f}s")
    if stats['errors']:
        for e in stats['errors'][:5]:
            print(f"    {e}")
    return stats


if __name__ == '__main__':
    main()
