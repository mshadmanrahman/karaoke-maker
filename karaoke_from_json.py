#!/usr/bin/env python3
"""
Create karaoke video from JSON lyrics file
Usage: python karaoke_from_json.py <audio_file> <lyrics.json>
"""
import sys
import json
from pathlib import Path
from separator import VocalSeparator
from video_generator import KaraokeVideoGenerator

TEMP_DIR = Path('/tmp/karaoke-temp')
OUTPUT_DIR = Path.home() / 'Downloads'


def create_karaoke(audio_path: str, json_file: str):
    """
    Create karaoke video from audio file and JSON lyrics

    Args:
        audio_path: Path to audio file
        json_file: Path to JSON file with lyrics
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    audio_path = Path(audio_path)
    title = audio_path.stem

    print(f"\n[1/3] Using audio file: {title}")

    # Separate vocals
    print(f"\n[2/3] Separating vocals (2-3 minutes)...")
    separator = VocalSeparator(TEMP_DIR)
    separated = separator.separate(str(audio_path))
    instrumental_path = separated['instrumental']
    print(f"✓ Instrumental track created")

    # Load lyrics from JSON
    print(f"\n[3/3] Loading lyrics from JSON...")
    with open(json_file, 'r', encoding='utf-8') as f:
        lyrics_data = json.load(f)

    print(f"✓ Loaded {len(lyrics_data['segments'])} lyric lines")

    # Generate karaoke video
    print(f"\n[4/4] Generating karaoke video (3-5 minutes)...")
    generator = KaraokeVideoGenerator()

    # Create output path
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    output_filename = f"{safe_title}_{timestamp}_karaoke.mp4"
    output_path = OUTPUT_DIR / output_filename

    generator.generate(
        audio_path=instrumental_path,
        lyrics_data=lyrics_data,
        output_path=str(output_path),
        title=title
    )

    print("\n" + "="*70)
    print("✓ SUCCESS! KARAOKE VIDEO READY")
    print("="*70)
    print(f"\nOutput: {output_path}")
    print("="*70 + "\n")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("\nKARAOKE MAKER - FROM JSON LYRICS")
        print("="*70)
        print("\nUsage:")
        print("  python karaoke_from_json.py <audio_file> <lyrics.json>")
        print("\nExample:")
        print("  python karaoke_from_json.py song.mp3 karaoke-lyrics.json")
        print("\nCreate lyrics file using the easy web editor:")
        print("  open easy_editor.html")
        print("="*70 + "\n")
        sys.exit(1)

    audio_file = sys.argv[1]
    json_file = sys.argv[2]

    try:
        create_karaoke(audio_file, json_file)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
