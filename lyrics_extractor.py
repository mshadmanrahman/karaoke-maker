"""
Lyrics extraction module using Whisper
Transcribes audio and extracts timestamped lyrics
"""
import logging
import os

# Ensure ffmpeg is in PATH (for Homebrew on macOS)
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

import whisper
from pathlib import Path
from typing import List, Dict
import json

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    TRANSLITERATION_AVAILABLE = True
except ImportError:
    TRANSLITERATION_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LyricsExtractor:
    """Extracts timestamped lyrics using Whisper"""

    def __init__(self, model_size: str = 'base', language: str = None):
        """
        Initialize lyrics extractor

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (e.g., 'en', 'es'), None for auto-detect
        """
        self.model_size = model_size
        self.language = language
        logger.info(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully")

    def extract(self, audio_path: str) -> Dict:
        """
        Extract timestamped lyrics from audio

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with lyrics and timestamps
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing audio with Whisper...")
        logger.info(f"This may take 1-2 minutes...")

        try:
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                str(audio_path),
                language=self.language,
                word_timestamps=True,
                verbose=False
            )

            # Extract segments with timestamps
            lyrics_data = {
                'full_text': result['text'],
                'language': result['language'],
                'segments': []
            }

            # Detect if we need transliteration based on language
            needs_transliteration = result['language'] in ['bn', 'hi', 'ur', 'pa', 'mr', 'ta', 'te']

            for segment in result['segments']:
                text = segment['text'].strip()

                # Transliterate Indic scripts to Roman if available
                if needs_transliteration and TRANSLITERATION_AVAILABLE:
                    try:
                        # Use IAST first, then clean up diacritics for readable romanization
                        if result['language'] in ['bn', 'as']:
                            text = transliterate(text, sanscript.BENGALI, sanscript.IAST)
                        elif result['language'] in ['hi', 'mr', 'sa']:
                            text = transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
                        elif result['language'] == 'ur':
                            text = transliterate(text, sanscript.URDU, sanscript.IAST)
                        elif result['language'] == 'ta':
                            text = transliterate(text, sanscript.TAMIL, sanscript.IAST)
                        elif result['language'] == 'te':
                            text = transliterate(text, sanscript.TELUGU, sanscript.IAST)

                        # Clean up diacritics for better readability
                        # Remove common diacritical marks
                        text = (text
                            .replace('ā', 'a').replace('ī', 'i').replace('ū', 'u')
                            .replace('ē', 'e').replace('ō', 'o')
                            .replace('ṛ', 'ri').replace('ṝ', 'ri')
                            .replace('ḷ', 'l').replace('ḹ', 'l')
                            .replace('ṃ', 'm').replace('ṁ', 'm').replace('ṅ', 'n')
                            .replace('ñ', 'n').replace('ṇ', 'n').replace('ṭ', 't')
                            .replace('ḍ', 'd').replace('ś', 'sh').replace('ṣ', 'sh')
                            .replace('ḥ', 'h').replace('Ā', 'A').replace('Ī', 'I')
                            .replace('Ū', 'U').replace('Ē', 'E').replace('Ō', 'O')
                            .replace('Ṛ', 'Ri').replace('Ṝ', 'Ri')
                            .replace('Ḷ', 'L').replace('Ḹ', 'L')
                            .replace('Ṃ', 'M').replace('Ṁ', 'M').replace('Ṅ', 'N')
                            .replace('Ñ', 'N').replace('Ṇ', 'N').replace('Ṭ', 'T')
                            .replace('Ḍ', 'D').replace('Ś', 'Sh').replace('Ṣ', 'Sh')
                            .replace('Ḥ', 'H')
                        )

                        logger.debug(f"Transliterated: {segment['text'].strip()} -> {text}")
                    except Exception as e:
                        logger.warning(f"Transliteration failed for segment, using original: {e}")
                        text = segment['text'].strip()
                elif needs_transliteration and not TRANSLITERATION_AVAILABLE:
                    logger.warning("Transliteration needed but indic-transliteration not installed")

                lyrics_data['segments'].append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': text
                })

            logger.info(f"Transcription complete!")
            logger.info(f"Language detected: {result['language']}")
            logger.info(f"Total segments: {len(lyrics_data['segments'])}")
            if needs_transliteration and TRANSLITERATION_AVAILABLE:
                logger.info(f"Applied transliteration for {result['language']}")

            return lyrics_data

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise

    def save_lyrics(self, lyrics_data: Dict, output_path: Path):
        """
        Save lyrics to JSON file

        Args:
            lyrics_data: Lyrics dictionary from extract()
            output_path: Path to save JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(lyrics_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Lyrics saved to: {output_path}")

    def format_for_karaoke(self, lyrics_data: Dict, lines_per_screen: int = 2) -> List[Dict]:
        """
        Format lyrics for karaoke display

        Args:
            lyrics_data: Lyrics dictionary from extract()
            lines_per_screen: Number of lines to show at once

        Returns:
            List of karaoke line dictionaries with timing
        """
        karaoke_lines = []

        for i, segment in enumerate(lyrics_data['segments']):
            karaoke_lines.append({
                'line_number': i,
                'text': segment['text'],
                'start': segment['start'],
                'end': segment['end'],
                'duration': segment['end'] - segment['start']
            })

        logger.info(f"Formatted {len(karaoke_lines)} karaoke lines")
        return karaoke_lines


def extract_lyrics(audio_path: str, model_size: str = 'base') -> Dict:
    """
    Convenience function to extract lyrics

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size

    Returns:
        Dictionary with lyrics and timestamps
    """
    extractor = LyricsExtractor(model_size=model_size)
    return extractor.extract(audio_path)


if __name__ == '__main__':
    # Test the extractor
    import sys
    if len(sys.argv) > 1:
        test_audio = sys.argv[1]
        result = extract_lyrics(test_audio)
        print(f"\nFull text: {result['full_text']}\n")
        print(f"Total segments: {len(result['segments'])}")
        for i, seg in enumerate(result['segments'][:5]):  # Show first 5
            print(f"{i+1}. [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
    else:
        print("Usage: python lyrics_extractor.py <audio_file>")
