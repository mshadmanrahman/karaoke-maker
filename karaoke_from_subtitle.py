#!/usr/bin/env python3
"""
Create karaoke video from subtitle file
Usage: python karaoke_from_subtitle.py <audio_file> <subtitle_file>
"""
import sys
from pathlib import Path
from downloader import YouTubeDownloader
from separator import VocalSeparator
from video_generator import KaraokeVideoGenerator
from subtitle_importer import import_subtitles

TEMP_DIR = Path('/tmp/karaoke-temp')
OUTPUT_DIR = Path.home() / 'Downloads'


def create_karaoke(audio_source: str, subtitle_file: str):
    """
    Create karaoke video from audio source and subtitle file

    Args:
        audio_source: Path to audio file OR YouTube URL
        subtitle_file: Path to .srt or .ass subtitle file
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Determine if audio_source is YouTube URL or local file
    if audio_source.startswith('http://') or audio_source.startswith('https://'):
        # Download from YouTube
        print(f"\n[1/4] Downloading from YouTube...")
        downloader = YouTubeDownloader(TEMP_DIR)
        result = downloader.download(audio_source)
        audio_path = result['audio_path']
        title = result['title']
        print(f"✓ Downloaded: {title}")
    else:
        # Use local audio file
        audio_path = audio_source
        title = Path(audio_source).stem
        print(f"\n[1/4] Using audio file: {title}")

    # Separate vocals
    print(f"\n[2/4] Separating vocals (2-3 minutes)...")
    separator = VocalSeparator(TEMP_DIR)
    separated = separator.separate(audio_path)
    instrumental_path = separated['instrumental']
    print(f"✓ Instrumental track created")

    # Import lyrics from subtitle file
    print(f"\n[3/4] Importing lyrics from subtitle file...")
    lyrics_data = import_subtitles(subtitle_file)
    print(f"✓ Imported {len(lyrics_data['segments'])} lyric lines")

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
        print("\nKARAOKE MAKER - FROM SUBTITLE FILE")
        print("="*70)
        print("\nUsage:")
        print("  python karaoke_from_subtitle.py <audio_source> <subtitle_file>")
        print("\nExamples:")
        print("  python karaoke_from_subtitle.py song.mp3 lyrics.srt")
        print("  python karaoke_from_subtitle.py https://youtu.be/xyz lyrics.ass")
        print("\nSubtitle formats supported:")
        print("  - .srt (SubRip)")
        print("  - .ass/.ssa (Aegisub)")
        print("\nTIP: Use Aegisub (free) to create subtitle files with perfect timing")
        print("     Download: https://aegisub.org/")
        print("="*70 + "\n")
        sys.exit(1)

    audio_source = sys.argv[1]
    subtitle_file = sys.argv[2]

    try:
        create_karaoke(audio_source, subtitle_file)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
