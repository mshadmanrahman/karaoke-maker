"""
YouTube audio downloader module
Downloads audio from YouTube videos using pytubefix
"""
import logging
import subprocess
from pathlib import Path
from pytubefix import YouTube
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Downloads audio from YouTube videos"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, output_filename: Optional[str] = None) -> Dict[str, str]:
        """
        Download audio from YouTube URL

        Args:
            url: YouTube video URL
            output_filename: Optional custom filename (without extension)

        Returns:
            Dictionary with paths to downloaded files and metadata
        """
        try:
            logger.info(f"Downloading audio from: {url}")
            
            # Create YouTube object
            yt = YouTube(url)
            title = yt.title
            duration = yt.length
            author = yt.author
            
            logger.info(f"Found video: {title}")
            
            # Get highest quality audio stream
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').last()
            
            if not audio_stream:
                # Fallback to any audio
                audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                raise Exception("No audio stream available")
            
            # Create safe filename
            if output_filename:
                safe_filename = output_filename
            else:
                safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            
            # Download the audio (will be .mp4 or .webm)
            logger.info(f"Downloading audio stream: {audio_stream}")
            downloaded_path = audio_stream.download(
                output_path=str(self.output_dir),
                filename=f"{safe_filename}_temp"
            )
            
            # Try to convert to MP3 using ffmpeg (optional)
            mp3_path = self.output_dir / f"{safe_filename}.mp3"
            try:
                logger.info(f"Converting to MP3: {mp3_path}")
                subprocess.run([
                    '/opt/homebrew/bin/ffmpeg', '-y', '-i', downloaded_path,
                    '-vn', '-acodec', 'libmp3lame', '-ab', '320k',
                    str(mp3_path)
                ], check=True, capture_output=True)
                
                # Remove temp file
                Path(downloaded_path).unlink(missing_ok=True)
                audio_path = mp3_path
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # ffmpeg not available or failed - keep original format
                logger.warning(f"Could not convert to MP3 (ffmpeg issue): {e}")
                # Rename temp file to final name with proper extension
                ext = Path(downloaded_path).suffix or '.webm'
                final_path = self.output_dir / f"{safe_filename}{ext}"
                Path(downloaded_path).rename(final_path)
                audio_path = final_path
                logger.info(f"Using original format: {audio_path}")
            
            result = {
                'audio_path': str(audio_path),
                'title': title,
                'duration': duration,
                'artist': author,
            }

            logger.info(f"Downloaded: {result['title']}")
            logger.info(f"Saved to: {audio_path}")

            return result

        except Exception as e:
            logger.error(f"Error downloading from YouTube: {e}")
            raise


def download_audio(url: str, output_dir: Path) -> Dict[str, str]:
    """
    Convenience function to download audio from YouTube

    Args:
        url: YouTube video URL
        output_dir: Directory to save audio file

    Returns:
        Dictionary with download results
    """
    downloader = YouTubeDownloader(output_dir)
    return downloader.download(url)


if __name__ == '__main__':
    # Test the downloader
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        result = download_audio(test_url, Path('/tmp/karaoke-test'))
        print(f"Downloaded: {result}")
    else:
        print("Usage: python downloader.py <youtube_url>")
