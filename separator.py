"""
Vocal separation module using Demucs
Separates vocals from instrumental tracks
"""
import logging
import subprocess
from pathlib import Path
from typing import Dict
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VocalSeparator:
    """Separates vocals from audio using Demucs"""

    def __init__(self, output_dir: Path, model: str = 'htdemucs', device: str = 'cpu'):
        """
        Initialize vocal separator

        Args:
            output_dir: Directory to save separated tracks
            model: Demucs model to use (htdemucs, htdemucs_ft, mdx_extra)
            device: Device to use ('cpu' or 'cuda')
        """
        self.output_dir = output_dir
        self.model = model
        self.device = device
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def separate(self, audio_path: str) -> Dict[str, str]:
        """
        Separate vocals from instrumental

        Args:
            audio_path: Path to input audio file

        Returns:
            Dictionary with paths to separated tracks
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting vocal separation with Demucs...")
        logger.info(f"Model: {self.model}, Device: {self.device}")
        logger.info(f"This may take 2-3 minutes for a 4-minute song...")

        try:
            # Run demucs command
            cmd = [
                'demucs',
                '--two-stems', 'vocals',  # Only separate vocals and accompaniment
                '--out', str(self.output_dir),
                '--device', self.device,
                '--name', self.model,
                '--mp3',  # Output as MP3
                '--mp3-bitrate', '320',  # High quality MP3
                str(audio_path)
            ]

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            logger.info("Vocal separation complete!")

            # Find the separated files
            # Demucs creates: output_dir/model_name/audio_filename/vocals.mp3 and no_vocals.mp3
            song_name = audio_path.stem
            separated_dir = self.output_dir / self.model / song_name

            vocals_path = separated_dir / 'vocals.mp3'
            instrumental_path = separated_dir / 'no_vocals.mp3'

            # If mp3 files don't exist, try wav
            if not vocals_path.exists():
                vocals_path = separated_dir / 'vocals.wav'
            if not instrumental_path.exists():
                instrumental_path = separated_dir / 'no_vocals.wav'

            if not instrumental_path.exists():
                raise FileNotFoundError(f"Separated files not found in {separated_dir}")

            return {
                'vocals': str(vocals_path),
                'instrumental': str(instrumental_path),
                'original': str(audio_path)
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Demucs error: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error during separation: {e}")
            raise


def separate_vocals(audio_path: str, output_dir: Path, model: str = 'htdemucs') -> Dict[str, str]:
    """
    Convenience function to separate vocals

    Args:
        audio_path: Path to audio file
        output_dir: Output directory
        model: Demucs model to use

    Returns:
        Dictionary with separated track paths
    """
    separator = VocalSeparator(output_dir, model=model)
    return separator.separate(audio_path)


if __name__ == '__main__':
    # Test the separator
    import sys
    if len(sys.argv) > 1:
        test_audio = sys.argv[1]
        result = separate_vocals(test_audio, Path('/tmp/karaoke-test'))
        print(f"Separated tracks: {result}")
    else:
        print("Usage: python separator.py <audio_file>")
