"""
YouTube audio downloader module
Downloads audio from YouTube videos using yt-dlp
"""
import logging
from pathlib import Path
import yt_dlp
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
        if not output_filename:
            output_filename = '%(title)s'

        output_path = str(self.output_dir / output_filename)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading audio from: {url}")
                info = ydl.extract_info(url, download=True)

                # Get the actual filename that was downloaded
                filename = ydl.prepare_filename(info)
                # Replace video extension with mp3
                audio_path = Path(filename).with_suffix('.mp3')

                result = {
                    'audio_path': str(audio_path),
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'artist': info.get('artist', info.get('uploader', 'Unknown')),
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
