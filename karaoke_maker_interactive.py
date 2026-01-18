"""
Interactive Karaoke Maker with Lyrics Editing
Allows users to review and edit lyrics before video generation
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict

from config import OUTPUT_DIR, TEMP_DIR
from downloader import YouTubeDownloader
from separator import VocalSeparator
from lyrics_extractor import LyricsExtractor
from video_generator import KaraokeVideoGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteractiveKaraokeMaker:
    """Interactive karaoke maker with lyrics editing step"""

    def __init__(self):
        self.downloader = YouTubeDownloader(TEMP_DIR)
        self.separator = VocalSeparator(TEMP_DIR)
        self.lyrics_extractor = LyricsExtractor()
        self.video_generator = KaraokeVideoGenerator()

        # Ensure output directories exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def step1_download_and_extract(self, youtube_url: str) -> tuple:
        """
        Step 1: Download audio, separate vocals, extract lyrics

        Returns:
            (audio_path, instrumental_path, lyrics_data, title)
        """
        print("\n" + "="*70)
        print("STEP 1: PROCESSING AUDIO & EXTRACTING LYRICS")
        print("="*70)

        # Download audio
        print("\n[1/3] Downloading audio from YouTube...")
        download_result = self.downloader.download(youtube_url)
        audio_path = download_result['audio_path']
        title = download_result['title']
        logger.info(f"✓ Downloaded: {title}")

        # Separate vocals
        print("\n[2/3] Separating vocals (this takes 2-3 minutes)...")
        separated = self.separator.separate(audio_path)
        instrumental_path = separated['instrumental']
        logger.info("✓ Instrumental track created")

        # Extract lyrics
        print("\n[3/3] Extracting lyrics with timestamps...")
        lyrics_data = self.lyrics_extractor.extract(audio_path)
        logger.info(f"✓ Extracted {len(lyrics_data['segments'])} lyric segments")

        return audio_path, instrumental_path, lyrics_data, title

    def step2_edit_lyrics(self, lyrics_data: Dict, title: str) -> Dict:
        """
        Step 2: Allow user to review and edit lyrics

        Returns:
            Updated lyrics_data
        """
        print("\n" + "="*70)
        print("STEP 2: REVIEW & EDIT LYRICS")
        print("="*70)
        print(f"\nSong: {title}")
        print(f"Language detected: {lyrics_data['language']}")
        print(f"Total segments: {len(lyrics_data['segments'])}")

        print("\n" + "-"*70)
        print("CURRENT LYRICS:")
        print("-"*70)

        # Display all lyrics with line numbers
        for i, segment in enumerate(lyrics_data['segments'], 1):
            timestamp = f"[{segment['start']:.1f}s - {segment['end']:.1f}s]"
            print(f"{i:3d}. {timestamp:20s} {segment['text']}")

        print("-"*70)
        print("\nOPTIONS:")
        print("1. Use these lyrics as-is")
        print("2. Edit specific lines")
        print("3. Replace all lyrics (paste your own)")
        print("4. Save lyrics to file for external editing")
        print("5. Load lyrics from file")
        print("6. Cancel")

        while True:
            choice = input("\nYour choice (1-6): ").strip()

            if choice == '1':
                print("\n✓ Using extracted lyrics")
                return lyrics_data

            elif choice == '2':
                # Edit specific lines
                lyrics_data = self._edit_specific_lines(lyrics_data)
                return lyrics_data

            elif choice == '3':
                # Replace all lyrics
                lyrics_data = self._replace_all_lyrics(lyrics_data)
                return lyrics_data

            elif choice == '4':
                # Save to file
                self._save_lyrics_to_file(lyrics_data, title)
                continue

            elif choice == '5':
                # Load from file
                lyrics_data = self._load_lyrics_from_file(lyrics_data)
                return lyrics_data

            elif choice == '6':
                print("\n✗ Cancelled")
                sys.exit(0)

            else:
                print("Invalid choice. Please enter 1-6.")

    def _edit_specific_lines(self, lyrics_data: Dict) -> Dict:
        """Edit specific lines interactively"""
        print("\n" + "-"*70)
        print("EDIT SPECIFIC LINES")
        print("-"*70)
        print("Enter line numbers to edit (comma-separated), or 'done' when finished")
        print("Example: 1,5,10")

        while True:
            line_input = input("\nLine numbers to edit (or 'done'): ").strip()

            if line_input.lower() == 'done':
                break

            try:
                line_numbers = [int(x.strip()) for x in line_input.split(',')]

                for line_num in line_numbers:
                    if 1 <= line_num <= len(lyrics_data['segments']):
                        idx = line_num - 1
                        segment = lyrics_data['segments'][idx]

                        print(f"\nLine {line_num}:")
                        print(f"  Current: {segment['text']}")

                        new_text = input("  New text: ").strip()
                        if new_text:
                            lyrics_data['segments'][idx]['text'] = new_text
                            print(f"  ✓ Updated line {line_num}")
                        else:
                            print(f"  ✗ Skipped line {line_num}")
                    else:
                        print(f"  ✗ Line {line_num} out of range (1-{len(lyrics_data['segments'])})")

            except ValueError:
                print("Invalid input. Use comma-separated numbers.")

        return lyrics_data

    def _replace_all_lyrics(self, lyrics_data: Dict) -> Dict:
        """Replace all lyrics with user-provided text"""
        print("\n" + "-"*70)
        print("REPLACE ALL LYRICS")
        print("-"*70)
        print("Paste your lyrics below (one line per segment)")
        print("Press Enter twice when done (empty line to finish)")
        print("-"*70)

        new_lines = []
        while True:
            line = input()
            if not line:
                break
            new_lines.append(line.strip())

        if not new_lines:
            print("✗ No lyrics entered. Keeping original.")
            return lyrics_data

        # Distribute the new lyrics across the existing timestamps
        if len(new_lines) == len(lyrics_data['segments']):
            # Perfect match - one-to-one replacement
            for i, new_text in enumerate(new_lines):
                lyrics_data['segments'][i]['text'] = new_text
        else:
            # Different number of lines - redistribute timing
            print(f"\nWarning: You provided {len(new_lines)} lines, but there are {len(lyrics_data['segments'])} segments.")
            print("Redistributing timing proportionally...")

            total_duration = lyrics_data['segments'][-1]['end']
            segment_duration = total_duration / len(new_lines)

            new_segments = []
            for i, text in enumerate(new_lines):
                new_segments.append({
                    'start': i * segment_duration,
                    'end': (i + 1) * segment_duration,
                    'text': text
                })

            lyrics_data['segments'] = new_segments

        print(f"\n✓ Replaced with {len(new_lines)} new lines")
        return lyrics_data

    def _save_lyrics_to_file(self, lyrics_data: Dict, title: str):
        """Save lyrics to a text file for external editing"""
        filename = f"{title.replace('/', '_')}_lyrics.txt"
        filepath = OUTPUT_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(lyrics_data['segments'], 1):
                f.write(f"{segment['text']}\n")

        print(f"\n✓ Lyrics saved to: {filepath}")
        print("  You can edit this file and load it back with option 5")

    def _load_lyrics_from_file(self, lyrics_data: Dict) -> Dict:
        """Load lyrics from a text file"""
        print("\n" + "-"*70)
        print("LOAD LYRICS FROM FILE")
        print("-"*70)

        filepath = input("Enter file path: ").strip()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                new_lines = [line.strip() for line in f if line.strip()]

            if not new_lines:
                print("✗ File is empty or invalid")
                return lyrics_data

            # Redistribute timing
            total_duration = lyrics_data['segments'][-1]['end']
            segment_duration = total_duration / len(new_lines)

            new_segments = []
            for i, text in enumerate(new_lines):
                new_segments.append({
                    'start': i * segment_duration,
                    'end': (i + 1) * segment_duration,
                    'text': text
                })

            lyrics_data['segments'] = new_segments
            print(f"\n✓ Loaded {len(new_lines)} lines from file")
            return lyrics_data

        except FileNotFoundError:
            print(f"✗ File not found: {filepath}")
            return lyrics_data
        except Exception as e:
            print(f"✗ Error reading file: {e}")
            return lyrics_data

    def step3_generate_video(self, instrumental_path: str, lyrics_data: Dict, title: str) -> str:
        """
        Step 3: Generate final karaoke video

        Returns:
            Output video path
        """
        print("\n" + "="*70)
        print("STEP 3: GENERATING KARAOKE VIDEO")
        print("="*70)

        # Generate output filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        output_filename = f"{safe_title}_{timestamp}_karaoke.mp4"
        output_path = OUTPUT_DIR / output_filename

        print(f"\nGenerating video (this takes 3-5 minutes)...")
        self.video_generator.generate(instrumental_path, lyrics_data, str(output_path), title)

        return str(output_path)

    def create(self, youtube_url: str):
        """
        Create karaoke video with interactive lyrics editing

        Args:
            youtube_url: YouTube video URL
        """
        try:
            # Step 1: Download and extract
            audio_path, instrumental_path, lyrics_data, title = self.step1_download_and_extract(youtube_url)

            # Step 2: Edit lyrics
            lyrics_data = self.step2_edit_lyrics(lyrics_data, title)

            # Step 3: Generate video
            output_path = self.step3_generate_video(instrumental_path, lyrics_data, title)

            print("\n" + "="*70)
            print("✓ SUCCESS! KARAOKE VIDEO READY")
            print("="*70)
            print(f"\nOutput: {output_path}")
            print("\n" + "="*70)

        except Exception as e:
            logger.error(f"Error: {e}")
            raise


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python karaoke_maker_interactive.py <youtube_url>")
        sys.exit(1)

    youtube_url = sys.argv[1]

    maker = InteractiveKaraokeMaker()
    maker.create(youtube_url)


if __name__ == '__main__':
    main()
