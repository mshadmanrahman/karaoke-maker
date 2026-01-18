#!/usr/bin/env python3
"""
Karaoke Maker
Creates karaoke videos from YouTube URLs

Usage:
    python karaoke_maker.py <youtube_url>
    python karaoke_maker.py <youtube_url> --output /path/to/output
"""
import argparse
import logging
from pathlib import Path
import sys
import shutil
from datetime import datetime

from downloader import YouTubeDownloader
from separator import VocalSeparator
from lyrics_extractor import LyricsExtractor
from video_generator import KaraokeVideoGenerator
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KaraokeMaker:
    """Main class for creating karaoke videos"""

    def __init__(self, output_dir: Path = None, temp_dir: Path = None):
        """
        Initialize Karaoke Maker

        Args:
            output_dir: Directory for final karaoke videos
            temp_dir: Directory for temporary files
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.temp_dir = temp_dir or config.TEMP_DIR

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.downloader = YouTubeDownloader(self.temp_dir)
        self.separator = VocalSeparator(
            self.temp_dir,
            model=config.DEMUCS_MODEL,
            device=config.DEMUCS_DEVICE
        )
        self.lyrics_extractor = LyricsExtractor(
            model_size=config.WHISPER_MODEL,
            language=config.WHISPER_LANGUAGE
        )
        self.video_generator = KaraokeVideoGenerator(
            width=config.VIDEO_WIDTH,
            height=config.VIDEO_HEIGHT,
            fps=config.VIDEO_FPS,
            font_size=config.FONT_SIZE,
            font_color=config.FONT_COLOR,
            highlight_color=config.HIGHLIGHT_COLOR
        )

    def create(self, youtube_url: str, custom_output_name: str = None) -> str:
        """
        Create karaoke video from YouTube URL

        Args:
            youtube_url: YouTube video URL
            custom_output_name: Optional custom output filename

        Returns:
            Path to generated karaoke video
        """
        logger.info("=" * 70)
        logger.info("KARAOKE MAKER - Starting process")
        logger.info("=" * 70)

        try:
            # Step 1: Download audio
            logger.info("\n[1/4] Downloading audio from YouTube...")
            download_result = self.downloader.download(youtube_url)
            audio_path = download_result['audio_path']
            title = download_result['title']
            logger.info(f"✓ Downloaded: {title}")

            # Step 2: Separate vocals
            logger.info("\n[2/4] Separating vocals (this takes 2-3 minutes)...")
            separated = self.separator.separate(audio_path)
            instrumental_path = separated['instrumental']
            logger.info(f"✓ Instrumental track created")

            # Step 3: Extract lyrics
            logger.info("\n[3/4] Extracting lyrics with timestamps...")
            lyrics_data = self.lyrics_extractor.extract(audio_path)
            logger.info(f"✓ Extracted {len(lyrics_data['segments'])} lyric segments")

            # Save lyrics for reference
            lyrics_json_path = Path(audio_path).parent / f"{Path(audio_path).stem}_lyrics.json"
            self.lyrics_extractor.save_lyrics(lyrics_data, lyrics_json_path)

            # Step 4: Generate video
            logger.info("\n[4/4] Generating karaoke video (this takes 3-5 minutes)...")

            # Determine output filename
            if custom_output_name:
                output_filename = custom_output_name
                if not output_filename.endswith('.mp4'):
                    output_filename += '.mp4'
            else:
                # Sanitize title for filename
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
                safe_title = safe_title.strip()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{safe_title}_{timestamp}_karaoke.mp4"

            output_path = str(self.output_dir / output_filename)

            self.video_generator.generate(
                instrumental_path,
                lyrics_data,
                output_path,
                title=title
            )

            logger.info("\n" + "=" * 70)
            logger.info("✓ KARAOKE VIDEO CREATED SUCCESSFULLY!")
            logger.info("=" * 70)
            logger.info(f"Output: {output_path}")
            logger.info(f"Lyrics: {lyrics_json_path}")
            logger.info("=" * 70)

            # Cleanup temp files
            self._cleanup_temp_files()

            return output_path

        except Exception as e:
            logger.error(f"\n✗ Error creating karaoke video: {e}")
            raise

    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            logger.info("\nCleaning up temporary files...")
            # Keep the temp directory but remove its contents
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info("✓ Cleanup complete")
        except Exception as e:
            logger.warning(f"Could not clean up temp files: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Create karaoke videos from YouTube URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python karaoke_maker.py "https://youtube.com/watch?v=dQw4w9WgXcQ"
  python karaoke_maker.py "https://youtube.com/watch?v=dQw4w9WgXcQ" --output "My Song"
  python karaoke_maker.py "https://youtube.com/watch?v=dQw4w9WgXcQ" --output-dir ~/Desktop/Karaoke
        """
    )

    parser.add_argument(
        'url',
        help='YouTube video URL'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Custom output filename (without extension)',
        default=None
    )

    parser.add_argument(
        '--output-dir',
        '-d',
        help=f'Output directory for karaoke videos (default: {config.OUTPUT_DIR})',
        type=Path,
        default=config.OUTPUT_DIR
    )

    parser.add_argument(
        '--temp-dir',
        '-t',
        help=f'Temporary files directory (default: {config.TEMP_DIR})',
        type=Path,
        default=config.TEMP_DIR
    )

    args = parser.parse_args()

    # Create karaoke maker
    maker = KaraokeMaker(
        output_dir=args.output_dir,
        temp_dir=args.temp_dir
    )

    # Create karaoke video
    try:
        output_path = maker.create(args.url, args.output)
        print(f"\n✓ Success! Your karaoke video is ready:")
        print(f"  {output_path}")
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
